"""Editor-side crop alignment: the level field, and the WYSIWYG preview."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import pygame
import pytest

pygame.init()
pygame.display.set_mode((640, 480))

import bodycaptcha_editor as ed

RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)


@pytest.fixture
def editor() -> ed.Editor:
    """An Editor with one level, built without touching the real levels file."""
    e = ed.Editor.__new__(ed.Editor)
    e._levels = [{"prompt": "P", "image": "two_tone.png", "grid": [3, 3],
                  "valid_cells": []}]
    e._idx    = 0
    e._dirty  = False
    e._bg_cache = {}
    e._thumb_cache = {}
    return e


@pytest.fixture
def images_dir(tmp_path: Path, monkeypatch) -> Path:
    # Green stripe on the far left, then red to the midpoint, then blue. Into a
    # square target the kept region is 500px wide, so a centered crop discards
    # the green — which is what tells a crop apart from the old squash-to-fit.
    surf = pygame.Surface((1000, 500))
    surf.fill(GREEN, pygame.Rect(0, 0, 100, 500))
    surf.fill(RED,   pygame.Rect(100, 0, 400, 500))
    surf.fill(BLUE,  pygame.Rect(500, 0, 500, 500))
    pygame.image.save(surf, str(tmp_path / "two_tone.png"))
    monkeypatch.setattr(ed, "_IMAGES", tmp_path)
    return tmp_path


# ── The crop_align field ───────────────────────────────────────────────────────

def test_align_defaults_to_center_when_absent(editor):
    assert editor._align() == "center"


def test_align_reads_the_stored_value(editor):
    editor._lv["crop_align"] = "bottom-right"
    assert editor._align() == "bottom-right"


def test_set_align_stores_the_anchor_and_marks_dirty(editor):
    editor._set_align("top")
    assert editor._lv["crop_align"] == "top"
    assert editor._dirty is True


def test_set_align_center_omits_the_key(editor):
    """Center is the default — writing it would add a key to every level."""
    editor._lv["crop_align"] = "top"
    editor._set_align("center")
    assert "crop_align" not in editor._lv
    assert editor._dirty is True


def test_default_level_has_no_crop_align_key():
    assert "crop_align" not in ed.DEFAULT_LEVEL


# ── The preview ────────────────────────────────────────────────────────────────

def test_get_bg_crops_to_the_requested_size(editor, images_dir):
    bg = editor._get_bg("two_tone.png", 300, 300, "center")
    assert bg.get_size() == (300, 300)


def test_get_bg_honors_alignment(editor, images_dir):
    assert editor._get_bg("two_tone.png", 300, 300, "left").get_at((5, 150))[:3] == GREEN
    assert editor._get_bg("two_tone.png", 300, 300, "left").get_at((290, 150))[:3] == RED
    assert editor._get_bg("two_tone.png", 300, 300, "right").get_at((10, 150))[:3] == BLUE


def test_get_bg_cache_is_keyed_by_alignment(editor, images_dir):
    """Switching anchors must not serve a stale surface from the cache."""
    first  = editor._get_bg("two_tone.png", 300, 300, "left")
    second = editor._get_bg("two_tone.png", 300, 300, "right")
    assert first.get_at((10, 150))[:3] != second.get_at((10, 150))[:3]


def test_get_bg_cache_is_keyed_by_size(editor, images_dir):
    """Changing the grid changes the preview rect — the cache must follow."""
    assert editor._get_bg("two_tone.png", 300, 300, "center").get_size() == (300, 300)
    assert editor._get_bg("two_tone.png", 400, 300, "center").get_size() == (400, 300)


def test_get_bg_missing_image_returns_none(editor, images_dir):
    assert editor._get_bg("nope.png", 300, 300, "center") is None


def test_thumbnails_are_cropped_not_squashed(editor, images_dir):
    """The picker shows the same framing the grid will."""
    thumb = editor._get_thumb("two_tone.png", 100, 100)
    assert thumb.get_size() == (100, 100)
    assert thumb.get_at((5, 50))[:3] == RED    # green stripe cropped off, not squashed in
    assert thumb.get_at((95, 50))[:3] == BLUE


# ── Preview geometry matches the game ──────────────────────────────────────────

def test_preview_rect_matches_the_cell_grid(editor):
    """WYSIWYG: the image occupies exactly the cells, as it does in the game."""
    editor._levels[0]["grid"] = [3, 3]
    cell = editor._cell_size()
    ox, oy = editor._grid_origin()
    assert editor._preview_rect() == pygame.Rect(ox, oy, cell * 3, cell * 3)


def test_preview_rect_follows_a_non_square_grid(editor):
    editor._levels[0]["grid"] = [4, 2]
    cell = editor._cell_size()
    ox, oy = editor._grid_origin()
    assert editor._preview_rect() == pygame.Rect(ox, oy, cell * 4, cell * 2)
