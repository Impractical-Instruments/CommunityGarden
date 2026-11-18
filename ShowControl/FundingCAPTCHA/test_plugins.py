"""Tests for Game loading — which Games the kiosk actually plays."""
from __future__ import annotations

import json
from pathlib import Path

import plugins
from levels import Levels

SIZE = (640, 480)

SETTINGS = json.loads((Path(plugins.__file__).parent / "captcha-settings.json").read_text())


def test_load_games_applies_levels_override(tmp_path: Path) -> None:
    """load_games hands the Levels it was given to the game it loaded."""
    p = tmp_path / "private-levels.json"
    p.write_text(json.dumps(
        [{"prompt": "PRIVATE", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1}]
    ))

    games = plugins.load_games(SETTINGS, SIZE, Levels(p))

    assert games, "expected bodycaptcha to load"
    assert [lv.get("prompt") for lv in games[0]._all_levels] == ["PRIVATE"]


def test_load_games_without_override_uses_default() -> None:
    games = plugins.load_games(SETTINGS, SIZE, Levels())

    assert [type(g).__name__ for g in games] == ["BodyCaptchaGame"]
    prompts = [lv.get("prompt") for lv in games[0]._all_levels]
    assert prompts != ["PRIVATE"], "override leaked from a previous test"
    assert prompts, "expected the default level set"
