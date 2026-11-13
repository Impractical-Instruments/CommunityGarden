"""--test-input for the kiosk: paint a foreground frame with the mouse instead of standing at a camera (ADR-0016).

    paint = PaintInput(cam_w, cam_h, depth_mm)
    paint.tick(game_w, screen_h)      # each tick: apply the mouse
    paint.push_frame(feed.queue)      # hand the canvas on as a normal foreground frame
    paint.draw_overlay(screen, game_w, screen_h)

Left-drag paints pixels at `depth_mm`; right-drag erases; clear() wipes.
Because the canvas goes down the same queue a camera frame would, Games run
unchanged.
"""
from __future__ import annotations

import queue

import numpy as np
import pygame


class PaintInput:
    BRUSH_R = 15                  # brush radius, camera pixels
    COLOR   = (0, 200, 220)       # overlay tint, and the colour of the on-screen hint

    def __init__(self, cam_w: int, cam_h: int, depth_mm: int) -> None:
        self._cam_w = cam_w
        self._cam_h = cam_h
        self._depth = depth_mm
        self.canvas = np.zeros((cam_h, cam_w), dtype=np.uint16)

    def clear(self) -> None:
        self.canvas[:] = 0

    def tick(self, game_w: int, screen_h: int) -> None:
        buttons = pygame.mouse.get_pressed()
        if not (buttons[0] or buttons[2]):
            return
        mx, my = pygame.mouse.get_pos()
        if mx < 0 or mx >= game_w or my < 0 or my >= screen_h:
            return
        cx = int(mx / game_w * self._cam_w)
        cy = int(my / screen_h * self._cam_h)
        val = np.uint16(self._depth) if buttons[0] else np.uint16(0)
        y_idx, x_idx = np.ogrid[:self._cam_h, :self._cam_w]
        disc = (x_idx - cx) ** 2 + (y_idx - cy) ** 2 <= self.BRUSH_R ** 2
        self.canvas[disc] = val

    def push_frame(self, out: queue.Queue) -> None:
        try:
            out.put_nowait({"type": "foreground", "frame": self.canvas.copy()})
        except queue.Full:
            pass

    def draw_overlay(self, screen: pygame.Surface, game_w: int, screen_h: int) -> None:
        mask = self.canvas > 0
        if not mask.any():
            return
        rgb = np.zeros((self._cam_w, self._cam_h, 3), dtype=np.uint8)
        rgb[mask.T] = self.COLOR      # surfarray wants (W, H, 3)
        surf = pygame.surfarray.make_surface(rgb)
        surf = pygame.transform.scale(surf, (game_w, screen_h))
        surf.set_alpha(128)
        screen.blit(surf, (0, 0))
