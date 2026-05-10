#!/usr/bin/env python3
"""
FundingCAPTCHA server — FastAPI + uvicorn.

Usage:
  python server.py [port]                # browser pointer-only (default 8080)
  python server.py --mock-camera         # mock blobs via WebSocket (no hardware)
  python server.py --camera              # real Orbbec depth camera

Endpoints:
  GET  /                       → index.html (kiosk game)
  GET  /upload.html            → kid photo upload page
  GET  /gallery.html           → organiser pairing tool
  POST /upload                 → save base64 photo to uploads/
  GET  /api/photos             → list uploaded photos
  GET  /api/pairs              → Upside Down pairs config
  POST /api/pairs              → save pairs config
  GET  /api/captcha-settings   → floor rect + camera config (for browser blob mapping)
  WS   /ws                     → pushes {blobs:[{id,x,y}]} when CV thread is running
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Paths ──────────────────────────────────────────────────────────────────────
DIR            = Path(os.path.dirname(os.path.abspath(__file__)))
UPLOADS        = DIR / "uploads"
PAIRS_FILE     = DIR / "pairs.json"
SETTINGS       = DIR / "captcha-settings.json"
SETTINGS_LOCAL = DIR / "captcha-settings.local.json"
UPLOADS.mkdir(exist_ok=True)


def _load_settings() -> dict:
    s = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    if SETTINGS_LOCAL.exists():
        s.update(json.loads(SETTINGS_LOCAL.read_text()))
    return s

MAX_UPLOAD_BYTES = 12 * 1024 * 1024  # 12 MB base64 ceiling
log = logging.getLogger("captcha")

# ── OSC Fabric ────────────────────────────────────────────────────────────────
_SHOWCONTROL = (DIR / "..").resolve()
sys.path.insert(0, str(_SHOWCONTROL))
try:
    from OSCFabric import FabricClient, load_network_config
    _FABRIC_AVAILABLE = True
except ImportError:
    _FABRIC_AVAILABLE = False

_fabric: "FabricClient | None" = None
_HEARTBEAT_TICK_S = 1.0


# ── IIVision CV imports — optional ────────────────────────────────────────────
_REPO = (DIR / "../..").resolve()
sys.path.insert(0, str(_REPO))
try:
    import numpy as np
    from IIVision import MockCamera, OrbbecCamera, StabilizerConfig, Transform, Rotator, Calibrator, DetectionConfig, run_pipeline
    _CV_AVAILABLE = True
except ImportError:
    _CV_AVAILABLE = False

# ── OSC receive — optional ────────────────────────────────────────────────────
try:
    from pythonosc.dispatcher import Dispatcher as _OscDispatcher
    from pythonosc.osc_server import ThreadingOSCUDPServer as _OscServer
    _OSC_RX_AVAILABLE = True
except ImportError:
    _OSC_RX_AVAILABLE = False

# ── WebSocket state ─────────────────────────────────────────────────────────────
_connections: set[WebSocket] = set()
_log_queues: list[asyncio.Queue] = []
_loop: asyncio.AbstractEventLoop | None = None
_cv_stop: threading.Event = threading.Event()
_cv_thread_handle: threading.Thread | None = None
_camera_factory: Callable[[], Any] | None = None   # set in main() when --camera/--mock-camera
_cv_settings: dict[str, Any] = {}
_osc_server: Any = None
_cv_status: dict[str, Any] = {"status": "unknown"}  # latest CV state; sent to new WS clients


class WebSocketLogHandler(logging.Handler):
    """Streams log records to all connected /logs WebSocket clients."""

    def emit(self, record: logging.LogRecord) -> None:
        if _loop is None or not _log_queues:
            return
        msg = json.dumps({
            "ts": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
        })
        for q in list(_log_queues):
            try:
                _loop.call_soon_threadsafe(q.put_nowait, msg)
            except Exception:
                pass


# ── App lifecycle ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _loop
    _loop = asyncio.get_running_loop()
    handler = WebSocketLogHandler()
    logging.getLogger("captcha").addHandler(handler)

    async def _heartbeat():
        while True:
            await asyncio.sleep(_HEARTBEAT_TICK_S)
            if _fabric is not None:
                _fabric.tick(_HEARTBEAT_TICK_S)

    task = asyncio.create_task(_heartbeat())
    try:
        yield
    finally:
        task.cancel()
        if _osc_server is not None:
            _osc_server.shutdown()
        # Signal CV thread to exit its pipeline loop, then wait for it to
        # release the camera before the process exits — prevents the camera
        # being left half-open for the next start.
        _cv_stop.set()
        if _cv_thread_handle is not None:
            _cv_thread_handle.join(timeout=5.0)
        for ws in list(_connections):
            try:
                await ws.close()
            except Exception:
                pass
        _connections.clear()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])


# ── REST routes ────────────────────────────────────────────────────────────────

@app.post("/upload")
async def post_upload(request: Request):
    body = await request.body()
    if len(body) > MAX_UPLOAD_BYTES:
        return {"ok": False, "error": "Upload too large"}
    try:
        data   = json.loads(body)
        label  = str(data.get("label", "untitled")).strip()[:80] or "untitled"
        who    = str(data.get("name", "")).strip()[:40]
        imgstr = data.get("data", "")
        if "," not in imgstr:
            raise ValueError("Missing data URL separator")
        header, b64 = imgstr.split(",", 1)
        ext = "jpg"
        if "png"  in header: ext = "png"
        elif "gif" in header: ext = "gif"
        elif "webp" in header: ext = "webp"

        def _safe(s: str) -> str:
            return s.replace(" ", "_").replace("/", "_")

        prefix   = f"{_safe(who)}__" if who else ""
        filename = f"{uuid.uuid4().hex[:8]}__{prefix}{_safe(label)}.{ext}"
        (UPLOADS / filename).write_bytes(base64.b64decode(b64))
        log.info("upload %s (%d kB)", filename, len(b64) // 1024)
        return {"ok": True, "filename": filename, "url": f"/uploads/{filename}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.delete("/upload/{filename}")
async def delete_upload(filename: str):
    # Reject any path traversal attempts
    target = (UPLOADS / filename).resolve()
    if target.parent != UPLOADS.resolve():
        return {"ok": False, "error": "Invalid filename"}
    try:
        target.unlink()
        log.info("delete %s", filename)
        return {"ok": True}
    except FileNotFoundError:
        return {"ok": False, "error": "Not found"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/photos")
async def get_photos():
    photos = []
    for f in sorted(UPLOADS.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            continue
        parts = f.stem.split("__", 2)
        who   = parts[1].replace("_", " ") if len(parts) == 3 else ""
        label = parts[-1].replace("_", " ") if len(parts) >= 2 else f.stem
        photos.append({"filename": f.name, "url": f"/uploads/{f.name}",
                       "label": label, "who": who})
    return photos


@app.get("/api/pairs")
async def get_pairs():
    return json.loads(PAIRS_FILE.read_text()) if PAIRS_FILE.exists() else []


@app.post("/api/pairs")
async def post_pairs(request: Request):
    try:
        pairs = json.loads(await request.body())
        PAIRS_FILE.write_text(json.dumps(pairs, indent=2))
        log.info("pairs saved %d pair(s)", len(pairs))
        return {"ok": True, "count": len(pairs)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/captcha-settings")
async def get_captcha_settings():
    return _load_settings()


@app.post("/api/game-event")
async def post_game_event(request: Request):
    """Receive game state from the browser and relay to the OSC fabric."""
    try:
        data = json.loads(await request.body())
    except Exception:
        return {"ok": False, "error": "invalid JSON"}

    game           = data.get("game")
    event          = data.get("event")
    score          = float(data.get("score", 0))
    win_score      = float(data.get("winScore", 1))
    timer_fraction = float(data.get("timerFraction", 1.0))

    if game == "rhythm":
        intensity = score / win_score if win_score > 0 else 0.0
    elif game == "upsidedown":
        intensity = 1.0 - max(0.0, min(1.0, timer_fraction))
    elif game is not None:
        intensity = 0.3
    else:
        intensity = 0.0

    if _fabric is not None:
        _fabric.report("intensity", float(intensity))
        if event in ("win", "lose"):
            _fabric.send_event("blowup")

    return {"ok": True}


# ── WebSocket ──────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _connections.add(websocket)
    try:
        # Immediately push current CV state so clients don't have to wait for the next frame.
        if _cv_status["status"] != "unknown":
            await websocket.send_text(json.dumps(_cv_status))
        while True:
            await asyncio.sleep(10)
    except (WebSocketDisconnect, asyncio.CancelledError, Exception):
        pass
    finally:
        _connections.discard(websocket)


def broadcast(state: dict[str, Any]) -> None:
    """Thread-safe: push a JSON blob to all connected browsers."""
    if not _connections or _loop is None:
        return
    payload = json.dumps(state)

    async def _send() -> None:
        dead: set[WebSocket] = set()
        for ws in list(_connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        _connections.difference_update(dead)

    asyncio.run_coroutine_threadsafe(_send(), _loop)


# ── CV thread ──────────────────────────────────────────────────────────────────

def _cv_thread(camera: Any, settings: dict) -> None:
    """Runs blob detection in a daemon thread; publishes positions via broadcast()."""
    try:
        _cv_thread_inner(camera, settings)
    except Exception as exc:
        global _cv_status
        _cv_status = {"status": "error", "error": str(exc)}
        log.error("CV thread crashed: %s", exc, exc_info=True)
        broadcast(_cv_status)


def _cv_thread_inner(camera: Any, settings: dict) -> None:
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

    global _cv_status
    calib_frames = settings.get("calibration_frames", 60)
    log.info("Calibrating (%d frames)…", calib_frames)
    calibrator = Calibrator(calib_frames)
    frame_idx = 0
    with camera:
        for frame in camera.frames():
            if _cv_stop.is_set():
                log.info("Calibration interrupted by shutdown")
                return  # camera closed cleanly by context manager exit
            frame_idx += 1
            _cv_status = {"status": "calibrating", "progress": frame_idx / calib_frames}
            broadcast(_cv_status)
            if calibrator.push_frame(frame):
                break
    calibration = calibrator.build()
    log.info("Calibration complete")
    _cv_status = {"status": "active", "blobs": []}

    detection_config = DetectionConfig(
        depth_delta_mm   = det_cfg.get("depth_delta_mm",   20),
        min_blob_pixels  = det_cfg.get("min_blob_pixels",  500),
        min_depth_mm     = det_cfg.get("min_depth_mm",     500),
        max_depth_mm     = det_cfg.get("max_depth_mm",     6000),
    )

    frame_count = 0
    t_last_log = time.monotonic()

    for tracked in run_pipeline(camera, cam_tf, calibration, stabilizer_config,
                                detection_config=detection_config):
        if _cv_stop.is_set():
            break
        frame_count += 1
        now = time.monotonic()
        if now - t_last_log >= 5.0:
            log.info("camera active | frame=%d blobs=%d", frame_count, len(tracked))
            t_last_log = now
        msg = {
            "status": "active",
            "blobs": [
                {"id":  int(t.stable_id),
                 "x":   float(t.world_pos_cm[0]),
                 "y":   float(t.world_pos_cm[1]),
                 "z":   float(t.world_pos_cm[2])}
                for t in tracked
            ],
        }
        _cv_status = msg
        broadcast(msg)


# ── CV pipeline restart ────────────────────────────────────────────────────────

def _restart_cv_pipeline() -> None:
    """Hard-restart: stop old CV thread, close camera, reopen, redo calibration."""
    global _cv_stop, _cv_thread_handle
    if _camera_factory is None:
        log.warning("Restart requested but no camera configured — ignoring")
        return
    log.info("CV pipeline restart requested via OSC")
    _cv_stop.set()
    if _cv_thread_handle and _cv_thread_handle.is_alive():
        _cv_thread_handle.join(timeout=5.0)
    _cv_stop.clear()
    t = threading.Thread(target=_cv_thread, args=(_camera_factory(), _cv_settings), daemon=True)
    t.start()
    _cv_thread_handle = t
    log.info("CV pipeline restarted")


def _start_osc_server(port: int) -> None:
    global _osc_server
    if not _OSC_RX_AVAILABLE:
        log.warning("python-osc not available — OSC listener disabled")
        return
    disp = _OscDispatcher()
    disp.map(
        "/captcha/restart",
        lambda addr, *a: threading.Thread(target=_restart_cv_pipeline, daemon=True).start(),
    )
    srv = _OscServer(("0.0.0.0", port), disp)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    _osc_server = srv
    log.info("OSC listening on 0.0.0.0:%d  (/captcha/restart)", port)


# ── Dashboard endpoints ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return JSONResponse({"ok": True})


@app.websocket("/logs")
async def logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=500)
    _log_queues.append(q)
    try:
        while True:
            msg = await q.get()
            await websocket.send_text(msg)
    except (WebSocketDisconnect, asyncio.CancelledError, Exception):
        pass
    finally:
        if q in _log_queues:
            _log_queues.remove(q)


# ── Static files (catch-all — must be registered last) ────────────────────────
app.mount("/", StaticFiles(directory=str(DIR), html=True), name="static")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="FundingCAPTCHA server")
    parser.add_argument("port", type=int, nargs="?", default=8080,
                        help="HTTP port (default: 8080)")
    parser.add_argument("--camera",      action="store_true",
                        help="Use real Orbbec depth camera (requires pyorbbecsdk2)")
    parser.add_argument("--mock-camera", action="store_true",
                        help="Use mock camera — fake blobs, no hardware needed")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = _load_settings()

    global _fabric
    if _FABRIC_AVAILABLE:
        try:
            network = load_network_config()
            th = network.get("elements", {}).get("treehouse", {})
            if th.get("ip") and th.get("osc_port"):
                _fabric = FabricClient("captcha", network)
                log.info("OSC fabric → TreeHouse %s:%d", th["ip"], th["osc_port"])
            else:
                log.warning("network.json: treehouse ip/osc_port not set — OSC fabric disabled")
        except FileNotFoundError as exc:
            log.warning("%s — OSC fabric disabled", exc)
    else:
        log.warning("OSCFabric not available — OSC fabric disabled")

    if args.camera or args.mock_camera:
        if not _CV_AVAILABLE:
            print("ERROR: CV libraries (numpy/scipy) not available.\n"
                  "       Install with: pip install -r requirements.txt\n"
                  "       (On Pi, prefer: sudo apt-get install python3-numpy python3-scipy)",
                  file=sys.stderr)
            sys.exit(1)

        cam_cfg = settings.get("camera", {})
        use_mock = args.mock_camera

        def _make_camera() -> Any:
            if use_mock:
                return MockCamera(
                    width  = cam_cfg.get("width",  640),
                    height = cam_cfg.get("height", 400),
                    fps    = cam_cfg.get("fps",     10),
                )
            return OrbbecCamera(
                serial = cam_cfg.get("serial") or None,
                width  = cam_cfg.get("width",  640),
                height = cam_cfg.get("height", 400),
                fps    = cam_cfg.get("fps",     10),
            )

        global _cv_thread_handle, _camera_factory, _cv_settings
        _camera_factory = _make_camera
        _cv_settings    = settings
        t = threading.Thread(target=_cv_thread, args=(_make_camera(), settings), daemon=True)
        t.start()
        _cv_thread_handle = t
        mode = "mock" if use_mock else "Orbbec"
        log.info("CV %s camera thread started", mode)

        # OSC inbound listener — accepts /captcha/restart to hard-restart the pipeline.
        # Port from network.json captcha.osc_port (ADR-0007), default 9003.
        osc_port = 9003
        if _FABRIC_AVAILABLE:
            try:
                _net = load_network_config()
                osc_port = _net.get("elements", {}).get("captcha", {}).get("osc_port", 9003)
            except Exception:
                pass
        _start_osc_server(osc_port)

    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    print(f"FundingCAPTCHA  port {args.port}")
    print(f"  Games:    http://{local_ip}:{args.port}/")
    print(f"  Upload:   http://{local_ip}:{args.port}/upload.html        ← share with kids")
    print(f"  Gallery:  http://{local_ip}:{args.port}/gallery.html       ← organiser tool")
    print(f"  Touch:    http://{local_ip}:{args.port}/touch-test.html    ← camera touch tester")
    print("Press Ctrl+C to stop.\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
