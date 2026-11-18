"""The kiosk's show loop, driven end to end with no display, camera, network or GL.

The camera, Dashboard port, Arc, screensavers, OSC client and clock are fakes; the
loop is run through `app.main()` and stepped one tick per scripted turn. What is pinned
is what the loop does, so these tests hold across a refactor of how it is organised.
"""
import logging
import sys
import threading
import time
import types

import numpy as np
import pygame
import pytest

import app
from arc import ArcStatus
from settings import with_defaults

SCREEN = (64, 48)
FRAME_SHAPE = (480, 480)          # the camera_roi default
PLAYER_DEPTH_MM = 2000            # inside the default depth slab
DWELL_S = 3.0                     # attract_dwell_s used here; one tick = one second
MIN_FG_PX = 100


def player_frame() -> np.ndarray:
    """A foreground frame with a Player in it: more pixels than min_foreground_pixels."""
    frame = np.zeros(FRAME_SHAPE, dtype=np.uint16)
    frame[:20, :20] = PLAYER_DEPTH_MM                    # 400 px
    return frame


def empty_frame() -> np.ndarray:
    return np.zeros(FRAME_SHAPE, dtype=np.uint16)


class FakeFeed:
    def __init__(self, settings, source):
        self.frame = None
        self.error = None
        self.queue = types.SimpleNamespace(put=lambda msg: None)
        self.started = 0
        self.stopped = 0
        self.reseeds = 0
        self.restarted = threading.Event()
        self.restarts = 0

    def start(self): self.started += 1
    def stop(self): self.stopped += 1
    def reseed(self): self.reseeds += 1

    def restart(self):
        self.restarts += 1
        self.restarted.set()

    def drain(self):
        frame, self.frame = self.frame, None
        return frame


class FakeMonitor:
    def __init__(self, port, commands=None):
        self.commands = commands or {}
        self.statuses: list[dict] = []

    def set_status(self, payload): self.statuses.append(dict(payload))
    def log_handler(self): return logging.NullHandler()
    def start(self): pass


class FakeSaver:
    def __init__(self):
        self.updates = 0
        self.last_fg = "unset"

    def update(self, dt, fg):
        self.updates += 1
        self.last_fg = fg

    def draw(self, surf): pass


class FakeArc:
    """Plays what the test tells it to: `next_status` is returned by every update."""
    def __init__(self, games):
        self.starts = 0
        self.updates = 0
        self.next_status = ArcStatus(intensity=0.5, blewup=False, finished=False)

    def start(self):
        self.starts += 1
        return "FakeGame"

    def update(self, fg, dt):
        self.updates += 1
        return self.next_status

    def draw(self, surf): pass


class FakeFabric:
    def __init__(self, *args):
        self.reports: list[tuple] = []
        self.events: list[str] = []

    def report(self, name, value): self.reports.append((name, value))
    def send_event(self, name): self.events.append(name)


class Rig:
    """Everything a test needs to step the loop and look at what it did."""

    def __init__(self):
        self.feed: FakeFeed
        self.monitor: FakeMonitor
        self.arc: FakeArc
        self.fabric: FakeFabric | None = None
        self.savers = [FakeSaver(), FakeSaver()]
        self.tick_ms = 1000
        self.now = 1000.0
        self.touch_handler = None

    def key(self, key):
        return pygame.event.Event(pygame.KEYDOWN, key=key)

    def http_restart(self):
        self.monitor.commands["/api/restart"]()

    def run(self, script):
        """Run main() until `script` (a generator, one yield per tick) is exhausted."""
        steps = script(self)

        def fake_get():
            try:
                events = next(steps)
            except StopIteration:
                return [pygame.event.Event(pygame.QUIT)]
            return events or []

        pygame.event.get = fake_get
        with pytest.raises(SystemExit):
            app.main()


@pytest.fixture
def rig(monkeypatch):
    r = Rig()
    settings = {"attract_dwell_s": DWELL_S, "min_foreground_pixels": MIN_FG_PX}

    def make_feed(s, source):
        r.feed = FakeFeed(s, source)
        return r.feed

    def make_monitor(port, commands=None):
        r.monitor = FakeMonitor(port, commands)
        return r.monitor

    def make_arc(games):
        r.arc = FakeArc(games)
        return r.arc

    monkeypatch.setattr(sys, "argv", ["app.py", "--mock-camera"])
    monkeypatch.setattr(app, "load_settings", lambda: with_defaults(settings))
    monkeypatch.setattr(app, "CameraFeed", make_feed)
    monkeypatch.setattr(app, "MonitoringServer", make_monitor)
    monkeypatch.setattr(app, "Arc", make_arc)
    monkeypatch.setattr(app, "load_games", lambda settings, levels_path=None: [])
    monkeypatch.setattr(app, "load_screensavers", lambda settings: list(r.savers))

    # Fabric: a configured TreeHouse, a client that records.
    monkeypatch.setattr(app, "_FABRIC_AVAILABLE", True, raising=False)
    monkeypatch.setattr(app, "load_network_config_or_empty",
                        lambda log: {"elements": {"treehouse": {"ip": "fabric.test", "osc_port": 1}}},
                        raising=False)

    def make_fabric(*args):
        r.fabric = FakeFabric(*args)
        return r.fabric

    monkeypatch.setattr(app, "FabricClient", make_fabric, raising=False)

    # No display, no audio, a clock the test owns.
    monkeypatch.setattr(pygame, "init", pygame.font.init)
    monkeypatch.setattr(pygame, "quit", lambda: None)
    monkeypatch.setattr(pygame.display, "Info",
                        lambda: types.SimpleNamespace(current_w=SCREEN[0], current_h=SCREEN[1]))
    monkeypatch.setattr(pygame.display, "set_mode", lambda *a, **k: pygame.Surface(SCREEN))
    monkeypatch.setattr(pygame.display, "set_caption", lambda *a, **k: None)
    monkeypatch.setattr(pygame.display, "flip", lambda: None)
    monkeypatch.setattr(pygame.mouse, "set_visible", lambda v: None)
    monkeypatch.setattr(pygame.event, "get", lambda: [])        # restored by monkeypatch

    class Clock:
        def tick(self, fps):
            r.now += r.tick_ms / 1000.0
            return r.tick_ms

    monkeypatch.setattr(pygame.time, "Clock", Clock)
    monkeypatch.setattr(time, "monotonic", lambda: r.now)
    return r


def states(rig) -> list[str]:
    return [s["state"] for s in rig.monitor.statuses]


def give_player(rig):
    rig.feed.frame = player_frame()


def start_game(rig):
    """Script fragment: feed a Player until the dwell elapses and the game starts."""
    for _ in range(int(DWELL_S) + 1):
        give_player(rig)
        yield


# ── SCREENSAVER → GAME ─────────────────────────────────────────────────────────

def test_starts_as_screensaver_and_reports_it(rig):
    def script(r):
        yield
        assert r.monitor.statuses[0] == {"state": "screensaver"}
        assert r.savers[0].updates + r.savers[1].updates == 1
        assert r.arc.starts == 0
    rig.run(script)


def test_player_after_the_attract_dwell_starts_the_arc(rig):
    def script(r):
        for _ in range(int(DWELL_S) - 1):                   # not long enough yet
            give_player(r)
            yield
        assert r.arc.starts == 0
        give_player(r)
        yield                                               # the dwell is reached on this tick
        assert r.arc.starts == 1
        assert r.monitor.statuses[-1] == {"state": "game"}
        yield
        assert r.arc.updates == 1                           # the next tick plays the Arc
    rig.run(script)


def test_no_player_never_starts_the_arc(rig):
    def script(r):
        for _ in range(int(DWELL_S) * 3):
            r.feed.frame = empty_frame()
            yield
        assert r.arc.starts == 0
    rig.run(script)


def test_player_leaving_during_the_dwell_restarts_the_countdown(rig):
    def script(r):
        for _ in range(int(DWELL_S) - 1):
            give_player(r)
            yield
        r.feed.frame = empty_frame()                        # steps away
        yield
        for _ in range(int(DWELL_S) - 1):                   # comes back: a full dwell again
            give_player(r)
            yield
        assert r.arc.starts == 0
    rig.run(script)


def test_the_player_count_is_reported_with_each_camera_frame(rig):
    def script(r):
        give_player(r)
        yield
        yield
        assert {"state": "screensaver", "fg_pixels": 400} in r.monitor.statuses
    rig.run(script)


def test_a_camera_crash_is_reported_as_an_error_state(rig):
    def script(r):
        yield
        r.feed.error = "usb unplugged"
        yield
        yield
        assert {"state": "error", "error": "usb unplugged"} in r.monitor.statuses
    rig.run(script)


def test_the_screensaver_sees_the_current_foreground(rig):
    def script(r):
        frame = player_frame()
        r.feed.frame = frame
        yield
        yield
        assert any(s.last_fg is frame for s in r.savers)
    rig.run(script)


def test_the_screensaver_rotates_after_its_dwell(rig):
    def script(r):
        yield
        first = next(s for s in r.savers if s.updates)
        other = next(s for s in r.savers if s is not first)
        assert other.updates == 0
        r.tick_ms = 121_000                                 # past SAVER_DWELL in one tick
        yield
        yield
        assert other.updates >= 1
    rig.run(script)


# ── GAME → SCREENSAVER ─────────────────────────────────────────────────────────

def _into_game(r):
    yield from start_game(r)
    yield
    assert r.arc.starts == 1


def test_a_win_returns_to_the_screensaver_without_a_blowup(rig):
    def script(r):
        yield from _into_game(r)
        r.arc.next_status = ArcStatus(intensity=0.2, blewup=False, finished=True)
        yield
        yield
        assert r.monitor.statuses[-1] == {"state": "screensaver"}
        assert r.fabric.events == []
        updates = r.arc.updates
        yield
        assert r.arc.updates == updates                     # no longer ticking the Arc
    rig.run(script)


def test_a_loss_returns_to_the_screensaver_and_sends_one_blowup(rig):
    def script(r):
        yield from _into_game(r)
        r.arc.next_status = ArcStatus(intensity=1.0, blewup=True, finished=True)
        yield
        yield
        yield
        assert r.monitor.statuses[-1] == {"state": "screensaver"}
        assert r.fabric.events == ["blowup"]
    rig.run(script)


def test_a_loss_without_fabric_still_returns_to_the_screensaver(rig, monkeypatch):
    monkeypatch.setattr(app, "_FABRIC_AVAILABLE", False, raising=False)

    def script(r):
        yield from _into_game(r)
        r.arc.next_status = ArcStatus(intensity=1.0, blewup=True, finished=True)
        yield
        yield
        assert r.fabric is None
        assert r.monitor.statuses[-1] == {"state": "screensaver"}
    rig.run(script)


def test_a_different_screensaver_follows_each_arc(rig):
    def script(r):
        yield
        before = next(s for s in r.savers if s.updates)
        yield from start_game(r)
        yield
        r.arc.next_status = ArcStatus(intensity=0.0, blewup=False, finished=True)
        yield
        yield
        yield
        after = next(s for s in r.savers if s is not before)
        assert after.updates >= 1
    rig.run(script)


def test_a_game_goes_on_when_the_player_steps_out_of_view(rig):
    """Leaving the camera does not end an Arc; only the Arc itself finishes (win, loss or its timer)."""
    def script(r):
        yield from _into_game(r)
        for _ in range(5):
            r.feed.frame = empty_frame()
            yield
        assert r.arc.starts == 1
        assert states(r)[-1] != "screensaver"
        assert r.arc.updates >= 5
    rig.run(script)


# ── OSC fabric ─────────────────────────────────────────────────────────────────

def test_intensity_reports_are_throttled_to_ten_hertz(rig):
    def script(r):
        yield from _into_game(r)
        r.tick_ms = 30                                      # ~33 ticks a second
        baseline = len(r.fabric.reports)
        for _ in range(20):                                 # 0.6 s of game
            yield
        sent = len(r.fabric.reports) - baseline
        assert 5 <= sent <= 7, sent
        assert all(name == "intensity" and value == 0.5 for name, value in r.fabric.reports)
    rig.run(script)


def test_no_intensity_is_reported_while_a_screensaver_runs(rig):
    def script(r):
        for _ in range(10):
            yield
        assert r.fabric.reports == []
    rig.run(script)


def test_osc_stays_off_when_the_treehouse_is_not_configured(rig, monkeypatch):
    monkeypatch.setattr(app, "load_network_config_or_empty", lambda log: {}, raising=False)

    def script(r):
        yield from _into_game(r)
        yield
        assert r.fabric is None
    rig.run(script)


# ── Restart ────────────────────────────────────────────────────────────────────

def _assert_clean_screensaver(r):
    """After a restart: the screensaver runs, there is no Player yet, and the dwell starts from zero."""
    arc_updates = r.arc.updates
    saver_updates = sum(s.updates for s in r.savers)
    yield
    assert r.feed.restarted.wait(2), "the camera was not restarted"
    assert r.arc.updates == arc_updates                     # back on the screensaver
    assert sum(s.updates for s in r.savers) > saver_updates
    assert any(s.last_fg is None for s in r.savers)         # the old frame is gone
    starts = r.arc.starts
    for _ in range(int(DWELL_S) - 1):                       # a full dwell is needed again
        give_player(r)
        yield
    assert r.arc.starts == starts
    give_player(r)                                          # and then it does start
    yield
    assert r.arc.starts == starts + 1


def test_http_restart_during_a_game_returns_to_a_clean_screensaver(rig):
    def script(r):
        yield from _into_game(r)
        r.http_restart()
        yield from _assert_clean_screensaver(r)
    rig.run(script)


def test_http_restart_on_the_screensaver_restarts_the_camera_and_the_dwell(rig):
    def script(r):
        for _ in range(int(DWELL_S) - 1):                   # almost there
            give_player(r)
            yield
        r.http_restart()
        yield
        assert r.feed.restarted.wait(2)
        starts = r.arc.starts
        for _ in range(int(DWELL_S) - 1):
            give_player(r)
            yield
        assert r.arc.starts == starts
    rig.run(script)


def test_http_restart_is_handled_once_per_request(rig):
    def script(r):
        yield
        r.http_restart()
        yield
        yield
        yield
        assert r.feed.restarts == 1
    rig.run(script)


def test_the_r_key_reseeds_the_background_and_leaves_the_show_alone(rig):
    def script(r):
        yield from _into_game(r)
        yield [r.key(pygame.K_r)]
        yield
        assert r.feed.reseeds == 1
        assert r.feed.restarts == 0
        assert states(r)[-1] == "game"
        assert r.arc.starts == 1
    rig.run(script)


# ── Quit ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("key", [pygame.K_q, pygame.K_ESCAPE])
def test_q_and_escape_stop_the_camera_and_exit(rig, key):
    def script(r):
        yield
        yield [r.key(key)]
        raise AssertionError("the loop went on after the quit key")
    rig.run(script)
    assert rig.feed.stopped == 1


def test_closing_the_window_stops_the_camera_and_exits(rig):
    def script(r):
        yield
        yield [pygame.event.Event(pygame.QUIT)]
        raise AssertionError("the loop went on after QUIT")
    rig.run(script)
    assert rig.feed.stopped == 1


# ── Startup ────────────────────────────────────────────────────────────────────

def test_startup_starts_the_camera_once_and_the_monitor_gets_the_restart_route(rig):
    def script(r):
        yield
        assert r.feed.started == 1
        assert "/api/restart" in r.monitor.commands
    rig.run(script)
