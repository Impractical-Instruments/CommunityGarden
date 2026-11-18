"""The editor's screen geometry, and a draw smoke test of every screen."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import pygame
import pytest

import bodycaptcha_editor as ed
from editor import views
from editor.theme import GRID_W, H, W
from levels import Levels


# ── Preview geometry matches the game (pure: no surface) ───────────────────────

def test_preview_rect_matches_the_cell_grid():
    """WYSIWYG: the image occupies exactly the cells, as it does in the game."""
    cell = views.cell_size(3, 3)
    ox, oy = views.grid_origin(3, 3)
    assert views.preview_rect(3, 3) == pygame.Rect(ox, oy, cell * 3, cell * 3)


def test_preview_rect_follows_a_non_square_grid():
    cell = views.cell_size(4, 2)
    ox, oy = views.grid_origin(4, 2)
    assert views.preview_rect(4, 2) == pygame.Rect(ox, oy, cell * 4, cell * 2)


def test_px_to_cell_finds_the_cell_under_a_pixel():
    rect = views.cell_rect(4, 3, 2, 1)
    assert views.px_to_cell(4, 3, *rect.center) == (2, 1)
    assert views.px_to_cell(4, 3, GRID_W + 5, 5) is None


def test_thumbnails_tile_the_grid_area_and_can_be_hit():
    names = [f"img{i}.png" for i in range(10)]
    rects = views.thumb_rects(names)
    assert [n for n, _ in rects] == names
    assert all(r.right <= GRID_W and r.bottom <= H for _, r in rects)
    name, rect = rects[5]
    assert views.px_to_image(names, *rect.center) == name


def test_no_images_means_no_thumbnails():
    assert views.thumb_rects([]) == []
    assert views.px_to_image([], 10, 10) is None


def test_image_cache_asks_for_a_missing_photo_only_once():
    calls = []

    class Missing:
        def background(self, name, w, h, align=None):
            calls.append(name)
            return None

    cache = views.ImageCache(Missing())
    for _ in range(3):
        assert cache.thumb("gone.png", 10, 10) is None
        assert cache.bg("gone.png", 10, 10, "center") is None
    assert calls == ["gone.png", "gone.png"]      # once as a thumb, once as a background


# ── Draw smoke test ────────────────────────────────────────────────────────────

@pytest.fixture
def editor(tmp_path: Path, monkeypatch) -> ed.Editor:
    """An Editor on an off-screen surface (pygame.SCALED needs a renderer CI lacks)."""
    p = tmp_path / "levels.json"
    p.write_text('[{"prompt": "P", "image": null, "grid": [2, 2], "valid_cells": [[0, 0]]}]')
    monkeypatch.setattr(pygame.display, "set_mode", lambda *a, **k: pygame.Surface((W, H)))
    monkeypatch.setattr(pygame.display, "set_caption", lambda title: None)
    return ed.Editor(Levels(p, images=tmp_path))


def test_every_screen_draws(editor):
    editor._grid.draw()
    editor._picker.draw()
    targets = editor._sidebar.draw()
    assert targets, "the sidebar registers click targets"


def test_editor_init_applies_the_caption(tmp_path: Path, monkeypatch):
    """Real assertion that __init__ actually hands the caption to pygame."""
    p = tmp_path / "private-levels.json"
    p.write_text('[{"prompt": "P", "image": null, "grid": [2, 2], "valid_cells": []}]')
    monkeypatch.setattr(pygame.display, "set_mode", lambda *a, **k: pygame.Surface((W, H)))
    captions: list[str] = []
    monkeypatch.setattr(pygame.display, "set_caption", captions.append)

    ed.Editor(Levels(p))
    assert captions and str(p) in captions[0]


def test_caption_names_the_default_levels_path():
    assert str(Levels().path) in ed.caption(Levels())


def test_a_click_on_a_sidebar_target_runs_its_action(editor):
    editor._targets = editor._sidebar.draw()
    next_btn = [r for r, _ in editor._targets if r.x > GRID_W][1]
    editor._on_click(next_btn.center)           # NEXT >: single level wraps to itself
    assert editor.model.idx == 0


def test_clicking_a_cell_toggles_it(editor):
    rect = views.cell_rect(2, 2, 1, 1)
    editor._on_click(rect.center)
    assert editor.model.valid_cells == {(0, 0), (1, 1)}
    assert editor.model.dirty


def test_save_commits_a_prompt_being_typed(editor):
    editor.edit_prompt()
    editor.ui.buf = "Typed"
    editor.save()
    assert editor.model.level["prompt"] == "Typed"
    assert editor.ui.editing is False
    assert editor.model.dirty is False
