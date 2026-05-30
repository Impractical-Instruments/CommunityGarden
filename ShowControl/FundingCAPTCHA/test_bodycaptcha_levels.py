"""Tests for bodycaptcha level/taunt hot-reload readers (reset() picks up git-pulled files)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from games.bodycaptcha import _read_levels, _read_taunts


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
