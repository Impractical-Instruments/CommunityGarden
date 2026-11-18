"""Letterboxed square-cell grid geometry for FundingCAPTCHA games (ADR-0019)."""
from __future__ import annotations
import pygame

from games.shell import top_bar_height


class Grid:
    """Letterboxed square-cell grid below the top bar (ADR-0019)."""

    def __init__(self, screen_w: int, screen_h: int,
                 cols: int, rows: int, top_reserve: int | None = None) -> None:
        self.cols = cols
        self.rows = rows
        top = top_bar_height(screen_h) if top_reserve is None else top_reserve
        area_h = screen_h - top
        cell = min(screen_w // cols, area_h // rows)
        gw, gh = cell * cols, cell * rows
        self._gx = (screen_w - gw) // 2
        self._gy = top + (area_h - gh) // 2
        self._cell = cell
        self._top_reserve = top

    @property
    def cell_size(self) -> int:
        return self._cell

    @property
    def top_reserve(self) -> int:
        return self._top_reserve

    @property
    def bounds_rect(self) -> pygame.Rect:
        return pygame.Rect(self._gx, self._gy,
                           self._cell * self.cols,
                           self._cell * self.rows)

    def cell_rect(self, col: int, row: int) -> pygame.Rect:
        return pygame.Rect(
            self._gx + col * self._cell,
            self._gy + row * self._cell,
            self._cell, self._cell,
        )
