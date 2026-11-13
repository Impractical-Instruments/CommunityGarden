#!/usr/bin/env python3
"""BodyCaptcha level editor/visualizer — standalone, no camera needed.

This file is the window, the event loop and the command line. The level list
and its edits are `editor/level_model.py`; the screens are `editor/views.py`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from editor.level_model import LevelModel
from editor.theme import DK_GREY, GRID_W, H, W, Fonts
from editor.views import (
    GridView, ImageCache, PickerView, SidebarView, UiState, px_to_cell, px_to_image,
)
from editor.widgets import Widgets
from levels import Levels


def caption(levels: Levels) -> str:
    return f"BodyCaptcha Level Editor — {levels.path}"


class Editor:
    def __init__(self, levels: Levels) -> None:
        pygame.init()
        pygame.display.set_caption(caption(levels))
        self._surf  = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        self._clock = pygame.time.Clock()

        fonts   = Fonts.load()
        images  = ImageCache(levels)
        self.model = LevelModel.open(levels)
        self.ui    = UiState()
        self._targets: list = []                   # sidebar click targets, from the last draw

        self._grid    = GridView(self._surf, fonts, self.model, self.ui, images)
        self._picker  = PickerView(self._surf, fonts, self.model, self.ui, images,
                                   levels.image_names())
        self._sidebar = SidebarView(Widgets(self._surf, fonts), self.model, self.ui, self)

    # ── Actions the sidebar and keys share ─────────────────────────────────

    def nav(self, d: int) -> None:
        self.model.nav(d)
        self.ui.editing = False
        self.ui.picking = False

    def edit_prompt(self) -> None:
        self.ui.editing = True
        self.ui.buf     = self.model.level.get("prompt", "")

    def open_picker(self) -> None:
        self.ui.picking = True

    def save(self) -> None:
        if self.ui.editing:
            self.model.set_prompt(self.ui.buf)
            self.ui.editing = False
        self.model.save()

    # ── Events ─────────────────────────────────────────────────────────────

    def _on_event(self, ev: pygame.event.Event) -> bool:
        ui = self.ui
        if ev.type == pygame.QUIT:
            return False

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE and ui.picking:
                ui.picking = False
                return True
            if ui.editing:
                self._key_prompt(ev)
            else:
                self._key_global(ev)

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self._on_click(ev.pos)

        if ev.type == pygame.MOUSEMOTION:
            x, y = ev.pos
            if ui.picking and x < GRID_W:
                ui.thumb_hover = px_to_image(self._picker.names, x, y)
            elif x < GRID_W and not ui.picking:
                ui.hover = px_to_cell(*self.model.grid_dims(), x, y)
                ui.thumb_hover = None
            else:
                ui.hover = None
                ui.thumb_hover = None

        return True

    def _key_prompt(self, ev: pygame.event.Event) -> None:
        ui = self.ui
        if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.model.set_prompt(ui.buf)
            ui.editing = False
        elif ev.key == pygame.K_BACKSPACE:
            ui.buf = ui.buf[:-1]
        else:
            ch = ev.unicode
            if ch and ch.isprintable():
                ui.buf += ch

    def _key_global(self, ev: pygame.event.Event) -> None:
        m    = self.model
        ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
        k    = ev.key

        if ctrl:
            if k == pygame.K_s:        self.save()
            elif k == pygame.K_n:      m.new_level()
            elif k == pygame.K_DELETE: m.delete_level()
            elif k == pygame.K_c:      m.clear_cells()
        else:
            if k == pygame.K_LEFT:     self.nav(-1)
            elif k == pygame.K_RIGHT:  self.nav(+1)
            elif k == pygame.K_e:      self.edit_prompt()
            elif k in (pygame.K_EQUALS, pygame.K_PLUS): m.adj_difficulty(+1)
            elif k == pygame.K_MINUS:  m.adj_difficulty(-1)
            elif k == pygame.K_UP:     m.adj_timer(+5)
            elif k == pygame.K_DOWN:   m.adj_timer(-5)

    def _on_click(self, pos: tuple[int, int]) -> None:
        x, y = pos
        if x < GRID_W:
            if self.ui.picking:
                name = px_to_image(self._picker.names, x, y)
                if name:
                    self.model.set_image(name)
                    self.ui.picking = False
                    self.ui.flash(f"Image set: {name}")
            else:
                cell = px_to_cell(*self.model.grid_dims(), x, y)
                if cell:
                    self.model.toggle(cell)
        else:
            for rect, action in self._targets:
                if rect.collidepoint(x, y):
                    action()
                    break

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        running = True
        while running:
            dt = self._clock.tick(60) / 1000.0
            if self.ui.flash_t > 0:
                self.ui.flash_t = max(0.0, self.ui.flash_t - dt)

            for ev in pygame.event.get():
                running = self._on_event(ev)

            notice = self.model.take_notice()
            if notice:
                self.ui.flash(notice)

            self._surf.fill(DK_GREY)

            if self.ui.picking:
                self._picker.draw()
            else:
                self._grid.draw()

            self._targets = self._sidebar.draw()
            pygame.display.flip()

        if self.model.dirty:
            print("WARNING: unsaved changes. Re-open and Ctrl+S to save.")
        pygame.quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="BodyCaptcha level editor")
    ap.add_argument("--levels", type=Path, default=None, metavar="PATH",
                    help="Alternate levels JSON to edit (default: bodycaptcha-levels.json)")
    args = ap.parse_args()
    Editor(Levels(args.levels)).run()
