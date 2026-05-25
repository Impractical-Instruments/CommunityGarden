"""Shared pygame grid and Game-UI shell helpers for FundingCAPTCHA games (ADR-0019)."""
from __future__ import annotations
import math
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

CELL_PAD = 4

# Shell layout (ADR-0019)
TOP_BAR_FRACTION = 0.12        # 12% of screen height
PROMPT_FONT_CAP  = 72          # max prompt font size — short prompts don't become billboards
TIMER_FONT_SIZE  = 32
TIMER_PAD        = 16          # right-edge padding for timer text
HOLD_RING_COLOR  = (0, 255, 130)
HOLD_RING_THICK  = 12          # perimeter ring thickness in pixels
HOLD_RING_INSET  = 2           # inset from grid bounds


def top_bar_height(screen_h: int) -> int:
    return int(screen_h * TOP_BAR_FRACTION)


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
        self._flashes: dict[tuple[int, int], tuple] = {}

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

    def inner_rect(self, col: int, row: int) -> pygame.Rect:
        return self.cell_rect(col, row).inflate(-CELL_PAD * 2, -CELL_PAD * 2)

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

    def blit_cell(self, surf: pygame.Surface,
                  img: pygame.Surface, col: int, row: int) -> None:
        r = self.inner_rect(col, row)
        surf.blit(pygame.transform.scale(img, (r.w, r.h)), r.topleft)


def hud_font(size: int = 20) -> pygame.font.Font:
    return pygame.font.SysFont("monospace", size, bold=True)


# ── Shell rendering (ADR-0019) ────────────────────────────────────────────────


def _fit_prompt_font(text: str, max_w: int, max_h: int) -> pygame.font.Font:
    """Largest monospace-bold font that fits text on one line within max_w × max_h."""
    if not text:
        return hud_font(min(PROMPT_FONT_CAP, max(8, max_h)))
    lo, hi = 8, min(PROMPT_FONT_CAP, max(8, max_h))
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        f   = hud_font(mid)
        w, h = f.size(text)
        if w <= max_w and h <= max_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return hud_font(best)


def draw_top_bar(surf: pygame.Surface,
                 screen_w: int, bar_h: int,
                 prompt: str,
                 time_remaining: float | None,
                 *,
                 timer_warn_s: float = 10.0) -> None:
    """Shared shell top bar: centered prompt + top-right timer (ADR-0019)."""
    pygame.draw.rect(surf, BLACK, (0, 0, screen_w, bar_h))

    timer_reserve = 0
    if time_remaining is not None:
        font_t = hud_font(TIMER_FONT_SIZE)
        color  = RED if time_remaining <= timer_warn_s else GREEN
        label  = f"{int(max(0.0, time_remaining))}s"
        t_surf = font_t.render(label, True, color)
        tx     = screen_w - t_surf.get_width() - TIMER_PAD
        ty     = (bar_h - t_surf.get_height()) // 2
        surf.blit(t_surf, (tx, ty))
        timer_reserve = t_surf.get_width() + TIMER_PAD * 2

    if prompt:
        avail_w = max(40, screen_w - 2 * timer_reserve)
        avail_h = int(bar_h * 0.7)
        font_p  = _fit_prompt_font(prompt, avail_w, avail_h)
        p_surf  = font_p.render(prompt, True, WHITE)
        px      = (screen_w - p_surf.get_width()) // 2
        py      = (bar_h - p_surf.get_height()) // 2
        surf.blit(p_surf, (px, py))


def draw_hold_ring(surf: pygame.Surface, bounds: pygame.Rect, pct: float) -> None:
    """Clockwise-filling perimeter ring on the grid bounds, no track (ADR-0019)."""
    pct = max(0.0, min(1.0, pct))
    if pct <= 0.0:
        return
    rect = bounds.inflate(-HOLD_RING_INSET * 2, -HOLD_RING_INSET * 2)
    # pygame.draw.arc draws counter-clockwise from start_angle to stop_angle.
    # We want a clockwise-filling arc starting at 12 o'clock (top).
    end_angle   = math.pi / 2.0
    start_angle = end_angle - 2.0 * math.pi * pct
    pygame.draw.arc(surf, HOLD_RING_COLOR, rect, start_angle, end_angle, HOLD_RING_THICK)


def _wrap_to_width(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for word in words:
        candidate = (cur + " " + word).strip()
        if font.size(candidate)[0] <= max_w or not cur:
            cur = candidate
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_center_text(surf: pygame.Surface, text: str, color: tuple,
                     screen_w: int, top_y: int, screen_h: int,
                     *, max_font: int = 96, padding: float = 0.08) -> None:
    """Big multi-line centered text inside the grid area below the top bar (ADR-0019)."""
    if not text:
        return
    area_h  = screen_h - top_y
    avail_w = int(screen_w * (1.0 - padding * 2))
    avail_h = int(area_h * (1.0 - padding * 2))

    lo, hi = 16, max_font
    best_font  = hud_font(lo)
    best_lines = [text]
    while lo <= hi:
        mid   = (lo + hi) // 2
        f     = hud_font(mid)
        lines = _wrap_to_width(text, f, avail_w)
        h     = len(lines) * f.get_height()
        if h <= avail_h and all(f.size(ln)[0] <= avail_w for ln in lines):
            best_font, best_lines = f, lines
            lo = mid + 1
        else:
            hi = mid - 1

    line_h  = best_font.get_height()
    total_h = line_h * len(best_lines)
    y       = top_y + (area_h - total_h) // 2
    for line in best_lines:
        s  = best_font.render(line, True, color)
        sx = (screen_w - s.get_width()) // 2
        surf.blit(s, (sx, y))
        y += line_h
