"""Tests for Grid letterbox geometry (ADR-0019). Pure arithmetic: no display."""
from __future__ import annotations

import pytest

from games.grid import Grid
from games.shell import top_bar_height


def test_default_top_reserve_is_the_shell_top_bar() -> None:
    g = Grid(1000, 800, 4, 4)
    assert g.top_reserve == top_bar_height(800)


def test_explicit_top_reserve_wins() -> None:
    assert Grid(1000, 800, 4, 4, top_reserve=50).top_reserve == 50


def test_cells_are_square_and_limited_by_the_tighter_axis() -> None:
    # 1000x800, bar 96 -> area 1000x704; 4x4 -> min(250, 176) = 176
    g = Grid(1000, 800, 4, 4)
    assert g.cell_size == 176


def test_wide_area_is_centred_horizontally() -> None:
    g = Grid(1000, 800, 4, 4)
    b = g.bounds_rect
    assert (b.width, b.height) == (704, 704)
    assert b.x == (1000 - 704) // 2
    assert b.y == g.top_reserve


def test_tall_area_is_centred_vertically_below_the_bar() -> None:
    # 400x1000, bar 120 -> area 400x880; 4x4 -> cell 100, grid 400x400
    g = Grid(400, 1000, 4, 4)
    b = g.bounds_rect
    assert g.cell_size == 100
    assert b.x == 0
    assert b.y == g.top_reserve + (880 - 400) // 2


def test_non_square_grid_uses_cols_and_rows_separately() -> None:
    g = Grid(900, 700, 6, 3, top_reserve=100)   # area 900x600; min(150, 200)
    assert g.cell_size == 150
    assert (g.bounds_rect.width, g.bounds_rect.height) == (900, 450)


def test_cell_rects_tile_the_bounds_without_gaps() -> None:
    g = Grid(1000, 800, 5, 3)
    b = g.bounds_rect
    assert g.cell_rect(0, 0).topleft == b.topleft
    last = g.cell_rect(4, 2)
    assert last.bottomright == b.bottomright
    assert g.cell_rect(1, 0).left == g.cell_rect(0, 0).right
    assert g.cell_rect(0, 1).top == g.cell_rect(0, 0).bottom
    assert all(g.cell_rect(c, r).size == (g.cell_size,) * 2
               for c in range(5) for r in range(3))


@pytest.mark.parametrize("w,h,cols,rows", [(1920, 1080, 4, 4), (1080, 1920, 3, 5), (640, 480, 7, 2)])
def test_grid_always_fits_inside_the_area_below_the_bar(w, h, cols, rows) -> None:
    g = Grid(w, h, cols, rows)
    b = g.bounds_rect
    assert b.left >= 0 and b.right <= w
    assert b.top >= g.top_reserve and b.bottom <= h
