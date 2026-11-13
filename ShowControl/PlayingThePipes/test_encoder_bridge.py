"""The encoder bridge: Pico serial lines in, /pipes/knobN/in OSC out, /health (#237),
and the Dashboard's virtual encoders (#263)."""
from __future__ import annotations

import json
import logging
import random
import re
import socket
import threading
from pathlib import Path

import pytest
import serial
from fastapi.testclient import TestClient
from pythonosc.osc_message import OscMessage

import encoder_bridge as eb

NETWORK = Path(__file__).resolve().parents[1] / "network.json"
DASHBOARD_PAGE = Path(__file__).resolve().parents[1] / "Dashboard" / "playingthepipes.html"


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


def test_detents_reach_reuben_as_knob_values_over_osc():
    """A detent goes through the controller and the control loop out as /pipes/knobN/... OSC."""
    import pipes_control as pc

    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.bind(("127.0.0.1", 0))
    rx.settimeout(2)
    from pythonosc.udp_client import SimpleUDPClient
    client = SimpleUDPClient("127.0.0.1", rx.getsockname()[1])
    s = pc.Settings.load()
    ctrl = pc.Controller(s)
    sender = pc.ChangeSender(lambda a, v: client.send_message(a, float(v)), s)
    ctrl.on_detents(eb.EncoderEvent(1, 3, 5).knob, 5, 0.0)
    sender(ctrl.tick(0.01), 0.01)
    got = {}
    try:
        while True:
            m = OscMessage(rx.recv(1024))
            got[m.address] = m.params[0]
    except socket.timeout:
        pass
    finally:
        rx.close()
    assert got["/pipes/knob9/position/in"] > 0.25     # board 1 enc 3 = knob 9, turned forward
    assert got["/pipes/knob9/level/in"] > 0
    assert got["/pipes/knob0/level/in"] == 0.0
    assert "/pipes/loop1/level/in" in got


def test_control_loop_ticks_and_sends_until_stopped():
    stop = threading.Event()
    calls = []

    class Ctrl:
        def tick(self, now):
            return {"/x": now}

    def send(values, now):
        calls.append(values)
        if len(calls) == 5:
            stop.set()
        return 1

    eb.run_control(Ctrl(), send, stop, tick_s=0.001)
    assert len(calls) == 5


def test_control_loop_survives_a_failing_tick(caplog):
    stop = threading.Event()
    n = []

    class Ctrl:
        def tick(self, now):
            n.append(now)
            if len(n) == 3:
                stop.set()
            raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR, logger="pipes-bridge"):
        eb.run_control(Ctrl(), lambda v, t: 0, stop, tick_s=0.001)
    assert len(n) == 3 and "control tick failed" in caplog.text


# ── State and health ──────────────────────────────────────────────────────────

class Clock:
    def __init__(self) -> None:
        self.t = 100.0

    def __call__(self) -> float:
        return self.t


def test_health_with_nothing_connected():
    assert eb.BridgeState().health(reuben_alive=False) == {
        "ok": False, "picos_connected": 0, "boards": [], "last_event_age_s": None,
        "last_virtual_age_s": None, "last_source": None,
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
                      "last_virtual_age_s": None, "last_source": "pico",
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
    client = TestClient(eb.make_app(state, lambda: True, fake_encoders=True,
                                    status=lambda: {"state": 4, "awake_knobs": 2}))
    resp = client.get("/health", headers={"Origin": "http://192.168.1.10:8000"})
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "*"
    assert resp.json()["picos_connected"] == 1
    assert resp.json()["reuben_alive"] is True
    assert resp.json()["fake_encoders"] is True
    assert resp.json()["state"] == 4 and resp.json()["awake_knobs"] == 2


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
    assert state.health(reuben_alive=False)["last_source"] == "fake"


# ── Virtual encoders: the Dashboard surface (#263) ────────────────────────────

def surface_app(state=None, sent=None, reuben_alive=True):
    """The app wired the way main() wires it, around a real controller."""
    import pipes_control as pc

    controller = pc.Controller(pc.Settings.load())
    state = state or eb.BridgeState()
    sent = [] if sent is None else sent

    def inject(event):
        sent.append(event)
        controller.on_detents(event.knob, event.delta, 0.0)

    app = eb.make_app(state, lambda: reuben_alive, status=controller.status,
                      on_event=inject, snapshot=controller.snapshot)
    return TestClient(app), controller, state, sent


def post_enc(client, line):
    return client.post("/control/enc", content=line, headers={"Content-Type": "text/plain"})


def test_a_posted_enc_line_reaches_the_controller_and_goes_out_as_osc():
    import pipes_control as pc

    client, controller, _, sent = surface_app()
    assert post_enc(client, "/enc 1 3 5").status_code == 204
    assert sent == [eb.EncoderEvent(1, 3, 5)]

    out = []
    pc.ChangeSender(lambda a, v: out.append((a, v)), controller.s)(controller.tick(0.01), 0.01)
    got = dict(out)
    assert got["/pipes/knob9/position/in"] > 0.25     # board 1 enc 3 = knob 9, turned forward
    assert got["/pipes/knob9/level/in"] > 0
    assert got["/pipes/knob0/level/in"] == 0.0


@pytest.mark.parametrize("body", [
    "", "garbage", "/enc 2 0 1", "/enc 0 6 1", "/enc 0 0", "/enc 0 0 1\n/enc 0 1 1",
    "/enc 0 0 " + "9" * 80,     # over the size limit
])
def test_a_malformed_or_out_of_range_line_is_refused_and_touches_nothing(body):
    client, controller, state, sent = surface_app()
    before = controller.snapshot()
    assert post_enc(client, body).status_code == 400
    assert sent == []
    assert controller.snapshot() == before
    assert state.health(reuben_alive=True)["last_source"] is None


def test_virtual_turns_stay_out_of_the_pico_health_numbers():
    clock = Clock()
    state = eb.BridgeState(clock)
    client, *_ = surface_app(state=state)
    assert post_enc(client, "/enc 0 0 1").status_code == 204
    assert post_enc(client, "/enc 1 5 -2").status_code == 204
    clock.t += 1.5
    health = client.get("/health").json()
    assert health["picos_connected"] == 0 and health["boards"] == []
    assert health["ok"] is False and health["last_event_age_s"] is None
    assert health["last_virtual_age_s"] == 1.5 and health["last_source"] == "virtual"

    state.event("COM3", eb.EncoderEvent(0, 0, 1))      # a real turn afterwards
    health = client.get("/health").json()
    assert health["last_source"] == "pico" and health["last_event_age_s"] == 0.0
    assert health["last_virtual_age_s"] == 1.5


def test_the_control_route_allows_cross_origin_posts():
    client, *_ = surface_app()
    resp = client.options("/control/enc", headers={
        "Origin": "http://192.168.1.10:8000", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert resp.status_code == 200
    assert "POST" in resp.headers["access-control-allow-methods"]


def test_state_counts_match_the_controller():
    import pipes_control as pc

    client, controller, *_ = surface_app()
    post_enc(client, "/enc 0 2 3")
    controller.tick(0.01)
    snap = client.get("/state").json()
    assert snap["layout"] == {"boards": eb.BOARDS, "encoders_per_board": eb.ENCODERS_PER_BOARD}
    assert len(snap["knobs"]) == len(controller.knobs) == eb.KNOBS
    assert len(snap["loops"]) == pc.LOOPS
    assert snap["max_state"] == controller.s.max_state
    assert snap["knobs"][2]["awake"] is True and snap["knobs"][2]["level"] > 0
    assert snap["knobs"][0] == {"awake": False, "level": 0.0, "position": snap["knobs"][0]["position"]}
    lo, hi = snap["position_range"]
    assert all(lo <= k["position"] <= hi for k in snap["knobs"])


def test_the_dashboard_page_reads_only_fields_the_bridge_returns():
    """Drift guard: playingthepipes.html names /health fields `health.x`, /state fields
    `snap.x`, layout fields `layout.x` and per-knob fields `kv.x`. Each must exist."""
    page = DASHBOARD_PAGE.read_text()
    client, controller, *_ = surface_app()
    health = client.get("/health").json()
    snap = client.get("/state").json()
    sources = {"health": health, "snap": snap, "layout": snap["layout"], "kv": snap["knobs"][0]}
    for name, fields in sources.items():
        used = set(re.findall(rf"\b{name}\.(\w+)", page))
        assert used, f"the page reads no {name}.* fields: has the naming convention changed?"
        missing = used - set(fields)
        assert not missing, f"playingthepipes.html reads {name}.{sorted(missing)}, which the bridge does not return"


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
