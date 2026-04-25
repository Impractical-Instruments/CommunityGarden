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
import os
import sys
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

# ── Paths ──────────────────────────────────────────────────────────────────────
DIR        = Path(os.path.dirname(os.path.abspath(__file__)))
UPLOADS    = DIR / "uploads"
PAIRS_FILE = DIR / "pairs.json"
SETTINGS   = DIR / "captcha-settings.json"
UPLOADS.mkdir(exist_ok=True)

MAX_UPLOAD_BYTES = 12 * 1024 * 1024  # 12 MB base64 ceiling

# ── ShowControl CV imports — optional ──────────────────────────────────────────
_SC = (DIR / "../../ShowControl/FlowerBeds").resolve()
sys.path.insert(0, str(_SC))
try:
    import numpy as np
    from blob_tracker import BlobTracker, CalibrationState
    from blob_stabilizer import BlobStabilizer, StabilizerConfig
    from camera import MockCamera, OrbbecCamera
    from transforms import Rotator, Transform, transform_position
    _CV_AVAILABLE = True
except ImportError:
    _CV_AVAILABLE = False

# ── WebSocket state ─────────────────────────────────────────────────────────────
_connections: set[WebSocket] = set()
_loop: asyncio.AbstractEventLoop | None = None


# ── App lifecycle ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _loop
    _loop = asyncio.get_running_loop()
    yield


app = FastAPI(lifespan=lifespan)


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
        print(f"  UPLOAD  {filename}  ({len(b64) // 1024} kB)")
        return {"ok": True, "filename": filename, "url": f"/uploads/{filename}"}
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
        print(f"  PAIRS   saved {len(pairs)} pair(s)")
        return {"ok": True, "count": len(pairs)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/captcha-settings")
async def get_captcha_settings():
    return json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}


# ── WebSocket ──────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            await asyncio.sleep(10)
    except (WebSocketDisconnect, Exception):
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
    """
    Runs blob detection in a daemon thread; publishes positions via broadcast().
    Follows the same pattern as ShowControl/FlowerBeds/main.py.
    """
    calib_frames = settings.get("calibration_frames", 60)
    stab_cfg     = settings.get("stabilizer", {})
    cam_cfg      = settings.get("camera", {})

    stabilizer = BlobStabilizer(StabilizerConfig(
        max_match_dist_cm  = stab_cfg.get("max_match_dist_cm",  80.0),
        smoothing_alpha    = stab_cfg.get("smoothing_alpha",     0.3),
        max_miss_frames    = stab_cfg.get("max_miss_frames",     8),
        min_confirm_frames = stab_cfg.get("min_confirm_frames",  2),
    ))
    tracker = BlobTracker()

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

    with camera:
        for frame in camera.frames():
            state = tracker._state
            if state == CalibrationState.NOT_CALIBRATED:
                tracker.begin_calibration(calib_frames, frame.width, frame.height)
                tracker.push_calibration_frame(frame)
            elif state == CalibrationState.IN_PROGRESS:
                tracker.push_calibration_frame(frame)
            else:
                result  = tracker.detect(frame)
                raw_pos = [
                    transform_position(cam_tf, b.world_pos_cm())
                    for b in result.world_blobs if b.valid
                ]
                tracked = stabilizer.update(raw_pos)
                broadcast({
                    "blobs": [
                        {"id":  int(t.stable_id),
                         "x":   float(t.world_pos_cm[0]),
                         "y":   float(t.world_pos_cm[1])}
                        for t in tracked
                    ]
                })


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

    settings: dict = {}
    if SETTINGS.exists():
        settings = json.loads(SETTINGS.read_text())

    if args.camera or args.mock_camera:
        if not _CV_AVAILABLE:
            print("ERROR: CV libraries (numpy/scipy) not available.\n"
                  "       Install with: pip install -r requirements.txt\n"
                  "       (On Pi, prefer: sudo apt-get install python3-numpy python3-scipy)",
                  file=sys.stderr)
            sys.exit(1)

        cam_cfg = settings.get("camera", {})
        if args.mock_camera:
            camera: Any = MockCamera(
                width  = cam_cfg.get("width",  640),
                height = cam_cfg.get("height", 400),
                fps    = cam_cfg.get("fps",     10),
            )
        else:
            camera = OrbbecCamera(
                serial = cam_cfg.get("serial") or None,
                width  = cam_cfg.get("width",  640),
                height = cam_cfg.get("height", 400),
                fps    = cam_cfg.get("fps",     10),
            )

        t = threading.Thread(target=_cv_thread, args=(camera, settings), daemon=True)
        t.start()
        mode = "mock" if args.mock_camera else "Orbbec"
        print(f"  CV      {mode} camera thread started")

    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    print(f"FundingCAPTCHA  port {args.port}")
    print(f"  Games:    http://{local_ip}:{args.port}/")
    print(f"  Upload:   http://{local_ip}:{args.port}/upload.html   ← share with kids")
    print(f"  Gallery:  http://{local_ip}:{args.port}/gallery.html  ← organiser tool")
    print("Press Ctrl+C to stop.\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
