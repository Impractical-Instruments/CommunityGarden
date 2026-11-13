"""Tests for the timer-expiry -> blow-up -> done -> "loss" path, and the Blowup effect.

Nothing here opens a display except the one test that draws.
"""
from __future__ import annotations

import json
from pathlib import Path

import pygame
import pytest

from games.blowup import BLOWUP_S, Blowup
from games.bodycaptcha import BodyCaptchaGame, _State
from games.grid import Grid
from levels import Levels

SIZE = (640, 480)
TIMER_S = 2.0
DT = 0.25

SETTINGS = {
    "camera_roi": {"x": 0, "y": 0, "w": 640, "h": 400},
    "depth_slabs": [{"near_mm": 1000, "far_mm": 3000, "slab_id": 0}],
    "cell_activation_threshold": 0.25,
    "bodycaptcha": {"timer_s": TIMER_S, "hold_s": 1.0, "hint_opacity": 0.1},
}


@pytest.fixture
def game(tmp_path: Path) -> BodyCaptchaGame:
    levels = tmp_path / "levels.json"
    levels.write_text(json.dumps([{
        "prompt": "TEST", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1,
    }]))
    return BodyCaptchaGame(SETTINGS, SIZE, Levels(levels))


def run_until(game: BodyCaptchaGame, state: _State, limit_s: float = 60.0):
    t = 0.0
    while game._state != state and t < limit_s:
        game.update(None, DT)
        t += DT
    assert game._state == state


def test_timer_expiry_starts_the_blowup(game) -> None:
    run_until(game, _State.BLOWUP)
    assert game._taunt


def test_no_loss_while_the_blowup_plays(game) -> None:
    run_until(game, _State.BLOWUP)
    intensity, event = game.update(None, DT)
    assert event is None and intensity == 0.0


def test_blowup_finishes_then_reports_loss_every_frame(game) -> None:
    run_until(game, _State.BLOWUP)
    run_until(game, _State.DONE)
    for _ in range(3):
        assert game.update(None, DT) == (0.0, "loss")


def test_loss_arrives_after_timer_plus_blowup(game) -> None:
    t, event = 0.0, None
    while event != "loss" and t < 60:
        _, event = game.update(None, DT)
        t += DT
    assert event == "loss"
    assert TIMER_S + BLOWUP_S <= t <= TIMER_S + BLOWUP_S + 3 * DT


def test_reset_after_loss_plays_again(game) -> None:
    run_until(game, _State.DONE)
    game.reset()
    assert game._state == _State.PLAYING
    _, event = game.update(None, DT)
    assert event is None


def test_blowup_effect_lifecycle() -> None:
    b = Blowup()
    assert not b.done
    b.start(Grid(640, 480, 2, 2))
    assert not b.done
    assert b.particle_count == 40
    b.update(BLOWUP_S / 2)
    assert not b.done
    b.update(BLOWUP_S / 2)
    assert b.done
    assert b.particle_count == 0


def test_blowup_with_no_grid_has_no_particles() -> None:
    b = Blowup()
    b.start(None)
    assert b.particle_count == 0


def test_blowup_draw_paints_particles() -> None:
    b = Blowup()
    b.start(Grid(64, 48, 2, 2, top_reserve=0))
    surf = pygame.Surface((64, 48))
    surf.fill((0, 0, 0))
    b.draw(surf)
    assert any(surf.get_at((x, y))[:3] != (0, 0, 0)
               for x in range(64) for y in range(48))
