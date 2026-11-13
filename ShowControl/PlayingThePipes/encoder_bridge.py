#!/usr/bin/env python3
"""
Playing the Pipes: encoder bridge. Pico serial lines in, reuben OSC out, plus /health.

The two encoder Picos (ADR-0014) send `/enc BOARD ENC DELTA` text lines over USB
serial. This bridge finds every Pico by its USB vendor ID, reads those lines, and
feeds each knob's detents (knob N = BOARD * 6 + ENC, 0-11) to pipes_control, which
turns them into the values the reuben instrument plays from: grain parameters
and a level per knob, and a level per loop (#177, #238). A 10 ms control loop
sends those to reuben as OSC. The address list in pipes_control is a cross-layer
contract, like /cg/ff/rot: ShowControl/PlayingThePipes/reuben/pipes.json has an
input pipe for each address, and the two must change together.

Which Pico is on which port does not matter: every line carries its board ID. A
Pico unplugged mid-show is picked up again when it comes back, without a restart.

GET /health (CORS open, for the Dashboard) reports:

    ok                  both boards connected and reuben alive
    picos_connected     serial ports open to a Pico (or a fake board)
    boards              board IDs seen on those ports
    last_event_age_s    seconds since the last Pico or fake encoder event, or null
    last_virtual_age_s  seconds since the last virtual turn (POST /control/enc), or null
    last_source         where the last turn came from: pico, fake or virtual (null before any)
    reuben_alive        reuben's structure channel accepts a TCP connection
    fake_encoders       true when --fake-encoders stands in for the Picos
    state               the loop mix state, 0-12 (how busy the pipes are)
    awake_knobs         knobs turned in the last few seconds

Virtual turns never count toward the Pico numbers (picos_connected, boards, ok,
last_event_age_s): health stays about the hardware.

POST /control/enc takes one ADR-0014 line, `/enc BOARD ENC DELTA`, as a text/plain
body: the Dashboard's virtual encoder surface (#263). It goes through parse_line
and the same inject path as the Picos, and mixes with them. It is always open; the
Dashboard page has the arm switch.

GET /state is what the surface draws: the layout (boards, encoders per board),
each knob's awake/level/position, the loop levels and the mix state.

Tuning comes from settings.json beside this file. Ports come from ShowControl/network.json, elements.pipes: http_port (health),
reuben_osc_port (reuben's OSC input) and reuben_structure_port (liveness). The
two reuben ports must equal what `reuben play` binds: its defaults, 9000 and
9124, since play has no flag to change them.

Usage (from the repo root):
  uv run python ShowControl/PlayingThePipes/encoder_bridge.py
  uv run python ShowControl/PlayingThePipes/encoder_bridge.py --fake-encoders   # no hardware
"""

from __future__ import annotations

import argparse
import logging
import random
import re
import socket
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import serial
import serial.tools.list_ports
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pythonosc.udp_client import SimpleUDPClient

from OSCFabric.config import load_network_config
from pipes_control import SETTINGS, ChangeSender, Controller, Settings

log = logging.getLogger("pipes-bridge")

PICO_USB_VID = 0x2E8A  # Raspberry Pi
BOARDS = 2
ENCODERS_PER_BOARD = 6
KNOBS = BOARDS * ENCODERS_PER_BOARD

SCAN_INTERVAL_S = 2.0
MALFORMED_WARN_INTERVAL_S = 10.0

MAX_CONTROL_BODY = 64  # one /enc line, generously

_ENC_LINE = re.compile(r"/enc (\d+) (\d+) (-?\d+)")


# ── Protocol ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EncoderEvent:
    board: int
    enc: int
    delta: int

    @property
    def knob(self) -> int:
        return self.board * ENCODERS_PER_BOARD + self.enc


def parse_line(line: str) -> EncoderEvent | None:
    """One `/enc BOARD ENC DELTA` line, or None if it is not a valid one."""
    m = _ENC_LINE.fullmatch(line.strip())
    if not m:
        return None
    board, enc, delta = (int(g) for g in m.groups())
    if board >= BOARDS or enc >= ENCODERS_PER_BOARD:
        return None
    return EncoderEvent(board, enc, delta)


# ── State ─────────────────────────────────────────────────────────────────────

class BridgeState:
    """What /health reports. Reader threads write it; the health route reads it."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._boards_by_port: dict[str, set[int]] = {}
        self._last_event: float | None = None
        self._last_virtual: float | None = None
        self._last_source: str | None = None

    def connected(self, port: str) -> None:
        with self._lock:
            self._boards_by_port[port] = set()

    def disconnected(self, port: str) -> None:
        with self._lock:
            self._boards_by_port.pop(port, None)

    def event(self, port: str, event: EncoderEvent, source: str = "pico") -> None:
        with self._lock:
            self._boards_by_port.setdefault(port, set()).add(event.board)
            self._last_event = self._clock()
            self._last_source = source

    def virtual_event(self) -> None:
        """A turn from the Dashboard surface: reported apart from the Picos."""
        with self._lock:
            self._last_virtual = self._clock()
            self._last_source = "virtual"

    def health(self, reuben_alive: bool, fake_encoders: bool = False) -> dict:
        with self._lock:
            ports = len(self._boards_by_port)
            boards = sorted(set().union(*self._boards_by_port.values()))
            now = self._clock()
            age = None if self._last_event is None else round(now - self._last_event, 1)
            virtual_age = None if self._last_virtual is None else round(now - self._last_virtual, 1)
            source = self._last_source
        return {
            "ok": len(boards) == BOARDS and reuben_alive,
            "picos_connected": ports,
            "boards": boards,
            "last_event_age_s": age,
            "last_virtual_age_s": virtual_age,
            "last_source": source,
            "reuben_alive": reuben_alive,
            "fake_encoders": fake_encoders,
        }


class RateLimitedWarning:
    """At most one warning per key per interval, counting the ones it held back."""

    def __init__(self, interval_s: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._interval = interval_s
        self._clock = clock
        self._last: dict[str, float] = {}
        self._held: dict[str, int] = {}

    def warn(self, key: str, msg: str, *args: object) -> bool:
        now = self._clock()
        last = self._last.get(key)
        if last is not None and now - last < self._interval:
            self._held[key] = self._held.get(key, 0) + 1
            return False
        held = self._held.pop(key, 0)
        self._last[key] = now
        if held:
            log.warning(msg + " (and %d more since the last warning)", *args, held)
        else:
            log.warning(msg, *args)
        return True


# ── Serial ────────────────────────────────────────────────────────────────────

def pico_ports() -> list[str]:
    """Serial ports whose USB vendor ID is Raspberry Pi's."""
    return sorted(p.device for p in serial.tools.list_ports.comports() if p.vid == PICO_USB_VID)


def read_port(
    port: str,
    state: BridgeState,
    on_event: Callable[[EncoderEvent], None],
    stop: threading.Event,
    malformed: RateLimitedWarning,
    open_serial: Callable[[str], serial.Serial] = lambda p: serial.Serial(p, 115200, timeout=0.5),
) -> None:
    """Read one Pico until it is unplugged or `stop` is set. The scanner restarts
    it when the port comes back."""
    try:
        ser = open_serial(port)
    except (serial.SerialException, OSError) as e:
        log.warning("%s: could not open: %s", port, e)
        return
    log.info("%s: Pico connected", port)
    state.connected(port)
    try:
        while not stop.is_set():
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("ascii", errors="replace").strip()
            if not line:
                continue
            event = parse_line(line)
            if event is None:
                malformed.warn(port, "%s: ignoring line that is not /enc BOARD ENC DELTA: %r", port, line[:80])
                continue
            state.event(port, event)
            on_event(event)
    except (serial.SerialException, OSError) as e:
        log.warning("%s: Pico lost: %s", port, e)
    finally:
        state.disconnected(port)
        try:
            ser.close()
        except Exception:  # closing a port whose device vanished can raise anything
            pass


class PortScanner:
    """Keeps one reader thread running for every Pico port present."""

    def __init__(
        self,
        state: BridgeState,
        on_event: Callable[[EncoderEvent], None],
        stop: threading.Event,
        list_ports: Callable[[], list[str]] = pico_ports,
        reader: Callable[..., None] = read_port,
    ) -> None:
        self._state = state
        self._on_event = on_event
        self._stop = stop
        self._list_ports = list_ports
        self._reader = reader
        self._malformed = RateLimitedWarning(MALFORMED_WARN_INTERVAL_S)
        self._threads: dict[str, threading.Thread] = {}

    def scan_once(self) -> None:
        for port in self._list_ports():
            thread = self._threads.get(port)
            if thread is not None and thread.is_alive():
                continue
            thread = threading.Thread(
                target=self._reader,
                args=(port, self._state, self._on_event, self._stop, self._malformed),
                name=f"pico-{port}",
                daemon=True,
            )
            self._threads[port] = thread
            thread.start()

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                self.scan_once()
            except Exception:
                log.exception("port scan failed")
            self._stop.wait(SCAN_INTERVAL_S)


# ── Fake encoders ─────────────────────────────────────────────────────────────

def fake_events(rng: random.Random) -> Iterator[tuple[float, EncoderEvent | None]]:
    """(seconds to wait, event) forever: a burst of turning on one random knob,
    then a pause (event None), the way visitors turn a valve and let go."""
    while True:
        knob = rng.randrange(KNOBS)
        board, enc = divmod(knob, ENCODERS_PER_BOARD)
        direction = rng.choice((-1, 1))
        for _ in range(rng.randint(5, 40)):
            yield rng.uniform(0.02, 0.06), EncoderEvent(board, enc, direction * rng.randint(1, 3))
        yield rng.uniform(0.5, 4.0), None


def run_fake_encoders(state: BridgeState, on_event: Callable[[EncoderEvent], None],
                      stop: threading.Event, seed: int | None = None) -> None:
    for board in range(BOARDS):
        state.connected(f"fake{board}")
    for wait, event in fake_events(random.Random(seed)):
        if stop.wait(wait):
            return
        if event is not None:
            state.event(f"fake{event.board}", event, source="fake")
            on_event(event)


# ── Control loop ──────────────────────────────────────────────────────────────

def run_control(controller: Controller, send: Callable[[dict[str, float], float], int],
                stop: threading.Event, tick_s: float, clock: Callable[[], float] = time.monotonic) -> None:
    """Tick the controller every tick_s and send what changed, without drifting."""
    next_tick = clock()
    while not stop.is_set():
        now = clock()
        try:
            send(controller.tick(now), now)
        except Exception:
            log.exception("control tick failed")
        next_tick += tick_s
        if next_tick < now:          # fell behind (a stall): skip ahead rather than burst
            next_tick = now + tick_s
        stop.wait(max(0.0, next_tick - clock()))


# ── Health ────────────────────────────────────────────────────────────────────

def tcp_port_open(host: str, port: int, timeout_s: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def make_app(state: BridgeState, reuben_alive: Callable[[], bool], fake_encoders: bool = False,
             status: Callable[[], dict] = dict,
             on_event: Callable[[EncoderEvent], None] = lambda event: None,
             snapshot: Callable[[], dict] = dict) -> FastAPI:
    app = FastAPI()
    # The Dashboard reads and posts to this from another host and port.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"])

    @app.get("/health")
    def health() -> dict:  # sync: the liveness probe blocks briefly, so it runs in the threadpool
        return {**state.health(reuben_alive(), fake_encoders), **status()}

    @app.get("/state")
    def control_state() -> dict:
        return {"layout": {"boards": BOARDS, "encoders_per_board": ENCODERS_PER_BOARD}, **snapshot()}

    @app.post("/control/enc", status_code=204)
    async def control_enc(request: Request) -> Response:
        body = await request.body()
        line = body[:MAX_CONTROL_BODY + 1].decode("ascii", errors="replace")
        event = parse_line(line) if len(body) <= MAX_CONTROL_BODY else None
        if event is None:
            raise HTTPException(400, "body must be one line: /enc BOARD ENC DELTA")
        state.virtual_event()
        on_event(event)
        return Response(status_code=204)

    return app


# ── Main ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PipesConfig:
    http_port: int
    reuben_osc_port: int
    reuben_structure_port: int


def load_pipes_config(network_path: str | Path | None = None) -> PipesConfig:
    pipes = load_network_config(network_path)["elements"]["pipes"]
    return PipesConfig(
        http_port=int(pipes["http_port"]),
        reuben_osc_port=int(pipes["reuben_osc_port"]),
        reuben_structure_port=int(pipes["reuben_structure_port"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Playing the Pipes encoder bridge: Picos → reuben, plus /health")
    parser.add_argument("--fake-encoders", action="store_true",
                        help="generate encoder turns instead of reading the Picos (no hardware needed)")
    parser.add_argument("--reuben-host", default="127.0.0.1",
                        help="where reuben runs (default: this machine)")
    parser.add_argument("--network", default=None, help="network.json path (default: ShowControl/network.json)")
    parser.add_argument("--settings", default=str(SETTINGS), help="tuning (default: settings.json beside this file)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_pipes_config(args.network)
    settings = Settings.load(args.settings)
    controller = Controller(settings)
    client = SimpleUDPClient(args.reuben_host, cfg.reuben_osc_port)
    sender = ChangeSender(lambda addr, v: client.send_message(addr, float(v)), settings)
    state = BridgeState()
    stop = threading.Event()

    def inject(event: EncoderEvent) -> None:
        """The one way detents reach the controller: Picos, fake encoders and the Dashboard."""
        controller.on_detents(event.knob, event.delta, time.monotonic())

    threading.Thread(target=run_control, args=(controller, sender, stop, settings.tick_s),
                     name="control", daemon=True).start()

    if args.fake_encoders:
        worker = threading.Thread(target=run_fake_encoders, args=(state, inject, stop), name="fake-encoders", daemon=True)
    else:
        worker = threading.Thread(target=PortScanner(state, inject, stop).run, name="pico-scan", daemon=True)
    worker.start()

    app = make_app(
        state,
        lambda: tcp_port_open(args.reuben_host, cfg.reuben_structure_port),
        fake_encoders=args.fake_encoders,
        status=controller.status,
        on_event=inject,
        snapshot=controller.snapshot,
    )
    log.info("sending knob and loop values to reuben at %s:%d%s", args.reuben_host,
             cfg.reuben_osc_port, " (fake encoders)" if args.fake_encoders else "")
    log.info("health: http://0.0.0.0:%d/health · virtual encoders: POST /control/enc", cfg.http_port)
    try:
        uvicorn.run(app, host="0.0.0.0", port=cfg.http_port, log_level="warning")
    finally:
        stop.set()


if __name__ == "__main__":
    main()
