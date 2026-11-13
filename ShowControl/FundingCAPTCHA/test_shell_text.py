"""Tests for the shell's text-fitting helpers (ADR-0019).

Fonts need pygame.font but no display, so nothing here opens a window.
"""
from __future__ import annotations

import pygame
import pytest

from games import shell
from games.shell import fit_prompt_font, wrap_to_width, draw_center_text, hud_font


@pytest.fixture(autouse=True)
def fonts():
    pygame.font.init()
    yield


def test_wrap_keeps_text_that_fits_on_one_line() -> None:
    f = hud_font(20)
    assert wrap_to_width("one two three", f, 10_000) == ["one two three"]


def test_wrap_breaks_between_words_and_every_line_fits() -> None:
    f = hud_font(20)
    text = "the quick brown fox jumps over the lazy dog"
    width = f.size("the quick brown")[0]
    lines = wrap_to_width(text, f, width)
    assert len(lines) > 1
    assert " ".join(lines) == text
    assert all(f.size(ln)[0] <= width for ln in lines)


def test_wrap_puts_an_overlong_word_on_its_own_line() -> None:
    f = hud_font(20)
    lines = wrap_to_width("a supercalifragilisticexpialidocious b", f, 20)
    assert "supercalifragilisticexpialidocious" in lines
    assert " ".join(lines) == "a supercalifragilisticexpialidocious b"


def test_wrap_of_empty_text_is_no_lines() -> None:
    assert wrap_to_width("", hud_font(20), 100) == []


def testfit_prompt_font_fits_the_box() -> None:
    text = "Make a T with your body"
    f = fit_prompt_font(text, 400, 60)
    w, h = f.size(text)
    assert w <= 400 and h <= 60


def testfit_prompt_font_is_the_largest_that_fits() -> None:
    text = "Make a T with your body"
    f = fit_prompt_font(text, 400, 60)
    size = next(s for s in range(8, shell.PROMPT_FONT_CAP + 1) if hud_font(s) is f)
    if size < min(shell.PROMPT_FONT_CAP, 60):
        w, h = hud_font(size + 1).size(text)
        assert w > 400 or h > 60


def test_short_prompt_is_capped_not_a_billboard() -> None:
    f = fit_prompt_font("Hi", 5000, 5000)
    assert f is hud_font(shell.PROMPT_FONT_CAP)


def test_unfittable_prompt_falls_back_to_the_smallest_font() -> None:
    assert fit_prompt_font("a very long prompt indeed", 1, 1) is hud_font(8)


def testfit_prompt_font_is_cached() -> None:
    assert fit_prompt_font("cached", 300, 50) is fit_prompt_font("cached", 300, 50)


def test_draw_center_text_stays_inside_the_area_below_the_bar() -> None:
    surf = pygame.Surface((400, 300))
    surf.fill((0, 0, 0))
    draw_center_text(surf, "Too Slow! You're not a robot.", (255, 0, 0),
                     400, 40, 300, max_font=120)
    lit = [(x, y) for x in range(400) for y in range(300)
           if surf.get_at((x, y))[:3] != (0, 0, 0)]
    assert lit, "text should be drawn"
    assert min(y for _, y in lit) >= 40, "nothing above the top bar line"
    pad = int(400 * 0.08)
    assert min(x for x, _ in lit) >= pad - 1 and max(x for x, _ in lit) <= 400 - pad


def test_draw_center_text_ignores_empty_text() -> None:
    surf = pygame.Surface((100, 100))
    surf.fill((0, 0, 0))
    draw_center_text(surf, "", (255, 255, 255), 100, 10, 100)
    assert surf.get_at((50, 50))[:3] == (0, 0, 0)
