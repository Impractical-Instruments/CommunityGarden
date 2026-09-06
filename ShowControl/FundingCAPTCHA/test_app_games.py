"""Tests for Game loading — which Games the kiosk actually plays.

FundingCAPTCHA ships as BodyCaptcha only. `games/body_keepaway.py` and its
Level/taunt data stay in the tree for a future return, so nothing but this
test stops them drifting back into the Arc's rotation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import pygame

import app

# Games size themselves against the live display surface at construction time.
pygame.init()
pygame.display.set_mode((640, 480))

SETTINGS = json.loads((Path(app.__file__).parent / "captcha-settings.json").read_text())


def test_loads_bodycaptcha_only() -> None:
    games = app._load_games(SETTINGS)
    assert [type(g).__name__ for g in games] == ["BodyCaptchaGame"]


def test_load_games_applies_levels_override(tmp_path: Path) -> None:
    """_load_games must set the override on the module it actually loaded —
    importlib gives each load a distinct module object."""
    p = tmp_path / "private-levels.json"
    p.write_text(json.dumps(
        [{"prompt": "PRIVATE", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1}]
    ))

    games = app._load_games(SETTINGS, levels_path=p)

    assert games, "expected bodycaptcha to load"
    assert [lv.get("prompt") for lv in games[0]._all_levels] == ["PRIVATE"]


def test_load_games_without_override_uses_default() -> None:
    games = app._load_games(SETTINGS)

    assert games, "expected bodycaptcha to load"
    prompts = [lv.get("prompt") for lv in games[0]._all_levels]
    assert prompts != ["PRIVATE"], "override leaked from a previous test"
    assert prompts, "expected the default level set"
