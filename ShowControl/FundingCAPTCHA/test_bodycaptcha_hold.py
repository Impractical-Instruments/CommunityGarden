"""Tests for BodyCaptcha hold accumulation under a noisy Body Grid.

A Player holding a correct pose must be able to win even when depth speckle
trips a spurious cell now and then. `hold_decay_rate` drains `_hold_elapsed`
on a bad frame instead of zeroing it, so one noise frame costs a fraction of
the hold rather than all of it.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import numpy as np
import pygame
import pytest

# Games size themselves against the live display surface at construction time.
pygame.init()
pygame.display.set_mode((640, 480))

from games.bodycaptcha import BodyCaptchaGame, _State, set_levels_path

ROI = {"x": 0, "y": 0, "w": 640, "h": 400}
GRID_COLS, GRID_ROWS = 2, 2
VALID_CELL = (0, 0)
NOISE_CELL = (1, 1)
DEPTH_MM = 2000  # inside the single configured slab

# 1/16 is exact in binary, so frame counts sum to hold_s with no float drift
# and the `== 0.0` clamp assertions below are safe. Close enough to the show's 15 fps.
FPS = 16.0
DT = 1.0 / FPS
HOLD_S = 1.0


SETTINGS = {
    "camera_roi": ROI,
    "depth_slabs": [{"near_mm": 1000, "far_mm": 3000, "slab_id": 0}],
    "cell_activation_threshold": 0.25,
    "bodycaptcha": {"timer_s": 35, "hold_s": HOLD_S, "hint_opacity": 0.1},
}


@pytest.fixture
def game(tmp_path: Path):
    """A BodyCaptchaGame on a deterministic single Level: 2x2 grid, one valid cell."""
    levels = tmp_path / "levels.json"
    levels.write_text(json.dumps([{
        "prompt": "TEST",
        "grid": [GRID_COLS, GRID_ROWS],
        "valid_cells": [list(VALID_CELL)],
        "difficulty": 1,
    }]))
    set_levels_path(levels)
    try:
        yield BodyCaptchaGame(SETTINGS)
    finally:
        set_levels_path(None)


def foreground(*cells: tuple[int, int]) -> np.ndarray:
    """A foreground frame that fully covers each given (col, row) grid cell."""
    fg = np.zeros((ROI["h"], ROI["w"]), dtype=np.uint16)
    for col, row in cells:
        y0 = int(row * ROI["h"] / GRID_ROWS)
        y1 = int((row + 1) * ROI["h"] / GRID_ROWS)
        x0 = int(col * ROI["w"] / GRID_COLS)
        x1 = int((col + 1) * ROI["w"] / GRID_COLS)
        fg[y0:y1, x0:x1] = DEPTH_MM
    return fg


def test_activating_the_valid_cell_alone_accumulates_hold(game) -> None:
    game.update(foreground(VALID_CELL), DT)
    assert game._hold_elapsed == pytest.approx(DT)


def test_uninterrupted_correct_pose_wins_after_hold_s(game) -> None:
    for _ in range(int(HOLD_S * FPS)):
        game.update(foreground(VALID_CELL), DT)

    assert game._state == _State.WIN_FLASH


def test_sustained_wrong_pose_drains_hold_to_zero_without_winning(game) -> None:
    # Build up most of a hold, then hold a wrong pose for a good while.
    for _ in range(int(HOLD_S * FPS) - 1):
        game.update(foreground(VALID_CELL), DT)
    assert game._hold_elapsed > 0

    for _ in range(int(2 * HOLD_S * FPS)):
        game.update(foreground(VALID_CELL, NOISE_CELL), DT)

    assert game._hold_elapsed == 0.0
    assert game._state == _State.PLAYING


def test_hold_never_goes_negative(game) -> None:
    for _ in range(int(5 * HOLD_S * FPS)):
        game.update(foreground(NOISE_CELL), DT)

    assert game._hold_elapsed == 0.0


def test_correct_pose_with_intermittent_speckle_still_wins(game) -> None:
    """The regression that matters.

    A Player nails the pose, but every tenth frame a noise cell trips. Under a
    hard reset this is arithmetically unwinnable — the hold never survives the
    16 consecutive clean frames it needs. With decay, nine good frames gain
    more than the tenth bad one drains, so the hold makes net progress.
    """
    for frame in range(int(6 * HOLD_S * FPS)):
        speckled = (frame % 10 == 9)
        cells = (VALID_CELL, NOISE_CELL) if speckled else (VALID_CELL,)
        game.update(foreground(*cells), DT)
        if game._state == _State.WIN_FLASH:
            break

    assert game._state == _State.WIN_FLASH, (
        "correct pose with 1-in-10 speckle should still reach a win"
    )


def test_decay_rate_is_configurable_per_level(tmp_path: Path) -> None:
    """hold_decay_rate follows the timer_s / hold_s / hint_opacity override pattern."""
    levels = tmp_path / "levels.json"
    levels.write_text(json.dumps([{
        "prompt": "TEST",
        "grid": [GRID_COLS, GRID_ROWS],
        "valid_cells": [list(VALID_CELL)],
        "difficulty": 1,
        "hold_decay_rate": 0.5,
    }]))
    set_levels_path(levels)
    try:
        settings = dict(SETTINGS)
        settings["bodycaptcha"] = dict(SETTINGS["bodycaptcha"], hold_decay_rate=9.0)
        g = BodyCaptchaGame(settings)

        assert g._hold_decay_rate == 0.5, "per-level value must beat the default"
    finally:
        set_levels_path(None)


def test_decay_rate_falls_back_to_settings_default(game) -> None:
    """With no per-level override, the bodycaptcha defaults block supplies it."""
    assert game._hold_decay_rate == 3.0
