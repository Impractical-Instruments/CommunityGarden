"""Shared pygame grid, tap detection, and HUD helpers for FundingCAPTCHA games."""
from __future__ import annotations
import pygame

BLACK    = (  0,   0,   0)
WHITE    = (255, 255, 255)
DK_GREY  = ( 28,  28,  28)
MID_GREY = ( 75,  75,  75)
LT_GREY  = (140, 140, 140)
GREEN    = (  0, 200,  75)
YELLOW   = (240, 200,   0)
CYAN     = (  0, 200, 220)
ORANGE   = (240, 130,   0)
RED      = (220,  50,  50)
BLUE     = ( 60, 130, 220)

SUCCESS_COLOR   = GREEN
WRONG_COLOR     = RED
WARN_COLOR      = YELLOW
DANGER_COLOR    = RED
HIT_COLOR       = GREEN
MISS_COLOR      = RED
HIGHLIGHT_COLOR = CYAN

HUD_W    = 220
CELL_PAD = 4


class Grid:
    """Letterboxed cell grid occupying the left portion of the screen."""

    def __init__(self, screen_w: int, screen_h: int,
                 cols: int, rows: int, hud_width: int = HUD_W) -> None:
        self.cols     = cols
        self.rows     = rows
        self.hud_rect = pygame.Rect(screen_w - hud_width, 0, hud_width, screen_h)

        game_w = screen_w - hud_width
        cell   = min(game_w // cols, screen_h // rows)
        gw, gh = cell * cols, cell * rows
        self._gx   = (game_w - gw) // 2
        self._gy   = (screen_h - gh) // 2
        self._cell = cell
        self._flashes: dict[tuple[int, int], tuple] = {}

    @property
    def cell_size(self) -> int:
        return self._cell

    def cell_rect(self, col: int, row: int) -> pygame.Rect:
        return pygame.Rect(
            self._gx + col * self._cell,
            self._gy + row * self._cell,
            self._cell, self._cell,
        )

    def inner_rect(self, col: int, row: int) -> pygame.Rect:
        return self.cell_rect(col, row).inflate(-CELL_PAD * 2, -CELL_PAD * 2)

    def blob_to_cell(self, blob: dict, projector,
                     max_plane_dist: float) -> tuple[int, int] | None:
        xyz = [blob["x"], blob["y"], blob["z"]]
        if not projector.in_bounds_3d(xyz, max_plane_dist):
            return None
        u, v = projector.project(xyz)
        return projector.uv_to_cell(u, v, self.cols, self.rows)

    def flash(self, col: int, row: int,
              color: tuple, duration_ms: int, alpha: int = 160) -> None:
        self._flashes[(col, row)] = (color, pygame.time.get_ticks() + duration_ms, alpha)

    def draw_background(self, surf: pygame.Surface,
                        fill: tuple = DK_GREY, border: tuple = MID_GREY) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                pygame.draw.rect(surf, fill,   self.cell_rect(c, r))
                pygame.draw.rect(surf, border, self.cell_rect(c, r), 1)

    def draw_flashes(self, surf: pygame.Surface) -> None:
        now  = pygame.time.get_ticks()
        dead = []
        tile = pygame.Surface((self._cell, self._cell), pygame.SRCALPHA)
        for (c, r), (color, expiry, alpha) in list(self._flashes.items()):
            if now >= expiry:
                dead.append((c, r))
                continue
            tile.fill((*color, alpha))
            surf.blit(tile, self.cell_rect(c, r).topleft)
        for k in dead:
            del self._flashes[k]

    def draw_hud_bg(self, surf: pygame.Surface) -> None:
        pygame.draw.rect(surf, (18, 18, 18), self.hud_rect)
        pygame.draw.line(surf, MID_GREY,
                         self.hud_rect.topleft, self.hud_rect.bottomleft, 1)

    def blit_cell(self, surf: pygame.Surface,
                  img: pygame.Surface, col: int, row: int) -> None:
        r = self.inner_rect(col, row)
        surf.blit(pygame.transform.scale(img, (r.w, r.h)), r.topleft)


class TapTracker:
    """Edge-detects new blob IDs as discrete taps."""

    def __init__(self) -> None:
        self._prev: set[int] = set()

    def update(self, active_ids: set[int]) -> set[int]:
        new = active_ids - self._prev
        self._prev = set(active_ids)
        return new

    def reset(self) -> None:
        self._prev = set()


def hud_font(size: int = 20) -> pygame.font.Font:
    return pygame.font.SysFont("monospace", size, bold=True)


def draw_hud_label(surf: pygame.Surface, font: pygame.font.Font,
                   label: str, value: str, x: int, y: int,
                   value_color: tuple = WHITE) -> int:
    """Draw label + value. Returns y below the row."""
    lbl = font.render(label, True, LT_GREY)
    val = font.render(value, True, value_color)
    surf.blit(lbl, (x + 8, y))
    surf.blit(val, (x + 8, y + lbl.get_height() + 2))
    return y + lbl.get_height() + val.get_height() + 14


def draw_progress_bar(surf: pygame.Surface,
                      x: int, y: int, w: int, h: int,
                      pct: float, color: tuple = GREEN) -> None:
    pygame.draw.rect(surf, MID_GREY, (x, y, w, h))
    pygame.draw.rect(surf, color,    (x, y, max(0, int(w * pct)), h))
    pygame.draw.rect(surf, WHITE,    (x, y, w, h), 1)
