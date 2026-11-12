"""The encoder bridge: Pico serial lines in, /pipes/knobN/in OSC out, /health (#237)."""
from __future__ import annotations

import json
import logging
import random
import socket
import threading
from pathlib import Path

import pytest
import serial
from fastapi.testclient import TestClient
from pythonosc.osc_message import OscMessage

import encoder_bridge as eb

NETWORK = Path(__file__).resolve().parents[1] / "network.json"


# ── Protocol ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("line, expected", [
    ("/enc 0 3 -2", eb.EncoderEvent(0, 3, -2)),
    ("/enc 1 5 7\r\n", eb.EncoderEvent(1, 5, 7)),
    ("  /enc 0 0 1  ", eb.EncoderEvent(0, 0, 1)),
])
def test_parse_line_reads_the_adr_0014_protocol(line, expected):
    assert eb.parse_line(line) == expected


@pytest.mark.parametrize("line", [
    "", "MicroPython v1.22.0 on 2024-01-01; Raspberry Pi Pico", "/enc 0 3", "/enc 0 3 -2 9",
    "/enc a b c", "/enc 2 0 1",   # board out of range
    "/enc 0 6 1",                 # encoder out of range
    "/enc -1 0 1", "/encx 0 0 1", "enc 0 0 1",
])
def test_parse_line_rejects_anything_else(line):
    assert eb.parse_line(line) is None


def test_knob_is_board_times_six_plus_encoder():
    knobs = [eb.EncoderEvent(b, e, 1).knob for b in range(2) for e in range(6)]
    assert knobs == list(range(12))
    assert eb.EncoderEvent(1, 2, 1).knob == 8


def test_knob_addresses_are_the_contract():
    assert [eb.knob_address(n) for n in (0, 5, 11)] == ["/pipes/knob0/in", "/pipes/knob5/in", "/pipes/knob11/in"]
    with pytest.raises(ValueError):
        eb.knob_address(12)


def test_osc_sender_sends_the_raw_delta_as_a_float_to_the_knob_pipe():
    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.bind(("127.0.0.1", 0))
    rx.settimeout(2)
    try:
        eb.OscSender("127.0.0.1", rx.getsockname()[1])(eb.EncoderEvent(1, 3, -2))
        msg = OscMessage(rx.recv(1024))
    finally:
        rx.close()
    assert msg.address == "/pipes/knob9/in"
    assert msg.params == [-2.0]


# ── State and health ──────────────────────────────────────────────────────────

class Clock:
    def __init__(self) -> None:
        self.t = 100.0

    def __call__(self) -> float:
        return self.t


def test_health_with_nothing_connected():
    assert eb.BridgeState().health(reuben_alive=False) == {
        "ok": False, "picos_connected": 0, "boards": [], "last_event_age_s": None,
        "reuben_alive": False, "fake_encoders": False,
    }


def test_health_is_ok_only_with_both_boards_and_reuben():
    clock = Clock()
    state = eb.BridgeState(clock)
    state.connected("COM3")
    state.connected("COM4")
    state.event("COM3", eb.EncoderEvent(1, 0, 1))
    assert state.health(reuben_alive=True)["ok"] is False      # board 0 not seen yet
    state.event("COM4", eb.EncoderEvent(0, 2, -1))
    clock.t += 3.25
    health = state.health(reuben_alive=True)
    assert health == {"ok": True, "picos_connected": 2, "boards": [0, 1], "last_event_age_s": 3.2,
                      "reuben_alive": True, "fake_encoders": False}
    assert state.health(reuben_alive=False)["ok"] is False


def test_unplugging_a_pico_forgets_its_board():
    state = eb.BridgeState()
    state.connected("COM3")
    state.event("COM3", eb.EncoderEvent(0, 0, 1))
    state.disconnected("COM3")
    health = state.health(reuben_alive=True)
    assert health["picos_connected"] == 0 and health["boards"] == []


def test_health_route_serves_the_state_with_cors():
    state = eb.BridgeState()
    state.connected("COM3")
    client = TestClient(eb.make_app(state, lambda: True, fake_encoders=True))
    resp = client.get("/health", headers={"Origin": "http://192.168.1.10:8000"})
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "*"
    assert resp.json()["picos_connected"] == 1
    assert resp.json()["reuben_alive"] is True
    assert resp.json()["fake_encoders"] is True


def test_tcp_port_open_tells_a_listener_from_nothing():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen()
    port = srv.getsockname()[1]
    try:
        assert eb.tcp_port_open("127.0.0.1", port)
    finally:
        srv.close()
    assert not eb.tcp_port_open("127.0.0.1", port)


# ── Serial reading ────────────────────────────────────────────────────────────

class FakeSerial:
    """Hands out `lines`, then either raises like an unplugged device or sets `stop`."""

    def __init__(self, lines: list[bytes], stop: threading.Event, unplug: bool = True) -> None:
        self.lines = list(lines)
        self.stop = stop
        self.unplug = unplug
        self.closed = False

    def readline(self) -> bytes:
        if self.lines:
            return self.lines.pop(0)
        if self.unplug:
            raise serial.SerialException("device reports readiness to read but returned no data")
        self.stop.set()
        return b""

    def close(self) -> None:
        self.closed = True


def read(lines: list[bytes], unplug: bool = True):
    stop = threading.Event()
    state = eb.BridgeState()
    sent: list[eb.EncoderEvent] = []
    port = FakeSerial(lines, stop, unplug)
    seen_while_open: dict = {}

    def on_event(ev):
        sent.append(ev)
        seen_while_open.update(state.health(reuben_alive=True))

    eb.read_port("COM3", state, on_event, stop, eb.RateLimitedWarning(10), open_serial=lambda p: port)
    return sent, state, port, seen_while_open


def test_reader_forwards_valid_lines_and_skips_the_rest(caplog):
    with caplog.at_level(logging.WARNING, logger="pipes-bridge"):
        sent, *_ = read([b"/enc 0 1 2\r\n", b"garbage\r\n", b"\r\n", b"/enc 1 5 -1\n", b"\xff\xfe\n"])
    assert sent == [eb.EncoderEvent(0, 1, 2), eb.EncoderEvent(1, 5, -1)]
    assert "garbage" in caplog.text


def test_reader_reports_the_port_connected_while_reading():
    _, _, _, health = read([b"/enc 1 0 1\n"])
    assert health["picos_connected"] == 1 and health["boards"] == [1]


def test_an_unplugged_pico_is_closed_and_forgotten(caplog):
    with caplog.at_level(logging.WARNING, logger="pipes-bridge"):
        _, state, port, _ = read([b"/enc 0 0 1\n"], unplug=True)
    assert port.closed
    assert state.health(reuben_alive=True)["picos_connected"] == 0
    assert "Pico lost" in caplog.text


def test_stop_ends_the_reader_cleanly():
    _, state, port, _ = read([b"/enc 0 0 1\n"], unplug=False)
    assert port.closed and state.health(reuben_alive=True)["picos_connected"] == 0


def test_a_port_that_will_not_open_is_skipped(caplog):
    def refuse(p):
        raise serial.SerialException("access denied")

    state = eb.BridgeState()
    with caplog.at_level(logging.WARNING, logger="pipes-bridge"):
        eb.read_port("COM9", state, lambda ev: None, threading.Event(), eb.RateLimitedWarning(10),
                     open_serial=refuse)
    assert "could not open" in caplog.text
    assert state.health(reuben_alive=True)["picos_connected"] == 0


def test_malformed_line_warnings_are_rate_limited(caplog):
    clock = Clock()
    limiter = eb.RateLimitedWarning(10, clock)
    with caplog.at_level(logging.WARNING, logger="pipes-bridge"):
        assert limiter.warn("COM3", "bad %s", 1)
        assert not limiter.warn("COM3", "bad %s", 2)
        assert not limiter.warn("COM3", "bad %s", 3)
        assert limiter.warn("COM4", "bad %s", 4)      # another port has its own limit
        clock.t += 10
        assert limiter.warn("COM3", "bad %s", 5)
    assert [r.getMessage() for r in caplog.records] == [
        "bad 1", "bad 4", "bad 5 (and 2 more since the last warning)",
    ]


# ── Scanning: reconnect without a restart ─────────────────────────────────────

def test_scanner_starts_one_reader_per_pico_and_restarts_it_after_a_replug():
    ports = ["COM3", "COM4"]
    started: list[str] = []
    release = {p: threading.Event() for p in ("COM3", "COM4")}

    def reader(port, state, on_event, stop, malformed):
        started.append(port)
        release[port].wait(5)   # "connected" until released, like a reader blocked in readline

    scanner = eb.PortScanner(eb.BridgeState(), lambda ev: None, threading.Event(),
                             list_ports=lambda: list(ports), reader=reader)
    scanner.scan_once()
    scanner.scan_once()                       # both still reading: nothing new
    assert sorted(started) == ["COM3", "COM4"]

    release["COM3"].set()                     # COM3 unplugged: its reader ends
    scanner._threads["COM3"].join(2)
    release["COM3"] = threading.Event()
    scanner.scan_once()                       # COM3 back: a new reader
    assert sorted(started) == ["COM3", "COM3", "COM4"]
    for ev in release.values():
        ev.set()


def test_pico_ports_filters_by_raspberry_pi_vendor_id(monkeypatch):
    class Info:
        def __init__(self, device, vid):
            self.device, self.vid = device, vid

    monkeypatch.setattr(eb.serial.tools.list_ports, "comports",
                        lambda: [Info("COM5", 0x2E8A), Info("COM1", None), Info("COM7", 0x0403), Info("COM3", 0x2E8A)])
    assert eb.pico_ports() == ["COM3", "COM5"]


# ── Fake encoders ─────────────────────────────────────────────────────────────

def test_fake_encoders_turn_every_knob_in_bursts_with_pauses():
    gen = eb.fake_events(random.Random(1))
    items = [next(gen) for _ in range(3000)]
    events = [e for _, e in items if e is not None]
    pauses = [w for w, e in items if e is None]
    assert {e.knob for e in events} == set(range(12))
    assert all(e.delta != 0 and abs(e.delta) <= 3 for e in events)
    assert pauses and all(0.5 <= w <= 4.0 for w in pauses)


def test_run_fake_encoders_reports_both_fake_boards_and_sends_events():
    stop = threading.Event()
    state = eb.BridgeState()
    sent: list[eb.EncoderEvent] = []

    def on_event(ev):
        sent.append(ev)
        if len(sent) >= 3:
            stop.set()

    eb.run_fake_encoders(state, on_event, stop, seed=2)
    assert len(sent) >= 3
    assert state.health(reuben_alive=False)["picos_connected"] == 2


# ── Config ────────────────────────────────────────────────────────────────────

def test_config_comes_from_network_json():
    pipes = json.loads(NETWORK.read_text())["elements"]["pipes"]
    cfg = eb.load_pipes_config()
    assert cfg == eb.PipesConfig(pipes["http_port"], pipes["reuben_osc_port"], pipes["reuben_structure_port"])


def test_reuben_ports_match_what_reuben_play_binds():
    """`reuben play` has no flags for these ports, so network.json must hold its defaults."""
    reuben = Path(__file__).resolve().parents[2] / "vendor" / "reuben" / "crates"
    osc_rs = reuben / "reuben-native" / "src" / "osc.rs"
    wire_rs = reuben / "reuben-api" / "src" / "engine" / "wire.rs"
    if not osc_rs.exists():
        pytest.skip("vendor/reuben is not checked out")
    cfg = eb.load_pipes_config()
    assert f"pub const DEFAULT_OSC_PORT: u16 = {cfg.reuben_osc_port};" in osc_rs.read_text()
    assert f'DEFAULT_STRUCTURE_ADDR: &str = "127.0.0.1:{cfg.reuben_structure_port}";' in wire_rs.read_text()
