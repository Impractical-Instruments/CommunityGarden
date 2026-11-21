"""Kiosk driven directly: tick by tick on an off-screen surface, no loop, no main()."""
import threading
import types

import numpy as np
import pygame
import pytest

from OSCFabric import FabricClient

from arc import ArcStatus
from kiosk import AppState, Kiosk
from settings import with_defaults


class _Feed:
    def __init__(self):
        self.frame, self.error, self.restarted = None, None, threading.Event()
        self.queue = None

    def drain(self):
        frame, self.frame = self.frame, None
        return frame

    def restart(self): self.restarted.set()
    def reseed(self): pass
    def stop(self): pass


class _Monitor:
    def __init__(self): self.statuses = []
    def set_status(self, payload): self.statuses.append(payload)


class _Arc:
    status = ArcStatus(intensity=0.0, blewup=False, finished=False)
    def start(self): return "G"
    def update(self, fg, dt): return self.status
    def draw(self, surf): pass


class _Wire:
    """What reached the TreeHouse: every OSC message, in order, as (address, *args)."""
    def __init__(self): self.sent = []
    def send(self, address, *args): self.sent.append((address, *args))


HEARTBEAT_S = 5.0
DT = 0.125                                                  # exact in binary: 40 ticks are one heartbeat


def _kiosk(fabric=None):
    pygame.font.init()
    settings = with_defaults({"attract_dwell_s": 1.0, "min_foreground_pixels": 10})
    return Kiosk(settings, feed=_Feed(), monitor=_Monitor(), arc=_Arc(), savers=[],
                 screen=pygame.Surface((32, 24)), fabric=fabric)


@pytest.fixture
def kiosk():
    return _kiosk()


@pytest.fixture
def wire():
    return _Wire()


@pytest.fixture
def wired(wire):
    """A Kiosk on a real FabricClient whose transport is the fake `wire`."""
    fabric = FabricClient("captcha", {"heartbeat_interval_s": HEARTBEAT_S, "change_epsilon": 0.01},
                          transport=wire)
    return _kiosk(fabric)


def _player():
    frame = np.zeros((480, 480), dtype=np.uint16)
    frame[:10, :10] = 2000
    return frame


def test_the_attract_dwell_moves_screensaver_to_game(kiosk):
    kiosk.feed.frame = _player()
    kiosk.tick(0.6)
    assert kiosk.state == AppState.SCREENSAVER
    kiosk.tick(0.6)
    assert kiosk.state == AppState.GAME


def test_a_finished_arc_moves_game_to_screensaver(kiosk):
    kiosk.state = AppState.GAME
    kiosk.arc.status = ArcStatus(intensity=0.0, blewup=False, finished=True)
    kiosk.tick(0.1)
    assert kiosk.state == AppState.SCREENSAVER
    assert kiosk.monitor.statuses[-1] == {"state": "screensaver"}


def test_restart_clears_the_state_whichever_way_it_is_asked_for(kiosk):
    for ask in (kiosk.restart, lambda: (kiosk.restart_requested.set(), kiosk.tick(0.1))):
        kiosk.state, kiosk.attract_elapsed = AppState.GAME, 0.7
        kiosk.foreground, kiosk.fg_pixel_count = _player(), 100
        kiosk.feed.restarted.clear()
        ask()
        assert kiosk.feed.restarted.wait(2)
        assert kiosk.state == AppState.SCREENSAVER
        assert kiosk.attract_elapsed == 0.0
        assert kiosk.sil_cache is None
        assert not kiosk.restart_requested.is_set()


# ── OSC Fabric: intensity is sent on change and on a heartbeat (docs/osc-fabric.md) ──

def test_a_constant_intensity_is_sent_again_every_heartbeat_during_a_game(wired, wire):
    wired.state = AppState.GAME
    wired.arc.status = ArcStatus(intensity=0.5, blewup=False, finished=False)
    wired.t_last_osc -= 1.0                                 # the 10 Hz throttle is open
    wired.tick(DT)
    assert wire.sent == [("/captcha/intensity", 0.5)]

    for _ in range(int(2 * HEARTBEAT_S / DT)):             # two heartbeats of game, intensity unchanged
        wired.tick(DT)
    assert wired.state == AppState.GAME
    assert wire.sent == [("/captcha/intensity", 0.5)] * 3


def test_zero_intensity_is_sent_every_heartbeat_through_the_screensaver(wired, wire):
    wired.tick(DT)
    assert wire.sent == [("/captcha/intensity", 0.0)]       # nobody has played yet

    for _ in range(int(2 * HEARTBEAT_S / DT)):
        wired.tick(DT)
    assert wired.state == AppState.SCREENSAVER
    assert wire.sent == [("/captcha/intensity", 0.0)] * 3


@pytest.mark.parametrize("blewup", [True, False])
def test_the_first_intensity_sent_after_an_arc_ends_is_zero(wired, wire, blewup):
    wired.state = AppState.GAME
    wired.arc.status = ArcStatus(intensity=0.9, blewup=False, finished=False)
    wired.t_last_osc -= 1.0
    wired.tick(DT)
    assert wire.sent == [("/captcha/intensity", 0.9)]

    wire.sent.clear()
    wired.arc.status = ArcStatus(intensity=1.0, blewup=blewup, finished=True)
    wired.tick(DT)                                         # the Arc ends inside the throttle interval
    assert wired.state == AppState.SCREENSAVER
    assert wire.sent == ([("/captcha/blowup",)] if blewup else []) + [("/captcha/intensity", 0.0)]

    wire.sent.clear()
    for _ in range(int(HEARTBEAT_S / DT) + 1):
        wired.tick(DT)
    assert wire.sent == [("/captcha/intensity", 0.0)]       # the heartbeat repeats 0


def test_a_restart_mid_arc_drops_intensity_to_zero(wired, wire):
    wired.state = AppState.GAME
    wired.arc.status = ArcStatus(intensity=0.7, blewup=False, finished=False)
    wired.t_last_osc -= 1.0
    wired.tick(DT)

    wire.sent.clear()
    wired.restart_requested.set()
    wired.tick(DT)
    assert wired.feed.restarted.wait(2)
    assert wire.sent == [("/captcha/intensity", 0.0)]
