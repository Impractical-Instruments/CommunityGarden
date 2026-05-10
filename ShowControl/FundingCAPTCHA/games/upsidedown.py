"""
Upside Down — memory matching game. Port of games/upsidedown.js.

Grid: 4×4 (8 pairs). Pieces are shown upside-down; tap matching pairs to
flip them right-side-up. Fixed all pairs before the timer hits zero.

Win  → on_win() called
Lose → on_lose() called (timer reaches zero)

Pair source: GET /api/pairs from FastAPI server. Falls back to DEFAULT_PAIRS.
Photos: fetched from server as raw image bytes, displayed with circular crop.
"""
from __future__ import annotations

import io
import random
import threading
from typing import Any

import pygame
import requests

COLS = 4
ROWS = 4

_DEFAULT_PAIRS = [
    ("Bus",    "Car",    "vehicles"),
    ("House",  "Shack",  "houses"),
    ("Tree",   "Pine",   "trees"),
    ("Soccer", "Football","balls"),
    ("Dog",    "Cat",    "pets"),
    ("Apple",  "Orange", "fruits"),
    ("Moon",   "Star",   "sky"),
    ("Key",    "Lock",   "locks"),
]

_TUNING = {
    "initial_time":   45,
    "time_min":       20,
    "time_per_level":  8,
}

# Colours
_BG          = (18, 8, 35, 210)
_CELL_NORMAL = (40, 20, 70, 230)
_CELL_SEL    = (100, 50, 180, 255)
_CELL_FIXED  = (30, 120, 60, 230)
_CELL_FLASH  = (200, 200, 80, 255)
_CELL_WRONG  = (180, 30, 30, 230)
_TEXT        = (230, 220, 255)
_BORDER      = (80, 50, 120)
_BORDER_SEL  = (160, 100, 255)
_BORDER_FIXED = (60, 200, 100)


def _circular_crop(surf: pygame.Surface, size: int) -> pygame.Surface:
    """Scale surf to size×size and apply a circular alpha mask."""
    scaled = pygame.transform.smoothscale(surf, (size, size))
    mask   = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
    result = pygame.Surface((size, size), pygame.SRCALPHA)
    result.blit(scaled, (0, 0))
    result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return result


class UpsideDownGame:
    COLS = COLS
    ROWS = ROWS

    def __init__(self, settings: dict, server_url: str = "http://localhost:8080") -> None:
        self._server      = server_url
        self._time        = float(_TUNING["initial_time"])
        self._pair_source: list[Any] = list(_DEFAULT_PAIRS)
        self._photo_cache: dict[str, pygame.Surface] = {}
        self._font        = pygame.font.SysFont("sans", 28, bold=True)
        self._font_sm     = pygame.font.SysFont("sans", 20)

        # Flash state: key → remaining seconds
        self._flash_cells: dict[str, float] = {}

        self._init_board()
        threading.Thread(target=self._fetch_pairs, daemon=True).start()

    # ── Pair loading ──────────────────────────────────────────────────────────

    def _fetch_pairs(self) -> None:
        try:
            r    = requests.get(f"{self._server}/api/pairs", timeout=3)
            data = r.json()
            if isinstance(data, list) and len(data) >= 2:
                # API format: [{label, a:{url,label}, b:{url,label}}]
                self._pair_source = data
                self._init_board()
        except Exception:
            pass

    def _piece_label(self, piece: Any) -> str:
        if isinstance(piece, dict):
            return piece.get("label", "")
        return str(piece)

    def _piece_url(self, piece: Any) -> str | None:
        if isinstance(piece, dict):
            return piece.get("url")
        return None

    def _load_photo(self, url: str, size: int) -> pygame.Surface | None:
        cache_key = f"{url}@{size}"
        if cache_key in self._photo_cache:
            return self._photo_cache[cache_key]
        try:
            full_url = url if url.startswith("http") else f"{self._server}{url}"
            r    = requests.get(full_url, timeout=3)
            surf = pygame.image.load(io.BytesIO(r.content)).convert_alpha()
            circ = _circular_crop(surf, size)
            self._photo_cache[cache_key] = circ
            return circ
        except Exception:
            return None

    # ── Board initialisation ──────────────────────────────────────────────────

    def _init_board(self) -> None:
        self._elapsed  = 0.0
        self._selected: tuple[int, int] | None = None
        self._fixed: set[str] = set()
        self._flash_cells = {}
        self._alive    = True
        self._won      = False

        total_cells = COLS * ROWS
        num_pairs   = total_cells // 2

        pairs = random.sample(self._pair_source, min(num_pairs, len(self._pair_source)))
        if len(pairs) < num_pairs:
            pairs = (pairs * (num_pairs // len(pairs) + 1))[:num_pairs]

        cells = [(c, r) for r in range(ROWS) for c in range(COLS)]
        random.shuffle(cells)

        # pieces[(col, row)] = {pairId, half(0|1), piece}
        self._pieces: dict[tuple[int, int], dict] = {}
        for idx, pair in enumerate(pairs):
            if isinstance(pair, dict):
                a_piece = pair.get("a", {})
                b_piece = pair.get("b", {})
            else:
                a_piece, b_piece = pair[0], pair[1]
            ca, ra = cells[idx * 2]
            cb, rb = cells[idx * 2 + 1]
            self._pieces[(ca, ra)] = {"pair_id": idx, "half": 0, "piece": a_piece}
            self._pieces[(cb, rb)] = {"pair_id": idx, "half": 1, "piece": b_piece}

    # ── Game loop ─────────────────────────────────────────────────────────────

    def update(self, dt: float) -> str | None:
        if not self._alive:
            return None
        self._elapsed += dt
        for k in list(self._flash_cells):
            self._flash_cells[k] -= dt
            if self._flash_cells[k] <= 0:
                del self._flash_cells[k]
        if self._elapsed >= self._time:
            self._alive = False
            return "lose"
        return None

    def on_tap(self, col: int, row: int) -> None:
        if not self._alive:
            return
        key  = (col, row)
        slot = self._pieces.get(key)
        if slot is None or key in self._fixed:
            return

        if self._selected is None:
            self._selected = key
            return

        if self._selected == key:
            self._selected = None
            return

        prev_key  = self._selected
        prev_slot = self._pieces.get(prev_key)
        self._selected = None

        if prev_slot and prev_slot["pair_id"] == slot["pair_id"] and prev_slot["half"] != slot["half"]:
            # Match
            self._fixed.add(key)
            self._fixed.add(prev_key)
            self._flash_cells[key]      = 0.5
            self._flash_cells[prev_key] = 0.5
            if len(self._fixed) == len(self._pieces):
                self._alive = False
                # Win is returned on next update() — set a flag
                self._won = True
        else:
            # Wrong
            self._flash_cells[key]      = -0.4   # negative = wrong flash
            self._flash_cells[prev_key] = -0.4

    # ── Rendering ─────────────────────────────────────────────────────────────

    def grid_rect(self, W: int, H: int) -> pygame.Rect:
        hud_h   = int(H * 0.14)
        avail_h = H - hud_h
        cell    = min(W // COLS, avail_h // ROWS)
        gw, gh  = cell * COLS, cell * ROWS
        return pygame.Rect((W - gw) // 2, hud_h + (avail_h - gh) // 2, gw, gh)

    def render(self, surf: pygame.Surface, W: int, H: int) -> None:
        gr       = self.grid_rect(W, H)
        cell_w   = gr.width  // COLS
        cell_h   = gr.height // ROWS
        pad      = max(4, cell_w // 14)
        img_size = min(cell_w, cell_h) - pad * 2

        # Grid background
        pygame.draw.rect(surf, _BG, gr, border_radius=12)

        for (c, r), slot in self._pieces.items():
            key   = (c, r)
            cx    = gr.x + c * cell_w
            cy    = gr.y + r * cell_h
            rect  = pygame.Rect(cx + pad, cy + pad, cell_w - pad * 2, cell_h - pad * 2)

            is_fixed = key in self._fixed
            is_sel   = key == self._selected
            flash    = self._flash_cells.get(key, 0)
            is_match_flash = flash > 0
            is_wrong_flash = flash < 0

            if is_match_flash:
                cell_col  = _CELL_FLASH
                bord_col  = _BORDER_FIXED
            elif is_wrong_flash:
                cell_col  = _CELL_WRONG
                bord_col  = (200, 50, 50)
            elif is_fixed:
                cell_col  = _CELL_FIXED
                bord_col  = _BORDER_FIXED
            elif is_sel:
                cell_col  = _CELL_SEL
                bord_col  = _BORDER_SEL
            else:
                cell_col  = _CELL_NORMAL
                bord_col  = _BORDER

            pygame.draw.rect(surf, cell_col, rect, border_radius=8)
            pygame.draw.rect(surf, bord_col, rect, width=2, border_radius=8)

            self._draw_piece(surf, slot["piece"], rect, img_size, is_fixed, is_wrong_flash)

    def _draw_piece(
        self,
        surf: pygame.Surface,
        piece: Any,
        rect: pygame.Rect,
        img_size: int,
        is_fixed: bool,
        is_wrong: bool,
    ) -> None:
        url = self._piece_url(piece)
        label = self._piece_label(piece)
        cx, cy = rect.centerx, rect.centery

        if url:
            img = self._load_photo(url, img_size)
            if img:
                if not is_fixed:
                    img = pygame.transform.rotate(img, 180)
                surf.blit(img, (cx - img_size // 2, cy - img_size // 2))
                return

        # Text fallback
        text = self._font.render(label[:8], True, _TEXT)
        if not is_fixed:
            text = pygame.transform.rotate(text, 180)
        surf.blit(text, text.get_rect(center=(cx, cy)))

    def render_hud(self, surf: pygame.Surface, W: int, H: int) -> None:
        hud_h   = int(H * 0.14)
        matched = len(self._fixed) // 2
        total   = len(self._pieces) // 2
        remaining = max(0.0, self._time - self._elapsed)
        frac    = remaining / self._time
        low_time = remaining <= 10

        # Timer bar
        bar_w = int(W * 0.5)
        bar_h = 12
        bar_x = (W - bar_w) // 2
        bar_y = hud_h - bar_h - 8
        pygame.draw.rect(surf, (50, 30, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        fill_w = int(bar_w * frac)
        bar_col = (220, 60, 60) if low_time else (80, 180, 80)
        if fill_w > 0:
            pygame.draw.rect(surf, bar_col, (bar_x, bar_y, fill_w, bar_h), border_radius=6)

        # Labels
        time_txt = self._font.render(f"{int(remaining)}s", True,
                                      (255, 100, 100) if low_time else (200, 240, 200))
        pair_txt = self._font.render(f"{matched}/{total} pairs", True, (200, 180, 255))
        title    = self._font_sm.render("Upside Down", True, (140, 100, 200))

        surf.blit(title,    title.get_rect(centerx=W // 2, top=6))
        surf.blit(time_txt, time_txt.get_rect(right=bar_x - 16, centery=bar_y + bar_h // 2))
        surf.blit(pair_txt, pair_txt.get_rect(left=bar_x + bar_w + 16, centery=bar_y + bar_h // 2))

    # ── Orchestrator interface ────────────────────────────────────────────────

    def intensity(self) -> float:
        """Arc intensity: 0 at start, 1 when timer is gone (urgency)."""
        return 1.0 - max(0.0, min(1.0, (self._time - self._elapsed) / self._time))

    def event_data(self) -> dict:
        matched = len(self._fixed) // 2
        total   = max(1, len(self._pieces) // 2)
        return {
            "score":         matched,
            "winScore":      total,
            "timerFraction": max(0.0, (self._time - self._elapsed) / self._time),
        }

    def next_level(self) -> None:
        self._time = max(float(_TUNING["time_min"]),
                         self._time - _TUNING["time_per_level"])
        self._init_board()

    def destroy(self) -> None:
        self._alive = False
