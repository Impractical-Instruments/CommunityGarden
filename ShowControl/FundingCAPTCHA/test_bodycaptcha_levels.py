"""BodyCaptchaGame's use of its Levels and taunts: fallback, and hot-reload at arc start."""
from __future__ import annotations

import json
from pathlib import Path

from games.bodycaptcha import BodyCaptchaGame, _read_taunts
from levels import DEFAULT_LEVEL, Levels

SIZE = (640, 480)
SETTINGS = json.loads((Path(__file__).parent / "captcha-settings.json").read_text())


# ── _read_taunts ────────────────────────────────────────────────────────────────

def test_read_taunts_good_file(tmp_path: Path):
    p = tmp_path / "taunts.json"
    taunts = ["Too slow!", "Beep boop."]
    p.write_text(json.dumps(taunts))
    assert _read_taunts(p) == taunts


def test_read_taunts_bad_file_returns_none(tmp_path: Path):
    p = tmp_path / "taunts.json"
    p.write_text("nonsense")
    assert _read_taunts(p) is None


# ── BodyCaptchaGame.__init__ fallback diagnostics ───────────────────────────────

def test_init_missing_levels_path_logs_warning_and_falls_back(tmp_path: Path, caplog):
    """A --levels path that does not exist must behave like any other unreadable
    levels file: fall back, log, keep running (spec: never collapse to a
    placeholder level with zero diagnostics)."""
    with caplog.at_level("WARNING", logger="games.bodycaptcha"):
        game = BodyCaptchaGame(SETTINGS, SIZE, Levels(tmp_path / "nope.json"))

    assert "missing/invalid" in caplog.text
    assert game._all_levels == [DEFAULT_LEVEL]


def test_reset_keeps_the_levels_it_was_given_across_repeated_arc_boundaries(tmp_path: Path):
    """The design spec requires the override be honoured 'on initial load and
    across an arc-start hot reload'. reset() -> _reload_data() must keep
    reading the Levels the game was handed every time, not just at
    construction — a regression here (e.g. reset() reading the default file)
    would pass every other test while reverting a live show to the public set
    at the first arc boundary."""
    p = tmp_path / "private-levels.json"
    p.write_text(json.dumps(
        [{"prompt": "PRIVATE", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1}]
    ))

    game = BodyCaptchaGame(SETTINGS, SIZE, Levels(p))
    assert [lv.get("prompt") for lv in game._all_levels] == ["PRIVATE"]

    game.reset()
    assert [lv.get("prompt") for lv in game._all_levels] == ["PRIVATE"]

    game.reset()
    assert [lv.get("prompt") for lv in game._all_levels] == ["PRIVATE"]


def test_reset_keeps_the_loaded_levels_when_the_file_goes_bad(tmp_path: Path):
    p = tmp_path / "levels.json"
    p.write_text(json.dumps(
        [{"prompt": "GOOD", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1}]
    ))
    game = BodyCaptchaGame(SETTINGS, SIZE, Levels(p))

    p.write_text("{ half-pulled")
    game.reset()

    assert [lv.get("prompt") for lv in game._all_levels] == ["GOOD"]


def test_two_games_with_different_levels_do_not_share_a_path(tmp_path: Path):
    """No module-global path: each game reads the Levels it was handed."""
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps([{"prompt": "A", "grid": [2, 2], "valid_cells": [[0, 0]]}]))
    b.write_text(json.dumps([{"prompt": "B", "grid": [2, 2], "valid_cells": [[0, 0]]}]))
    ga = BodyCaptchaGame(SETTINGS, SIZE, Levels(a))
    gb = BodyCaptchaGame(SETTINGS, SIZE, Levels(b))
    ga.reset()
    assert [lv["prompt"] for lv in ga._all_levels] == ["A"]
    assert [lv["prompt"] for lv in gb._all_levels] == ["B"]
