#!/usr/bin/env python3
"""
FundingCAPTCHA kiosk: screensaver until a Player stands in view, then an Arc of Games (ADR-0012, ADR-0013, ADR-0016, ADR-0023).

Usage:
  python3 app.py [--camera | --mock-camera | --test-input [--test-depth N]] [--port 8080]

States:
  SCREENSAVER → idle; detects player and counts down attract dwell
  GAME        → active Arc

There is no calibration screen. The depth background is learned continuously
from the first frame, with people in view (ADR-0023): the floor is live in
under a second, and anyone standing there at launch shows up after one step.

Keys:
  R          → reseed the depth background from the next camera frame
  Q / Escape → quit
  C          → clear paint canvas (--test-input only)

This file is the show loop. What it runs on lives beside it: settings.py
(settings and their defaults), camera_feed.py (camera → foreground frames),
monitor.py (the Dashboard's port), paint_input.py (--test-input),
plugins.py (loading Games and screensavers), arc.py (running Games).
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
from enum import Enum, auto
from pathlib import Path
from typing import Any

import numpy as np
import pygame

from arc import Arc, ShuffleBag
from camera_feed import CameraFeed, source_from_args
from monitor import MonitoringServer
from paint_input import PaintInput
from plugins import NoSaver, load_games, load_screensavers
from settings import load_settings, slab_color as slab_color_of
from silhouette import render_silhouette

try:
    from OSCFabric import FabricClient, load_network_config_or_empty
    _FABRIC_AVAILABLE = True
except ImportError:
    _FABRIC_AVAILABLE = False

log = logging.getLogger("captcha")

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)

FPS = 30


class AppState(Enum):
    SCREENSAVER = auto()
    GAME        = auto()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="FundingCAPTCHA unified pygame app")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--camera",      action="store_true")
    mode.add_argument("--mock-camera", action="store_true")
    mode.add_argument("--test-input",  action="store_true",
                      help="Camera-free dev mode: mouse-paint foreground canvas (ADR-0016)")
    ap.add_argument("--test-depth",    type=int, default=None,
                    help="Depth value (mm) painted by left-drag in --test-input mode")
    ap.add_argument("--port",          type=int, default=8080)
    ap.add_argument("--levels", type=Path, default=None, metavar="PATH",
                    help="Alternate BodyCaptcha levels JSON (default: bodycaptcha-levels.json). "
                         "A missing or malformed file falls back to the default set.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    http_restart = threading.Event()        # set by POST /api/restart, handled in the loop
    monitor = MonitoringServer(args.port, commands={"/api/restart": http_restart.set})
    logging.getLogger().addHandler(monitor.log_handler())

    settings = load_settings()
    cam_cfg  = settings["camera"]
    use_test_input = args.test_input
    feed     = CameraFeed(settings, source_from_args(args))

    # Silhouette / attract config
    slabs_cfg     = settings["depth_slabs"]
    roi           = settings["camera_roi"]
    slab_color    = slab_color_of(settings)
    sil_opacity   = float(settings["silhouette_opacity"])
    attract_dwell = float(settings["attract_dwell_s"])
    min_fg_px     = int(settings["min_foreground_pixels"])

    # ── Test input handler ────────────────────────────────────────────────────
    test_handler: PaintInput | None = None
    if use_test_input:
        cam_w, cam_h = cam_cfg["width"], cam_cfg["height"]
        if args.test_depth is not None:
            depth_mm = args.test_depth
        else:                                   # the middle of the first slab
            depth_mm = (slabs_cfg[0]["near_mm"] + slabs_cfg[0]["far_mm"]) // 2
        test_handler = PaintInput(cam_w, cam_h, depth_mm)
        log.info("Test-input mode: cam %dx%d  paint depth %dmm  (brush r=%dpx)",
                 cam_w, cam_h, depth_mm, PaintInput.BRUSH_R)

    # ── OSC fabric ────────────────────────────────────────────────────────────
    fabric: Any = None
    if _FABRIC_AVAILABLE:
        network = load_network_config_or_empty(log)
        th = network.get("elements", {}).get("treehouse", {})
        if th.get("ip") and th.get("osc_port"):
            fabric = FabricClient("captcha", network)
            log.info("OSC fabric → TreeHouse %s:%d", th["ip"], th["osc_port"])
        else:
            log.warning("network.json: treehouse not configured — OSC disabled")

    monitor.start()

    # ── Pygame ────────────────────────────────────────────────────────────────
    pygame.init()
    info   = pygame.display.Info()
    WW, WH = info.current_w, info.current_h
    screen = pygame.display.set_mode((WW, WH), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("CAPTCHA")
    pygame.mouse.set_visible(use_test_input)
    clock  = pygame.time.Clock()

    font_big = pygame.font.SysFont("monospace", 48, bold=True)
    font_sml = pygame.font.SysFont("monospace", 32)

    # Full-screen game area (no HUD column — ADR-0019)
    game_w = WW

    # ── Arc ───────────────────────────────────────────────────────────────────
    arc        = Arc(load_games(settings, levels_path=args.levels))

    # ── Screensavers ──────────────────────────────────────────────────────────
    savers     = load_screensavers(settings)
    saver_bag  = ShuffleBag(savers)
    no_saver   = NoSaver()
    cur_saver  = saver_bag.next() or no_saver

    # ── State ─────────────────────────────────────────────────────────────────
    state:             AppState          = AppState.SCREENSAVER
    current_foreground: np.ndarray | None = None
    sil_cache:         pygame.Surface | None = None   # scaled silhouette, rebuilt on new frames
    fg_pixel_count     = 0
    attract_elapsed    = 0.0
    saver_elapsed      = 0.0
    SAVER_DWELL        = 120.0
    t_last_osc         = time.monotonic()

    feed.start()
    monitor.set_status({"state": "screensaver"})

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        dt = clock.tick(FPS) / 1000.0

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                feed.stop(); pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    feed.stop(); pygame.quit(); sys.exit(0)
                elif event.key == pygame.K_r:
                    feed.reseed()
                    log.info("R: reseeding the depth background from the next frame")
                elif event.key == pygame.K_c and test_handler:
                    test_handler.clear()

        # HTTP restart
        if http_restart.is_set():
            http_restart.clear()
            if state == AppState.GAME:
                cur_saver     = saver_bag.next() or no_saver
                saver_elapsed = 0.0
            state = AppState.SCREENSAVER
            current_foreground = None
            sil_cache          = None
            fg_pixel_count     = 0
            attract_elapsed    = 0.0
            threading.Thread(target=feed.restart, daemon=True).start()   # joins the old thread: off the loop

        # Test-input: update paint canvas and push as foreground frame
        if test_handler:
            test_handler.tick(game_w, WH)
            test_handler.push_frame(feed.queue)

        # Newest camera frame, if one arrived this tick
        newest = feed.drain()
        fg_new = newest is not None
        if fg_new:
            current_foreground = newest
            fg_pixel_count     = int(np.count_nonzero(current_foreground))
            monitor.set_status({"state": state.name.lower(),
                                "fg_pixels": fg_pixel_count})
        if feed.error:
            monitor.set_status({"state": "error", "error": feed.error})

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BLACK)

        if state == AppState.SCREENSAVER:
            saver_elapsed += dt
            if saver_elapsed >= SAVER_DWELL:
                saver_elapsed = 0.0
                cur_saver = saver_bag.next() or no_saver
                log.info("Screensaver dwell elapsed — rotating to %s", type(cur_saver).__name__)

            cur_saver.update(dt, current_foreground)
            cur_saver.draw(screen)

            player_present = (fg_pixel_count >= min_fg_px)
            if player_present:
                attract_elapsed += dt

                # Silhouette overlay — rebuild only when a fresh camera frame
                # arrived (camera ≈15 fps vs 30 fps render), else reuse the cached
                # scaled surface instead of re-masking + re-scaling to full HD.
                if current_foreground is not None:
                    if fg_new or sil_cache is None:
                        sil_cache = render_silhouette(current_foreground, slabs_cfg,
                                                      roi, slab_color, game_w, WH)
                        sil_cache.set_alpha(int(sil_opacity * 255))
                    screen.blit(sil_cache, (0, 0))

                # Countdown text
                remaining = max(0.0, attract_dwell - attract_elapsed)
                t_big = font_big.render(f"Game starts in {int(remaining) + 1}...", True, WHITE)
                screen.blit(t_big, t_big.get_rect(center=(game_w // 2, WH // 2 - 40)))

                if attract_elapsed >= attract_dwell:
                    state           = AppState.GAME
                    attract_elapsed = 0.0
                    game_name       = arc.start()
                    log.info("Player detected — starting Arc (%s)", game_name)
                    monitor.set_status({"state": "game"})
            else:
                attract_elapsed = 0.0

        elif state == AppState.GAME:
            status = arc.update(current_foreground, dt)
            arc.draw(screen)

            if status.finished:
                log.info("Arc ended — returning to screensaver")
                if fabric and status.blewup:
                    fabric.send_event("blowup")
                state         = AppState.SCREENSAVER
                cur_saver     = saver_bag.next() or no_saver
                saver_elapsed = 0.0
                monitor.set_status({"state": "screensaver"})

            now = time.monotonic()
            if now - t_last_osc >= 0.1 and fabric:
                t_last_osc = now
                fabric.report("intensity", float(status.intensity))

        # Test-input overlay
        if test_handler:
            test_handler.draw_overlay(screen, game_w, WH)
            hint = font_sml.render(
                "TEST MODE  |  LMB: paint  RMB: erase  C: clear", True, PaintInput.COLOR)
            screen.blit(hint, (8, 8))

        pygame.display.flip()


if __name__ == "__main__":
    main()
