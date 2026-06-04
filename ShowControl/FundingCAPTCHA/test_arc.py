"""Tests for the Arc — the central game lifecycle.

The Arc's test surface is exactly what the report promised: drive a Game through
the Arc frame by frame and assert the Blow-Up Signal fires once, win finishes
without it, and an ongoing Arc stays live. No camera, no display.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import numpy as np

from arc import Arc, ArcStatus, ShuffleBag, blend_intensity


class _ScriptedGame:
    """A Game that returns a fixed sequence of (intensity, event) per update."""

    def __init__(self, script: list[tuple[float, str | None]]) -> None:
        self._script = list(script)
        self.reset_calls = 0
        self.drawn = False

    def update(self, foreground, dt):
        return self._script.pop(0)

    def draw(self, surf):
        self.drawn = True

    def reset(self):
        self.reset_calls += 1


# ── ArcStatus mapping ───────────────────────────────────────────────────────

def test_loss_sets_blewup_and_finished():
    arc = Arc([_ScriptedGame([(0.7, "loss")])])
    arc.start()
    status = arc.update(None, 0.1)
    assert status == ArcStatus(intensity=0.7, blewup=True, finished=True)


def test_win_finishes_without_blewup():
    arc = Arc([_ScriptedGame([(0.9, "win")])])
    arc.start()
    status = arc.update(None, 0.1)
    assert status.finished is True
    assert status.blewup is False
    assert status.intensity == 0.9


def test_ongoing_arc_is_not_finished():
    arc = Arc([_ScriptedGame([(0.3, None)])])
    arc.start()
    status = arc.update(None, 0.1)
    assert status.finished is False
    assert status.blewup is False
    assert status.intensity == 0.3


def test_drive_frames_until_blowup_fires_once():
    # Play three live frames, then the Game blows up. blewup fires on exactly
    # the loss tick — the Blow-Up Signal is sent once, not every frame after.
    game = _ScriptedGame([(0.1, None), (0.4, None), (0.8, None), (1.0, "loss")])
    arc  = Arc([game])
    arc.start()
    blewups = [arc.update(None, 0.1).blewup for _ in range(4)]
    assert blewups == [False, False, False, True]


def test_start_selects_and_resets_a_game():
    game = _ScriptedGame([(0.0, None)])
    arc  = Arc([game])
    name = arc.start()
    assert name == "_ScriptedGame"
    assert game.reset_calls == 1


def test_start_falls_back_to_no_game_when_empty():
    arc = Arc([])
    name = arc.start()
    assert name == "_NoGame"
    # _NoGame just idles — never finishes, never blows up.
    status = arc.update(None, 0.1)
    assert status == ArcStatus(intensity=0.0, blewup=False, finished=False)


# ── ShuffleBag ──────────────────────────────────────────────────────────────

def test_shuffle_bag_draws_all_before_repeating():
    bag   = ShuffleBag(["a", "b", "c"])
    first = {bag.next() for _ in range(3)}
    assert first == {"a", "b", "c"}          # whole set drawn, no repeat
    assert bag.next() in {"a", "b", "c"}     # refills on the 4th draw


def test_shuffle_bag_empty_returns_none():
    assert ShuffleBag([]).next() is None


# ── blend_intensity ─────────────────────────────────────────────────────────

def test_blend_intensity_combines_weighted_terms():
    # difficulty 5/5 * 0.4  +  half the timer * 0.6  =  0.4 + 0.3 = 0.7
    assert blend_intensity(5, 5.0, 10.0, 0.4, 0.6) == 0.7


def test_blend_intensity_clamps_to_unit_range():
    assert blend_intensity(10, 100.0, 1.0, 0.4, 0.6) == 1.0
    assert blend_intensity(0, 0.0, 10.0, 0.4, 0.6) == 0.0


def test_blend_intensity_guards_zero_duration():
    # No division-by-zero on a zero-length Game clock.
    assert blend_intensity(0, 1.0, 0.0, 0.4, 0.6) == 1.0
