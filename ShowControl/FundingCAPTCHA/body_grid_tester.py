#!/usr/bin/env python3
"""
FundingCAPTCHA body grid tester.

Displays silhouettes detected in configurable depth slabs on a configurable grid.
Used to tune camera ROI, slab depths, and grid size for the BodyGrid game.

States:
  BG_CAL  → solid black; camera builds background depth model
  LIVE    → grid + silhouette display

Keys:
  D    → toggle debug overlay
  R    → restart from BG_CAL
  Q    → quit

Config keys (captcha-settings.json / captcha-settings.local.json):
  grid                      [cols, rows]        default [4, 4]
  camera_roi                {x,y,w,h}           default full frame
  depth_slabs               [{near_mm,far_mm,slab_id}]
  slab_styles               {"<slab_id>": {"color": [R,G,B]}}
  cell_activation_threshold float               default 0.30
  activation_rule           "additive"|"max"    default "additive"
  calibration_frames        int                 default 60
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import queue
import sys
import threading
import time
from enum import Enum, auto
from pathlib import Path

import numpy as np
import pygame

DIR = Path(__file__).parent
SETTINGS = DIR / "captcha-settings.json"
SETTINGS_LOCAL = DIR / "captcha-settings.local.json"

sys.path.insert(0, str(DIR.parent.parent))
sys.path.insert(0, str(DIR))

try:
    from IIVision import MockCamera, OrbbecCamera, Calibrator, BlobTracker, DetectionConfig
    _CV_AVAILABLE = True
except ImportError:
    _CV_AVAILABLE = False

from body_grid import BodyGridActivator, BodyGridConfig, SlabConfig, CellActivations

log = logging.getLogger("bodygrid-tester")

BLACK    = (  0,   0,   0)
WHITE    = (255, 255, 255)
DK_GREY  = ( 28,  28,  28)
MID_GREY = ( 75,  75,  75)
LT_GREY  = (140, 140, 140)
GREEN    = (  0, 200,  75)
YELLOW   = (240, 200,   0)
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


def _build_config(settings: dict, cols: int | None, rows: int | None) -> BodyGridConfig:
    grid = settings.get("grid", [4, 4])
    cam = settings.get("camera", {})
    w = cam.get("width", 640)
    h = cam.get("height", 400)
    roi = settings.get("camera_roi", {"x": 0, "y": 0, "w": w, "h": h})
    raw_slabs = settings.get("depth_slabs", [{"near_mm": 800, "far_mm": 2500, "slab_id": 0}])
    slabs = [SlabConfig(**s) for s in raw_slabs]
    return BodyGridConfig(
        cols=cols or grid[0],
        rows=rows or grid[1],
        camera_roi=roi,
        slabs=slabs,
        cell_activation_threshold=settings.get("cell_activation_threshold", 0.30),
        activation_rule=settings.get("activation_rule", "additive"),
    )


# ── Monitoring server ──────────────────────────────────────────────────────────

_ws_clients: set = set()
_mon_loop: asyncio.AbstractEventLoop | None = None
_app_status: dict = {"state": "starting"}
_debug_toggle_event = threading.Event()


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


async def _ws_handler(ws) -> None:
    _ws_clients.add(ws)
    try:
        await ws.send(json.dumps(_app_status))
        async for msg in ws:
            try:
                data = json.loads(msg)
                if data.get("cmd") == "debug_toggle":
                    _debug_toggle_event.set()
            except Exception:
                pass
    finally:
        _ws_clients.discard(ws)


async def _process_request(connection, request):
    from websockets.http11 import Response
    from websockets.datastructures import Headers

    path = request.path
    if path == "/ws":
        return None

    if path == "/api/debug/toggle":
        _debug_toggle_event.set()
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
            log.info("Monitoring on 0.0.0.0:%d  (WS /ws  POST /api/debug/toggle)", port)
            await asyncio.Future()

    loop.run_until_complete(_serve())


# ── Camera thread ──────────────────────────────────────────────────────────────

def _camera_thread(camera, settings: dict, cam_q: queue.Queue,
                   stop: threading.Event) -> None:
    try:
        _camera_inner(camera, settings, cam_q, stop)
    except Exception as exc:
        log.error("Camera thread crashed: %s", exc, exc_info=True)
        cam_q.put({"type": "error", "msg": str(exc)})


def _camera_inner(camera, settings: dict, cam_q: queue.Queue,
                  stop: threading.Event) -> None:
    det_cfg = settings.get("detection", {})
    detection_config = DetectionConfig(
        depth_delta_mm  = det_cfg.get("depth_delta_mm",   25),
        min_blob_pixels = det_cfg.get("min_blob_pixels",  500),
        min_depth_mm    = det_cfg.get("min_depth_mm",     500),
        max_depth_mm    = det_cfg.get("max_depth_mm",     4000),
    )

    calib_frames = settings.get("calibration_frames", 60)
    log.info("BG_CAL: collecting %d frames", calib_frames)
    calibrator = Calibrator(calib_frames)
    frame_idx = 0

    with camera:
        for frame in camera.frames():
            if stop.is_set():
                return
            frame_idx += 1
            cam_q.put({"type": "cal_progress", "frame": frame_idx, "total": calib_frames})
            if calibrator.push_frame(frame):
                break

        if stop.is_set():
            return

        calibration = calibrator.build()
        log.info("BG_CAL complete")
        cam_q.put({"type": "cal_done"})

        tracker = BlobTracker(calibration, detection_config)

        for frame in camera.frames():
            if stop.is_set():
                break
            fg = tracker.detect_foreground(frame)
            cam_q.put({"type": "foreground", "frame": fg, "raw": frame})


# ── Drawing ────────────────────────────────────────────────────────────────────

def _letterbox(win_w: int, win_h: int, aspect: float) -> tuple[int, int, int, int]:
    if win_w / win_h > aspect:
        gh = win_h; gw = int(gh * aspect)
    else:
        gw = win_w; gh = int(gw / aspect)
    return (win_w - gw) // 2, (win_h - gh) // 2, gw, gh


def _draw_cal(surf: pygame.Surface, fonts: dict,
              WW: int, WH: int, frame: int, total: int) -> None:
    pct = frame / max(total, 1)
    msg = fonts["big"].render(f"BG_CAL  {frame}/{total}", True, YELLOW)
    surf.blit(msg, (WW // 2 - msg.get_width() // 2, WH // 2 - 30))
    bw, bh = 400, 20
    bx, by = WW // 2 - bw // 2, WH // 2 + 20
    pygame.draw.rect(surf, MID_GREY, (bx, by, bw, bh))
    pygame.draw.rect(surf, GREEN, (bx, by, int(bw * pct), bh))
    pygame.draw.rect(surf, WHITE, (bx, by, bw, bh), 1)


def _draw_grid(surf: pygame.Surface, cfg: BodyGridConfig,
               activations: CellActivations, slab_styles: dict,
               gx: int, gy: int, gw: int, gh: int) -> None:
    cell_w = gw / cfg.cols
    cell_h = gh / cfg.rows

    for row in range(cfg.rows):
        for col in range(cfg.cols):
            x0 = int(gx + col * cell_w)
            y0 = int(gy + row * cell_h)
            x1 = int(gx + (col + 1) * cell_w)
            y1 = int(gy + (row + 1) * cell_h)
            pygame.draw.rect(surf, DK_GREY, (x0, y0, x1 - x0, y1 - y0))

            if (col, row) in activations:
                slabs = activations[(col, row)]
                if slabs:
                    slab_id, _ = max(slabs, key=lambda s: s[1])
                    style = slab_styles.get(str(slab_id), {})
                    color = tuple(style.get("color", [0, 220, 100]))
                    tile = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
                    tile.fill((*color, 120))
                    surf.blit(tile, (x0, y0))

            pygame.draw.rect(surf, MID_GREY, (x0, y0, x1 - x0, y1 - y0), 1)


def _draw_silhouette(surf: pygame.Surface, foreground_roi: np.ndarray,
                     cfg: BodyGridConfig, slab_styles: dict,
                     gx: int, gy: int, gw: int, gh: int) -> None:
    roi_h, roi_w = foreground_roi.shape
    if roi_w == 0 or roi_h == 0:
        return

    rgb = np.zeros((roi_h, roi_w, 3), dtype=np.uint8)
    for slab in cfg.slabs:
        style = slab_styles.get(str(slab.slab_id), {})
        color = style.get("color", [0, 220, 100])
        mask = (foreground_roi > 0) & (foreground_roi >= slab.near_mm) & (foreground_roi < slab.far_mm)
        rgb[mask] = color

    sil_surf = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
    sil_surf.set_colorkey((0, 0, 0))
    sil_surf = pygame.transform.scale(sil_surf, (gw, gh))
    surf.blit(sil_surf, (gx, gy))


def _crop_foreground_roi(foreground: np.ndarray, cfg: BodyGridConfig) -> np.ndarray:
    roi = cfg.camera_roi
    flipped = foreground[:, ::-1]
    return flipped[roi["y"]:roi["y"] + roi["h"], roi["x"]:roi["x"] + roi["w"]]


def _draw_debug(surf: pygame.Surface, fonts: dict,
                foreground_roi: np.ndarray | None,
                raw_frame: np.ndarray | None,
                activations: CellActivations,
                cfg: BodyGridConfig,
                fps: float,
                gx: int, gy: int, gw: int, gh: int) -> None:
    # Semi-transparent debug panel on right side
    panel_w = max(220, gw // 4)
    panel_x = gx + gw - panel_w
    panel = pygame.Surface((panel_w, gh), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    surf.blit(panel, (panel_x, gy))

    f = fonts["sml"]
    y = gy + 6
    x = panel_x + 6

    def _line(text: str, color: tuple = LT_GREY) -> None:
        nonlocal y
        surf.blit(f.render(text, True, color), (x, y))
        y += f.get_height() + 2

    _line(f"FPS: {fps:.0f}", WHITE)
    _line(f"Active: {len(activations)}/{cfg.cols * cfg.rows}", CYAN)
    _line(f"Grid: {cfg.cols}×{cfg.rows}")
    _line(f"Rule: {cfg.activation_rule}")
    _line(f"Threshold: {cfg.cell_activation_threshold:.0%}")
    y += 4
    _line("Slabs:", YELLOW)
    for slab in cfg.slabs:
        _line(f"  [{slab.slab_id}] {slab.near_mm}–{slab.far_mm}mm")

    # Per-cell coverage in debug: draw on grid cells
    cell_w = gw / cfg.cols
    cell_h = gh / cfg.rows
    small = fonts["tiny"]
    for (col, row), slab_list in activations.items():
        cx = int(gx + col * cell_w + 4)
        cy = int(gy + row * cell_h + 4)
        for i, (sid, cov) in enumerate(slab_list):
            lbl = small.render(f"{sid}:{cov:.0%}", True, WHITE)
            surf.blit(lbl, (cx, cy + i * (small.get_height() + 1)))

    # Mini depth views — raw (top) and foreground ROI (bottom)
    def _mini_surf(arr: np.ndarray, mini_h: int) -> pygame.Surface:
        mini_w = int(mini_h * arr.shape[1] / max(arr.shape[0], 1))
        max_d = max(int(arr.max()), 1)
        norm = (arr.astype(float) / max_d * 255).clip(0, 255).astype(np.uint8)
        rgb = np.stack([norm, norm, norm], axis=-1)
        s = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        return pygame.transform.scale(s, (mini_w, mini_h)), mini_w

    mini_h = min(gh // 5, 80)
    bottom_y = gy + gh - 6

    for arr, label in [(foreground_roi, "foreground ROI"), (raw_frame, "raw depth")]:
        if arr is None or arr.size == 0:
            continue
        s, mini_w = _mini_surf(arr, mini_h)
        mini_x = panel_x + (panel_w - mini_w) // 2
        bottom_y -= mini_h
        surf.blit(s, (mini_x, bottom_y))
        pygame.draw.rect(surf, MID_GREY, (mini_x, bottom_y, mini_w, mini_h), 1)
        lbl = fonts["tiny"].render(label, True, LT_GREY)
        surf.blit(lbl, (mini_x, bottom_y - lbl.get_height() - 1))
        bottom_y -= lbl.get_height() + 5


# ── App state ──────────────────────────────────────────────────────────────────

class AppState(Enum):
    BG_CAL = auto()
    LIVE   = auto()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="FundingCAPTCHA body grid tester")
    ap.add_argument("--camera",      action="store_true")
    ap.add_argument("--mock-camera", action="store_true")
    ap.add_argument("--port",        type=int, default=8081)
    ap.add_argument("--cols",        type=int, default=None)
    ap.add_argument("--rows",        type=int, default=None)
    ap.add_argument("--debug",       action="store_true", help="Start with debug overlay")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    settings   = load_settings()
    bg_cfg     = _build_config(settings, args.cols, args.rows)
    activator  = BodyGridActivator(bg_cfg)
    slab_styles = settings.get("slab_styles", {"0": {"color": [0, 220, 100]}})
    cam_cfg    = settings.get("camera", {})
    use_mock   = args.mock_camera
    debug      = args.debug

    if (args.camera or use_mock) and not _CV_AVAILABLE:
        sys.exit("ERROR: CV libraries not available — pip install -r requirements.txt")

    threading.Thread(target=_run_monitoring, args=(args.port,), daemon=True).start()

    pygame.init()
    info   = pygame.display.Info()
    WW, WH = info.current_w, info.current_h
    screen = pygame.display.set_mode((WW, WH), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("BodyGrid Tester")
    pygame.mouse.set_visible(False)
    clock  = pygame.time.Clock()

    fonts = {
        "big":  pygame.font.SysFont("monospace", 32, bold=True),
        "sml":  pygame.font.SysFont("monospace", 16),
        "tiny": pygame.font.SysFont("monospace", 12),
    }

    gx, gy, gw, gh = _letterbox(WW, WH, 4.0 / 3.0)

    def _make_camera():
        if use_mock:
            return MockCamera(width=cam_cfg.get("width", 640),
                              height=cam_cfg.get("height", 400),
                              fps=cam_cfg.get("fps", 10))
        return OrbbecCamera(serial=cam_cfg.get("serial") or None,
                            width=cam_cfg.get("width", 640),
                            height=cam_cfg.get("height", 400),
                            fps=cam_cfg.get("fps", 10))

    cam: dict = {"q": queue.Queue(maxsize=32), "stop": threading.Event(), "thread": None}

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
        else:
            cam["q"].put({"type": "cal_done"})

    state: AppState       = AppState.BG_CAL
    activations: CellActivations = {}
    foreground_roi: np.ndarray | None = None
    raw_frame: np.ndarray | None = None
    cal_frame, cal_total  = 0, settings.get("calibration_frames", 60)
    fps_display           = 0.0

    _start_camera()

    while True:
        dt = clock.tick(FPS) / 1000.0
        fps_display = 0.9 * fps_display + 0.1 * (1.0 / max(dt, 1e-6))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cam["stop"].set(); pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    cam["stop"].set(); pygame.quit(); sys.exit(0)
                elif event.key == pygame.K_d:
                    debug = not debug
                    log.info("Debug overlay %s", "on" if debug else "off")
                elif event.key == pygame.K_r:
                    state = AppState.BG_CAL
                    activations = {}
                    foreground_roi = None
                    raw_frame = None
                    cam["stop"].set()
                    threading.Thread(target=_start_camera, daemon=True).start()

        if _debug_toggle_event.is_set():
            _debug_toggle_event.clear()
            debug = not debug
            log.info("Debug overlay %s (remote)", "on" if debug else "off")

        try:
            while True:
                msg = cam["q"].get_nowait()
                mtype = msg["type"]

                if mtype == "cal_progress":
                    cal_frame = msg["frame"]
                    cal_total = msg["total"]
                    broadcast({"state": "bg_cal", "progress": cal_frame / max(cal_total, 1)})

                elif mtype == "cal_done":
                    state = AppState.LIVE
                    log.info("BG_CAL complete — LIVE")
                    broadcast({"state": "live"})

                elif mtype == "foreground":
                    fg: np.ndarray = msg["frame"]
                    raw_frame = msg.get("raw")
                    activations = activator.activate(fg)
                    foreground_roi = _crop_foreground_roi(fg, bg_cfg)
                    broadcast({"state": "live", "active_cells": len(activations)})

                elif mtype == "error":
                    log.error("Camera: %s", msg["msg"])
                    broadcast({"state": "error", "error": msg["msg"]})

        except queue.Empty:
            pass

        screen.fill(BLACK)

        if state == AppState.BG_CAL:
            _draw_cal(screen, fonts, WW, WH, cal_frame, cal_total)

        elif state == AppState.LIVE:
            _draw_grid(screen, bg_cfg, activations, slab_styles, gx, gy, gw, gh)
            if foreground_roi is not None:
                _draw_silhouette(screen, foreground_roi, bg_cfg, slab_styles, gx, gy, gw, gh)
            if debug:
                _draw_debug(screen, fonts, foreground_roi, raw_frame, activations,
                            bg_cfg, fps_display, gx, gy, gw, gh)

        pygame.display.flip()


if __name__ == "__main__":
    main()
