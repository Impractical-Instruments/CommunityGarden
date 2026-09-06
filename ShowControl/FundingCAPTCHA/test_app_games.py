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
