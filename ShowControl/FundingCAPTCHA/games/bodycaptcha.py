"""BodyCaptcha — silhouette CAPTCHA grid-matching game (ADR-0013, ADR-0019)."""
from __future__ import annotations

import json
import logging
import random
from enum import Enum, auto
from pathlib import Path

import numpy as np
import pygame

log = logging.getLogger(__name__)

from games.blowup import Blowup
from games.grid import Grid
from games.shell import (
    BLACK, DK_GREY, MID_GREY, GREEN, RED,
    HOLD_RING_COLOR,
    draw_top_bar, draw_hold_ring, draw_center_text,
)
from body_grid import BodyGridActivator, BodyGridConfig, SlabConfig, CellActivations
from silhouette import render_silhouette
from arc import blend_intensity
from levels import Levels, new_default_level
from settings import slab_color, with_defaults

_TAUNTS = Path(__file__).parent.parent / "taunts.json"


HINT_COLOR   = (100, 180, 255)
COVER_VALID  = (  0, 220,  80)
COVER_EXTRA  = (220,  50,  50)

_WIN_FLASH_S = 0.5


class _State(Enum):
    PLAYING   = auto()
    WIN_FLASH = auto()
    BLOWUP    = auto()
    DONE      = auto()


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


_DEFAULT_TAUNT = "Too Slow! You're not a robot."


def _read_taunts(path: Path = _TAUNTS) -> list[str] | None:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, list) and data else None


def _make_activator(level: dict, settings: dict) -> BodyGridActivator:
    cols, rows = level.get("grid", [4, 4])
    roi   = settings["camera_roi"]
    slabs = [SlabConfig(**s) for s in settings["depth_slabs"]]
    threshold = settings["cell_activation_threshold"]
    return BodyGridActivator(BodyGridConfig(
        cols=cols, rows=rows, camera_roi=roi,
        slabs=slabs, cell_activation_threshold=threshold,
    ))


class BodyCaptchaGame:
    def __init__(self, settings: dict, size: tuple[int, int],
                 levels: Levels) -> None:
        """`size` is the (width, height) of the surface draw() will be given."""
        self._settings   = settings = with_defaults(settings)
        self._levels     = levels
        self._defaults   = settings["bodycaptcha"]      # a Level may override any of these
        self._all_levels = self._levels.read()
        if self._all_levels is None:
            log.warning("%s missing/invalid — falling back to default level",
                        self._levels.path)
            self._all_levels = [new_default_level()]
        self._taunts     = _read_taunts() or [_DEFAULT_TAUNT]
        self._bag        = _LevelBag(self._all_levels)
        self._w_diff     = self._defaults["intensity_weights"]["difficulty"]
        self._w_time     = self._defaults["intensity_weights"]["time_pressure"]
        self._slabs_cfg  = settings["depth_slabs"]
        self._roi        = settings["camera_roi"]
        self._slab_color = slab_color(settings)
        self._WW, self._WH = size

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
        self._blowup       = Blowup()
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
        self._bg_img     = self._levels.background(
            level.get("image"), bounds.width, bounds.height, level.get("crop_align"))
        self._activator  = _make_activator(level, self._settings)
        self._valid_set  = {tuple(c) for c in level.get("valid_cells", [])}
        self._elapsed    = 0.0
        self._hold_elapsed = 0.0
        self._state_t    = 0.0
        self._state      = _State.PLAYING
        self._activations = {}

    @property
    def _timer_s(self) -> float:
        return float(self._level.get("timer_s",
                     self._defaults["timer_s"]))

    @property
    def _hold_s(self) -> float:
        return float(self._level.get("hold_s",
                     self._defaults["hold_s"]))

    @property
    def _hold_decay_rate(self) -> float:
        """How fast a wrong pose drains the hold, as a multiple of real time.

        1.0 drains as fast as it fills; 3.0 empties a full hold in a third of
        hold_s. Keeps the hold reachable when depth speckle trips a stray cell
        for a frame — see the drain in update().
        """
        return float(self._level.get("hold_decay_rate",
                     self._defaults["hold_decay_rate"]))

    @property
    def _hint_opacity(self) -> float:
        return float(self._level.get("hint_opacity",
                     self._defaults["hint_opacity"]))

    # ── Public API ────────────────────────────────────────────────────────────

    def _reload_data(self) -> None:
        """Re-read levels + taunts from disk at arc start (hot-reload, ADR pending).

        Levels arrive via `git pull` on the box; this picks them up on the next
        arc with no service restart. A missing/malformed/empty file keeps the
        last-known-good set in memory so a bad pull never degrades a live show.
        """
        levels = self._levels.read()
        if levels is not None:
            self._all_levels = levels
            self._bag        = _LevelBag(levels)
        else:
            log.warning("%s missing/invalid — keeping %d loaded levels",
                        self._levels.path, len(self._all_levels))

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
            self._blowup.update(dt)
            if self._blowup.done:
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
            # Drain rather than reset: a single speckle-tripped cell must not
            # cost a Player the whole hold. A genuinely wrong pose still runs
            # the hold down to zero, just decay_rate× faster than it built up.
            self._hold_elapsed = max(
                0.0, self._hold_elapsed - dt * self._hold_decay_rate)

        return self._intensity, None

    # ── Blow-Up ───────────────────────────────────────────────────────────────

    def _begin_blowup(self) -> None:
        self._state   = _State.BLOWUP
        self._taunt   = random.choice(self._taunts)
        self._blowup.start(self._grid)

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
            self._blowup.draw(surf)
            draw_center_text(surf, self._taunt, RED,
                             self._WW, bar_h, self._WH, max_font=120)
            draw_top_bar(surf, self._WW, bar_h, prompt, None)
            return

        # Photo, clipped to grid bounds
        if self._bg_img is not None:
            surf.blit(self._bg_img, bounds.topleft)

        # Silhouette overlay (faint), scaled to grid bounds
        if self._foreground is not None:
            sil = render_silhouette(self._foreground, self._slabs_cfg,
                                    self._roi, self._slab_color,
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


def create(settings: dict, size: tuple[int, int], levels: Levels) -> BodyCaptchaGame:
    return BodyCaptchaGame(settings, size, levels)
