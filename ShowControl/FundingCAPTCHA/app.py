#!/usr/bin/env python3
"""
FundingCAPTCHA unified pygame app (ADR-0012).

Replaces: server.py, touch_calibration.py, captcha-kiosk.service

Usage:
  python app.py [--camera | --mock-camera] [--port 8080]
               [--max-plane-dist CM] [--cal-dwell N] [--stable-cm CM]

States:
  BG_CAL     → solid black; camera builds background depth model
  CORNER_CAL → operator touches three corners (BL → BR → TL)
  LIVE       → game rotation

Keys:
  R          → wipe corners, restart from BG_CAL
  Q / Escape → quit
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import math
import queue
import random
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

sys.path.insert(0, str(DIR.parent.parent))  # IIVision
sys.path.insert(0, str(DIR.parent))         # OSCFabric
sys.path.insert(0, str(DIR))                # screen_projector, games

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    from IIVision import (
        MockCamera, OrbbecCamera,
        StabilizerConfig, Transform, Rotator,
        Calibrator, DetectionConfig, run_pipeline,
    )
    _CV_AVAILABLE = True
except ImportError:
    _CV_AVAILABLE = False

try:
    from OSCFabric import FabricClient, load_network_config
    _FABRIC_AVAILABLE = True
except ImportError:
    _FABRIC_AVAILABLE = False

from screen_projector import ScreenProjector

log = logging.getLogger("captcha")

# ── Colours ───────────────────────────────────────────────────────────────────
BLACK    = (  0,   0,   0)
WHITE    = (255, 255, 255)
DK_GREY  = ( 28,  28,  28)
MID_GREY = ( 75,  75,  75)
LT_GREY  = (140, 140, 140)
GREEN    = (  0, 200,  75)
YELLOW   = (240, 200,   0)
CYAN     = (  0, 200, 220)
ORANGE   = (240, 130,   0)

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


def _save_local(data: dict) -> None:
    SETTINGS_LOCAL.write_text(json.dumps(data, indent=2))


# ── Corner calibration ────────────────────────────────────────────────────────

_CAL_CORNERS   = ["BOTTOM-LEFT", "BOTTOM-RIGHT", "TOP-LEFT"]
_CAL_KEYS      = ["bottom_left", "bottom_right", "top_left"]
_CAL_CORNER_UV = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]


class CornerCal:
    def __init__(self, dwell_frames: int, stable_cm: float = 15.0) -> None:
        self._dwell     = max(1, dwell_frames)
        self._stable    = stable_cm
        self.idx        = 0
        self._pts: list[list[float]] = []
        self._last_xyz: list[float] | None = None
        self._df        = 0
        self.just_accepted  = False
        self.detected_xyz: list[float] | None = None
        self.blob_count     = 0

    @property
    def name(self) -> str:
        return _CAL_CORNERS[self.idx] if not self.done else "Done!"

    @property
    def done(self) -> bool:
        return len(self._pts) == 3

    @property
    def dwell_progress(self) -> float:
        return min(1.0, self._df / self._dwell)

    def push_blobs(self, blobs: list[dict]) -> None:
        self.just_accepted = False
        self.detected_xyz  = None
        self.blob_count    = len(blobs)
        if self.done:
            return
        if len(blobs) != 1:
            self._last_xyz = None
            self._df       = 0
            return
        xyz = [blobs[0]["x"], blobs[0]["y"], blobs[0]["z"]]
        self.detected_xyz = xyz
        if self._last_xyz is None:
            moved = True
        else:
            dist  = math.sqrt(sum((a - b) ** 2 for a, b in zip(xyz, self._last_xyz)))
            moved = dist > self._stable
        if moved:
            self._last_xyz = xyz
            self._df       = 1
        else:
            self._df += 1
        if self._df >= self._dwell:
            self._pts.append(xyz[:])
            self.idx      += 1
            self._last_xyz = None
            self._df       = 0
            self.just_accepted = True

    def result(self) -> dict:
        return {k: v for k, v in zip(_CAL_KEYS, self._pts)}

    def reset(self) -> None:
        self.idx           = 0
        self._pts          = []
        self._last_xyz     = None
        self._df           = 0
        self.just_accepted = False
        self.detected_xyz  = None
        self.blob_count    = 0


# ── App state ─────────────────────────────────────────────────────────────────

class AppState(Enum):
    BG_CAL     = auto()
    CORNER_CAL = auto()
    LIVE       = auto()


# ── Monitoring server ─────────────────────────────────────────────────────────

_ws_clients:  set  = set()
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


def broadcast(payload: dict) -> None:
    global _app_status
    _app_status = payload
    if _mon_loop is None or not _ws_clients:
        return
    text = json.dumps(payload)
    asyncio.run_coroutine_threadsafe(_send_ws(text), _mon_loop)


async def _send_ws(text: str) -> None:
    dead = set()
    for ws in list(_ws_clients):
        try:
            await ws.send(text)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


async def _ws_handler(ws: Any) -> None:
    path = ws.request.path
    if path == "/ws":
        _ws_clients.add(ws)
        try:
            await ws.send(json.dumps(_app_status))
        except Exception:
            pass
        try:
            await ws.wait_closed()
        finally:
            _ws_clients.discard(ws)
    elif path == "/logs":
        _log_clients.add(ws)
        try:
            await ws.wait_closed()
        finally:
            _log_clients.discard(ws)


async def _process_request(connection: Any, request: Any) -> Any:
    from websockets.http11 import Response
    from websockets.datastructures import Headers

    path = request.path

    if path in ("/ws", "/logs"):
        return None  # proceed with WebSocket upgrade

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
            log.info("Monitoring on 0.0.0.0:%d  (WS /ws /logs  GET /  POST /api/restart)", port)
            await asyncio.Future()

    loop.run_until_complete(_serve())


# ── Camera thread ─────────────────────────────────────────────────────────────

def _camera_thread(camera: Any, settings: dict,
                   cam_q: queue.Queue, stop: threading.Event) -> None:
    try:
        _camera_inner(camera, settings, cam_q, stop)
    except Exception as exc:
        log.error("Camera thread crashed: %s", exc, exc_info=True)
        cam_q.put({"type": "error", "msg": str(exc)})


def _camera_inner(camera: Any, settings: dict,
                  cam_q: queue.Queue, stop: threading.Event) -> None:
    stab_cfg = settings.get("stabilizer", {})
    cam_cfg  = settings.get("camera", {})
    det_cfg  = settings.get("detection", {})

    stabilizer_config = StabilizerConfig(
        max_match_dist_cm  = stab_cfg.get("max_match_dist_cm",  80.0),
        smoothing_alpha    = stab_cfg.get("smoothing_alpha",     0.3),
        max_miss_frames    = stab_cfg.get("max_miss_frames",     8),
        min_confirm_frames = stab_cfg.get("min_confirm_frames",  2),
    )

    pos_cm = cam_cfg.get("pos_cm", [0.0, 0.0, 200.0])
    rot    = cam_cfg.get("rotation", {})
    cam_tf = Transform(
        translation=np.array(pos_cm, dtype=float),
        rotation=Rotator(
            pitch=rot.get("pitch", 0.0),
            yaw=rot.get("yaw",     0.0),
            roll=rot.get("roll",   0.0),
        ),
    )

    calib_frames = settings.get("calibration_frames", 60)
    log.info("BG_CAL: collecting %d frames", calib_frames)

    calibrator = Calibrator(calib_frames)
    frame_idx  = 0

    with camera:
        for frame in camera.frames():
            if stop.is_set():
                return
            frame_idx += 1
            cam_q.put({"type": "cal_progress",
                        "frame": frame_idx, "total": calib_frames})
            if calibrator.push_frame(frame):
                break

        if stop.is_set():
            return

        calibration = calibrator.build()
        log.info("BG_CAL complete")
        cam_q.put({"type": "cal_done"})

        detection_config = DetectionConfig(
            depth_delta_mm   = det_cfg.get("depth_delta_mm",   25),
            min_blob_pixels  = det_cfg.get("min_blob_pixels",  500),
            min_depth_mm     = det_cfg.get("min_depth_mm",     500),
            max_depth_mm     = det_cfg.get("max_depth_mm",     2000),
        )

        for tracked in run_pipeline(camera, cam_tf, calibration,
                                     stabilizer_config,
                                     detection_config=detection_config):
            if stop.is_set():
                break
            cam_q.put({"type": "blobs", "blobs": [
                {"id":  int(t.stable_id),
                 "x":   float(t.world_pos_cm[0]),
                 "y":   float(t.world_pos_cm[1]),
                 "z":   float(t.world_pos_cm[2])}
                for t in tracked
            ]})


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _letterbox(win_w: int, win_h: int, aspect: float) -> tuple[int, int, int, int]:
    if win_w / win_h > aspect:
        gh = win_h; gw = int(gh * aspect)
    else:
        gw = win_w; gh = int(gw / aspect)
    return (win_w - gw) // 2, (win_h - gh) // 2, gw, gh


def _uv_to_px(u: float, v: float,
               gx: int, gy: int, gw: int, gh: int) -> tuple[int, int]:
    return int(gx + u * gw), int(gy + (1.0 - v) * gh)


def _dwell_arc(surf: pygame.Surface, cx: int, cy: int,
               progress: float, radius: int = 36) -> None:
    if progress <= 0:
        return
    for a in range(0, int(progress * 360), 4):
        rad = math.radians(a - 90)
        pygame.draw.circle(surf, GREEN,
                           (int(cx + radius * math.cos(rad)),
                            int(cy + radius * math.sin(rad))), 3)


def _draw_corner_cal(surf: pygame.Surface, fonts: dict,
                      WW: int, WH: int,
                      gx: int, gy: int, gw: int, gh: int,
                      cal: CornerCal) -> None:
    pygame.draw.rect(surf, DK_GREY,  (gx, gy, gw, gh))
    pygame.draw.rect(surf, MID_GREY, (gx, gy, gw, gh), 2)

    if not cal.done:
        u, v   = _CAL_CORNER_UV[cal.idx]
        tx, ty = _uv_to_px(u, v, gx, gy, gw, gh)
        pulse  = int(abs(pygame.time.get_ticks() % 1000 - 500) / 500 * 60 + 195)
        pygame.draw.circle(surf, (pulse, pulse, 0), (tx, ty), 28, 4)
        pygame.draw.circle(surf, YELLOW, (tx, ty), 7)
        _dwell_arc(surf, tx, ty, cal.dwell_progress)

    for i in range(cal.idx):
        u, v   = _CAL_CORNER_UV[i]
        px, py = _uv_to_px(u, v, gx, gy, gw, gh)
        pygame.draw.circle(surf, GREEN, (px, py), 10)
        surf.blit(fonts["sml"].render(f"OK {_CAL_CORNERS[i]}", True, GREEN),
                  (px + 14, py - 9))

    msg = (f"Touch {cal.name} corner  ({min(cal.idx + 1, 3)}/3)"
           if not cal.done else "Calibration complete!")
    lbl = fonts["big"].render(msg, True, YELLOW)
    surf.blit(lbl, (WW // 2 - lbl.get_width() // 2, 18))

    if cal.detected_xyz is not None:
        x, y, z = cal.detected_xyz
        info = fonts["sml"].render(
            f"blob  x={x:+.1f}  y={y:+.1f}  z={z:+.1f} cm  |  hold still…",
            True, CYAN)
        surf.blit(info, (WW // 2 - info.get_width() // 2, 62))
    elif cal.blob_count == 0:
        t = fonts["sml"].render("No blob detected — step into camera view", True, LT_GREY)
        surf.blit(t, (WW // 2 - t.get_width() // 2, 62))
    else:
        t = fonts["sml"].render(f"{cal.blob_count} blobs — one person only", True, ORANGE)
        surf.blit(t, (WW // 2 - t.get_width() // 2, 62))

    bw = 320
    bx = WW // 2 - bw // 2
    by = WH - 44
    pygame.draw.rect(surf, MID_GREY, (bx, by, bw, 18))
    pygame.draw.rect(surf, GREEN,    (bx, by, int(bw * cal.dwell_progress), 18))
    pygame.draw.rect(surf, WHITE,    (bx, by, bw, 18), 1)
    surf.blit(fonts["sml"].render("R=restart  Q=quit", True, LT_GREY),
              (WW // 2 - fonts["sml"].size("R=restart  Q=quit")[0] // 2, WH - 20))


# ── Game interface ────────────────────────────────────────────────────────────

class Game:
    """Base class for FundingCAPTCHA games.

    update() returns (intensity, event):
      intensity — float 0–1, Arc progress toward Blow-Up
      event     — 'win' | 'loss' | None
    """

    def update(self, blobs: list[dict], projector: ScreenProjector | None,
               max_plane_dist: float, dt: float) -> tuple[float, str | None]:
        return 0.0, None

    def draw(self, surf: pygame.Surface) -> None:
        pass

    def reset(self) -> None:
        pass


class _NoGame(Game):
    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(DK_GREY)


def _load_games(settings: dict) -> list[Game]:
    games: list[Game] = []
    for name in ("upsidedown", "rhythm", "keepaway"):
        path = DIR / "games" / f"{name}.py"
        if not path.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"games.{name}", path)
            mod  = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)                  # type: ignore[union-attr]
            games.append(mod.create(settings))
            log.info("Loaded game: %s", name)
        except Exception as exc:
            log.warning("Could not load game %s: %s", name, exc)
    return games


class _ShuffleBag:
    def __init__(self, games: list[Game]) -> None:
        self._games = list(games)
        self._bag:  list[Game] = []

    def next(self) -> Game | None:
        if not self._games:
            return None
        if not self._bag:
            self._bag = list(self._games)
            random.shuffle(self._bag)
        return self._bag.pop()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="FundingCAPTCHA unified pygame app")
    ap.add_argument("--camera",         action="store_true")
    ap.add_argument("--mock-camera",    action="store_true")
    ap.add_argument("--port",           type=int,   default=8080)
    ap.add_argument("--max-plane-dist", type=float, default=None,  metavar="CM")
    ap.add_argument("--cal-dwell",      type=int,   default=20,    metavar="N")
    ap.add_argument("--stable-cm",      type=float, default=15.0,  metavar="CM")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger().addHandler(_LogHandler())

    settings       = load_settings()
    max_plane_dist = args.max_plane_dist or settings.get("max_plane_dist_cm", 10.0)
    cal_dwell      = args.cal_dwell
    stable_cm      = args.stable_cm
    cam_cfg        = settings.get("camera", {})
    use_mock       = args.mock_camera

    if (args.camera or use_mock) and not _CV_AVAILABLE:
        sys.exit("ERROR: CV libraries not available — pip install -r requirements.txt")

    # ── OSC fabric ────────────────────────────────────────────────────────────
    fabric: Any = None
    if _FABRIC_AVAILABLE:
        try:
            network = load_network_config()
            th = network.get("elements", {}).get("treehouse", {})
            if th.get("ip") and th.get("osc_port"):
                fabric = FabricClient("captcha", network)
                log.info("OSC fabric → TreeHouse %s:%d", th["ip"], th["osc_port"])
            else:
                log.warning("network.json: treehouse not configured — OSC disabled")
        except FileNotFoundError as exc:
            log.warning("%s — OSC disabled", exc)

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
    pygame.display.set_caption("FundingCAPTCHA")
    pygame.mouse.set_visible(False)
    clock  = pygame.time.Clock()

    fonts = {
        "big": pygame.font.SysFont("monospace", 32, bold=True),
        "sml": pygame.font.SysFont("monospace", 18),
    }

    # ── Games ─────────────────────────────────────────────────────────────────
    games    = _load_games(settings)
    bag      = _ShuffleBag(games)
    no_game  = _NoGame()
    cur_game = bag.next() or no_game
    cur_game.reset()

    # ── Camera thread state (mutable dict for safe swap across closures) ──────
    cam: dict[str, Any] = {
        "q":      queue.Queue(maxsize=32),
        "stop":   threading.Event(),
        "thread": None,
    }

    def _start_camera() -> None:
        cam["q"]    = queue.Queue(maxsize=32)
        cam["stop"] = threading.Event()
        if args.camera or use_mock:
            t = threading.Thread(
                target=_camera_thread,
                args=(_make_camera(), settings, cam["q"], cam["stop"]),
                daemon=True,
            )
            t.start()
            cam["thread"] = t
            log.info("Camera thread started (%s)", "mock" if use_mock else "Orbbec")
        else:
            # No camera: skip BG_CAL immediately
            cam["q"].put({"type": "cal_done"})

    def _do_restart() -> None:
        cam["stop"].set()
        if cam["thread"] and cam["thread"].is_alive():
            cam["thread"].join(timeout=5.0)
        _save_local({})
        _start_camera()
        log.info("Camera restarted — entering BG_CAL")

    # ── State ─────────────────────────────────────────────────────────────────
    state: AppState                 = AppState.BG_CAL
    projector: ScreenProjector | None = None
    corner_cal: CornerCal | None    = None
    current_blobs: list[dict]       = []
    cal_frame                       = 0
    cal_total                       = settings.get("calibration_frames", 60)
    gx, gy, gw, gh                  = _letterbox(WW, WH, 4.0 / 3.0)
    t_last_osc                      = time.monotonic()
    intensity                       = 0.0

    _start_camera()

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
                    state = AppState.BG_CAL
                    projector = corner_cal = None
                    current_blobs = []
                    threading.Thread(target=_do_restart, daemon=True).start()

        # HTTP restart
        if _http_restart.is_set():
            _http_restart.clear()
            state = AppState.BG_CAL
            projector = corner_cal = None
            current_blobs = []
            threading.Thread(target=_do_restart, daemon=True).start()

        # Drain camera queue
        try:
            while True:
                msg   = cam["q"].get_nowait()
                mtype = msg["type"]

                if mtype == "cal_progress":
                    cal_frame = msg["frame"]
                    cal_total = msg["total"]
                    broadcast({"state": "bg_cal",
                                "progress": cal_frame / max(cal_total, 1)})

                elif mtype == "cal_done":
                    saved = load_settings().get("screen_corners")
                    if saved:
                        try:
                            projector = ScreenProjector(
                                saved["bottom_left"],
                                saved["bottom_right"],
                                saved["top_left"],
                            )
                            gx, gy, gw, gh = _letterbox(WW, WH, projector.aspect)
                            state = AppState.LIVE
                            log.info("Corners loaded — entering LIVE")
                        except Exception as exc:
                            log.warning("Bad saved corners (%s) — entering CORNER_CAL", exc)
                            corner_cal = CornerCal(cal_dwell, stable_cm)
                            state      = AppState.CORNER_CAL
                    else:
                        corner_cal = CornerCal(cal_dwell, stable_cm)
                        state      = AppState.CORNER_CAL
                        log.info("No corners — entering CORNER_CAL")
                    broadcast({"state": state.name.lower()})

                elif mtype == "blobs":
                    current_blobs = msg["blobs"]
                    broadcast({"state": "live", "blobs": current_blobs})

                elif mtype == "error":
                    log.error("Camera: %s", msg["msg"])
                    broadcast({"state": "error", "error": msg["msg"]})

        except queue.Empty:
            pass

        # Draw
        screen.fill(BLACK)

        if state == AppState.BG_CAL:
            pass  # solid black — projector output minimised during depth bg capture

        elif state == AppState.CORNER_CAL:
            assert corner_cal is not None
            corner_cal.push_blobs(current_blobs)

            if corner_cal.just_accepted and not corner_cal.done:
                log.info("Corner accepted: %s", _CAL_CORNERS[corner_cal.idx - 1])

            if corner_cal.done:
                result    = corner_cal.result()
                projector = ScreenProjector(result["bottom_left"],
                                            result["bottom_right"],
                                            result["top_left"])
                gx, gy, gw, gh = _letterbox(WW, WH, projector.aspect)
                _save_local({"screen_corners": result})
                log.info("Corners saved to %s", SETTINGS_LOCAL)
                corner_cal = None
                state      = AppState.LIVE
                broadcast({"state": "live"})
                cur_game = bag.next() or no_game
                cur_game.reset()
            else:
                _draw_corner_cal(screen, fonts, WW, WH, gx, gy, gw, gh, corner_cal)

        elif state == AppState.LIVE:
            intensity, event = cur_game.update(
                current_blobs, projector, max_plane_dist, dt)
            cur_game.draw(screen)

            if event in ("win", "loss"):
                if event == "loss":
                    log.info("Blow-Up — cycling game")
                    if fabric:
                        fabric.send_event("blowup")
                cur_game = bag.next() or no_game
                cur_game.reset()
                intensity = 0.0

            now = time.monotonic()
            if now - t_last_osc >= 0.1 and fabric:
                t_last_osc = now
                fabric.report("intensity", float(intensity))

        pygame.display.flip()


if __name__ == "__main__":
    main()
