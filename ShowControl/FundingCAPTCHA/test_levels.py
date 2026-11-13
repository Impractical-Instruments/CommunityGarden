"""levels.py: the levels file, the default level, and level photos."""
from __future__ import annotations

import json
from pathlib import Path

import pygame
import pytest

import levels as lv
from levels import DEFAULT_LEVEL, Levels, load_image, read_levels, write_levels

RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)


# ── read_levels ─────────────────────────────────────────────────────────────────

def test_read_levels_good_file(tmp_path: Path):
    p = tmp_path / "levels.json"
    levels = [{"prompt": "A", "grid": [3, 3], "valid_cells": [[1, 1]], "difficulty": 1}]
    p.write_text(json.dumps(levels))
    assert read_levels(p) == levels


def test_read_levels_missing_file_returns_none(tmp_path: Path):
    assert read_levels(tmp_path / "nope.json") is None


def test_read_levels_malformed_json_returns_none(tmp_path: Path):
    p = tmp_path / "levels.json"
    p.write_text("{ not valid json,,,")  # e.g. half-written during copy
    assert read_levels(p) is None


def test_read_levels_empty_list_returns_none(tmp_path: Path):
    p = tmp_path / "levels.json"
    p.write_text("[]")
    assert read_levels(p) is None


def test_read_levels_non_list_returns_none(tmp_path: Path):
    p = tmp_path / "levels.json"
    p.write_text('{"prompt": "not a list"}')
    assert read_levels(p) is None


# ── write_levels ────────────────────────────────────────────────────────────────

def test_write_levels_sorts_by_image_then_prompt(tmp_path: Path):
    p = tmp_path / "levels.json"
    write_levels(p, [{"prompt": "b", "image": "z.png"}, {"prompt": "a", "image": "z.png"},
                     {"prompt": "c", "image": None}])
    assert [(x["prompt"]) for x in json.loads(p.read_text())] == ["c", "a", "b"]


def test_write_levels_creates_a_missing_parent_directory(tmp_path: Path):
    """A typoed --levels path (missing parent dir) must not crash the editor on save."""
    p = tmp_path / "shwo" / "levels.json"
    write_levels(p, [{"prompt": "P"}])
    assert json.loads(p.read_text())[0]["prompt"] == "P"


def test_write_levels_round_trips_through_read_levels(tmp_path: Path):
    p = tmp_path / "levels.json"
    levels = [{"prompt": "P", "image": None, "grid": [2, 2], "valid_cells": []}]
    write_levels(p, levels)
    assert read_levels(p) == levels


# ── Levels ──────────────────────────────────────────────────────────────────────

def test_levels_defaults_to_the_public_levels_file():
    assert Levels().path == lv.DEFAULT_LEVELS_PATH


def test_levels_accepts_str_and_path(tmp_path: Path):
    assert Levels(str(tmp_path / "a.json")).path == tmp_path / "a.json"
    assert Levels(tmp_path / "a.json").path == tmp_path / "a.json"


def test_levels_reads_and_writes_its_own_path_only(tmp_path: Path):
    """Saving a private set must never touch the public levels file."""
    a, b = Levels(tmp_path / "a.json"), Levels(tmp_path / "b.json")
    a.write([{"prompt": "A"}])
    assert a.read() == [{"prompt": "A"}]
    assert b.read() is None


def test_levels_reads_the_file_afresh_every_call(tmp_path: Path):
    """The game re-reads at each arc start: an edit on disk must show up."""
    p = tmp_path / "levels.json"
    levels = Levels(p)
    p.write_text(json.dumps([{"prompt": "1"}]))
    assert levels.read()[0]["prompt"] == "1"
    p.write_text(json.dumps([{"prompt": "2"}]))
    assert levels.read()[0]["prompt"] == "2"


def test_image_names_lists_photos_as_sorted_relative_paths(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    for name in ("b.png", "a.JPG", "sub/c.webp", "notes.txt"):
        (tmp_path / name).write_bytes(b"x")
    assert Levels(images=tmp_path).image_names() == ["a.JPG", "b.png", "sub/c.webp"]


def test_default_level_has_no_crop_align_key():
    assert "crop_align" not in DEFAULT_LEVEL


def test_default_level_is_winnable():
    """A level with no valid cells is 'won' by standing still."""
    assert DEFAULT_LEVEL["valid_cells"]


# ── Photos ──────────────────────────────────────────────────────────────────────
# Loading a photo converts it to the display's pixel format, so these need a
# display (SDL's dummy driver under test).

@pytest.fixture
def images_dir(tmp_path: Path, display) -> Path:
    """A 1000x500 photo: green stripe far left, red to the midpoint, then blue.

    Into a square target the kept region is 500px wide, so a centered crop
    discards the green — which is what tells a crop apart from squash-to-fit.
    """
    surf = pygame.Surface((1000, 500))
    surf.fill(GREEN, pygame.Rect(0, 0, 100, 500))
    surf.fill(RED,   pygame.Rect(100, 0, 400, 500))
    surf.fill(BLUE,  pygame.Rect(500, 0, 500, 500))
    pygame.image.save(surf, str(tmp_path / "two_tone.png"))
    return tmp_path


def test_background_left_align_keeps_the_left_of_the_photo(images_dir):
    bg = Levels(images=images_dir).background("two_tone.png", 300, 300, "left")
    assert bg.get_at((5, 150))[:3] == GREEN     # the far-left stripe survives
    assert bg.get_at((290, 150))[:3] == RED     # and blue is cropped away


def test_background_right_align_keeps_the_right(images_dir):
    bg = Levels(images=images_dir).background("two_tone.png", 300, 300, "right")
    assert bg.get_at((10, 150))[:3] == BLUE


def test_background_is_cropped_not_squashed_without_an_align(images_dir):
    thumb = Levels(images=images_dir).background("two_tone.png", 100, 100)
    assert thumb.get_size() == (100, 100)
    assert thumb.get_at((5, 50))[:3] == RED     # green stripe cropped off, not squashed in
    assert thumb.get_at((95, 50))[:3] == BLUE


def test_background_missing_image_returns_none(images_dir):
    assert Levels(images=images_dir).background("nope.png", 300, 300, "center") is None


def test_background_no_name_returns_none(images_dir):
    assert Levels(images=images_dir).background(None, 300, 300) is None


def test_load_image_refuses_a_git_lfs_pointer(tmp_path: Path, display):
    p = tmp_path / "photo.jpg"
    p.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:0\nsize 1\n")
    with pytest.raises(RuntimeError, match="Git LFS"):
        load_image(p)


def test_background_survives_a_git_lfs_pointer(tmp_path: Path, display):
    (tmp_path / "photo.jpg").write_text("version https://git-lfs.github.com/spec/v1\n")
    assert Levels(images=tmp_path).background("photo.jpg", 10, 10) is None
