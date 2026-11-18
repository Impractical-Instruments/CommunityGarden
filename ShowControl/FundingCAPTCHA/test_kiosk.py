"""Kiosk driven directly: tick by tick on an off-screen surface, no loop, no main()."""
import threading
import types

import numpy as np
import pygame
import pytest

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


@pytest.fixture
def kiosk():
    pygame.font.init()
    settings = with_defaults({"attract_dwell_s": 1.0, "min_foreground_pixels": 10})
    return Kiosk(settings, feed=_Feed(), monitor=_Monitor(), arc=_Arc(), savers=[],
                 screen=pygame.Surface((32, 24)))


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
