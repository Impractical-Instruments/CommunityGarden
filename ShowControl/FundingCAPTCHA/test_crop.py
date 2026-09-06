"""Tests for aspect-preserving crop geometry used by BodyCaptcha level images."""
from __future__ import annotations

import pytest

from crop import crop_rect


# ── No-op: source already matches the destination aspect ────────────────────────

def test_matching_aspect_returns_full_source():
    assert crop_rect(800, 600, 400, 300) == (0, 0, 800, 600)


def test_matching_aspect_ignores_align():
    assert crop_rect(800, 600, 400, 300, "top-left") == (0, 0, 800, 600)


# ── Wide source into a square target: crop horizontally ─────────────────────────

def test_wide_source_center_crops_equally_from_both_sides():
    # 1000x500 into a square: keep 500x500, 500px of slack split evenly.
    assert crop_rect(1000, 500, 300, 300, "center") == (250, 0, 500, 500)


def test_wide_source_left_keeps_the_left_edge():
    assert crop_rect(1000, 500, 300, 300, "left") == (0, 0, 500, 500)


def test_wide_source_right_is_flush_with_the_right_edge():
    assert crop_rect(1000, 500, 300, 300, "right") == (500, 0, 500, 500)


def test_wide_source_top_left_behaves_like_left_on_the_cropped_axis():
    # Vertical anchor is irrelevant when only width is trimmed.
    assert crop_rect(1000, 500, 300, 300, "top-left") == (0, 0, 500, 500)


# ── Tall source into a wide target: crop vertically ─────────────────────────────

def test_tall_source_center_crops_equally_from_top_and_bottom():
    # 600x1000 into 4:3: keep 600x450, 550px of slack split evenly.
    assert crop_rect(600, 1000, 400, 300, "center") == (0, 275, 600, 450)


def test_tall_source_top_keeps_the_top_edge():
    assert crop_rect(600, 1000, 400, 300, "top") == (0, 0, 600, 450)


def test_tall_source_bottom_is_flush_with_the_bottom_edge():
    assert crop_rect(600, 1000, 400, 300, "bottom") == (0, 550, 600, 450)


# ── Fallbacks: a bad level file must never take the show down ───────────────────

def test_align_defaults_to_center():
    assert crop_rect(1000, 500, 300, 300) == crop_rect(1000, 500, 300, 300, "center")


def test_unknown_align_falls_back_to_center():
    assert crop_rect(1000, 500, 300, 300, "sideways") == (250, 0, 500, 500)


def test_none_align_falls_back_to_center():
    assert crop_rect(1000, 500, 300, 300, None) == (250, 0, 500, 500)


def test_non_string_align_falls_back_to_center():
    assert crop_rect(1000, 500, 300, 300, [0.5, 0.5]) == (250, 0, 500, 500)


# ── Rounding: the crop must stay inside the source at every anchor ──────────────

@pytest.mark.parametrize("align", ["top-left", "top", "top-right", "left", "center",
                                   "right", "bottom-left", "bottom", "bottom-right"])
@pytest.mark.parametrize("src", [(1001, 500), (500, 1001), (777, 331), (331, 777)])
def test_crop_stays_within_source_bounds(src, align):
    sw, sh = src
    x, y, w, h = crop_rect(sw, sh, 300, 300, align)
    assert x >= 0 and y >= 0
    assert w > 0 and h > 0
    assert x + w <= sw
    assert y + h <= sh


@pytest.mark.parametrize("align", ["top-left", "center", "bottom-right"])
def test_crop_matches_destination_aspect_within_a_pixel(align):
    x, y, w, h = crop_rect(1001, 331, 400, 300, align)
    assert abs(w / h - 400 / 300) < 0.01


# ── crop_scale: the pygame wrapper ─────────────────────────────────────────────

def _two_tone(w: int, h: int) -> "pygame.Surface":
    """Left half red, right half blue — so the kept region is identifiable."""
    import pygame
    surf = pygame.Surface((w, h))
    surf.fill(RED, pygame.Rect(0, 0, w // 2, h))
    surf.fill(BLUE, pygame.Rect(w // 2, 0, w - w // 2, h))
    return surf


RED  = (255, 0, 0)
BLUE = (0, 0, 255)


def test_crop_scale_returns_the_requested_size():
    from crop import crop_scale
    out = crop_scale(_two_tone(1000, 500), 300, 300, "center")
    assert out.get_size() == (300, 300)


def test_crop_scale_left_keeps_only_the_left_half():
    from crop import crop_scale
    out = crop_scale(_two_tone(1000, 500), 300, 300, "left")
    assert out.get_at((10, 150))[:3] == RED
    assert out.get_at((290, 150))[:3] == RED


def test_crop_scale_right_keeps_only_the_right_half():
    from crop import crop_scale
    out = crop_scale(_two_tone(1000, 500), 300, 300, "right")
    assert out.get_at((10, 150))[:3] == BLUE
    assert out.get_at((290, 150))[:3] == BLUE


def test_crop_scale_matching_aspect_is_a_plain_resize():
    from crop import crop_scale
    out = crop_scale(_two_tone(800, 600), 400, 300, "center")
    assert out.get_size() == (400, 300)
    assert out.get_at((10, 150))[:3] == RED
    assert out.get_at((390, 150))[:3] == BLUE
