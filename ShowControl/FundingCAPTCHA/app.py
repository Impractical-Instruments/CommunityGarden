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

This file is argument parsing and wiring. The show loop is kiosk.py; what it
runs on lives beside it: settings.py (settings and their defaults),
camera_feed.py (camera → foreground frames), monitor.py (the Dashboard's port),
paint_input.py (--test-input), plugins.py (loading Games and screensavers),
arc.py (running Games).
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
from pathlib import Path
from typing import Any

import pygame

from arc import Arc
from camera_feed import CameraFeed, source_from_args
from kiosk import Kiosk
from levels import Levels
from monitor import MonitoringServer
from paint_input import PaintInput
from plugins import load_games, load_screensavers
from settings import load_settings

try:
    from OSCFabric import FabricClient, load_network_config_or_empty
    _FABRIC_AVAILABLE = True
except ImportError:
    _FABRIC_AVAILABLE = False

log = logging.getLogger("captcha")


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
    restart_requested = threading.Event()   # set by POST /api/restart, handled in the Kiosk's loop
    monitor = MonitoringServer(args.port, commands={"/api/restart": restart_requested.set})
    logging.getLogger().addHandler(monitor.log_handler())

    settings = load_settings()
    feed     = CameraFeed(settings, source_from_args(args))
    paint    = build_paint_input(args, settings) if args.test_input else None
    fabric   = build_fabric()

    monitor.start()

    pygame.init()
    info   = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h),
                                     pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("CAPTCHA")
    pygame.mouse.set_visible(args.test_input)

    kiosk = Kiosk(settings, feed=feed, monitor=monitor, screen=screen, fabric=fabric,
                  paint=paint, restart_requested=restart_requested,
                  arc=Arc(load_games(settings, screen.get_size(), Levels(args.levels))),
                  savers=load_screensavers(settings))
    feed.start()
    kiosk.run()


def build_paint_input(args: argparse.Namespace, settings: dict) -> PaintInput:
    """The mouse-painted foreground for --test-input (ADR-0016)."""
    cam_cfg   = settings["camera"]
    slabs_cfg = settings["depth_slabs"]
    cam_w, cam_h = cam_cfg["width"], cam_cfg["height"]
    if args.test_depth is not None:
        depth_mm = args.test_depth
    elif not slabs_cfg:
        sys.exit("ERROR: --test-input paints at the first depth slab, and depth_slabs is "
                 "empty — add a slab or pass --test-depth MM")
    else:                                   # the middle of the first slab
        depth_mm = (slabs_cfg[0]["near_mm"] + slabs_cfg[0]["far_mm"]) // 2
    log.info("Test-input mode: cam %dx%d  paint depth %dmm  (brush r=%dpx)",
             cam_w, cam_h, depth_mm, PaintInput.BRUSH_R)
    return PaintInput(cam_w, cam_h, depth_mm)


def build_fabric() -> Any:
    """The OSC client to the TreeHouse, or None when OSCFabric or the treehouse address is missing."""
    if not _FABRIC_AVAILABLE:
        return None
    network = load_network_config_or_empty(log)
    th = network.get("elements", {}).get("treehouse", {})
    if not (th.get("ip") and th.get("osc_port")):
        log.warning("network.json: treehouse not configured — OSC disabled")
        return None
    log.info("OSC fabric → TreeHouse %s:%d", th["ip"], th["osc_port"])
    return FabricClient("captcha", network)


if __name__ == "__main__":
    main()
