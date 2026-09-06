#!/usr/bin/env python3
"""BodyCaptcha level editor/visualizer — standalone, no camera needed."""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pygame

from crop import ANCHORS, DEFAULT_ALIGN, crop_scale

# When frozen by PyInstaller, data lives next to the .exe, not inside the
# unpacked bundle (which is a temp dir and read-only across launches).
if getattr(sys, "frozen", False):
    _DIR = Path(sys.executable).parent
else:
    _DIR = Path(__file__).parent
_LEVELS_DEFAULT = _DIR / "bodycaptcha-levels.json"
_levels_path: Path = _LEVELS_DEFAULT
_IMAGES = _DIR / "images"


def set_levels_path(path: "Path | str | None") -> None:
    """Edit an alternate levels file, or None to restore the default."""
    global _levels_path
    _levels_path = _LEVELS_DEFAULT if path is None else Path(path)


def get_levels_path() -> Path:
    return _levels_path


def _img_load(path: Path) -> "pygame.Surface":
    """Load image via pygame, falling back to Pillow for JPEG on Pi (SDL_image JPEG-less builds)."""
    try:
        return pygame.image.load(str(path)).convert()
    except Exception:
        pass
    from PIL import Image as _PILImage
    pil = _PILImage.open(str(path)).convert("RGB")
    return pygame.image.frombuffer(pil.tobytes(), pil.size, "RGB").convert()

# ── Colors ─────────────────────────────────────────────────────────────────
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
DK_GREY    = ( 28,  28,  28)
MID_GREY   = ( 75,  75,  75)
LT_GREY    = (160, 160, 160)
GREEN      = (  0, 170,  60)
RED        = (180,  40,  40)
CYAN       = (  0, 200, 220)
YELLOW     = (220, 180,   0)
SIDEBAR_BG = ( 20,  20,  28)
FIELD_BG   = ( 38,  38,  52)
BTN_NRM    = ( 52,  52,  72)
BTN_HOV    = ( 78,  78, 108)
VALID_ON   = (  0, 200,  80)
VALID_HOV  = ( 60, 240, 120)
CELL_OFF   = ( 42,  42,  55)
CELL_HOV   = ( 62,  62,  80)
GRID_LINE  = ( 90,  90, 105)

W, H    = 1060, 700
SIDE_W  = 300
GRID_W  = W - SIDE_W

# alpha for overlays when an image is behind the grid
_VALID_ALPHA   = 160
_INVALID_ALPHA = 55   # subtle dark tint
_HOVER_ALPHA   = 90

_THUMB_COLS = 4

DEFAULT_LEVEL: dict = {
    "prompt": "Select all ...",
    "image": None,
    "difficulty": 1,
    "grid": [3, 3],
    "valid_cells": [],
    "timer_s": 40,
}


def _load() -> list[dict]:
    try:
        data = json.loads(get_levels_path().read_text())
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return [deepcopy(DEFAULT_LEVEL)]


def _sort_key(lv: dict) -> tuple[str, str]:
    return (lv.get("image") or "", lv.get("prompt") or "")


def _save(levels: list[dict]) -> None:
    ordered = sorted(levels, key=_sort_key)
    get_levels_path().write_text(json.dumps(ordered, indent=2) + "\n")


def _wrap(text: str, max_chars: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if len(candidate) > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines or [""]


def _all_image_paths() -> list[str]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(
        p.relative_to(_IMAGES).as_posix()
        for p in _IMAGES.rglob("*")
        if p.suffix.lower() in exts
    )


class Editor:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("BodyCaptcha Level Editor")
        self._surf    = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        self._clock   = pygame.time.Clock()
        self._f15     = pygame.font.SysFont("monospace", 15, bold=True)
        self._f12     = pygame.font.SysFont("monospace", 12)
        self._f11     = pygame.font.SysFont("monospace", 11)
        self._f20     = pygame.font.SysFont("monospace", 20, bold=True)

        self._levels  = _load()
        self._idx     = 0
        self._dirty   = False

        self._editing  = False   # prompt text field active
        self._buf      = ""

        self._hover: tuple[int, int] | None = None
        self._btns:  list[tuple[pygame.Rect, object]] = []

        self._flash_msg = ""
        self._flash_t   = 0.0

        self._all_images: list[str] = _all_image_paths()
        self._picking = False                          # thumbnail browser open
        self._thumb_hover: str | None = None          # hovered image in picker
        self._bg_cache:    dict[str, pygame.Surface] = {}
        self._thumb_cache: dict[str, pygame.Surface] = {}

    # ── Accessors ──────────────────────────────────────────────────────────

    @property
    def _lv(self) -> dict:
        return self._levels[self._idx]

    @property
    def _vset(self) -> set[tuple[int, int]]:
        return {tuple(c) for c in self._lv.get("valid_cells", [])}

    def _write_valid(self, cells: set[tuple[int, int]]) -> None:
        self._lv["valid_cells"] = sorted([list(c) for c in cells])
        self._dirty = True

    def _grid_dims(self) -> tuple[int, int]:
        return tuple(self._lv.get("grid", [4, 4]))

    def _align(self) -> str:
        a = self._lv.get("crop_align")
        return a if a in ANCHORS else DEFAULT_ALIGN

    def _set_align(self, align: str) -> None:
        # Center is the default; storing it would add a key to every level.
        if align == DEFAULT_ALIGN:
            self._lv.pop("crop_align", None)
        else:
            self._lv["crop_align"] = align
        self._dirty = True

    # ── Image loading ──────────────────────────────────────────────────────

    def _get_bg(self, name: str, w: int, h: int, align: str) -> pygame.Surface | None:
        key = f"{name}_{w}_{h}_{align}"
        if key not in self._bg_cache:
            path = _IMAGES / name
            if not path.exists():
                return None
            try:
                self._bg_cache[key] = crop_scale(_img_load(path), w, h, align)
            except Exception:
                return None
        return self._bg_cache.get(key)

    def _get_thumb(self, name: str, tw: int, th: int) -> pygame.Surface | None:
        key = f"{name}_{tw}_{th}"
        if key not in self._thumb_cache:
            path = _IMAGES / name
            if not path.exists():
                return None
            try:
                self._thumb_cache[key] = crop_scale(_img_load(path), tw, th)
            except Exception:
                return None
        return self._thumb_cache.get(key)

    # ── Grid geometry ──────────────────────────────────────────────────────

    def _cell_size(self) -> int:
        cols, rows = self._grid_dims()
        return min(GRID_W // cols, H // rows)

    def _grid_origin(self) -> tuple[int, int]:
        cols, rows = self._grid_dims()
        cell = self._cell_size()
        return (GRID_W - cell * cols) // 2, (H - cell * rows) // 2

    def _preview_rect(self) -> pygame.Rect:
        """Where a level image is drawn — the cell grid itself.

        The game blits the photo into `Grid.bounds_rect`, so the editor must
        use the same rect or the anchor you pick here frames a different crop
        than the show renders.
        """
        cols, rows = self._grid_dims()
        cell   = self._cell_size()
        ox, oy = self._grid_origin()
        return pygame.Rect(ox, oy, cell * cols, cell * rows)

    def _cell_rect(self, col: int, row: int) -> pygame.Rect:
        cell = self._cell_size()
        ox, oy = self._grid_origin()
        return pygame.Rect(ox + col * cell, oy + row * cell, cell, cell)

    def _px_to_cell(self, px: int, py: int) -> tuple[int, int] | None:
        cols, rows = self._grid_dims()
        for r in range(rows):
            for c in range(cols):
                if self._cell_rect(c, r).collidepoint(px, py):
                    return (c, r)
        return None

    # ── Thumbnail picker geometry ──────────────────────────────────────────

    def _thumb_rects(self) -> list[tuple[str, pygame.Rect]]:
        n     = len(self._all_images)
        cols  = _THUMB_COLS
        rows  = (n + cols - 1) // cols
        pad   = 4
        tw    = (GRID_W - pad * (cols + 1)) // cols
        th    = (H - pad * (rows + 1)) // rows
        result = []
        for i, name in enumerate(self._all_images):
            c = i % cols
            r = i // cols
            x = pad + c * (tw + pad)
            y = pad + r * (th + pad)
            result.append((name, pygame.Rect(x, y, tw, th)))
        return result

    def _px_to_image(self, px: int, py: int) -> str | None:
        for name, rect in self._thumb_rects():
            if rect.collidepoint(px, py):
                return name
        return None

    # ── Events ─────────────────────────────────────────────────────────────

    def _on_event(self, ev: pygame.event.Event) -> bool:
        if ev.type == pygame.QUIT:
            return False

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE and self._picking:
                self._picking = False
                return True
            if self._editing:
                self._key_prompt(ev)
            else:
                self._key_global(ev)

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self._on_click(ev.pos)

        if ev.type == pygame.MOUSEMOTION:
            x, y = ev.pos
            if self._picking and x < GRID_W:
                self._thumb_hover = self._px_to_image(x, y)
            elif x < GRID_W and not self._picking:
                self._hover = self._px_to_cell(x, y)
                self._thumb_hover = None
            else:
                self._hover = None
                self._thumb_hover = None

        return True

    def _key_prompt(self, ev: pygame.event.Event) -> None:
        if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self._lv["prompt"] = self._buf
            self._editing = False
            self._dirty   = True
        elif ev.key == pygame.K_BACKSPACE:
            self._buf = self._buf[:-1]
        else:
            ch = ev.unicode
            if ch and ch.isprintable():
                self._buf += ch

    def _key_global(self, ev: pygame.event.Event) -> None:
        ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
        k    = ev.key

        if ctrl:
            if k == pygame.K_s:        self._do_save()
            elif k == pygame.K_n:      self._new_level()
            elif k == pygame.K_DELETE: self._del_level()
            elif k == pygame.K_c:      self._clear()
        else:
            if k == pygame.K_LEFT:     self._nav(-1)
            elif k == pygame.K_RIGHT:  self._nav(+1)
            elif k == pygame.K_e:      self._edit_prompt()
            elif k in (pygame.K_EQUALS, pygame.K_PLUS): self._adj_diff(+1)
            elif k == pygame.K_MINUS:  self._adj_diff(-1)
            elif k == pygame.K_UP:     self._adj_timer(+5)
            elif k == pygame.K_DOWN:   self._adj_timer(-5)

    def _on_click(self, pos: tuple[int, int]) -> None:
        x, y = pos
        if x < GRID_W:
            if self._picking:
                name = self._px_to_image(x, y)
                if name:
                    self._lv["image"] = name
                    self._dirty   = True
                    self._picking = False
                    self._flash(f"Image set: {name}")
            else:
                cell = self._px_to_cell(x, y)
                if cell:
                    self._toggle(cell)
        else:
            for rect, action in self._btns:
                if rect.collidepoint(x, y):
                    action()
                    break

    # ── Level mutations ────────────────────────────────────────────────────

    def _toggle(self, cell: tuple[int, int]) -> None:
        v = self._vset
        v.discard(cell) if cell in v else v.add(cell)
        self._write_valid(v)

    def _clear(self) -> None:
        self._write_valid(set())

    def _adj_diff(self, d: int) -> None:
        self._lv["difficulty"] = max(1, min(5, self._lv.get("difficulty", 1) + d))
        self._dirty = True

    def _adj_cols(self, d: int) -> None:
        cols, rows = self._grid_dims()
        nc = max(2, min(8, cols + d))
        self._lv["grid"] = [nc, rows]
        self._write_valid({(c, r) for c, r in self._vset if c < nc})

    def _adj_rows(self, d: int) -> None:
        cols, rows = self._grid_dims()
        nr = max(2, min(8, rows + d))
        self._lv["grid"] = [cols, nr]
        self._write_valid({(c, r) for c, r in self._vset if r < nr})

    def _adj_timer(self, d: int) -> None:
        self._lv["timer_s"] = max(5, self._lv.get("timer_s", 40) + d)
        self._dirty = True

    def _adj_hold(self, d: float) -> None:
        h = self._lv.get("hold_s", 1.0)
        self._lv["hold_s"] = round(max(0.5, h + d), 1)
        self._dirty = True

    def _add_hold(self) -> None:
        self._lv["hold_s"] = 1.0
        self._dirty = True

    def _remove_hold(self) -> None:
        self._lv.pop("hold_s", None)
        self._dirty = True

    def _clear_image(self) -> None:
        self._lv["image"] = None
        self._dirty = True

    def _nav(self, d: int) -> None:
        self._idx     = (self._idx + d) % len(self._levels)
        self._editing = False
        self._picking = False

    def _edit_prompt(self) -> None:
        self._editing = True
        self._buf     = self._lv.get("prompt", "")

    def _new_level(self) -> None:
        lv = deepcopy(DEFAULT_LEVEL)
        self._levels.insert(self._idx + 1, lv)
        self._idx  += 1
        self._dirty = True
        self._flash("New level added")

    def _del_level(self) -> None:
        if len(self._levels) <= 1:
            self._flash("Can't delete only level")
            return
        del self._levels[self._idx]
        self._idx   = min(self._idx, len(self._levels) - 1)
        self._dirty = True
        self._flash("Level deleted")

    def _do_save(self) -> None:
        if self._editing:
            self._lv["prompt"] = self._buf
            self._editing = False
        current = self._lv
        self._levels.sort(key=_sort_key)
        self._idx = self._levels.index(current)
        _save(self._levels)
        self._dirty = False
        self._flash("Saved!")

    def _flash(self, msg: str) -> None:
        self._flash_msg = msg
        self._flash_t   = 2.0

    # ── Drawing — grid area ────────────────────────────────────────────────

    def _draw_grid(self) -> None:
        surf  = self._surf
        cols, rows = self._grid_dims()
        valid = self._vset
        cell  = self._cell_size()
        has_image = bool(self._lv.get("image"))

        # Background — photo confined to the cell grid, letterboxed around it
        pygame.draw.rect(surf, DK_GREY, (0, 0, GRID_W, H))
        if has_image:
            rect = self._preview_rect()
            bg   = self._get_bg(self._lv["image"], rect.w, rect.h, self._align())
            if bg:
                surf.blit(bg, rect.topleft)

        # Cell overlays (always alpha)
        tile = pygame.Surface((cell, cell), pygame.SRCALPHA)
        for r in range(rows):
            for c in range(cols):
                rect = self._cell_rect(c, r)
                key  = (c, r)
                on   = key in valid
                hov  = key == self._hover

                if on and hov:
                    color, alpha = VALID_HOV, _VALID_ALPHA
                elif on:
                    color, alpha = VALID_ON, _VALID_ALPHA
                elif hov:
                    color, alpha = CELL_HOV, _HOVER_ALPHA if has_image else 200
                elif has_image:
                    color, alpha = BLACK, _INVALID_ALPHA
                else:
                    color, alpha = CELL_OFF, 255

                tile.fill((0, 0, 0, 0))
                tile.fill((*color, alpha))
                surf.blit(tile, rect.topleft)

                # Grid lines
                pygame.draw.rect(surf, GRID_LINE, rect, 1)

                # col,row label (skip if cells are very small)
                if cell >= 36:
                    label_col = (15, 15, 15) if (on and not has_image) else MID_GREY
                    t = self._f11.render(f"{c},{r}", True, label_col)
                    surf.blit(t, (rect.x + 3, rect.y + 3))

        # Status line
        t = self._f12.render(f"{len(valid)} cells selected", True, LT_GREY)
        surf.blit(t, (6, 6))

    def _draw_picker(self) -> None:
        """Draw the thumbnail image browser over the grid area."""
        surf = self._surf
        pygame.draw.rect(surf, (15, 15, 20), (0, 0, GRID_W, H))

        cur_image = self._lv.get("image")

        for name, rect in self._thumb_rects():
            thumb = self._get_thumb(name, rect.w - 2, rect.h - 2)
            if thumb:
                surf.blit(thumb, (rect.x + 1, rect.y + 1))
            else:
                pygame.draw.rect(surf, (40, 40, 50), rect)

            # Border: cyan if current, white if hovered, grey otherwise
            if name == cur_image:
                border, bw = CYAN, 3
            elif name == self._thumb_hover:
                border, bw = WHITE, 2
            else:
                border, bw = MID_GREY, 1
            pygame.draw.rect(surf, border, rect, bw)

            # Short filename label at bottom of thumbnail
            short = Path(name).name[:22]
            t = self._f11.render(short, True, WHITE)
            ts = pygame.Surface((t.get_width() + 4, t.get_height() + 2), pygame.SRCALPHA)
            ts.fill((0, 0, 0, 160))
            ts.blit(t, (2, 1))
            surf.blit(ts, (rect.x + 1, rect.bottom - ts.get_height() - 1))

        # Header bar
        header = self._f15.render(
            "PICK IMAGE — click to assign   ESC to cancel", True, CYAN)
        hs = pygame.Surface((GRID_W, header.get_height() + 8), pygame.SRCALPHA)
        hs.fill((0, 0, 0, 180))
        hs.blit(header, (8, 4))
        surf.blit(hs, (0, 0))

    # ── Drawing — sidebar ──────────────────────────────────────────────────

    def _sidebar(self) -> None:
        surf = self._surf
        sx   = GRID_W
        self._btns = []

        pygame.draw.rect(surf, SIDEBAR_BG, (sx, 0, SIDE_W, H))
        pygame.draw.line(surf, MID_GREY, (sx, 0), (sx, H), 1)

        y  = 12
        lv = self._lv

        # ── Nav header ─────────────────────────────────────────────────────
        nav = f"LEVEL  {self._idx + 1} / {len(self._levels)}"
        t = self._f20.render(nav, True, CYAN)
        surf.blit(t, (sx + 8, y))
        y += t.get_height()
        if self._dirty:
            t = self._f11.render("unsaved changes", True, YELLOW)
            surf.blit(t, (sx + 8, y))
        y += 14

        y = self._btn_row(surf, sx, y,
            ("< PREV",  lambda: self._nav(-1)),
            ("NEXT >",  lambda: self._nav(+1)),
        )
        y += 6

        # ── Prompt ─────────────────────────────────────────────────────────
        y = self._label(surf, sx, y, "PROMPT  (click or E to edit)")
        text = (self._buf + "|") if self._editing else lv.get("prompt", "")
        y = self._text_field(surf, sx, y, text, self._editing, self._edit_prompt)
        y += 4

        # ── Difficulty ─────────────────────────────────────────────────────
        y = self._label(surf, sx, y, "DIFFICULTY  (+/-)")
        diff = lv.get("difficulty", 1)
        stars = "★" * diff + "☆" * (5 - diff)
        y = self._stepper(surf, sx, y, f"{diff}/5  {stars}",
            lambda: self._adj_diff(-1), lambda: self._adj_diff(+1))
        y += 4

        # ── Grid ───────────────────────────────────────────────────────────
        y = self._label(surf, sx, y, "GRID SIZE")
        cols, rows = self._grid_dims()
        y = self._labeled_stepper(surf, sx, y, "cols", str(cols),
            lambda: self._adj_cols(-1), lambda: self._adj_cols(+1))
        y = self._labeled_stepper(surf, sx, y, "rows", str(rows),
            lambda: self._adj_rows(-1), lambda: self._adj_rows(+1))
        y += 4

        # ── Timer ──────────────────────────────────────────────────────────
        y = self._label(surf, sx, y, "TIMER  (↑↓ \xb15s)")
        timer = lv.get("timer_s", 40)
        y = self._stepper(surf, sx, y, f"{timer}s",
            lambda: self._adj_timer(-5), lambda: self._adj_timer(+5))
        y += 4

        # ── Hold ───────────────────────────────────────────────────────────
        hold = lv.get("hold_s")
        y = self._label(surf, sx, y, "HOLD DURATION  (optional)")
        if hold is None:
            y = self._btn(surf, sx, y, SIDE_W - 16, "ADD HOLD", self._add_hold)
        else:
            y = self._stepper(surf, sx, y, f"{hold:.1f}s",
                lambda: self._adj_hold(-0.5), lambda: self._adj_hold(+0.5))
            y = self._btn(surf, sx, y, SIDE_W - 16, "REMOVE HOLD", self._remove_hold)
        y += 4

        # ── Image ──────────────────────────────────────────────────────────
        img = lv.get("image")
        y = self._label(surf, sx, y, "IMAGE")
        if img:
            # Show short filename
            short = Path(img).name
            t = self._f11.render(short[:34], True, LT_GREY)
            surf.blit(t, (sx + 8, y))
            y += t.get_height() + 3
            y = self._btn(surf, sx, y, (SIDE_W - 20) // 2,
                "CHANGE", lambda: setattr(self, "_picking", True))
            # draw CLEAR next to it (already advanced y, back up)
            clear_rect = pygame.Rect(sx + 8 + (SIDE_W - 20) // 2 + 4, y - 28,
                                     (SIDE_W - 20) // 2, 24)
            mx, my = pygame.mouse.get_pos()
            pygame.draw.rect(surf, (BTN_HOV if clear_rect.collidepoint(mx, my) else BTN_NRM),
                             clear_rect, border_radius=3)
            ct = self._f12.render("CLEAR", True, WHITE)
            surf.blit(ct, ct.get_rect(center=clear_rect.center))
            self._btns.append((clear_rect, self._clear_image))
        else:
            y = self._btn(surf, sx, y, SIDE_W - 16,
                "PICK IMAGE ▶", lambda: setattr(self, "_picking", True))
        y += 4

        # ── Crop alignment ─────────────────────────────────────────────────
        if img:
            y = self._label(surf, sx, y, "CROP ALIGN")
            y = self._align_pad(surf, sx, y)
            y += 4

        # ── Valid cells list ───────────────────────────────────────────────
        vset = self._vset
        if vset:
            y = self._label(surf, sx, y, "VALID CELLS")
            cell_str = "  ".join(f"({c},{r})" for c, r in sorted(vset))
            for line in _wrap(cell_str, 32):
                t = self._f11.render(line, True, (0, 200, 80))
                surf.blit(t, (sx + 8, y))
                y += t.get_height() + 1
            y += 3

        # ── Bottom actions ─────────────────────────────────────────────────
        action_y = max(y + 4, H - 148)
        pygame.draw.line(surf, MID_GREY, (sx, action_y), (sx + SIDE_W, action_y), 1)
        y = action_y + 6

        y = self._btn(surf, sx, y, SIDE_W - 16, "CLEAR CELLS  (Ctrl+C)",
            self._clear, col=RED)
        y = self._btn(surf, sx, y, SIDE_W - 16, "+ NEW LEVEL  (Ctrl+N)",
            self._new_level)
        y = self._btn(surf, sx, y, SIDE_W - 16, "DELETE LEVEL  (Ctrl+Del)",
            self._del_level, col=RED)

        save_y = H - 44
        pygame.draw.line(surf, MID_GREY, (sx, save_y), (sx + SIDE_W, save_y), 1)
        self._btn(surf, sx, save_y + 6, SIDE_W - 16,
            "SAVE  (Ctrl+S)", self._do_save, col=GREEN)

        # ── Flash message ──────────────────────────────────────────────────
        if self._flash_msg and self._flash_t > 0:
            alpha = min(255, int(255 * self._flash_t))
            msg_s = self._f15.render(self._flash_msg, True, WHITE)
            msg_s.set_alpha(alpha)
            surf.blit(msg_s, (sx + 8, H // 2 - 10))

    def _align_pad(self, surf, sx, y) -> int:
        """3x3 anchor pad — which part of an off-aspect photo survives the crop."""
        cur   = self._align()
        cell  = 26
        pad   = 3
        mx, my = pygame.mouse.get_pos()
        names = [n for n, _ in sorted(ANCHORS.items(), key=lambda kv: (kv[1][1], kv[1][0]))]

        for i, name in enumerate(names):
            rect = pygame.Rect(sx + 8 + (i % 3) * (cell + pad),
                               y + (i // 3) * (cell + pad), cell, cell)
            on  = name == cur
            hov = rect.collidepoint(mx, my)
            col = CYAN if on else (BTN_HOV if hov else BTN_NRM)
            pygame.draw.rect(surf, col, rect, border_radius=3)
            # A dot marks the kept region's anchor within the cell.
            fx, fy = ANCHORS[name]
            dot = (rect.x + 5 + int((cell - 10) * fx), rect.y + 5 + int((cell - 10) * fy))
            pygame.draw.circle(surf, (20, 20, 28) if on else LT_GREY, dot, 3)
            self._btns.append((rect, lambda n=name: self._set_align(n)))

        t = self._f11.render(cur, True, CYAN)
        surf.blit(t, (sx + 8 + 3 * (cell + pad) + 6, y + cell))
        return y + 3 * (cell + pad) + 2

    # ── Sidebar widget helpers ─────────────────────────────────────────────

    def _label(self, surf, sx, y, text):
        t = self._f11.render(text, True, LT_GREY)
        surf.blit(t, (sx + 8, y))
        return y + t.get_height() + 2

    def _text_field(self, surf, sx, y, text, active, click_fn):
        pad  = 4
        lines = _wrap(text, 28)[:3]
        lh    = self._f12.get_height() + 1
        fh    = max(22, len(lines) * lh + pad * 2)
        rect  = pygame.Rect(sx + 8, y, SIDE_W - 16, fh)
        bg     = (55, 55, 80) if active else FIELD_BG
        border = CYAN if active else MID_GREY
        pygame.draw.rect(surf, bg,     rect, border_radius=3)
        pygame.draw.rect(surf, border, rect, 1, border_radius=3)
        for i, line in enumerate(lines):
            t = self._f12.render(line, True, WHITE)
            surf.blit(t, (rect.x + pad, rect.y + pad + i * lh))
        self._btns.append((rect, click_fn))
        return y + fh + 2

    def _stepper(self, surf, sx, y, label, on_dec, on_inc):
        bw = 26
        vw = SIDE_W - 16 - 2 * bw - 8
        x  = sx + 8
        mx, my = pygame.mouse.get_pos()
        h = 22
        for rx, txt, fn in [
            (x,                    "-", on_dec),
            (x + bw + 4 + vw + 4, "+", on_inc),
        ]:
            r = pygame.Rect(rx, y, bw, h)
            pygame.draw.rect(surf, BTN_HOV if r.collidepoint(mx, my) else BTN_NRM,
                             r, border_radius=3)
            t = self._f15.render(txt, True, WHITE)
            surf.blit(t, t.get_rect(center=r.center))
            self._btns.append((r, fn))
        vr = pygame.Rect(x + bw + 4, y, vw, h)
        pygame.draw.rect(surf, FIELD_BG, vr, border_radius=3)
        t = self._f15.render(label, True, WHITE)
        surf.blit(t, t.get_rect(center=vr.center))
        return y + h + 4

    def _labeled_stepper(self, surf, sx, y, lbl, val, on_dec, on_inc):
        lw = 36
        bw = 22
        vw = 28
        x  = sx + 8
        mx, my = pygame.mouse.get_pos()
        h = 20
        t = self._f11.render(lbl, True, LT_GREY)
        surf.blit(t, (x, y + 3))
        bx = x + lw
        for rx, txt, fn in [
            (bx,                    "-", on_dec),
            (bx + bw + 2 + vw + 2, "+", on_inc),
        ]:
            r = pygame.Rect(rx, y, bw, h)
            pygame.draw.rect(surf, BTN_HOV if r.collidepoint(mx, my) else BTN_NRM,
                             r, border_radius=3)
            t2 = self._f12.render(txt, True, WHITE)
            surf.blit(t2, t2.get_rect(center=r.center))
            self._btns.append((r, fn))
        vr = pygame.Rect(bx + bw + 2, y, vw, h)
        pygame.draw.rect(surf, FIELD_BG, vr, border_radius=3)
        t2 = self._f12.render(val, True, WHITE)
        surf.blit(t2, t2.get_rect(center=vr.center))
        return y + h + 3

    def _btn_row(self, surf, sx, y, *buttons):
        bw  = (SIDE_W - 20) // len(buttons)
        x   = sx + 8
        mx, my = pygame.mouse.get_pos()
        h   = 24
        for label, fn in buttons:
            r = pygame.Rect(x, y, bw - 4, h)
            pygame.draw.rect(surf, BTN_HOV if r.collidepoint(mx, my) else BTN_NRM,
                             r, border_radius=3)
            t = self._f12.render(label, True, WHITE)
            surf.blit(t, t.get_rect(center=r.center))
            self._btns.append((r, fn))
            x += bw
        return y + h + 4

    def _btn(self, surf, sx, y, width, label, fn, col=None):
        rect = pygame.Rect(sx + 8, y, width, 24)
        mx, my = pygame.mouse.get_pos()
        hov = rect.collidepoint(mx, my)
        if col:
            bg = tuple(min(255, c + 25) for c in col) if hov else col
        else:
            bg = BTN_HOV if hov else BTN_NRM
        pygame.draw.rect(surf, bg, rect, border_radius=3)
        t = self._f12.render(label, True, WHITE)
        surf.blit(t, t.get_rect(center=rect.center))
        self._btns.append((rect, fn))
        return y + 28

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        running = True
        while running:
            dt = self._clock.tick(60) / 1000.0
            if self._flash_t > 0:
                self._flash_t = max(0.0, self._flash_t - dt)

            for ev in pygame.event.get():
                running = self._on_event(ev)

            self._surf.fill(DK_GREY)

            if self._picking:
                self._draw_picker()
            else:
                self._draw_grid()

            self._sidebar()
            pygame.display.flip()

        if self._dirty:
            print("WARNING: unsaved changes. Re-open and Ctrl+S to save.")
        pygame.quit()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="BodyCaptcha level editor")
    ap.add_argument("--levels", type=Path, default=None, metavar="PATH",
                    help="Alternate levels JSON to edit (default: bodycaptcha-levels.json)")
    args = ap.parse_args()
    set_levels_path(args.levels)
    Editor().run()
