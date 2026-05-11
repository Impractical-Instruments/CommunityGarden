"""Upside Down — match upside-down piece pairs before time runs out."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pygame

from games.grid import (
    Grid, TapTracker,
    BLACK, WHITE, DK_GREY, LT_GREY, GREEN, YELLOW, RED,
    HUD_W, hud_font, draw_hud_label, draw_progress_bar,
    SUCCESS_COLOR, WRONG_COLOR,
)

_DIR    = Path(__file__).parent.parent
_IMAGES = _DIR / "images"
_PAIRS  = _DIR / "pairs.json"

_COLS, _ROWS = 4, 4
_NUM_PAIRS   = (_COLS * _ROWS) // 2
_TIME_S      = 45.0

_DEFAULT_PAIRS = [
    ("BUS",   "CAR"),
    ("HOME",  "HUT"),
    ("OAK",   "PINE"),
    ("BALL",  "HOOP"),
    ("DOG",   "CAT"),
    ("APPLE", "LIME"),
    ("MOON",  "STAR"),
    ("KEY",   "LOCK"),
]


def _text_surf(text: str, cell_px: int) -> pygame.Surface:
    font = pygame.font.SysFont("monospace", cell_px // 3, bold=True)
    surf = pygame.Surface((cell_px, cell_px))
    surf.fill(DK_GREY)
    t = font.render(text[:6], True, WHITE)
    surf.blit(t, t.get_rect(center=(cell_px // 2, cell_px // 2)))
    return surf


def _img_surf(filename: str, cell_px: int) -> pygame.Surface:
    path = _IMAGES / filename
    if path.exists():
        try:
            img = pygame.image.load(str(path)).convert()
            return pygame.transform.scale(img, (cell_px, cell_px))
        except Exception:
            pass
    return _text_surf(Path(filename).stem[:6], cell_px)


def _load_pair_surfs(cell_px: int) -> list[tuple[pygame.Surface, pygame.Surface]]:
    try:
        data = json.loads(_PAIRS.read_text())
        if isinstance(data, list) and len(data) >= _NUM_PAIRS:
            return [
                (_img_surf(e["a"], cell_px), _img_surf(e["b"], cell_px))
                for e in data[:_NUM_PAIRS]
            ]
    except Exception:
        pass
    return [
        (_text_surf(a, cell_px), _text_surf(b, cell_px))
        for a, b in _DEFAULT_PAIRS[:_NUM_PAIRS]
    ]


class UpsideDownGame:
    def __init__(self, settings: dict) -> None:
        WW, WH       = pygame.display.get_surface().get_size()
        self._grid   = Grid(WW, WH, _COLS, _ROWS)
        self._taps   = TapTracker()
        self._surfs  = _load_pair_surfs(self._grid.cell_size)
        self._font_b = hud_font(22)
        self._font_s = hud_font(16)
        self._pieces: dict[tuple[int, int], dict] = {}
        self._fixed:  set[tuple[int, int]]        = set()
        self._selected: tuple[int, int] | None    = None
        self._elapsed  = 0.0
        self._alive    = False
        # {(col,row): {elapsed, delay}} for vortex animation
        self._vortex:  dict[tuple[int, int], dict] | None = None
        self._deal()

    def _deal(self) -> None:
        self._pieces.clear()
        self._fixed.clear()
        self._selected = None
        self._elapsed  = 0.0
        self._alive    = True
        self._vortex   = None

        cells = [(c, r) for r in range(_ROWS) for c in range(_COLS)]
        random.shuffle(cells)
        pairs = list(range(_NUM_PAIRS))
        random.shuffle(pairs)
        for i, pi in enumerate(pairs):
            self._pieces[cells[i * 2]]     = {"pair_id": pi, "half": 0}
            self._pieces[cells[i * 2 + 1]] = {"pair_id": pi, "half": 1}

    def reset(self) -> None:
        self._taps.reset()
        self._surfs = _load_pair_surfs(self._grid.cell_size)
        self._deal()

    def update(self, blobs: list[dict], projector,
               max_plane_dist: float, dt: float) -> tuple[float, str | None]:
        # Advance vortex animation
        if self._vortex is not None:
            for v in self._vortex.values():
                v["elapsed"] += dt
            done = all(
                (v["elapsed"] - v["delay"]) >= 0.5
                for v in self._vortex.values()
            )
            if done:
                self._vortex = None
                return 0.0, "loss"
            return 0.0, None

        if not self._alive:
            return 0.0, None

        self._elapsed += dt
        if self._elapsed >= _TIME_S:
            self._alive  = False
            unfixed = [k for k in self._pieces if k not in self._fixed]
            random.shuffle(unfixed)
            self._vortex = {
                (c, r): {"elapsed": 0.0, "delay": i * 0.08}
                for i, (c, r) in enumerate(unfixed)
            }
            return 0.0, None

        active = {b["id"] for b in blobs}
        if projector is not None:
            for bid in self._taps.update(active):
                blob = next((b for b in blobs if b["id"] == bid), None)
                if blob is None:
                    continue
                cell = self._grid.blob_to_cell(blob, projector, max_plane_dist)
                if cell:
                    self._on_tap(*cell)
        else:
            self._taps.update(active)

        if len(self._fixed) == len(self._pieces):
            self._alive = False
            return 1.0, "win"

        return self._elapsed / _TIME_S, None

    def _on_tap(self, col: int, row: int) -> None:
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
        prev      = self._selected
        self._selected = None
        prev_slot = self._pieces[prev]
        if (prev_slot["pair_id"] == slot["pair_id"]
                and prev_slot["half"] != slot["half"]):
            self._fixed.add(prev)
            self._fixed.add(key)
            self._grid.flash(col, row, SUCCESS_COLOR, 500)
            self._grid.flash(*prev, SUCCESS_COLOR, 500)
        else:
            self._grid.flash(col, row, WRONG_COLOR, 400)
            self._grid.flash(*prev, WRONG_COLOR, 400)

    def draw(self, surf: pygame.Surface) -> None:
        g = self._grid
        surf.fill(BLACK)
        g.draw_background(surf)

        for (c, r), slot in self._pieces.items():
            pi, half = slot["pair_id"], slot["half"]
            piece    = self._surfs[pi][half] if pi < len(self._surfs) else None
            if piece is None:
                continue
            is_fixed = (c, r) in self._fixed
            is_sel   = self._selected == (c, r)

            # Vortex: spin + shrink unfixed cells
            if self._vortex and (c, r) in self._vortex:
                v    = self._vortex[(c, r)]
                prog = max(0.0, min(1.0, (v["elapsed"] - v["delay"]) / 0.5))
                if prog > 0.0:
                    inner   = g.inner_rect(c, r)
                    scale_f = max(0.01, 1.0 - prog)
                    rotated = pygame.transform.rotozoom(piece, prog * 360.0, scale_f)
                    surf.blit(rotated, rotated.get_rect(center=inner.center))
                    continue

            display = piece if is_fixed else pygame.transform.rotate(piece, 180)
            g.blit_cell(surf, display, c, r)

            if is_sel:
                pygame.draw.rect(surf, YELLOW,   g.cell_rect(c, r), 3)
            elif is_fixed:
                pygame.draw.rect(surf, GREEN, g.cell_rect(c, r), 2)

        g.draw_flashes(surf)
        self._draw_hud(surf)

    def _draw_hud(self, surf: pygame.Surface) -> None:
        g = self._grid
        g.draw_hud_bg(surf)
        x = g.hud_rect.x
        w = g.hud_rect.width
        y = 20
        remaining = max(0.0, _TIME_S - self._elapsed)
        matched   = len(self._fixed) // 2
        total     = len(self._pieces) // 2
        vc = RED if remaining <= 10 else GREEN
        y  = draw_hud_label(surf, self._font_b, "TIME", f"{int(remaining)}s",
                             x, y, value_color=vc)
        draw_progress_bar(surf, x + 8, y, w - 24, 12, remaining / _TIME_S, color=vc)
        y += 22
        y  = draw_hud_label(surf, self._font_b, "PAIRS", f"{matched}/{total}", x, y)

        lh = self._font_s.get_height() + 2
        for i, line in enumerate(["Tap two", "pieces that", "belong", "together"]):
            t = self._font_s.render(line, True, LT_GREY)
            surf.blit(t, (x + 8, g.hud_rect.bottom - 80 + i * lh))


def create(settings: dict) -> UpsideDownGame:
    return UpsideDownGame(settings)
