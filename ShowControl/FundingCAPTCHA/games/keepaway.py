"""Football Keepaway — survive with the ball until time runs out."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pygame

from games.grid import (
    Grid, TapTracker,
    BLACK, WHITE, DK_GREY, MID_GREY, LT_GREY, GREEN, YELLOW, RED, CYAN,
    HUD_W, hud_font, draw_hud_label, draw_progress_bar,
    SUCCESS_COLOR, DANGER_COLOR, HIGHLIGHT_COLOR,
)

_DIR    = Path(__file__).parent.parent
_IMAGES = _DIR / "images"
_CFG    = _DIR / "keepaway-images.json"

_COLS, _ROWS = 5, 5

_TARGET_TIME  = 12.0
_TICK_BASE_MS = 1000.0
_TICK_SCALE   = 80.0
_TICK_MIN_MS  = 300.0
_EASE_IN      = 1.6

_OFFENSE_START = [(1,1),(3,1),(0,3),(2,3),(4,3)]
_DEFENSE_START = [(4,0),(0,4),(4,4),(2,2)]


def _img_surf(filename: str, size: int) -> pygame.Surface | None:
    path = _IMAGES / filename
    if not path.exists():
        return None
    try:
        img = pygame.image.load(str(path)).convert()
        return pygame.transform.scale(img, (size, size))
    except Exception:
        return None


def _load_player_photos(cell_px: int) -> list[pygame.Surface | None]:
    try:
        data = json.loads(_CFG.read_text())
        if isinstance(data, list) and data:
            surfs = [_img_surf(f, cell_px) for f in data]
            surfs = [s for s in surfs if s is not None]
            if surfs:
                random.shuffle(surfs)
                return surfs
    except Exception:
        pass
    return []


class KeepawayGame:
    def __init__(self, settings: dict) -> None:
        WW, WH         = pygame.display.get_surface().get_size()
        self._grid     = Grid(WW, WH, _COLS, _ROWS)
        self._taps     = TapTracker()
        self._photos   = _load_player_photos(self._grid.cell_size)
        self._font_b   = hud_font(22)
        self._font_s   = hud_font(16)
        self._target   = _TARGET_TIME
        self._difficulty = 1
        self._offense: list[dict] = []
        self._defense: list[dict] = []
        self._ball_idx = 0
        self._phase    = "select"
        self._selected: int | None = None
        self._elapsed  = 0.0
        self._alive    = False
        self._lose_timer: float | None = None
        self._tick_ms  = _TICK_BASE_MS
        self._tick_acc = 0.0
        self._init()

    def _init(self) -> None:
        self._offense = [{"c": c, "r": r} for c, r in _OFFENSE_START]
        self._defense = [{"c": c, "r": r} for c, r in _DEFENSE_START]
        self._ball_idx   = 0
        self._phase      = "select"
        self._selected   = None
        self._elapsed    = 0.0
        self._alive      = True
        self._lose_timer = None
        base = max(_TICK_BASE_MS - self._difficulty * _TICK_SCALE, _TICK_MIN_MS)
        self._tick_ms  = base * _EASE_IN
        self._tick_acc = 0.0

    def reset(self) -> None:
        self._taps.reset()
        self._photos = _load_player_photos(self._grid.cell_size)
        self._target = _TARGET_TIME
        self._difficulty = 1
        self._init()

    def update(self, blobs: list[dict], projector,
               max_plane_dist: float, dt: float) -> tuple[float, str | None]:
        # Lose delay (flash then return event)
        if self._lose_timer is not None:
            self._lose_timer -= dt
            if self._lose_timer <= 0.0:
                return 0.0, "loss"
            return 0.0, None

        if not self._alive:
            return 0.0, None

        self._elapsed += dt

        # Win
        if self._elapsed >= self._target:
            self._alive = False
            return 1.0, "win"

        # Ease-in: ramp tick speed to 1× by round end
        progress = min(self._elapsed / self._target, 1.0)
        base     = max(_TICK_BASE_MS - self._difficulty * _TICK_SCALE, _TICK_MIN_MS)
        self._tick_ms = base * (_EASE_IN - (_EASE_IN - 1.0) * progress)

        # Defender tick
        self._tick_acc += dt * 1000.0
        if self._tick_acc >= self._tick_ms:
            self._tick_acc -= self._tick_ms
            self._move_defenders()
            if self._check_caught():
                return 0.0, None

        # Tap detection
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

        return min(1.0, self._elapsed / self._target), None

    def _move_defenders(self) -> None:
        ball = self._offense[self._ball_idx]
        occupied = {(d["c"], d["r"]) for d in self._defense}

        for di, def_ in enumerate(self._defense):
            # Even defenders chase ball; odd chase farthest receiver
            if di % 2 == 0:
                target = ball
            else:
                best, best_d = None, -1
                for oi, o in enumerate(self._offense):
                    if oi == self._ball_idx:
                        continue
                    d = abs(o["c"] - ball["c"]) + abs(o["r"] - ball["r"])
                    if d > best_d:
                        best_d = d
                        best = o
                target = best or ball

            dc = (target["c"] - def_["c"])
            dr = (target["r"] - def_["r"])
            candidates = []
            if dc:
                candidates.append((def_["c"] + (1 if dc > 0 else -1), def_["r"]))
            if dr:
                candidates.append((def_["c"], def_["r"] + (1 if dr > 0 else -1)))
            if dc and dr:
                candidates.append((
                    def_["c"] + (1 if dc > 0 else -1),
                    def_["r"] + (1 if dr > 0 else -1),
                ))
            candidates.append((def_["c"], def_["r"]))

            others = occupied - {(def_["c"], def_["r"])}
            for nc, nr in candidates:
                if not (0 <= nc < _COLS and 0 <= nr < _ROWS):
                    continue
                if (nc, nr) not in others:
                    occupied.discard((def_["c"], def_["r"]))
                    def_["c"], def_["r"] = nc, nr
                    occupied.add((nc, nr))
                    break

    def _check_caught(self) -> bool:
        ball = self._offense[self._ball_idx]
        for d in self._defense:
            if d["c"] == ball["c"] and d["r"] == ball["r"]:
                self._alive = False
                self._grid.flash(ball["c"], ball["r"], DANGER_COLOR, 800)
                self._lose_timer = 0.85
                return True
        return False

    def _on_tap(self, col: int, row: int) -> None:
        off_idx = next(
            (i for i, o in enumerate(self._offense) if o["c"] == col and o["r"] == row),
            None,
        )
        is_ball = off_idx == self._ball_idx

        if self._phase == "select":
            if is_ball:
                self._selected = off_idx
                self._phase    = "pass"
            return

        # pass phase
        if off_idx is not None and off_idx != self._ball_idx:
            recv = self._offense[off_idx]
            if any(d["c"] == recv["c"] and d["r"] == recv["r"]
                   for d in self._defense):
                self._grid.flash(col, row, DANGER_COLOR, 300)
                return
            self._ball_idx = off_idx
            self._selected = None
            self._phase    = "select"
            self._grid.flash(col, row, SUCCESS_COLOR, 400)
        elif is_ball:
            self._selected = None
            self._phase    = "select"

    def _is_defended(self, c: int, r: int) -> bool:
        return any(d["c"] == c and d["r"] == r for d in self._defense)

    def draw(self, surf: pygame.Surface) -> None:
        g = self._grid
        surf.fill(BLACK)
        g.draw_background(surf)

        # Defenders
        for d in self._defense:
            rect = g.inner_rect(d["c"], d["r"])
            pygame.draw.circle(surf, RED, rect.center, rect.w // 3)
            pygame.draw.rect(surf, (180, 0, 0), g.cell_rect(d["c"], d["r"]), 2)

        # Offense
        for i, o in enumerate(self._offense):
            is_ball = i == self._ball_idx
            is_sel  = self._selected == i
            is_open = not self._is_defended(o["c"], o["r"])
            rect    = g.inner_rect(o["c"], o["r"])

            if self._photos:
                img = self._photos[i % len(self._photos)]
                img = pygame.transform.scale(img, (rect.w, rect.h))
                if not is_open and not is_ball:
                    img = img.copy()
                    img.set_alpha(100)
                surf.blit(img, rect.topleft)
            else:
                color = YELLOW if is_ball else (GREEN if is_open else MID_GREY)
                pygame.draw.circle(surf, color, rect.center, rect.w // 3)

            if is_ball:
                # ball badge
                badge = self._font_s.render("B", True, WHITE)
                surf.blit(badge, badge.get_rect(bottomright=rect.bottomright))
                border = YELLOW if is_sel else WHITE
                pygame.draw.rect(surf, border, g.cell_rect(o["c"], o["r"]), 3)
            elif is_sel:
                pygame.draw.rect(surf, YELLOW, g.cell_rect(o["c"], o["r"]), 3)
            elif is_open:
                pygame.draw.rect(surf, HIGHLIGHT_COLOR, g.cell_rect(o["c"], o["r"]), 1)

        g.draw_flashes(surf)
        self._draw_hud(surf)

    def _draw_hud(self, surf: pygame.Surface) -> None:
        g = self._grid
        g.draw_hud_bg(surf)
        x = g.hud_rect.x
        w = g.hud_rect.width
        y = 20
        remaining = max(0.0, self._target - self._elapsed)
        vc = RED if remaining <= 3 else GREEN
        y  = draw_hud_label(surf, self._font_b, "SURVIVE", f"{int(remaining)}s",
                             x, y, value_color=vc)
        draw_progress_bar(surf, x + 8, y, w - 24, 12,
                          remaining / self._target, color=vc)
        y += 22
        draw_hud_label(surf, self._font_b, "LEVEL", str(self._difficulty), x, y)

        if self._phase == "select":
            lines = ["Tap ball", "carrier"]
        else:
            lines = ["Tap open", "teammate"]
        for i, line in enumerate(lines):
            t = self._font_s.render(line, True, LT_GREY)
            surf.blit(t, (x + 8, g.hud_rect.bottom - 60 +
                          i * (self._font_s.get_height() + 2)))


def create(settings: dict) -> KeepawayGame:
    return KeepawayGame(settings)
