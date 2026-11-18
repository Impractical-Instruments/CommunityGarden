"""The Kiosk: the show state machine (SCREENSAVER <-> GAME) and the loop that ticks it.

States:
  SCREENSAVER → idle; detects a Player and counts down the attract dwell
  GAME        → active Arc

Everything the loop knows lives on the Kiosk as fields. `app.py` builds the
collaborators (camera feed, Dashboard port, Arc, screensavers, OSC client)
and hands them in; the Kiosk ticks them. One `restart()` returns the Kiosk to
a clean SCREENSAVER, whoever asked (ADR-0012, ADR-0023).
"""
from __future__ import annotations

import logging
import sys
import threading
import time
from enum import Enum, auto
from typing import Any

import numpy as np
import pygame

from arc import Arc, ShuffleBag
from camera_feed import CameraFeed
from monitor import MonitoringServer
from paint_input import PaintInput
from plugins import NoSaver
from settings import slab_color as slab_color_of
from silhouette import render_silhouette

log = logging.getLogger("captcha")

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)

FPS = 30
SAVER_DWELL     = 120.0     # seconds a screensaver runs before the next one
OSC_INTERVAL_S  = 0.1       # intensity goes to the TreeHouse at most this often


class AppState(Enum):
    SCREENSAVER = auto()
    GAME        = auto()


class Kiosk:
    """One show: owns the state, the per-state ticks and the restart.

    `restart_requested` is set from another thread (the Dashboard's
    POST /api/restart); the loop notices it on its next tick.
    """

    def __init__(self, settings: dict, *, feed: CameraFeed, monitor: MonitoringServer,
                 arc: Arc, savers: list, screen: pygame.Surface,
                 fabric: Any = None, paint: PaintInput | None = None,
                 restart_requested: threading.Event | None = None) -> None:
        self.feed     = feed
        self.monitor  = monitor
        self.arc      = arc
        self.fabric   = fabric
        self.paint    = paint
        self.screen   = screen
        self.restart_requested = restart_requested or threading.Event()

        self.slabs_cfg     = settings["depth_slabs"]
        self.roi           = settings["camera_roi"]
        self.slab_color    = slab_color_of(settings)
        self.sil_opacity   = float(settings["silhouette_opacity"])
        self.attract_dwell = float(settings["attract_dwell_s"])
        self.min_fg_px     = int(settings["min_foreground_pixels"])

        # Full-screen game area (no HUD column — ADR-0019)
        self.width, self.height = screen.get_size()
        self.font_big = pygame.font.SysFont("monospace", 48, bold=True)
        self.font_sml = pygame.font.SysFont("monospace", 32)

        self.saver_bag = ShuffleBag(savers)
        self.no_saver  = NoSaver()
        self.cur_saver = self.saver_bag.next() or self.no_saver

        self.state:              AppState = AppState.SCREENSAVER
        self.foreground:         np.ndarray | None = None
        self.sil_cache:          pygame.Surface | None = None   # scaled silhouette, rebuilt on new frames
        self.fg_pixel_count      = 0
        self.fg_new              = False        # a camera frame arrived this tick
        self.attract_elapsed     = 0.0
        self.saver_elapsed       = 0.0
        self.t_last_osc          = time.monotonic()

    # ── Loop ──────────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Tick at FPS until the window closes or Q / Escape is pressed. Does not return."""
        clock = pygame.time.Clock()
        self.monitor.set_status({"state": "screensaver"})
        while True:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.tick(dt)
            pygame.display.flip()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.quit()
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.quit()
            elif event.key == pygame.K_r:
                self.feed.reseed()
                log.info("R: reseeding the depth background from the next frame")
            elif event.key == pygame.K_c and self.paint:
                self.paint.clear()

    def quit(self) -> None:
        self.feed.stop()
        pygame.quit()
        sys.exit(0)

    # ── One frame ─────────────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance the show one frame and draw it on `screen`."""
        if self.restart_requested.is_set():
            self.restart_requested.clear()
            self.restart()

        # Test-input: update paint canvas and push as foreground frame
        if self.paint:
            self.paint.tick(self.width, self.height)
            self.paint.push_frame(self.feed.queue)

        self._take_camera_frame()

        self.screen.fill(BLACK)
        if self.state == AppState.SCREENSAVER:
            self.tick_screensaver(dt)
        elif self.state == AppState.GAME:
            self.tick_game(dt)

        # Test-input overlay
        if self.paint:
            self.paint.draw_overlay(self.screen, self.width, self.height)
            hint = self.font_sml.render(
                "TEST MODE  |  LMB: paint  RMB: erase  C: clear", True, PaintInput.COLOR)
            self.screen.blit(hint, (8, 8))

    def _take_camera_frame(self) -> None:
        """Newest camera frame, if one arrived this tick; a camera crash goes to the Dashboard."""
        newest = self.feed.drain()
        self.fg_new = newest is not None
        if self.fg_new:
            self.foreground     = newest
            self.fg_pixel_count = int(np.count_nonzero(self.foreground))
            self.monitor.set_status({"state": self.state.name.lower(),
                                     "fg_pixels": self.fg_pixel_count})
        if self.feed.error:
            self.monitor.set_status({"state": "error", "error": self.feed.error})

    # ── SCREENSAVER ───────────────────────────────────────────────────────────

    def tick_screensaver(self, dt: float) -> None:
        self.saver_elapsed += dt
        if self.saver_elapsed >= SAVER_DWELL:
            self._next_saver()
            log.info("Screensaver dwell elapsed — rotating to %s", type(self.cur_saver).__name__)

        self.cur_saver.update(dt, self.foreground)
        self.cur_saver.draw(self.screen)

        if self.fg_pixel_count < self.min_fg_px:
            self.attract_elapsed = 0.0
            return

        self.attract_elapsed += dt
        self._draw_silhouette()

        remaining = max(0.0, self.attract_dwell - self.attract_elapsed)
        t_big = self.font_big.render(f"Game starts in {int(remaining) + 1}...", True, WHITE)
        self.screen.blit(t_big, t_big.get_rect(center=(self.width // 2, self.height // 2 - 40)))

        if self.attract_elapsed >= self.attract_dwell:
            self.state           = AppState.GAME
            self.attract_elapsed = 0.0
            game_name            = self.arc.start()
            log.info("Player detected — starting Arc (%s)", game_name)
            self.monitor.set_status({"state": "game"})

    def _draw_silhouette(self) -> None:
        """Silhouette overlay — rebuild only when a fresh camera frame arrived
        (camera ≈15 fps vs 30 fps render), else reuse the cached scaled surface
        instead of re-masking + re-scaling to full HD."""
        if self.foreground is None:
            return
        if self.fg_new or self.sil_cache is None:
            self.sil_cache = render_silhouette(self.foreground, self.slabs_cfg, self.roi,
                                               self.slab_color, self.width, self.height)
            self.sil_cache.set_alpha(int(self.sil_opacity * 255))
        self.screen.blit(self.sil_cache, (0, 0))

    # ── GAME ──────────────────────────────────────────────────────────────────

    def tick_game(self, dt: float) -> None:
        status = self.arc.update(self.foreground, dt)
        self.arc.draw(self.screen)

        if status.finished:
            log.info("Arc ended — returning to screensaver")
            if self.fabric and status.blewup:
                self.fabric.send_event("blowup")
            self.state = AppState.SCREENSAVER
            self._next_saver()
            self.monitor.set_status({"state": "screensaver"})

        now = time.monotonic()
        if now - self.t_last_osc >= OSC_INTERVAL_S and self.fabric:
            self.t_last_osc = now
            self.fabric.report("intensity", float(status.intensity))

    # ── Restart ───────────────────────────────────────────────────────────────

    def restart(self) -> None:
        """Back to a clean SCREENSAVER with no Player yet; the camera restarts and relearns its background."""
        if self.state == AppState.GAME:
            self._next_saver()
        self.state          = AppState.SCREENSAVER
        self.foreground     = None
        self.sil_cache      = None
        self.fg_pixel_count = 0
        self.attract_elapsed = 0.0
        threading.Thread(target=self.feed.restart, daemon=True).start()   # joins the old thread: off the loop

    def _next_saver(self) -> None:
        self.cur_saver     = self.saver_bag.next() or self.no_saver
        self.saver_elapsed = 0.0
