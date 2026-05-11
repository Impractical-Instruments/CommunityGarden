"""Music Rhythm — tap the column when the note reaches the bottom row."""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pygame

from games.grid import (
    Grid, TapTracker,
    BLACK, WHITE, DK_GREY, MID_GREY, LT_GREY, GREEN, YELLOW, RED, CYAN, ORANGE,
    HUD_W, hud_font, draw_hud_label, draw_progress_bar,
    HIT_COLOR, MISS_COLOR, HIGHLIGHT_COLOR,
)

_DIR    = Path(__file__).parent.parent
_IMAGES = _DIR / "images"
_CFG    = _DIR / "rhythm-images.json"

_COLS, _ROWS  = 4, 5
_TRIGGER_ROW  = _ROWS - 1

_NOTES  = [261.6, 293.7, 329.6, 392.0]   # C D E G
_LABELS = ["C", "D", "E", "G"]

_SONG = [
    2,1,0,1, 2,2,2,-1, 1,1,1,-1, 2,3,3,-1,
    2,1,0,1, 2,2,2, 2, 1,1,2,1,  0,-1,-1,-1,
]

_BEAT_MS       = 420
_BEAT_MS_MIN   = 260
_ROW_TRAVEL_F  = 0.85
_SPAWN_F       = 0.70
_TOLERANCE     = 0.38
_WIN_SCORE     = 18
_MISS_PENALTY  = 2
_WRONG_PENALTY = 1
_NOTE_AHEAD    = 3
_EASE_IN       = 2.0


def _make_tone(freq: float, sr: int = 44100) -> pygame.mixer.Sound | None:
    try:
        dur  = 0.18
        t    = np.linspace(0, dur, int(sr * dur), endpoint=False)
        wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        wave = (wave * 0.35 * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack([wave, wave]))
    except Exception:
        return None


def _img_surf(filename: str, size: int) -> pygame.Surface | None:
    path = _IMAGES / filename
    if not path.exists():
        return None
    try:
        img = pygame.image.load(str(path)).convert()
        return pygame.transform.scale(img, (size, size))
    except Exception:
        return None


def _load_col_photos(cell_px: int) -> list[pygame.Surface | None]:
    try:
        data = json.loads(_CFG.read_text())
        if isinstance(data, list) and data:
            random.shuffle(data)
            surfs = [_img_surf(f, cell_px) for f in data]
            surfs = [s for s in surfs if s is not None]
            if surfs:
                return [surfs[i % len(surfs)] for i in range(_COLS)]
    except Exception:
        pass
    return [None] * _COLS


class RhythmGame:
    def __init__(self, settings: dict) -> None:
        WW, WH        = pygame.display.get_surface().get_size()
        self._grid    = Grid(WW, WH, _COLS, _ROWS)
        self._taps    = TapTracker()
        self._col_img = _load_col_photos(self._grid.cell_size)
        self._tones   = [_make_tone(f) for f in _NOTES]
        self._font_b  = hud_font(22)
        self._font_s  = hud_font(16)
        self._queue:  list[dict] = []
        self._song_pos = 0
        self._beat_ms  = float(_BEAT_MS)
        self._score    = 0
        self._alive    = True
        self._init_song()

    def _init_song(self) -> None:
        self._queue    = []
        self._song_pos = 0
        self._beat_ms  = float(_BEAT_MS) * _EASE_IN
        self._score    = 0
        for _ in range(_NOTE_AHEAD):
            self._spawn_next()

    def _spawn_next(self) -> None:
        if self._song_pos >= len(_SONG):
            return
        col = _SONG[self._song_pos]
        self._song_pos += 1
        self._queue.append({"col": col, "advance": 0.0,
                             "row": -1, "hit": False,
                             "rest": col < 0, "penalised": False})

    def reset(self) -> None:
        self._taps.reset()
        self._col_img = _load_col_photos(self._grid.cell_size)
        self._alive   = True
        self._init_song()

    def update(self, blobs: list[dict], projector,
               max_plane_dist: float, dt: float) -> tuple[float, str | None]:
        if not self._alive:
            return 0.0, None

        # Ease-in: ramp beat speed up to full over the song
        progress      = min(self._song_pos / len(_SONG), 1.0)
        target_ms     = float(_BEAT_MS)
        self._beat_ms = target_ms * (_EASE_IN - (_EASE_IN - 1.0) * progress)

        dt_ms          = dt * 1000.0
        row_travel_ms  = self._beat_ms * _ROW_TRAVEL_F

        for n in self._queue:
            n["advance"] += dt_ms
            n["row"] = int((n["advance"] / row_travel_ms) * _ROWS)

        # Miss penalty for notes scrolled past trigger
        for n in self._queue:
            if n["row"] > _TRIGGER_ROW and not n["hit"] and not n["penalised"]:
                if not n["rest"]:
                    n["penalised"] = True
                    self._score = max(0, self._score - _MISS_PENALTY)
                    self._grid.flash(n["col"], _TRIGGER_ROW, MISS_COLOR, 300)

        self._queue = [n for n in self._queue if n["row"] <= _TRIGGER_ROW + 1]

        # Spawn next note
        last = self._queue[-1] if self._queue else None
        if not last or last["advance"] > self._beat_ms * _SPAWN_F:
            self._spawn_next()

        # Song ended
        if self._song_pos >= len(_SONG) and not self._queue:
            if self._score >= _WIN_SCORE:
                self._alive = False
                return 1.0, "win"
            self._init_song()

        # Tap detection → score
        active = {b["id"] for b in blobs}
        if projector is not None:
            for bid in self._taps.update(active):
                blob = next((b for b in blobs if b["id"] == bid), None)
                if blob is None:
                    continue
                cell = self._grid.blob_to_cell(blob, projector, max_plane_dist)
                if cell and cell[1] == _TRIGGER_ROW:
                    self._on_tap(cell[0])
        else:
            self._taps.update(active)

        pct = min(1.0, self._score / _WIN_SCORE)
        return pct, None

    def _on_tap(self, col: int) -> None:
        if self._tones[col]:
            self._tones[col].play()

        best, best_dist = None, float("inf")
        for n in self._queue:
            if n["col"] != col or n["hit"] or n["rest"]:
                continue
            row_travel_ms = self._beat_ms * _ROW_TRAVEL_F
            frac  = n["advance"] / row_travel_ms
            dist  = abs(frac - 1.0)
            if dist < best_dist:
                best_dist = dist
                best = n

        if best is not None and best_dist < _TOLERANCE:
            best["hit"]  = True
            self._score += 1
            self._grid.flash(col, _TRIGGER_ROW, HIT_COLOR, 350)
            if self._score >= _WIN_SCORE:
                self._alive = False
        else:
            self._score = max(0, self._score - _WRONG_PENALTY)
            self._grid.flash(col, _TRIGGER_ROW, MISS_COLOR, 300)
            if self._score == 0:
                self._queue    = []
                self._song_pos = 0
                self._spawn_next()

    def draw(self, surf: pygame.Surface) -> None:
        g = self._grid
        surf.fill(BLACK)
        g.draw_background(surf)

        # Trigger row: column icons
        for c in range(_COLS):
            rect = g.inner_rect(c, _TRIGGER_ROW)
            pygame.draw.rect(surf, (45, 45, 45), g.cell_rect(c, _TRIGGER_ROW))
            pygame.draw.rect(surf, YELLOW, g.cell_rect(c, _TRIGGER_ROW), 2)
            if self._col_img[c]:
                img = pygame.transform.scale(self._col_img[c], (rect.w, rect.h))
                surf.blit(img, rect.topleft)
            else:
                lbl = self._font_b.render(_LABELS[c], True, YELLOW)
                surf.blit(lbl, lbl.get_rect(center=rect.center))

        # Falling notes
        for n in self._queue:
            if n["col"] < 0 or n["hit"]:
                continue
            r = max(0, min(_TRIGGER_ROW - 1, n["row"]))
            near = n["row"] >= _TRIGGER_ROW - 1
            rect = g.inner_rect(n["col"], r)
            color = YELLOW if near else LT_GREY
            if self._col_img[n["col"]]:
                size  = int(rect.w * (0.72 if near else 0.55))
                img   = pygame.transform.scale(self._col_img[n["col"]], (size, size))
                pygame.draw.circle(surf, color,
                                   rect.center, size // 2 + 3, 3 if near else 2)
                surf.blit(img, img.get_rect(center=rect.center))
            else:
                pygame.draw.circle(surf, color, rect.center,
                                   rect.w // 3 if near else rect.w // 4)

        g.draw_flashes(surf)
        self._draw_hud(surf)

    def _draw_hud(self, surf: pygame.Surface) -> None:
        g = self._grid
        g.draw_hud_bg(surf)
        x = g.hud_rect.x
        w = g.hud_rect.width
        y = 20
        pct = min(1.0, self._score / _WIN_SCORE)
        vc  = GREEN if pct >= 0.7 else (RED if self._score <= 2 else WHITE)
        y   = draw_hud_label(surf, self._font_b, "SCORE", str(self._score),
                              x, y, value_color=vc)
        draw_progress_bar(surf, x + 8, y, w - 24, 12, pct)
        y += 22
        draw_hud_label(surf, self._font_b, "GOAL", str(_WIN_SCORE), x, y)

        hint = ("Tap face when" if any(self._col_img) else "Tap column when")
        lh   = self._font_s.get_height() + 2
        for i, line in enumerate([hint, "it reaches", "the bottom"]):
            t = self._font_s.render(line, True, LT_GREY)
            surf.blit(t, (x + 8, g.hud_rect.bottom - 70 + i * lh))


def create(settings: dict) -> RhythmGame:
    return RhythmGame(settings)
