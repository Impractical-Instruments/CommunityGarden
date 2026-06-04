"""BodyKeepaway — silhouette survival game (ADR-0013, ADR-0019)."""
from __future__ import annotations

import json
import logging
import math
import random
from enum import Enum, auto
from pathlib import Path

import numpy as np
import pygame

log = logging.getLogger(__name__)

from games.grid import (
    Grid,
    BLACK, WHITE, DK_GREY, MID_GREY, LT_GREY, GREEN, YELLOW, RED, BLUE,
    hud_font, top_bar_height, draw_top_bar, draw_center_text,
)
from body_grid import BodyGridActivator, BodyGridConfig, SlabConfig, CellActivations
from silhouette import render_silhouette
from arc import blend_intensity

_DIR    = Path(__file__).parent.parent
_LEVELS = _DIR / "keepaway-body-levels.json"
_TAUNTS = _DIR / "keepaway-body-taunts.json"

RUNNER_COLOR   = (60, 130, 220)
DEFENDER_COLOR = (220, 50, 50)
WIN_COLOR      = (0, 220, 80)

_WIN_FLASH_S = 0.5
_WIN_FINAL_S = 2.0
_BLOWUP_S    = 2.8


class _State(Enum):
    GRACE      = auto()
    PLAYING    = auto()
    NO_RUNNERS = auto()
    WIN_FLASH  = auto()
    WIN_FINAL  = auto()
    BLOWUP     = auto()
    DONE       = auto()


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "life", "max_life")

    def __init__(self, x, y, vx, vy, color, size, life):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.color = color; self.size = size
        self.life = life; self.max_life = life

    def update(self, dt):
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.vy  += 500 * dt
        self.life -= dt


class _Defender:
    def __init__(self, col: int, row: int, speed: float, cols: int, rows: int) -> None:
        self.x     = float(col)
        self.y     = float(row)
        self.speed = speed
        self._cols = cols
        self._rows = rows
        self._tx   = float(col)
        self._ty   = float(row)

    @property
    def cell(self) -> tuple[int, int]:
        return int(self.x + 0.5), int(self.y + 0.5)

    def move(self, dt: float, runner_cells: set[tuple[int, int]]) -> None:
        if not runner_cells:
            return
        dist  = self.speed * dt
        iters = 0
        while dist > 0.0 and iters < 20:
            iters += 1
            dx = self._tx - self.x
            dy = self._ty - self.y
            d  = math.hypot(dx, dy)
            if d < 1e-6:
                self._pick_next(runner_cells)
                dx = self._tx - self.x
                dy = self._ty - self.y
                d  = math.hypot(dx, dy)
                if d < 1e-6:
                    break
            if dist < d:
                self.x += dx / d * dist
                self.y += dy / d * dist
                dist = 0.0
            else:
                self.x  = self._tx
                self.y  = self._ty
                dist   -= d
                self._pick_next(runner_cells)

    def _pick_next(self, runner_cells: set[tuple[int, int]]) -> None:
        col = int(round(self.x))
        row = int(round(self.y))
        nearest = min(runner_cells, key=lambda rc: abs(rc[0] - col) + abs(rc[1] - row))
        dc = nearest[0] - col
        dr = nearest[1] - row
        if dc == 0 and dr == 0:
            return
        # Manhattan routing: move on axis with greater distance; tie-break horizontal
        if abs(dc) >= abs(dr):
            sc, sr = (1 if dc > 0 else -1), 0
        else:
            sc, sr = 0, (1 if dr > 0 else -1)
        self._tx = float(max(0, min(self._cols - 1, col + sc)))
        self._ty = float(max(0, min(self._rows - 1, row + sr)))


def _load_levels() -> list[dict]:
    try:
        data = json.loads(_LEVELS.read_text())
        if data:
            return data
    except Exception:
        pass
    return [
        {"survive_s": 10, "defenders": [{"speed": 1.5}]},
        {"survive_s": 15, "defenders": [{"speed": 2.0}]},
        {"survive_s": 20, "defenders": [{"speed": 2.0}, {"speed": 2.0}]},
        {"survive_s": 25, "defenders": [{"speed": 2.5}, {"speed": 2.5}]},
        {"survive_s": 30, "defenders": [{"speed": 2.5}, {"speed": 2.5}, {"speed": 2.5}]},
    ]


def _load_taunts() -> list[str]:
    try:
        data = json.loads(_TAUNTS.read_text())
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return ["CAUGHT!", "TAGGED!", "YOU'VE BEEN CAUGHT!"]


def _make_activator(level: dict, settings: dict, defaults: dict) -> BodyGridActivator:
    cols, rows = level.get("grid", defaults.get("grid", [8, 6]))
    roi        = settings.get("camera_roi", {"x": 0, "y": 0, "w": 640, "h": 400})
    slabs      = [SlabConfig(**s) for s in settings.get("depth_slabs",
                  [{"near_mm": 800, "far_mm": 2500, "slab_id": 0}])]
    threshold  = settings.get("cell_activation_threshold", 0.30)
    return BodyGridActivator(BodyGridConfig(
        cols=cols, rows=rows, camera_roi=roi,
        slabs=slabs, cell_activation_threshold=threshold,
    ))


def _spawn_defenders(defender_cfgs: list[dict], cols: int, rows: int) -> list[_Defender]:
    n = len(defender_cfgs)
    positions = {
        1: [(cols // 2, 0)],
        2: [(0, 0), (cols - 1, 0)],
        3: [(0, 0), (cols - 1, 0), (cols // 2, rows - 1)],
    }.get(n, [(i % cols, i // cols) for i in range(n)])
    return [
        _Defender(positions[i][0], positions[i][1], cfg["speed"], cols, rows)
        for i, cfg in enumerate(defender_cfgs)
    ]


def _draw_stick_figure(surf: pygame.Surface, cx: int, cy: int,
                       cell_px: int, color: tuple) -> None:
    """KoL-style stick figure centered at (cx, cy)."""
    head_r  = max(4, cell_px // 7)
    body_h  = cell_px // 3
    arm_len = cell_px // 5
    leg_len = cell_px // 4
    lw      = max(2, cell_px // 14)

    head_cy  = cy - body_h // 2 - head_r
    pygame.draw.circle(surf, color, (cx, head_cy), head_r, lw)

    body_top = head_cy + head_r
    body_bot = body_top + body_h
    pygame.draw.line(surf, color, (cx, body_top), (cx, body_bot), lw)

    arm_y = body_top + body_h // 3
    pygame.draw.line(surf, color, (cx, arm_y), (cx - arm_len, arm_y + arm_len // 2), lw)
    pygame.draw.line(surf, color, (cx, arm_y), (cx + arm_len, arm_y + arm_len // 2), lw)

    pygame.draw.line(surf, color, (cx, body_bot), (cx - leg_len, body_bot + leg_len), lw)
    pygame.draw.line(surf, color, (cx, body_bot), (cx + leg_len, body_bot + leg_len), lw)


class BodyKeepawayGame:
    def __init__(self, settings: dict) -> None:
        self._settings   = settings
        self._defaults   = settings.get("keepaway_body", {})
        self._all_levels = _load_levels()
        self._taunts     = _load_taunts()
        self._w_diff     = self._defaults.get("intensity_weights", {}).get("difficulty", 0.4)
        self._w_time     = self._defaults.get("intensity_weights", {}).get("time_pressure", 0.6)
        self._slabs_cfg  = settings.get("depth_slabs", [{"near_mm": 800, "far_mm": 2500, "slab_id": 0}])
        self._roi        = settings.get("camera_roi", {"x": 0, "y": 0, "w": 640, "h": 400})

        WW, WH       = pygame.display.get_surface().get_size()
        self._WW     = WW
        self._WH     = WH

        self._level_idx:   int                      = 0
        self._grid:        Grid | None              = None
        self._activator:   BodyGridActivator | None = None
        self._defenders:   list[_Defender]          = []
        self._activations: CellActivations          = {}
        self._foreground:  np.ndarray | None        = None
        self._elapsed      = 0.0
        self._state_t      = 0.0
        self._abandon_t    = 0.0
        self._intensity    = 0.0
        self._state        = _State.GRACE
        self._final_event: str | None = None
        self._taunt        = ""
        self._particles:   list[_Particle]          = []

        self._load_level()

    # ── Level helpers ─────────────────────────────────────────────────────────

    def _load_level(self) -> None:
        level      = self._all_levels[self._level_idx]
        cols, rows = level.get("grid", self._defaults.get("grid", [8, 6]))
        self._grid       = Grid(self._WW, self._WH, cols, rows)
        self._activator  = _make_activator(level, self._settings, self._defaults)
        self._elapsed    = 0.0
        self._state_t    = 0.0
        self._abandon_t  = 0.0
        self._state      = _State.GRACE
        self._activations = {}
        self._particles  = []
        self._defenders  = _spawn_defenders(level["defenders"], cols, rows)

    @property
    def _level(self) -> dict:
        return self._all_levels[self._level_idx]

    @property
    def _survive_s(self) -> float:
        return float(self._level.get("survive_s", 10.0))

    @property
    def _grace_s(self) -> float:
        return float(self._level.get("grace_s", self._defaults.get("grace_s", 3.0)))

    @property
    def _abandon_s(self) -> float:
        return float(self._level.get("abandon_s", self._defaults.get("abandon_s", 5.0)))

    # ── Public API ────────────────────────────────────────────────────────────

    def reset(self) -> None:
        self._level_idx   = 0
        self._final_event = None
        self._load_level()

    def update(self, foreground: np.ndarray | None, dt: float) -> tuple[float, str | None]:
        self._foreground = foreground

        if foreground is not None and self._activator is not None:
            self._activations = self._activator.activate(foreground)
        else:
            self._activations = {}

        runner_cells = set(self._activations.keys())

        # ── Terminal states ───────────────────────────────────────────────────

        if self._state == _State.DONE:
            return 0.0, self._final_event

        if self._state == _State.BLOWUP:
            self._state_t += dt
            for p in self._particles:
                p.update(dt)
            self._particles = [p for p in self._particles if p.life > 0]
            if self._state_t >= _BLOWUP_S:
                self._state = _State.DONE
            return 0.0, None

        if self._state == _State.WIN_FINAL:
            self._state_t += dt
            if self._state_t >= _WIN_FINAL_S:
                self._state = _State.DONE
            return self._intensity, None

        if self._state == _State.WIN_FLASH:
            self._state_t += dt
            if self._state_t >= _WIN_FLASH_S:
                self._level_idx += 1
                self._load_level()
            return self._intensity, None

        # ── Grace period ──────────────────────────────────────────────────────

        if self._state == _State.GRACE:
            self._state_t += dt
            if self._state_t >= self._grace_s:
                self._state   = _State.PLAYING
                self._state_t = 0.0
            return self._intensity, None

        # ── Playing / No-runners ──────────────────────────────────────────────

        if not runner_cells:
            if self._state == _State.PLAYING:
                self._state     = _State.NO_RUNNERS
                self._abandon_t = 0.0
            else:
                self._abandon_t += dt
                if self._abandon_t >= self._abandon_s:
                    self._final_event = "loss"
                    self._begin_blowup()
            return self._intensity, None

        if self._state == _State.NO_RUNNERS:
            self._state     = _State.PLAYING
            self._abandon_t = 0.0

        # ── Playing ───────────────────────────────────────────────────────────

        self._elapsed += dt
        level_idx      = self._level_idx + 1  # 1-based

        self._intensity = blend_intensity(level_idx, self._elapsed, self._survive_s,
                                          self._w_diff, self._w_time)

        for d in self._defenders:
            d.move(dt, runner_cells)

        if any(d.cell in runner_cells for d in self._defenders):
            self._final_event = "loss"
            self._begin_blowup()
            return 0.0, None

        if self._elapsed >= self._survive_s:
            if self._level_idx >= len(self._all_levels) - 1:
                self._state       = _State.WIN_FINAL
                self._state_t     = 0.0
                self._final_event = "win"
            else:
                self._state   = _State.WIN_FLASH
                self._state_t = 0.0
            return self._intensity, None

        return self._intensity, None

    # ── Blow-Up ───────────────────────────────────────────────────────────────

    def _begin_blowup(self) -> None:
        self._state   = _State.BLOWUP
        self._state_t = 0.0
        self._taunt   = random.choice(self._taunts)
        self._particles = self._spawn_confetti()

    def _spawn_confetti(self) -> list[_Particle]:
        if self._grid is None:
            return []
        g      = self._grid
        colors = [GREEN, YELLOW, RED, (0, 200, 220), (200, 50, 255), WHITE, (255, 100, 0)]
        result = []
        for r in range(g.rows):
            for c in range(g.cols):
                rect   = g.cell_rect(c, r)
                cx, cy = rect.centerx, rect.centery
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    spd   = random.uniform(60, 400)
                    vx    = math.cos(angle) * spd
                    vy    = math.sin(angle) * spd - 200
                    color = random.choice(colors)
                    size  = random.randint(4, 16)
                    life  = random.uniform(1.2, _BLOWUP_S)
                    result.append(_Particle(cx, cy, vx, vy, color, size, life))
        return result

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface) -> None:
        g = self._grid
        if g is None:
            surf.fill(DK_GREY)
            return

        surf.fill(BLACK)
        bounds = g.bounds_rect
        bar_h  = g.top_reserve
        prompt = self._level.get("prompt", "")  # optional — Keepaway levels have none today

        if self._state == _State.BLOWUP:
            self._draw_confetti(surf)
            draw_center_text(surf, self._taunt, RED,
                             self._WW, bar_h, self._WH, max_font=120)
            draw_top_bar(surf, self._WW, bar_h, prompt, None)
            return

        # Silhouette overlay (faint), scaled to grid bounds
        if self._foreground is not None:
            slab_color = tuple(self._settings.get("slab_styles", {})
                               .get("0", {}).get("color", [0, 220, 100]))
            sil = render_silhouette(self._foreground, self._slabs_cfg,
                                    self._roi, slab_color,
                                    bounds.width, bounds.height)
            sil.set_alpha(60)
            surf.blit(sil, bounds.topleft)

        # Runner cell highlights
        tile = pygame.Surface((g.cell_size, g.cell_size), pygame.SRCALPHA)
        if self._state in (_State.WIN_FLASH, _State.WIN_FINAL):
            highlight_rgba = (*WIN_COLOR, 200)
        else:
            highlight_rgba = (*RUNNER_COLOR, 140)
        for (c, r) in self._activations:
            tile.fill((0, 0, 0, 0))
            tile.fill(highlight_rgba)
            surf.blit(tile, g.cell_rect(c, r).topleft)

        # Grid lines
        for r in range(g.rows):
            for c in range(g.cols):
                pygame.draw.rect(surf, MID_GREY, g.cell_rect(c, r), 1)

        # Defenders (hidden during win states)
        if self._state not in (_State.WIN_FLASH, _State.WIN_FINAL):
            r0 = g.cell_rect(0, 0)
            gx, gy = r0.x, r0.y
            for d in self._defenders:
                px = int(gx + d.x * g.cell_size + g.cell_size * 0.5)
                py = int(gy + d.y * g.cell_size + g.cell_size * 0.5)
                _draw_stick_figure(surf, px, py, g.cell_size, DEFENDER_COLOR)

        # State overlays (centered text inside grid area)
        if self._state == _State.GRACE:
            remaining = max(0.0, self._grace_s - self._state_t)
            n         = math.ceil(remaining)
            label     = str(n) if n > 0 else "GO!"
            draw_center_text(surf, label, WHITE,
                             self._WW, bar_h, self._WH, max_font=180)
        elif self._state == _State.NO_RUNNERS:
            self._draw_no_runners_overlay(surf, bar_h)
        elif self._state == _State.WIN_FLASH:
            draw_center_text(surf, "LEVEL CLEAR!", GREEN,
                             self._WW, bar_h, self._WH, max_font=140)
        elif self._state == _State.WIN_FINAL:
            draw_center_text(surf, "YOU SURVIVED", WHITE,
                             self._WW, bar_h, self._WH, max_font=140)

        # Top bar: prompt (optional) + level timer
        if self._state in (_State.GRACE, _State.PLAYING, _State.NO_RUNNERS):
            remaining: float | None = max(0.0, self._survive_s - self._elapsed)
        else:
            remaining = None
        draw_top_bar(surf, self._WW, bar_h, prompt, remaining, timer_warn_s=5.0)

    def _draw_no_runners_overlay(self, surf: pygame.Surface, bar_h: int) -> None:
        area_h  = self._WH - bar_h
        overlay = pygame.Surface((self._WW, area_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, bar_h))

        # "GET ON THE FIELD" + abandon countdown bar, centered
        font_huge = pygame.font.SysFont("monospace", 72, bold=True)
        t1 = font_huge.render("GET ON THE FIELD", True, YELLOW)
        cx = self._WW // 2
        cy = bar_h + area_h // 2 - 40
        surf.blit(t1, t1.get_rect(center=(cx, cy)))

        remaining = max(0.0, self._abandon_s - self._abandon_t)
        pct       = remaining / max(self._abandon_s, 0.001)
        bar_w     = self._WW * 2 // 3
        bar_h_px  = 20
        bx        = (self._WW - bar_w) // 2
        by        = bar_h + area_h // 2 + 30
        pygame.draw.rect(surf, MID_GREY, (bx, by, bar_w, bar_h_px))
        pygame.draw.rect(surf, RED, (bx, by, max(0, int(bar_w * pct)), bar_h_px))
        pygame.draw.rect(surf, WHITE, (bx, by, bar_w, bar_h_px), 1)

    def _draw_confetti(self, surf: pygame.Surface) -> None:
        for p in self._particles:
            alpha = max(0, int(255 * p.life / p.max_life))
            s     = p.size
            tile  = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            tile.fill((*p.color, alpha))
            surf.blit(tile, (int(p.x) - s, int(p.y) - s))


def create(settings: dict) -> BodyKeepawayGame:
    return BodyKeepawayGame(settings)
