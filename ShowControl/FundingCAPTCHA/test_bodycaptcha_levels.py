"""Tests for bodycaptcha level/taunt hot-reload readers (reset() picks up git-pulled files)."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import pygame
import pytest

from games.bodycaptcha import _read_levels, _read_taunts

# Games size themselves against the live display surface at construction time.
pygame.init()
pygame.display.set_mode((640, 480))


# ── _read_levels ────────────────────────────────────────────────────────────────

def test_read_levels_good_file(tmp_path: Path):
    p = tmp_path / "levels.json"
    levels = [{"prompt": "A", "grid": [3, 3], "valid_cells": [[1, 1]], "difficulty": 1}]
    p.write_text(json.dumps(levels))
    assert _read_levels(p) == levels


def test_read_levels_missing_file_returns_none(tmp_path: Path):
    assert _read_levels(tmp_path / "nope.json") is None


def test_read_levels_malformed_json_returns_none(tmp_path: Path):
    p = tmp_path / "levels.json"
    p.write_text("{ not valid json,,,")  # e.g. half-written during copy
    assert _read_levels(p) is None


def test_read_levels_empty_list_returns_none(tmp_path: Path):
    p = tmp_path / "levels.json"
    p.write_text("[]")
    assert _read_levels(p) is None


def test_read_levels_non_list_returns_none(tmp_path: Path):
    p = tmp_path / "levels.json"
    p.write_text('{"prompt": "not a list"}')
    assert _read_levels(p) is None


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


# ── levels path override ────────────────────────────────────────────────────────

from games.bodycaptcha import get_levels_path, set_levels_path, _LEVELS_DEFAULT


@pytest.fixture(autouse=True)
def _restore_levels_path():
    """Every test in this module leaves the module-level path as it found it."""
    yield
    set_levels_path(None)


def test_default_levels_path_is_unchanged():
    assert get_levels_path() == _LEVELS_DEFAULT


def test_set_levels_path_overrides_default(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    set_levels_path(p)
    assert get_levels_path() == p


def test_set_levels_path_none_restores_default(tmp_path: Path):
    set_levels_path(tmp_path / "private-levels.json")
    set_levels_path(None)
    assert get_levels_path() == _LEVELS_DEFAULT


def test_set_levels_path_accepts_str(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    set_levels_path(str(p))
    assert get_levels_path() == Path(p)


def test_read_levels_follows_override(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    levels = [{"prompt": "P", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1}]
    p.write_text(json.dumps(levels))
    set_levels_path(p)
    assert _read_levels() == levels


def test_read_levels_resolves_override_at_call_time(tmp_path: Path):
    """The override must be read per call, not captured as a default argument —
    _reload_data() calls _read_levels() with no argument at every arc start."""
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps([{"prompt": "A", "grid": [2, 2], "valid_cells": [[0, 0]]}]))
    b.write_text(json.dumps([{"prompt": "B", "grid": [2, 2], "valid_cells": [[0, 0]]}]))
    set_levels_path(a)
    assert _read_levels()[0]["prompt"] == "A"
    set_levels_path(b)
    assert _read_levels()[0]["prompt"] == "B"


def test_read_levels_missing_override_returns_none(tmp_path: Path):
    """A --levels path that does not exist must fall back, never raise."""
    set_levels_path(tmp_path / "nope.json")
    assert _read_levels() is None


def test_read_levels_explicit_arg_still_wins(tmp_path: Path):
    """Existing callers that pass a path explicitly are unaffected by the override."""
    override = tmp_path / "override.json"
    override.write_text(json.dumps([{"prompt": "override"}]))
    explicit = tmp_path / "explicit.json"
    explicit.write_text(json.dumps([{"prompt": "explicit"}]))
    set_levels_path(override)
    assert _read_levels(explicit)[0]["prompt"] == "explicit"


# ── BodyCaptchaGame.__init__ fallback diagnostics ───────────────────────────────

from games.bodycaptcha import BodyCaptchaGame, _DEFAULT_LEVEL  # noqa: E402

SETTINGS = json.loads((Path(__file__).parent / "captcha-settings.json").read_text())


def test_init_missing_levels_path_logs_warning_and_falls_back(tmp_path: Path, caplog):
    """A --levels path that does not exist must behave like any other unreadable
    levels file: fall back, log, keep running (spec: never collapse to a
    placeholder level with zero diagnostics)."""
    set_levels_path(tmp_path / "nope.json")

    with caplog.at_level("WARNING", logger="games.bodycaptcha"):
        game = BodyCaptchaGame(SETTINGS)

    assert "missing/invalid" in caplog.text
    assert game._all_levels == [_DEFAULT_LEVEL]
