"""Stub screensaver: idle title screen. Replace with generative visuals."""
from __future__ import annotations

import math
import time

import pygame

_BLACK   = (  0,   0,   0)
_DK_GREY = ( 18,  18,  18)
_GREY    = ( 60,  60,  60)
_WHITE   = (200, 200, 200)


class WaitingScreensaver:
    def __init__(self, settings: dict) -> None:
        self._t    = 0.0
        self._font = None

    def update(self, dt: float, foreground_frame) -> None:
        self._t += dt

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(_DK_GREY)
        WW, WH = surf.get_size()

        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 42, bold=True)

        pulse = int(40 + 30 * math.sin(self._t * 1.2))
        color = (pulse, pulse, pulse)

        title = self._font.render("FundingCAPTCHA", True, color)
        surf.blit(title, title.get_rect(center=(WW // 2, WH // 2)))

        small = pygame.font.SysFont("monospace", 20)
        sub   = small.render("Step into frame to begin", True, _GREY)
        surf.blit(sub, sub.get_rect(center=(WW // 2, WH // 2 + 60)))


def create(settings: dict) -> WaitingScreensaver:
    return WaitingScreensaver(settings)
