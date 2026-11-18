"""The sidebar's drawable controls (labels, fields, steppers, buttons) and the click targets they register."""
from __future__ import annotations

from typing import Callable

import pygame

from editor.theme import (
    BTN_HOV, BTN_NRM, CYAN, FIELD_BG, GRID_W, LT_GREY, MID_GREY, SIDE_W, WHITE, Fonts,
)

Action = Callable[[], object]


def wrap(text: str, max_chars: int) -> list[str]:
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


class Widgets:
    """Draws sidebar controls onto `surf` and records where each can be clicked.

    Every method draws at vertical offset `y` and returns the next free `y`.
    `targets` is cleared by whoever starts a sidebar redraw (`begin`).
    """

    def __init__(self, surf: pygame.Surface, fonts: Fonts) -> None:
        self.surf    = surf
        self.fonts   = fonts
        self.x       = GRID_W
        self.targets: list[tuple[pygame.Rect, Action]] = []

    def begin(self) -> None:
        self.targets = []

    def label(self, y: int, text: str) -> int:
        t = self.fonts.f11.render(text, True, LT_GREY)
        self.surf.blit(t, (self.x + 8, y))
        return y + t.get_height() + 2

    def text_field(self, y: int, text: str, active: bool, click_fn: Action) -> int:
        pad   = 4
        lines = wrap(text, 28)[:3]
        lh    = self.fonts.f12.get_height() + 1
        fh    = max(22, len(lines) * lh + pad * 2)
        rect  = pygame.Rect(self.x + 8, y, SIDE_W - 16, fh)
        bg     = (55, 55, 80) if active else FIELD_BG
        border = CYAN if active else MID_GREY
        pygame.draw.rect(self.surf, bg,     rect, border_radius=3)
        pygame.draw.rect(self.surf, border, rect, 1, border_radius=3)
        for i, line in enumerate(lines):
            t = self.fonts.f12.render(line, True, WHITE)
            self.surf.blit(t, (rect.x + pad, rect.y + pad + i * lh))
        self.targets.append((rect, click_fn))
        return y + fh + 2

    def stepper(self, y: int, label: str, on_dec: Action, on_inc: Action) -> int:
        surf = self.surf
        bw = 26
        vw = SIDE_W - 16 - 2 * bw - 8
        x  = self.x + 8
        mx, my = pygame.mouse.get_pos()
        h = 22
        for rx, txt, fn in [
            (x,                    "-", on_dec),
            (x + bw + 4 + vw + 4, "+", on_inc),
        ]:
            r = pygame.Rect(rx, y, bw, h)
            pygame.draw.rect(surf, BTN_HOV if r.collidepoint(mx, my) else BTN_NRM,
                             r, border_radius=3)
            t = self.fonts.f15.render(txt, True, WHITE)
            surf.blit(t, t.get_rect(center=r.center))
            self.targets.append((r, fn))
        vr = pygame.Rect(x + bw + 4, y, vw, h)
        pygame.draw.rect(surf, FIELD_BG, vr, border_radius=3)
        t = self.fonts.f15.render(label, True, WHITE)
        surf.blit(t, t.get_rect(center=vr.center))
        return y + h + 4

    def labeled_stepper(self, y: int, lbl: str, val: str,
                        on_dec: Action, on_inc: Action) -> int:
        surf = self.surf
        lw = 36
        bw = 22
        vw = 28
        x  = self.x + 8
        mx, my = pygame.mouse.get_pos()
        h = 20
        t = self.fonts.f11.render(lbl, True, LT_GREY)
        surf.blit(t, (x, y + 3))
        bx = x + lw
        for rx, txt, fn in [
            (bx,                    "-", on_dec),
            (bx + bw + 2 + vw + 2, "+", on_inc),
        ]:
            r = pygame.Rect(rx, y, bw, h)
            pygame.draw.rect(surf, BTN_HOV if r.collidepoint(mx, my) else BTN_NRM,
                             r, border_radius=3)
            t2 = self.fonts.f12.render(txt, True, WHITE)
            surf.blit(t2, t2.get_rect(center=r.center))
            self.targets.append((r, fn))
        vr = pygame.Rect(bx + bw + 2, y, vw, h)
        pygame.draw.rect(surf, FIELD_BG, vr, border_radius=3)
        t2 = self.fonts.f12.render(val, True, WHITE)
        surf.blit(t2, t2.get_rect(center=vr.center))
        return y + h + 3

    def btn_row(self, y: int, *buttons: tuple[str, Action]) -> int:
        surf = self.surf
        bw  = (SIDE_W - 20) // len(buttons)
        x   = self.x + 8
        mx, my = pygame.mouse.get_pos()
        h   = 24
        for label, fn in buttons:
            r = pygame.Rect(x, y, bw - 4, h)
            pygame.draw.rect(surf, BTN_HOV if r.collidepoint(mx, my) else BTN_NRM,
                             r, border_radius=3)
            t = self.fonts.f12.render(label, True, WHITE)
            surf.blit(t, t.get_rect(center=r.center))
            self.targets.append((r, fn))
            x += bw
        return y + h + 4

    def btn(self, y: int, width: int, label: str, fn: Action, col=None) -> int:
        surf = self.surf
        rect = pygame.Rect(self.x + 8, y, width, 24)
        mx, my = pygame.mouse.get_pos()
        hov = rect.collidepoint(mx, my)
        if col:
            bg = tuple(min(255, c + 25) for c in col) if hov else col
        else:
            bg = BTN_HOV if hov else BTN_NRM
        pygame.draw.rect(surf, bg, rect, border_radius=3)
        t = self.fonts.f12.render(label, True, WHITE)
        surf.blit(t, t.get_rect(center=rect.center))
        self.targets.append((rect, fn))
        return y + 28
