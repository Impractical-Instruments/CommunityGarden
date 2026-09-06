"""Level images are cropped, not squashed, into the grid bounds (crop_align)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import pygame
import pytest

pygame.init()
pygame.display.set_mode((640, 480))

import games.bodycaptcha as bc

RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)


@pytest.fixture
def images_dir(tmp_path: Path, monkeypatch) -> Path:
    """An images/ dir holding a 1000x500 photo.

    A green stripe on the far left, then red to the midpoint, then blue.
    Into a square target the kept region is 500px wide, so a centered crop
    discards the green entirely — which is what distinguishes a crop from
    the old squash-to-fit (that kept every stripe, just narrower).
    """
    surf = pygame.Surface((1000, 500))
    surf.fill(GREEN, pygame.Rect(0, 0, 100, 500))
    surf.fill(RED,   pygame.Rect(100, 0, 400, 500))
    surf.fill(BLUE,  pygame.Rect(500, 0, 500, 500))
    pygame.image.save(surf, str(tmp_path / "two_tone.png"))
    monkeypatch.setattr(bc, "_IMAGES", tmp_path)
    return tmp_path


def test_load_bg_crops_to_the_requested_aspect(images_dir):
    bg = bc._load_bg("two_tone.png", 300, 300, "center")
    assert bg.get_size() == (300, 300)


def test_load_bg_left_align_keeps_the_left_of_the_photo(images_dir):
    bg = bc._load_bg("two_tone.png", 300, 300, "left")
    assert bg.get_at((5, 150))[:3] == GREEN     # the far-left stripe survives
    assert bg.get_at((290, 150))[:3] == RED     # and blue is cropped away


def test_load_bg_right_align_keeps_the_right_of_the_photo(images_dir):
    bg = bc._load_bg("two_tone.png", 300, 300, "right")
    assert bg.get_at((10, 150))[:3] == BLUE
    assert bg.get_at((290, 150))[:3] == BLUE


def test_load_bg_defaults_to_center(images_dir):
    bg = bc._load_bg("two_tone.png", 300, 300)
    assert bg.get_at((5, 150))[:3] == RED      # green stripe cropped off, not squashed in
    assert bg.get_at((290, 150))[:3] == BLUE


def test_load_bg_missing_image_returns_none(images_dir):
    assert bc._load_bg("nope.png", 300, 300, "center") is None


def test_load_level_passes_crop_align_from_the_level(images_dir, monkeypatch):
    """The level's crop_align must reach _load_bg — not be dropped in the middle."""
    seen: dict = {}
    monkeypatch.setattr(bc, "_load_bg",
                        lambda name, w, h, align=None: seen.update(align=align))
    monkeypatch.setattr(bc, "_make_activator", lambda level, settings: None)
    game = bc.BodyCaptchaGame.__new__(bc.BodyCaptchaGame)
    game._settings = {}
    game._WW, game._WH = 640, 480
    game._load_level({"image": "two_tone.png", "grid": [3, 3], "crop_align": "bottom"})
    assert seen["align"] == "bottom"
