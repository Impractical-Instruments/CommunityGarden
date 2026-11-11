#!/usr/bin/env python3
"""
FundingCAPTCHA unified pygame app (ADR-0012, ADR-0013, ADR-0016, ADR-0023).

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
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import queue
import sys
import threading
import time
from enum import Enum, auto
from pathlib import Path
from typing import Any

import numpy as np
import pygame

# ── Paths ─────────────────────────────────────────────────────────────────────
DIR            = Path(__file__).parent
SETTINGS       = DIR / "captcha-settings.json"
SETTINGS_LOCAL = DIR / "captcha-settings.local.json"

from silhouette import build_cam_transform, apply_cam_transform, render_silhouette
from arc import Arc, Game, ShuffleBag

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    from IIVision import (MockCamera, OrbbecCamera, AdaptiveBackground,
                          AdaptiveBackgroundConfig, DetectionConfig, BlobTracker)
    _CV_AVAILABLE = True
except ImportError:
    _CV_AVAILABLE = False

try:
    from OSCFabric import FabricClient, load_network_config_or_empty
    _FABRIC_AVAILABLE = True
except ImportError:
    _FABRIC_AVAILABLE = False

log = logging.getLogger("captcha")

# ── Colours ───────────────────────────────────────────────────────────────────
BLACK    = (  0,   0,   0)
WHITE    = (255, 255, 255)
DK_GREY  = ( 28,  28,  28)
CYAN     = (  0, 200, 220)

FPS = 30


# ── Settings ──────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    s = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    if SETTINGS_LOCAL.exists():
        try:
            s.update(json.loads(SETTINGS_LOCAL.read_text()))
        except Exception:
            pass
    return s


def restart_camera(cam: dict, start_camera) -> None:
    """Stop the camera thread and start a fresh one (POST /api/restart).

    Touches no settings file: captcha-settings.local.json is the operator's.
    """
    cam["stop"].set()
    if cam["thread"] and cam["thread"].is_alive():
        cam["thread"].join(timeout=5.0)
    start_camera()
    log.info("Camera restarted — background relearning from the first frame")


# ── App state ─────────────────────────────────────────────────────────────────

class AppState(Enum):
    SCREENSAVER = auto()
    GAME        = auto()


# ── Monitoring server ─────────────────────────────────────────────────────────

_log_clients: set  = set()
_mon_loop:    asyncio.AbstractEventLoop | None = None
_app_status:  dict[str, Any] = {"state": "starting"}
_http_restart = threading.Event()


class _LogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if _mon_loop is None or not _log_clients:
            return
        msg = json.dumps({
            "ts":    time.strftime("%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "msg":   record.getMessage(),
        })
        asyncio.run_coroutine_threadsafe(_send_log(msg), _mon_loop)


async def _send_log(msg: str) -> None:
    dead = set()
    for ws in list(_log_clients):
        try:
            await ws.send(msg)
        except Exception:
            dead.add(ws)
    _log_clients.difference_update(dead)


def set_status(payload: dict) -> None:
    """Record the status GET /health reports."""
    global _app_status
    _app_status = payload


async def _ws_handler(ws: Any) -> None:
    if ws.request.path == "/logs":
        _log_clients.add(ws)
        try:
            await ws.wait_closed()
        finally:
            _log_clients.discard(ws)


async def _process_request(connection: Any, request: Any) -> Any:
    from websockets.http11 import Response
    from websockets.datastructures import Headers

    path = request.path

    if path == "/logs":
        return None

    if path == "/api/restart":
        _http_restart.set()
        body = b'{"ok":true}'
        return Response(200, "OK",
                        Headers([("Content-Type", "application/json"),
                                  ("Content-Length", str(len(body)))]),
                        body)

    if path in ("/", "/health"):
        body = json.dumps(_app_status).encode()
        return Response(200, "OK",
                        Headers([("Content-Type", "application/json"),
                                  ("Content-Length", str(len(body)))]),
                        body)

    return Response(404, "Not Found", Headers([("Content-Length", "0")]), b"")


def _run_monitoring(port: int) -> None:
    global _mon_loop
    from websockets.asyncio.server import serve as ws_serve

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _mon_loop = loop

    async def _serve() -> None:
        async with ws_serve(_ws_handler, "0.0.0.0", port,
                            process_request=_process_request):
            log.info("Monitoring on 0.0.0.0:%d  (WS /logs  GET /health  POST /api/restart)", port)
            await asyncio.Future()

    loop.run_until_complete(_serve())


# ── Camera thread ─────────────────────────────────────────────────────────────

def build_detection_config(settings: dict) -> "DetectionConfig":
    det_cfg = settings.get("detection", {})
    return DetectionConfig(
        depth_delta_mm  = det_cfg.get("depth_delta_mm",  25),
        min_depth_mm    = det_cfg.get("min_depth_mm",    500),
        max_depth_mm    = det_cfg.get("max_depth_mm",    2500),
    )


def build_background(settings: dict, detection_config: "DetectionConfig") -> "AdaptiveBackground":
    """The self-learning depth background (ADR-0023), from settings["background"].

    detection.depth_delta_mm is the lower bound on its per-pixel threshold.
    """
    cfg = AdaptiveBackgroundConfig.from_dict(
        settings.get("background", {}),
        depth_delta_mm=detection_config.depth_delta_mm)
    return AdaptiveBackground(cfg)


def _camera_thread(camera: Any, settings: dict,
                   cam_q: queue.Queue, stop: threading.Event,
                   reseed: threading.Event | None = None) -> None:
    try:
        _camera_inner(camera, settings, cam_q, stop, reseed)
    except Exception as exc:
        log.error("Camera thread crashed: %s", exc, exc_info=True)
        cam_q.put({"type": "error", "msg": str(exc)})


def _camera_inner(camera: Any, settings: dict,
                  cam_q: queue.Queue, stop: threading.Event,
                  reseed: threading.Event | None = None) -> None:
    """Every frame updates the background model and emits foreground — from frame 1.

    Setting `reseed` makes the model relearn the background from the next frame.
    """
    detection_config = build_detection_config(settings)
    background       = build_background(settings, detection_config)
    tracker          = BlobTracker(background, detection_config)
    cam_transform    = build_cam_transform(settings)
    sil_dilation_px  = int(settings.get("silhouette_dilation_px", 1))

    with camera:
        for frame in camera.frames():
            if stop.is_set():
                break
            if reseed is not None and reseed.is_set():
                reseed.clear()
                background.reseed()
            background.push(frame)
            foreground = tracker.detect_foreground(frame)
            corrected  = apply_cam_transform(
                foreground, getattr(frame, "intrinsics", None), cam_transform,
                dilation_px=sil_dilation_px,
            )
            cam_q.put({"type": "foreground", "frame": corrected})


# ── Test input handler ────────────────────────────────────────────────────────

class TestInputHandler:
    """Mouse-paint foreground canvas for --test-input mode (ADR-0016).

    Left-drag paints pixels at test_depth_mm; right-drag erases; C clears.
    Canvas is pushed to cam_q each tick as a normal foreground frame so the
    full BodyGridActivator pipeline is exercised without any game code changes.
    """

    BRUSH_R = 15  # brush radius in camera pixels

    def __init__(self, cam_w: int, cam_h: int, test_depth_mm: int) -> None:
        self._cam_w = cam_w
        self._cam_h = cam_h
        self._depth = test_depth_mm
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

    def push_frame(self, cam_q: queue.Queue) -> None:
        try:
            cam_q.put_nowait({"type": "foreground", "frame": self.canvas.copy()})
        except queue.Full:
            pass

    def draw_overlay(self, screen: pygame.Surface, game_w: int, screen_h: int) -> None:
        mask = self.canvas > 0
        if not mask.any():
            return
        rgb = np.zeros((self._cam_w, self._cam_h, 3), dtype=np.uint8)
        t = mask.T  # surfarray wants (W, H, 3)
        rgb[t, 0] = CYAN[0]
        rgb[t, 1] = CYAN[1]
        rgb[t, 2] = CYAN[2]
        surf = pygame.surfarray.make_surface(rgb)
        surf = pygame.transform.scale(surf, (game_w, screen_h))
        surf.set_alpha(128)
        screen.blit(surf, (0, 0))


# ── Game loading ──────────────────────────────────────────────────────────────
# The Game interface, _NoGame stand-in, ShuffleBag, and the Arc lifecycle now
# live in arc.py — imported above. This module only knows how to find and load
# Games from disk; selecting and running them is the Arc's job.

def _load_games(settings: dict, levels_path: Path | None = None) -> list[Game]:
    games: list[Game] = []
    for name in ("bodycaptcha",):
        path = DIR / "games" / f"{name}.py"
        if not path.exists():
            log.warning("Game not found: %s", path)
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"games.{name}", path)
            mod  = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            sys.modules[spec.name] = mod                  # dataclass field resolution needs this
            spec.loader.exec_module(mod)                  # type: ignore[union-attr]
            if levels_path is not None and hasattr(mod, "set_levels_path"):
                mod.set_levels_path(levels_path)
                log.info("Levels override for %s: %s", name, levels_path)
            games.append(mod.create(settings))
            log.info("Loaded game: %s", name)
        except Exception as exc:
            log.warning("Could not load game %s: %s", name, exc)
    return games


# ── Screensaver interface ─────────────────────────────────────────────────────

class _NoSaver:
    def update(self, dt: float, foreground: np.ndarray | None) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(DK_GREY)


def _load_screensavers(settings: dict) -> list:
    config_path = DIR / "screensavers.json"
    try:
        names = json.loads(config_path.read_text())
    except Exception:
        names = []

    savers = []
    for name in names:
        path = DIR / name
        if not path.exists():
            log.warning("Screensaver not found: %s", path)
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"ss.{Path(name).stem}", path)
            mod  = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            sys.modules[spec.name] = mod                  # dataclass field resolution needs this
            spec.loader.exec_module(mod)                  # type: ignore[union-attr]
            savers.append(mod.create(settings))
            log.info("Loaded screensaver: %s", name)
        except Exception as exc:
            log.warning("Could not load screensaver %s: %s", name, exc)
    return savers


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
    logging.getLogger().addHandler(_LogHandler())

    settings = load_settings()
    cam_cfg  = settings.get("camera", {})
    use_mock       = args.mock_camera
    use_test_input = args.test_input

    if (args.camera or use_mock) and not _CV_AVAILABLE:
        sys.exit("ERROR: CV libraries not available — from the repo root: pip install -e \".[fundingcaptcha,camera]\"")

    # Silhouette / attract config
    slabs_cfg     = settings.get("depth_slabs",
                                 [{"near_mm": 800, "far_mm": 2500, "slab_id": 0}])
    roi           = settings.get("camera_roi",
                                 {"x": 0, "y": 0, "w": cam_cfg.get("width", 640),
                                                   "h": cam_cfg.get("height", 400)})
    slab_color    = tuple(settings.get("slab_styles", {})
                          .get("0", {}).get("color", [0, 220, 100]))
    sil_opacity   = float(settings.get("silhouette_opacity", 0.5))
    attract_dwell = float(settings.get("attract_dwell_s", 3.0))
    min_fg_px     = int(settings.get("min_foreground_pixels", 2000))

    # ── Test input handler ────────────────────────────────────────────────────
    test_handler: TestInputHandler | None = None
    if use_test_input:
        cam_w = cam_cfg.get("width",  640)
        cam_h = cam_cfg.get("height", 400)
        if args.test_depth is not None:
            depth_mm = args.test_depth
        else:
            first_slab = slabs_cfg[0] if slabs_cfg else {"near_mm": 800, "far_mm": 2500}
            depth_mm   = (first_slab["near_mm"] + first_slab["far_mm"]) // 2
        test_handler = TestInputHandler(cam_w, cam_h, depth_mm)
        log.info("Test-input mode: cam %dx%d  paint depth %dmm  (brush r=%dpx)",
                 cam_w, cam_h, depth_mm, TestInputHandler.BRUSH_R)

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

    # ── Camera factory ────────────────────────────────────────────────────────
    def _make_camera() -> Any:
        if use_mock:
            return MockCamera(width=cam_cfg.get("width", 640),
                              height=cam_cfg.get("height", 400),
                              fps=cam_cfg.get("fps", 10))
        return OrbbecCamera(serial=cam_cfg.get("serial") or None,
                            width=cam_cfg.get("width", 640),
                            height=cam_cfg.get("height", 400),
                            fps=cam_cfg.get("fps", 10))

    # ── Monitoring server ─────────────────────────────────────────────────────
    threading.Thread(target=_run_monitoring, args=(args.port,), daemon=True).start()

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
    arc        = Arc(_load_games(settings, levels_path=args.levels))

    # ── Screensavers ──────────────────────────────────────────────────────────
    savers     = _load_screensavers(settings)
    saver_bag  = ShuffleBag(savers)
    no_saver   = _NoSaver()
    cur_saver  = saver_bag.next() or no_saver

    # ── Camera thread state ───────────────────────────────────────────────────
    cam: dict[str, Any] = {
        "q":      queue.Queue(maxsize=32),
        "stop":   threading.Event(),
        "reseed": threading.Event(),
        "thread": None,
    }

    def _start_camera() -> None:
        cam["q"]      = queue.Queue(maxsize=32)
        cam["stop"]   = threading.Event()
        cam["reseed"] = threading.Event()
        if args.camera or use_mock:
            t = threading.Thread(
                target=_camera_thread,
                args=(_make_camera(), settings, cam["q"], cam["stop"], cam["reseed"]),
                daemon=True,
            )
            t.start()
            cam["thread"] = t
            log.info("Camera thread started (%s) — background learns from the first frame",
                     "mock" if use_mock else "Orbbec")

    # ── State ─────────────────────────────────────────────────────────────────
    state:             AppState          = AppState.SCREENSAVER
    current_foreground: np.ndarray | None = None
    sil_cache:         pygame.Surface | None = None   # scaled silhouette, rebuilt on new frames
    fg_pixel_count     = 0
    attract_elapsed    = 0.0
    saver_elapsed      = 0.0
    SAVER_DWELL        = 120.0
    t_last_osc         = time.monotonic()

    _start_camera()
    set_status({"state": "screensaver"})

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        dt = clock.tick(FPS) / 1000.0

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cam["stop"].set(); pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    cam["stop"].set(); pygame.quit(); sys.exit(0)
                elif event.key == pygame.K_r:
                    cam["reseed"].set()
                    log.info("R: reseeding the depth background from the next frame")
                elif event.key == pygame.K_c and test_handler:
                    test_handler.clear()

        # HTTP restart
        if _http_restart.is_set():
            _http_restart.clear()
            if state == AppState.GAME:
                cur_saver     = saver_bag.next() or no_saver
                saver_elapsed = 0.0
            state = AppState.SCREENSAVER
            current_foreground = None
            sil_cache          = None
            fg_pixel_count     = 0
            attract_elapsed    = 0.0
            threading.Thread(target=restart_camera, args=(cam, _start_camera), daemon=True).start()

        # Test-input: update paint canvas and push as foreground frame
        if test_handler:
            test_handler.tick(game_w, WH)
            test_handler.push_frame(cam["q"])

        # Drain camera queue
        fg_new = False   # did a fresh foreground frame arrive this tick?
        try:
            while True:
                msg   = cam["q"].get_nowait()
                mtype = msg["type"]

                if mtype == "foreground":
                    current_foreground = msg["frame"]
                    fg_new             = True
                    fg_pixel_count     = int(np.count_nonzero(current_foreground))
                    set_status({"state": state.name.lower(),
                               "fg_pixels": fg_pixel_count})

                elif mtype == "error":
                    log.error("Camera: %s", msg["msg"])
                    set_status({"state": "error", "error": msg["msg"]})

        except queue.Empty:
            pass

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
                    set_status({"state": "game"})
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
                set_status({"state": "screensaver"})

            now = time.monotonic()
            if now - t_last_osc >= 0.1 and fabric:
                t_last_osc = now
                fabric.report("intensity", float(status.intensity))

        # Test-input overlay
        if test_handler:
            test_handler.draw_overlay(screen, game_w, WH)
            hint = font_sml.render(
                "TEST MODE  |  LMB: paint  RMB: erase  C: clear", True, CYAN)
            screen.blit(hint, (8, 8))

        pygame.display.flip()


if __name__ == "__main__":
    main()
