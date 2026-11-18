"""The editor's three screens: the cell grid, the image picker, and the sidebar; each draws the model and records nothing else."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pygame

from crop import ANCHORS
from editor.level_model import Cell, LevelModel
from editor.theme import (
    BLACK, BTN_HOV, BTN_NRM, CELL_HOV, CELL_OFF, CYAN, DK_GREY, GRID_LINE, GRID_W, GREEN,
    H, LT_GREY, MID_GREY, RED, SIDEBAR_BG, SIDE_W, VALID_HOV, VALID_ON, WHITE, YELLOW, Fonts,
)
from editor.widgets import Widgets, wrap
from levels import Levels

# alpha for overlays when an image is behind the grid
_VALID_ALPHA   = 160
_INVALID_ALPHA = 55   # subtle dark tint
_HOVER_ALPHA   = 90

_THUMB_COLS = 4


@dataclass
class UiState:
    """What the screens show beyond the model: modes, hover, and the flash message."""
    editing:     bool = False                  # prompt text field active
    buf:         str = ""                      # the prompt being typed
    picking:     bool = False                  # thumbnail browser open
    hover:       Cell | None = None            # hovered grid cell
    thumb_hover: str | None = None             # hovered image in picker
    flash_msg:   str = ""
    flash_t:     float = 0.0

    def flash(self, msg: str) -> None:
        self.flash_msg = msg
        self.flash_t   = 2.0


class SidebarActions(Protocol):
    """What the sidebar's buttons ask of the editor beyond editing the model."""
    def nav(self, d: int) -> None: ...
    def edit_prompt(self) -> None: ...
    def open_picker(self) -> None: ...
    def save(self) -> None: ...


# ── Geometry (pure: no surface needed) ─────────────────────────────────────

def cell_size(cols: int, rows: int) -> int:
    return min(GRID_W // cols, H // rows)


def grid_origin(cols: int, rows: int) -> tuple[int, int]:
    cell = cell_size(cols, rows)
    return (GRID_W - cell * cols) // 2, (H - cell * rows) // 2


def preview_rect(cols: int, rows: int) -> pygame.Rect:
    """Where a level image is drawn — the cell grid itself.

    The game blits the photo into `Grid.bounds_rect`, so the editor must
    use the same rect or the anchor you pick here frames a different crop
    than the show renders.
    """
    cell   = cell_size(cols, rows)
    ox, oy = grid_origin(cols, rows)
    return pygame.Rect(ox, oy, cell * cols, cell * rows)


def cell_rect(cols: int, rows: int, col: int, row: int) -> pygame.Rect:
    cell   = cell_size(cols, rows)
    ox, oy = grid_origin(cols, rows)
    return pygame.Rect(ox + col * cell, oy + row * cell, cell, cell)


def px_to_cell(cols: int, rows: int, px: int, py: int) -> Cell | None:
    for r in range(rows):
        for c in range(cols):
            if cell_rect(cols, rows, c, r).collidepoint(px, py):
                return (c, r)
    return None


def thumb_rects(names: list[str]) -> list[tuple[str, pygame.Rect]]:
    if not names:                      # nothing to browse (this used to divide by zero)
        return []
    n     = len(names)
    cols  = _THUMB_COLS
    rows  = (n + cols - 1) // cols
    pad   = 4
    tw    = (GRID_W - pad * (cols + 1)) // cols
    th    = (H - pad * (rows + 1)) // rows
    result = []
    for i, name in enumerate(names):
        c = i % cols
        r = i // cols
        x = pad + c * (tw + pad)
        y = pad + r * (th + pad)
        result.append((name, pygame.Rect(x, y, tw, th)))
    return result


def px_to_image(names: list[str], px: int, py: int) -> str | None:
    for name, rect in thumb_rects(names):
        if rect.collidepoint(px, py):
            return name
    return None


# ── Image cache ────────────────────────────────────────────────────────────

class ImageCache:
    """Scaled level photos, remembered by size so redraws cost nothing.

    A photo that fails to load is remembered too, so it is logged once rather
    than on every frame.
    """

    def __init__(self, levels: Levels) -> None:
        self._levels = levels
        self._bg:    dict[str, pygame.Surface | None] = {}
        self._thumb: dict[str, pygame.Surface | None] = {}

    def bg(self, name: str, w: int, h: int, align: str) -> pygame.Surface | None:
        key = f"{name}_{w}_{h}_{align}"
        if key not in self._bg:
            self._bg[key] = self._levels.background(name, w, h, align)
        return self._bg[key]

    def thumb(self, name: str, tw: int, th: int) -> pygame.Surface | None:
        key = f"{name}_{tw}_{th}"
        if key not in self._thumb:
            self._thumb[key] = self._levels.background(name, tw, th)
        return self._thumb[key]


# ── Screens ────────────────────────────────────────────────────────────────

class GridView:
    """The cell grid, with the level photo behind it."""

    def __init__(self, surf: pygame.Surface, fonts: Fonts, model: LevelModel,
                 ui: UiState, images: ImageCache) -> None:
        self._surf, self._fonts, self._model, self._ui, self._images = (
            surf, fonts, model, ui, images)

    def draw(self) -> None:
        surf, model, ui = self._surf, self._model, self._ui
        cols, rows = model.grid_dims()
        valid = model.valid_cells
        cell  = cell_size(cols, rows)
        image = model.level.get("image")
        has_image = bool(image)

        # Background — photo confined to the cell grid, letterboxed around it
        pygame.draw.rect(surf, DK_GREY, (0, 0, GRID_W, H))
        if has_image:
            rect = preview_rect(cols, rows)
            bg   = self._images.bg(image, rect.w, rect.h, model.align())
            if bg:
                surf.blit(bg, rect.topleft)

        # Cell overlays (always alpha)
        tile = pygame.Surface((cell, cell), pygame.SRCALPHA)
        for r in range(rows):
            for c in range(cols):
                rect = cell_rect(cols, rows, c, r)
                key  = (c, r)
                on   = key in valid
                hov  = key == ui.hover

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
                    t = self._fonts.f11.render(f"{c},{r}", True, label_col)
                    surf.blit(t, (rect.x + 3, rect.y + 3))

        # Status line
        t = self._fonts.f12.render(f"{len(valid)} cells selected", True, LT_GREY)
        surf.blit(t, (6, 6))


class PickerView:
    """The thumbnail image browser, drawn over the grid area."""

    def __init__(self, surf: pygame.Surface, fonts: Fonts, model: LevelModel,
                 ui: UiState, images: ImageCache, names: list[str]) -> None:
        self._surf, self._fonts, self._model, self._ui, self._images = (
            surf, fonts, model, ui, images)
        self.names = names

    def draw(self) -> None:
        surf = self._surf
        pygame.draw.rect(surf, (15, 15, 20), (0, 0, GRID_W, H))

        cur_image = self._model.level.get("image")

        for name, rect in thumb_rects(self.names):
            thumb = self._images.thumb(name, rect.w - 2, rect.h - 2)
            if thumb:
                surf.blit(thumb, (rect.x + 1, rect.y + 1))
            else:
                pygame.draw.rect(surf, (40, 40, 50), rect)

            # Border: cyan if current, white if hovered, grey otherwise
            if name == cur_image:
                border, bw = CYAN, 3
            elif name == self._ui.thumb_hover:
                border, bw = WHITE, 2
            else:
                border, bw = MID_GREY, 1
            pygame.draw.rect(surf, border, rect, bw)

            # Short filename label at bottom of thumbnail
            short = Path(name).name[:22]
            t = self._fonts.f11.render(short, True, WHITE)
            ts = pygame.Surface((t.get_width() + 4, t.get_height() + 2), pygame.SRCALPHA)
            ts.fill((0, 0, 0, 160))
            ts.blit(t, (2, 1))
            surf.blit(ts, (rect.x + 1, rect.bottom - ts.get_height() - 1))

        # Header bar
        header = self._fonts.f15.render(
            "PICK IMAGE — click to assign   ESC to cancel", True, CYAN)
        hs = pygame.Surface((GRID_W, header.get_height() + 8), pygame.SRCALPHA)
        hs.fill((0, 0, 0, 180))
        hs.blit(header, (8, 4))
        surf.blit(hs, (0, 0))


class SidebarView:
    """The right-hand panel: level navigation and every field of the selected level."""

    def __init__(self, widgets: Widgets, model: LevelModel, ui: UiState,
                 actions: SidebarActions) -> None:
        self._w, self._model, self._ui, self._actions = widgets, model, ui, actions

    def draw(self) -> list:
        """Draw the panel; returns the click targets it registered."""
        w, model, ui, act = self._w, self._model, self._ui, self._actions
        surf, fonts, sx = w.surf, w.fonts, w.x
        w.begin()

        pygame.draw.rect(surf, SIDEBAR_BG, (sx, 0, SIDE_W, H))
        pygame.draw.line(surf, MID_GREY, (sx, 0), (sx, H), 1)

        y  = 12
        lv = model.level

        # ── Nav header ─────────────────────────────────────────────────────
        nav = f"LEVEL  {model.idx + 1} / {len(model.levels)}"
        t = fonts.f20.render(nav, True, CYAN)
        surf.blit(t, (sx + 8, y))
        y += t.get_height()
        if model.dirty:
            t = fonts.f11.render("unsaved changes", True, YELLOW)
            surf.blit(t, (sx + 8, y))
        y += 14

        y = w.btn_row(y,
            ("< PREV",  lambda: act.nav(-1)),
            ("NEXT >",  lambda: act.nav(+1)),
        )
        y += 6

        # ── Prompt ─────────────────────────────────────────────────────────
        y = w.label(y, "PROMPT  (click or E to edit)")
        text = (ui.buf + "|") if ui.editing else lv.get("prompt", "")
        y = w.text_field(y, text, ui.editing, act.edit_prompt)
        y += 4

        # ── Difficulty ─────────────────────────────────────────────────────
        y = w.label(y, "DIFFICULTY  (+/-)")
        diff = lv.get("difficulty", 1)
        stars = "★" * diff + "☆" * (5 - diff)
        y = w.stepper(y, f"{diff}/5  {stars}",
            lambda: model.adj_difficulty(-1), lambda: model.adj_difficulty(+1))
        y += 4

        # ── Grid ───────────────────────────────────────────────────────────
        y = w.label(y, "GRID SIZE")
        cols, rows = model.grid_dims()
        y = w.labeled_stepper(y, "cols", str(cols),
            lambda: model.adj_cols(-1), lambda: model.adj_cols(+1))
        y = w.labeled_stepper(y, "rows", str(rows),
            lambda: model.adj_rows(-1), lambda: model.adj_rows(+1))
        y += 4

        # ── Timer ──────────────────────────────────────────────────────────
        y = w.label(y, "TIMER  (↑↓ \xb15s)")
        timer = lv.get("timer_s", 40)
        y = w.stepper(y, f"{timer}s",
            lambda: model.adj_timer(-5), lambda: model.adj_timer(+5))
        y += 4

        # ── Hold ───────────────────────────────────────────────────────────
        hold = lv.get("hold_s")
        y = w.label(y, "HOLD DURATION  (optional)")
        if hold is None:
            y = w.btn(y, SIDE_W - 16, "ADD HOLD", model.add_hold)
        else:
            y = w.stepper(y, f"{hold:.1f}s",
                lambda: model.adj_hold(-0.5), lambda: model.adj_hold(+0.5))
            y = w.btn(y, SIDE_W - 16, "REMOVE HOLD", model.remove_hold)
        y += 4

        # ── Image ──────────────────────────────────────────────────────────
        img = lv.get("image")
        y = w.label(y, "IMAGE")
        if img:
            # Show short filename
            short = Path(img).name
            t = fonts.f11.render(short[:34], True, LT_GREY)
            surf.blit(t, (sx + 8, y))
            y += t.get_height() + 3
            y = w.btn(y, (SIDE_W - 20) // 2, "CHANGE", act.open_picker)
            # draw CLEAR next to it (already advanced y, back up)
            clear_rect = pygame.Rect(sx + 8 + (SIDE_W - 20) // 2 + 4, y - 28,
                                     (SIDE_W - 20) // 2, 24)
            mx, my = pygame.mouse.get_pos()
            pygame.draw.rect(surf, (BTN_HOV if clear_rect.collidepoint(mx, my) else BTN_NRM),
                             clear_rect, border_radius=3)
            ct = fonts.f12.render("CLEAR", True, WHITE)
            surf.blit(ct, ct.get_rect(center=clear_rect.center))
            w.targets.append((clear_rect, lambda: model.set_image(None)))
        else:
            y = w.btn(y, SIDE_W - 16, "PICK IMAGE ▶", act.open_picker)
        y += 4

        # ── Crop alignment ─────────────────────────────────────────────────
        if img:
            y = w.label(y, "CROP ALIGN")
            y = self._align_pad(y)
            y += 4

        # ── Valid cells list ───────────────────────────────────────────────
        vset = model.valid_cells
        if vset:
            y = w.label(y, "VALID CELLS")
            cell_str = "  ".join(f"({c},{r})" for c, r in sorted(vset))
            for line in wrap(cell_str, 32):
                t = fonts.f11.render(line, True, (0, 200, 80))
                surf.blit(t, (sx + 8, y))
                y += t.get_height() + 1
            y += 3

        # ── Bottom actions ─────────────────────────────────────────────────
        action_y = max(y + 4, H - 148)
        pygame.draw.line(surf, MID_GREY, (sx, action_y), (sx + SIDE_W, action_y), 1)
        y = action_y + 6

        y = w.btn(y, SIDE_W - 16, "CLEAR CELLS  (Ctrl+C)", model.clear_cells, col=RED)
        y = w.btn(y, SIDE_W - 16, "+ NEW LEVEL  (Ctrl+N)", model.new_level)
        y = w.btn(y, SIDE_W - 16, "DELETE LEVEL  (Ctrl+Del)", model.delete_level, col=RED)

        save_y = H - 44
        pygame.draw.line(surf, MID_GREY, (sx, save_y), (sx + SIDE_W, save_y), 1)
        w.btn(save_y + 6, SIDE_W - 16, "SAVE  (Ctrl+S)", act.save, col=GREEN)

        # ── Flash message ──────────────────────────────────────────────────
        if ui.flash_msg and ui.flash_t > 0:
            alpha = min(255, int(255 * ui.flash_t))
            msg_s = fonts.f15.render(ui.flash_msg, True, WHITE)
            msg_s.set_alpha(alpha)
            surf.blit(msg_s, (sx + 8, H // 2 - 10))

        return w.targets

    def _align_pad(self, y: int) -> int:
        """3x3 anchor pad — which part of an off-aspect photo survives the crop."""
        w, model = self._w, self._model
        surf, sx = w.surf, w.x
        cur   = model.align()
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
            w.targets.append((rect, lambda n=name: model.set_align(n)))

        t = w.fonts.f11.render(cur, True, CYAN)
        surf.blit(t, (sx + 8 + 3 * (cell + pad) + 6, y + cell))
        return y + 3 * (cell + pad) + 2
