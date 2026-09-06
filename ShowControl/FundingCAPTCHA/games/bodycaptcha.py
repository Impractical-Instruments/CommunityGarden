"""BodyCaptcha — silhouette CAPTCHA grid-matching game (ADR-0013, ADR-0019)."""
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
    BLACK, WHITE, DK_GREY, MID_GREY, LT_GREY, GREEN, YELLOW, RED, CYAN, ORANGE,
    HOLD_RING_COLOR,
    top_bar_height, draw_top_bar, draw_hold_ring, draw_center_text,
)
from body_grid import BodyGridActivator, BodyGridConfig, SlabConfig, CellActivations
from silhouette import render_silhouette
from arc import blend_intensity
from crop import crop_scale

_DIR    = Path(__file__).parent.parent
_IMAGES = _DIR / "images"
_LEVELS = _DIR / "bodycaptcha-levels.json"
_TAUNTS = _DIR / "taunts.json"

HINT_COLOR   = (100, 180, 255)
COVER_VALID  = (  0, 220,  80)
COVER_EXTRA  = (220,  50,  50)

_WIN_FLASH_S = 0.5
_BLOWUP_S    = 2.8


class _State(Enum):
    PLAYING   = auto()
    WIN_FLASH = auto()
    BLOWUP    = auto()
    DONE      = auto()


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "life", "max_life")

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: tuple, size: int, life: float) -> None:
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.color = color; self.size = size
        self.life = life; self.max_life = life

    def update(self, dt: float) -> None:
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.vy  += 500 * dt  # gravity
        self.life -= dt


class _LevelBag:
    """Shuffle-bag over eligible levels (same difficulty or +1)."""

    def __init__(self, levels: list[dict]) -> None:
        self._all        = levels
        self._bag:  list[dict] = []
        self._difficulty = 1

    def reset(self) -> None:
        self._difficulty = 1
        self._bag        = []

    def next(self, beat_difficulty: int | None = None) -> dict:
        if beat_difficulty is not None:
            self._difficulty = min(beat_difficulty + 1, 5)
            self._bag = []

        if not self._bag:
            eligible = [l for l in self._all
                        if l.get("difficulty", 1) in (self._difficulty, self._difficulty + 1)]
            if not eligible:
                eligible = list(self._all)
            self._bag = eligible[:]
            random.shuffle(self._bag)

        return self._bag.pop()


_DEFAULT_LEVEL = {"prompt": "Cover the center", "image": None, "difficulty": 1,
                  "grid": [3, 3], "valid_cells": [[1, 1]]}
_DEFAULT_TAUNT = "Too Slow! You're not a robot."


def _read_levels(path: Path = _LEVELS) -> list[dict] | None:
    """Read the levels file. Returns None on ANY failure — missing, bad JSON,
    empty, or not a non-empty list — so callers choose fallback vs keep-last-good.

    Reloaded at every arc start (BodyCaptchaGame.reset), so a malformed or
    half-pulled file must never silently collapse the show to a default level.
    """
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, list) and data else None


def _read_taunts(path: Path = _TAUNTS) -> list[str] | None:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, list) and data else None


def _img_load(path: Path) -> pygame.Surface:
    """Load image via pygame, falling back to Pillow for unsupported formats (e.g. JPEG on Pi)."""
    with open(path, "rb") as f:
        if f.read(20).startswith(b"version https://git-"):
            raise RuntimeError(
                f"Git LFS pointer at {path} — run `git lfs pull` in the repo root"
            )
    try:
        return pygame.image.load(str(path)).convert()
    except Exception:
        pass
    from PIL import Image as _PILImage
    pil = _PILImage.open(str(path)).convert("RGB")
    raw = pil.tobytes()
    return pygame.image.frombuffer(raw, pil.size, "RGB").convert()


def _load_bg(image_name: str | None, w: int, h: int,
             align: object = None) -> pygame.Surface | None:
    if not image_name:
        return None
    path = _IMAGES / image_name
    if not path.exists():
        log.warning("Background image not found: %s", path)
        return None
    try:
        img = _img_load(path)
        return crop_scale(img, w, h, align)
    except Exception as exc:
        log.warning("Failed to load background image %s: %s", path, exc)
        return None


def _make_activator(level: dict, settings: dict) -> BodyGridActivator:
    cols, rows = level.get("grid", [4, 4])
    roi   = settings.get("camera_roi", {"x": 0, "y": 0, "w": 640, "h": 400})
    slabs = [SlabConfig(**s) for s in settings.get("depth_slabs",
             [{"near_mm": 800, "far_mm": 2500, "slab_id": 0}])]
    threshold = settings.get("cell_activation_threshold", 0.30)
    return BodyGridActivator(BodyGridConfig(
        cols=cols, rows=rows, camera_roi=roi,
        slabs=slabs, cell_activation_threshold=threshold,
    ))


class BodyCaptchaGame:
    def __init__(self, settings: dict) -> None:
        self._settings   = settings
        self._defaults   = settings.get("bodycaptcha", {})
        self._all_levels = _read_levels() or [_DEFAULT_LEVEL]
        self._taunts     = _read_taunts() or [_DEFAULT_TAUNT]
        self._bag        = _LevelBag(self._all_levels)
        self._w_diff     = self._defaults.get("intensity_weights", {}).get("difficulty",     0.4)
        self._w_time     = self._defaults.get("intensity_weights", {}).get("time_pressure",  0.6)
        self._slabs_cfg  = settings.get("depth_slabs", [{"near_mm": 800, "far_mm": 2500, "slab_id": 0}])
        self._roi        = settings.get("camera_roi",  {"x": 0, "y": 0, "w": 640, "h": 400})
        WW, WH           = pygame.display.get_surface().get_size()
        self._WW         = WW
        self._WH         = WH

        # Live state (set by _load_level)
        self._level:       dict             = {}
        self._grid:        Grid | None      = None
        self._bg_img:      pygame.Surface | None = None
        self._activator:   BodyGridActivator | None = None
        self._valid_set:   set[tuple]       = set()
        self._elapsed      = 0.0
        self._hold_elapsed = 0.0
        self._state_t      = 0.0
        self._state:       _State          = _State.PLAYING
        self._taunt        = ""
        self._particles:   list[_Particle] = []
        self._intensity    = 0.0
        self._activations: CellActivations = {}
        self._foreground:  np.ndarray | None = None

        self._load_level(self._bag.next())

    # ── Level helpers ─────────────────────────────────────────────────────────

    def _load_level(self, level: dict) -> None:
        self._level      = level
        cols, rows       = level.get("grid", [4, 4])
        self._grid       = Grid(self._WW, self._WH, cols, rows)
        bounds           = self._grid.bounds_rect
        self._bg_img     = _load_bg(level.get("image"), bounds.width, bounds.height,
                                    level.get("crop_align"))
        self._activator  = _make_activator(level, self._settings)
        self._valid_set  = {tuple(c) for c in level.get("valid_cells", [])}
        self._elapsed    = 0.0
        self._hold_elapsed = 0.0
        self._state_t    = 0.0
        self._state      = _State.PLAYING
        self._particles  = []
        self._activations = {}

    @property
    def _timer_s(self) -> float:
        return float(self._level.get("timer_s",
                     self._defaults.get("timer_s", 35.0)))

    @property
    def _hold_s(self) -> float:
        return float(self._level.get("hold_s",
                     self._defaults.get("hold_s", 1.0)))

    @property
    def _hint_opacity(self) -> float:
        return float(self._level.get("hint_opacity",
                     self._defaults.get("hint_opacity", 0.1)))

    # ── Public API ────────────────────────────────────────────────────────────

    def _reload_data(self) -> None:
        """Re-read levels + taunts from disk at arc start (hot-reload, ADR pending).

        Levels arrive via `git pull` on the box; this picks them up on the next
        arc with no service restart. A missing/malformed/empty file keeps the
        last-known-good set in memory so a bad pull never degrades a live show.
        """
        levels = _read_levels()
        if levels is not None:
            self._all_levels = levels
            self._bag        = _LevelBag(levels)
        else:
            log.warning("bodycaptcha-levels.json missing/invalid — keeping %d loaded levels",
                        len(self._all_levels))

        taunts = _read_taunts()
        if taunts is not None:
            self._taunts = taunts

        log.info("BodyCaptcha data: %d levels, %d taunts active",
                 len(self._all_levels), len(self._taunts))

    def reset(self) -> None:
        self._reload_data()
        self._bag.reset()
        self._load_level(self._bag.next())

    def update(self, foreground: np.ndarray | None, dt: float) -> tuple[float, str | None]:
        self._foreground = foreground

        if self._state == _State.DONE:
            return 0.0, "loss"

        if self._state == _State.BLOWUP:
            self._state_t += dt
            for p in self._particles:
                p.update(dt)
            self._particles = [p for p in self._particles if p.life > 0]
            if self._state_t >= _BLOWUP_S:
                self._state = _State.DONE
            return 0.0, None

        if self._state == _State.WIN_FLASH:
            self._state_t += dt
            if self._state_t >= _WIN_FLASH_S:
                self._load_level(self._bag.next(self._level.get("difficulty", 1)))
            return self._intensity, None

        # ── PLAYING ───────────────────────────────────────────────────────────
        self._elapsed += dt
        difficulty     = self._level.get("difficulty", 1)
        timer_s        = self._timer_s

        self._intensity = blend_intensity(difficulty, self._elapsed, timer_s,
                                          self._w_diff, self._w_time)

        if self._elapsed >= timer_s:
            self._begin_blowup()
            return 0.0, None

        # Compute activations
        if foreground is not None and self._activator is not None:
            self._activations = self._activator.activate(foreground)
        else:
            self._activations = {}

        covered = set(self._activations.keys())
        missing = self._valid_set - covered
        extras  = covered - self._valid_set

        if not missing and not extras:
            self._hold_elapsed += dt
            if self._hold_elapsed >= self._hold_s:
                self._state   = _State.WIN_FLASH
                self._state_t = 0.0
        else:
            self._hold_elapsed = 0.0

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
        g       = self._grid
        colors  = [GREEN, YELLOW, RED, CYAN, ORANGE, WHITE, (200, 50, 255), (255, 100, 0)]
        result  = []
        for r in range(g.rows):
            for c in range(g.cols):
                rect    = g.cell_rect(c, r)
                cx, cy  = rect.centerx, rect.centery
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(60, 400)
                    vx    = math.cos(angle) * speed
                    vy    = math.sin(angle) * speed - 200
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
        bounds  = g.bounds_rect
        bar_h   = g.top_reserve
        prompt  = self._level.get("prompt", "")

        if self._state == _State.BLOWUP:
            self._draw_confetti(surf)
            draw_center_text(surf, self._taunt, RED,
                             self._WW, bar_h, self._WH, max_font=120)
            draw_top_bar(surf, self._WW, bar_h, prompt, None)
            return

        # Photo, clipped to grid bounds
        if self._bg_img is not None:
            surf.blit(self._bg_img, bounds.topleft)

        # Silhouette overlay (faint), scaled to grid bounds
        if self._foreground is not None:
            slab_color  = tuple(self._settings.get("slab_styles", {})
                                .get("0", {}).get("color", [0, 220, 100]))
            sil = render_silhouette(self._foreground, self._slabs_cfg,
                                    self._roi, slab_color,
                                    bounds.width, bounds.height)
            sil.set_alpha(60)
            surf.blit(sil, bounds.topleft)

        # Cell overlays
        covered     = set(self._activations.keys())
        valid       = self._valid_set
        hold_active = (self._hold_elapsed > 0 and self._state == _State.PLAYING
                       and not (valid - covered) and not (covered - valid))
        hint_alpha  = int(self._hint_opacity * 255)
        tile        = pygame.Surface((g.cell_size, g.cell_size), pygame.SRCALPHA)

        for r in range(g.rows):
            for c in range(g.cols):
                key        = (c, r)
                is_valid   = key in valid
                is_covered = key in covered

                if self._state == _State.WIN_FLASH:
                    if is_valid:
                        color, alpha = GREEN, 230
                    else:
                        continue
                elif is_covered and is_valid:
                    color, alpha = (HOLD_RING_COLOR if hold_active else COVER_VALID), 190
                elif is_covered and not is_valid:
                    color, alpha = COVER_EXTRA, 160
                elif is_valid and not is_covered:
                    color, alpha = HINT_COLOR, hint_alpha
                else:
                    continue

                tile.fill((0, 0, 0, 0))
                tile.fill((*color, alpha))
                surf.blit(tile, g.cell_rect(c, r).topleft)

        # Grid lines
        for r in range(g.rows):
            for c in range(g.cols):
                pygame.draw.rect(surf, MID_GREY, g.cell_rect(c, r), 1)

        # Hold-progress ring on grid perimeter
        if self._state == _State.PLAYING and self._hold_elapsed > 0:
            draw_hold_ring(surf, bounds, self._hold_elapsed / max(self._hold_s, 0.001))

        # Win flash centered text
        if self._state == _State.WIN_FLASH:
            draw_center_text(surf, "LEVEL CLEAR!", GREEN,
                             self._WW, bar_h, self._WH, max_font=140)

        # Top bar (prompt + timer)
        remaining = max(0.0, self._timer_s - self._elapsed)
        draw_top_bar(surf, self._WW, bar_h, prompt, remaining)

    def _draw_confetti(self, surf: pygame.Surface) -> None:
        for p in self._particles:
            alpha = max(0, int(255 * p.life / p.max_life))
            s     = p.size
            tile  = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            tile.fill((*p.color, alpha))
            surf.blit(tile, (int(p.x) - s, int(p.y) - s))


def create(settings: dict) -> BodyCaptchaGame:
    return BodyCaptchaGame(settings)
