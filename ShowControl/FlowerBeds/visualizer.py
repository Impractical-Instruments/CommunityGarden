"""
Remote visualizer — FastAPI WebSocket server + embedded browser client.

The show computer runs this server (default port 8765).
Open  http://<show-computer-ip>:8765  on your laptop to see a live top-down
view of blobs, clusters, and camera positions.

State is pushed to all connected browsers on every frame.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Any, TypedDict

import uvicorn  # type: ignore[import]
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore[import]


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class BlobState(TypedDict):
    id: int
    x: float
    y: float


class ClusterState(TypedDict):
    motor_id: int
    x: float
    y: float
    yaw_deg: float
    has_target: bool
    target_id: int | None


class CameraState(TypedDict):
    name: str
    x: float
    y: float
    yaw_deg: float


class VisualizerState(TypedDict):
    frame: int
    blobs: list[BlobState]
    clusters: list[ClusterState]
    cameras: list[CameraState]
    calibration_state: str
    missing_motor_ids: list[int]

# ---------------------------------------------------------------------------
# Embedded HTML/JS client
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Flower Beds — Live View</title>
<style>
  body { background:#111; color:#eee; font-family:monospace; margin:0; display:flex;
         flex-direction:column; align-items:center; }
  h1   { margin:.5em 0 0; font-size:1.1em; letter-spacing:.1em; }
  #status { font-size:.8em; color:#888; margin:.3em 0; }
  canvas { border:1px solid #333; background:#1a1a2e; }
  #legend { font-size:.75em; color:#aaa; margin:.4em; display:flex; gap:1.5em; }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%;
         margin-right:4px; vertical-align:middle; }
</style>
</head>
<body>
<h1>🌸 Flower Beds — Live View</h1>
<div id="status">connecting…</div>
<div id="banner" style="display:none; background:#5a1e1e; color:#ffd0d0; padding:.4em .8em;
     border:1px solid #ff6b6b; border-radius:4px; font-size:.85em; margin:.3em 0; max-width:90%;"></div>
<div id="legend">
  <span><span class="dot" style="background:#00d4ff"></span>blob</span>
  <span><span class="dot" style="background:#ff6b6b"></span>cluster (no target)</span>
  <span><span class="dot" style="background:#51cf66"></span>cluster (has target)</span>
  <span><span class="dot" style="background:#ffd43b"></span>camera</span>
</div>
<canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
const status = document.getElementById('status');

// Fit canvas to window, leaving room for header
function resize() {
  const w = Math.min(window.innerWidth  - 20, 900);
  const h = Math.min(window.innerHeight - 130, 700);
  canvas.width  = w;
  canvas.height = h;
}
resize();
window.addEventListener('resize', resize);

let lastState = null;

// ------------------------------------------------------------------ draw
function draw(state) {
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  // Collect all world positions to auto-scale
  const allX = [], allY = [];
  (state.blobs    || []).forEach(b => { allX.push(b.x); allY.push(b.y); });
  (state.clusters || []).forEach(c => { allX.push(c.x); allY.push(c.y); });
  (state.cameras  || []).forEach(c => { allX.push(c.x); allY.push(c.y); });

  if (allX.length === 0) {
    ctx.fillStyle = '#555';
    ctx.textAlign = 'center';
    ctx.font = '14px monospace';
    ctx.fillText('no data yet', W/2, H/2);
    return;
  }

  const pad   = 60;
  const minX  = Math.min(...allX) - 100;
  const maxX  = Math.max(...allX) + 100;
  const minY  = Math.min(...allY) - 100;
  const maxY  = Math.max(...allY) + 100;
  const scaleX = (W - pad*2) / (maxX - minX || 1);
  const scaleY = (H - pad*2) / (maxY - minY || 1);
  const scale  = Math.min(scaleX, scaleY);

  // world → canvas  (X=right, Y=forward→down)
  function toCanvas(wx, wy) {
    return [
      pad + (wx - minX) * scale,            // world X (right) → canvas X (right)
      pad + (wy - minY) * scale,            // world Y (forward) → canvas Y (down)
    ];
  }

  // Grid lines (every 100 cm)
  ctx.strokeStyle = '#252540';
  ctx.lineWidth   = 1;
  for (let gx = Math.floor(minX/100)*100; gx <= maxX; gx += 100) {
    const [cx0, cy0] = toCanvas(gx, minY);
    const [cx1, cy1] = toCanvas(gx, maxY);
    ctx.beginPath(); ctx.moveTo(cx0, cy0); ctx.lineTo(cx1, cy1); ctx.stroke();
  }
  for (let gy = Math.floor(minY/100)*100; gy <= maxY; gy += 100) {
    const [cx0, cy0] = toCanvas(minX, gy);
    const [cx1, cy1] = toCanvas(maxX, gy);
    ctx.beginPath(); ctx.moveTo(cx0, cy0); ctx.lineTo(cx1, cy1); ctx.stroke();
  }

  // Origin cross
  const [ox, oy] = toCanvas(0, 0);
  ctx.strokeStyle = '#444'; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(ox-8,oy); ctx.lineTo(ox+8,oy); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(ox,oy-8); ctx.lineTo(ox,oy+8); ctx.stroke();

  // ---- axis indicator (fixed top-left corner) ----
  const axOriginX = 52, axOriginY = 52, axLen = 36;
  // +X axis: world X (right) → canvas right
  ctx.strokeStyle = '#e05252'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(axOriginX, axOriginY); ctx.lineTo(axOriginX + axLen, axOriginY); ctx.stroke();
  // arrowhead
  ctx.beginPath(); ctx.moveTo(axOriginX + axLen, axOriginY);
  ctx.lineTo(axOriginX + axLen - 8, axOriginY - 4); ctx.lineTo(axOriginX + axLen - 8, axOriginY + 4); ctx.closePath();
  ctx.fillStyle = '#e05252'; ctx.fill();
  ctx.fillStyle = '#e05252'; ctx.font = 'bold 10px monospace'; ctx.textAlign = 'left';
  ctx.fillText('+X (right)', axOriginX + axLen + 4, axOriginY + 4);
  // +Y axis: world Y (forward) → canvas down
  ctx.strokeStyle = '#52e07a'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(axOriginX, axOriginY); ctx.lineTo(axOriginX, axOriginY + axLen); ctx.stroke();
  // arrowhead
  ctx.beginPath(); ctx.moveTo(axOriginX, axOriginY + axLen);
  ctx.lineTo(axOriginX - 4, axOriginY + axLen - 8); ctx.lineTo(axOriginX + 4, axOriginY + axLen - 8); ctx.closePath();
  ctx.fillStyle = '#52e07a'; ctx.fill();
  ctx.fillStyle = '#52e07a'; ctx.font = 'bold 10px monospace'; ctx.textAlign = 'center';
  ctx.fillText('+Y (fwd)', axOriginX, axOriginY + axLen + 12);


  // ---- cameras ----
  (state.cameras || []).forEach(cam => {
    const [cx, cy] = toCanvas(cam.x, cam.y);
    const yawRad   = (cam.yaw_deg || 0) * Math.PI / 180;
    // Triangle pointing in the look direction
    const tipX = cx + Math.sin(yawRad) * 18;
    const tipY = cy + Math.cos(yawRad) * 18;
    const lx   = cx + Math.sin(yawRad - 2.4) * 10;
    const ly   = cy + Math.cos(yawRad - 2.4) * 10;
    const rx   = cx + Math.sin(yawRad + 2.4) * 10;
    const ry   = cy + Math.cos(yawRad + 2.4) * 10;
    ctx.fillStyle = '#ffd43b';
    ctx.beginPath(); ctx.moveTo(tipX, tipY);
    ctx.lineTo(lx, ly); ctx.lineTo(rx, ry); ctx.closePath(); ctx.fill();

    ctx.fillStyle = '#aaa'; ctx.font = '10px monospace'; ctx.textAlign = 'center';
    ctx.fillText(cam.name || 'cam', cx, cy + 22);
  });

  // ---- clusters ----
  (state.clusters || []).forEach(cl => {
    const [cx, cy]  = toCanvas(cl.x, cl.y);
    const yawRad    = (cl.yaw_deg || 0) * Math.PI / 180;
    const hasTarget = cl.has_target;

    // Circle
    ctx.beginPath(); ctx.arc(cx, cy, 7, 0, Math.PI*2);
    ctx.fillStyle   = hasTarget ? '#51cf66' : '#ff6b6b';
    ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.stroke();

    // Arrow showing yaw
    const arrowLen = 18;
    const ax = cx + Math.sin(yawRad) * arrowLen;
    const ay = cy + Math.cos(yawRad) * arrowLen;
    ctx.strokeStyle = hasTarget ? '#51cf66' : '#ff6b6b';
    ctx.lineWidth   = 2;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ax, ay); ctx.stroke();

    // Motor ID and current yaw
    ctx.fillStyle = '#fff'; ctx.font = '9px monospace'; ctx.textAlign = 'center';
    ctx.fillText('M' + cl.motor_id, cx, cy - 11);
    ctx.fillStyle = hasTarget ? '#51cf66' : '#888';
    ctx.fillText((cl.yaw_deg || 0).toFixed(1) + '°', cx, cy + 20);
  });

  // ---- blobs ----
  (state.blobs || []).forEach(blob => {
    const [cx, cy] = toCanvas(blob.x, blob.y);
    ctx.beginPath(); ctx.arc(cx, cy, 14, 0, Math.PI*2);
    ctx.fillStyle   = 'rgba(0,212,255,0.25)';
    ctx.fill();
    ctx.strokeStyle = '#00d4ff'; ctx.lineWidth = 2; ctx.stroke();

    ctx.fillStyle = '#00d4ff'; ctx.font = '9px monospace'; ctx.textAlign = 'center';
    ctx.fillText('#' + blob.id, cx, cy + 3);
  });

  // ---- calibration badge ----
  ctx.fillStyle = state.calibration_state === 'calibrated' ? '#51cf66' : '#ffd43b';
  ctx.font = '11px monospace'; ctx.textAlign = 'left';
  ctx.fillText('CAL: ' + (state.calibration_state || '?'), 8, 18);

  // ---- frame counter ----
  ctx.fillStyle = '#666'; ctx.font = '10px monospace'; ctx.textAlign = 'right';
  ctx.fillText('frame ' + (state.frame || 0), W - 8, 18);
}

// ------------------------------------------------------------------ WS
function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws    = new WebSocket(proto + '://' + location.host + '/ws');

  ws.onopen    = () => { status.textContent = 'connected'; };
  ws.onclose   = () => {
    status.textContent = 'disconnected — retrying…';
    setTimeout(connect, 2000);
  };
  ws.onerror   = () => ws.close();
  ws.onmessage = (ev) => {
    lastState = JSON.parse(ev.data);
    draw(lastState);
    const nb = (lastState.blobs || []).length;
    const nc = (lastState.clusters || []).length;
    status.textContent =
      (lastState.calibration_state || '?') +
      ' | ' + nb + ' blob' + (nb!==1?'s':'') +
      ' | ' + nc + ' cluster' + (nc!==1?'s':'');
    const banner = document.getElementById('banner');
    const missing = lastState.missing_motor_ids || [];
    if (missing.length > 0) {
      banner.style.display = 'block';
      banner.textContent = '⚠ ' + missing.length + ' motor ID' +
        (missing.length===1?'':'s') + ' configured but not found on any controller: [' +
        missing.join(', ') + ']  — those flowers will not move.';
    } else {
      banner.style.display = 'none';
    }
  };
}

connect();

// Redraw on resize in case canvas size changed
window.addEventListener('resize', () => { resize(); if (lastState) draw(lastState); });
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
_connections: set[WebSocket] = set()
_log_queues: list[asyncio.Queue] = []
_loop: asyncio.AbstractEventLoop | None = None


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


@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


@app.get("/health")
async def health():
    return JSONResponse({"ok": True})


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            # Keep the connection alive; we push from the main thread.
            await asyncio.sleep(10)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _connections.discard(websocket)


@app.websocket("/logs")
async def logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=500)
    _log_queues.append(q)
    try:
        while True:
            msg = await q.get()
            await websocket.send_text(msg)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        if q in _log_queues:
            _log_queues.remove(q)


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None:
        raise RuntimeError("Visualizer not started")
    return _loop


def broadcast(state: VisualizerState) -> None:
    """
    Thread-safe: push a state snapshot to all connected browsers.
    Call this from the main (non-async) processing loop.
    """
    if not _connections or _loop is None:
        return

    payload = json.dumps(state)

    async def _send():
        dead: set[WebSocket] = set()
        for ws in list(_connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        _connections.difference_update(dead)

    asyncio.run_coroutine_threadsafe(_send(), _loop)


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    """
    Launch the FastAPI server in a background daemon thread.
    Returns immediately; the server keeps running until the process exits.
    """
    global _loop

    ready = threading.Event()

    def _run():
        global _loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _loop = loop
        ready.set()
        config = uvicorn.Config(app, host=host, port=port, log_level="warning", loop="asyncio")
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    ready.wait()
    handler = WebSocketLogHandler()
    logging.getLogger("flower_beds").addHandler(handler)
    print(f"Visualizer: http://{host}:{port}")
