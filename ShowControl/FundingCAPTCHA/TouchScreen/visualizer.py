"""
Remote visualizer — FastAPI WebSocket server + embedded browser client.

The show computer runs this server (default port 8766).
Open  http://<show-computer-ip>:8766  on any browser to see:
  Left panel  — Camera view: raw touch positions in camera pixel space.
                During calibration shows progress and recorded corner pixels.
  Right panel — Screen view: the projected grid with confirmed touch cells
                highlighted.  During corner calibration shows the 4 corner
                markers and which one is "next".

State is pushed to all connected browsers on every frame.
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

import uvicorn  # type: ignore[import]
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore[import]
from fastapi.responses import HTMLResponse  # type: ignore[import]

# ---------------------------------------------------------------------------
# Embedded HTML / JS client
# ---------------------------------------------------------------------------

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FundingCAPTCHA Touch Debug</title>
<style>
  * { box-sizing: border-box; }
  body { background:#0a0a14; color:#ddd; font-family:monospace; margin:0;
         display:flex; flex-direction:column; height:100vh; overflow:hidden; }
  #header { padding:6px 14px; display:flex; align-items:center; gap:20px;
             border-bottom:1px solid #222; flex-shrink:0; }
  h1  { margin:0; font-size:1em; letter-spacing:.1em; color:#00d4ff; }
  #status { font-size:.8em; color:#888; flex:1; }
  #legend { font-size:.75em; color:#aaa; display:flex; gap:1.2em; }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%;
         margin-right:4px; vertical-align:middle; }
  canvas { display:block; }
</style>
</head>
<body>
<div id="header">
  <h1>FundingCAPTCHA Touch Debug</h1>
  <div id="status">connecting…</div>
  <div id="legend">
    <span><span class="dot" style="background:#00d4ff"></span>raw touch</span>
    <span><span class="dot" style="background:#51cf66"></span>confirmed cell / recorded corner</span>
    <span><span class="dot" style="background:#ffd43b"></span>next corner</span>
  </div>
</div>
<canvas id="c"></canvas>

<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
const statusEl = document.getElementById('status');

function resize() {
  const hdr = document.getElementById('header').offsetHeight;
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight - hdr;
}
resize();
window.addEventListener('resize', () => { resize(); if (lastState) draw(lastState); });

let lastState = null;

// ------------------------------------------------------------------ draw
function draw(s) {
  const W = canvas.width, H = canvas.height;
  const t = performance.now();

  ctx.clearRect(0, 0, W, H);

  // Split canvas in two equal halves
  const midX = Math.floor(W / 2);
  drawCameraPanel(ctx, 0,    0, midX, H, s, t);
  drawScreenPanel(ctx, midX, 0, W - midX, H, s, t);

  // Divider
  ctx.strokeStyle = '#222';
  ctx.lineWidth   = 1;
  ctx.beginPath(); ctx.moveTo(midX, 0); ctx.lineTo(midX, H); ctx.stroke();
}

// ------------------------------------------------------------------ camera panel
function drawCameraPanel(ctx, px, py, pw, ph, s, t) {
  ctx.fillStyle = '#0d0d1a';
  ctx.fillRect(px, py, pw, ph);

  ctx.fillStyle = '#444';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('CAMERA', px + pw / 2, py + 14);

  // Camera frame rectangle (correct aspect ratio)
  const camW_px = (s.camera && s.camera.width)  || 640;
  const camH_px = (s.camera && s.camera.height) || 400;
  const camAR   = camW_px / camH_px;
  const pad     = 36;
  let fw = pw - pad * 2, fh = ph - pad * 2 - 20;
  if (fw / camAR > fh) { fw = fh * camAR; } else { fh = fw / camAR; }
  const fx = px + (pw - fw) / 2;
  const fy = py + (ph - fh) / 2 + 10;

  // Camera frame border
  ctx.strokeStyle = '#2a2a3a';
  ctx.lineWidth   = 1;
  ctx.strokeRect(fx, fy, fw, fh);

  // Map camera pixel → canvas
  function cam(x, y) {
    return [fx + (x / camW_px) * fw, fy + (y / camH_px) * fh];
  }

  // --- Background calibration progress ---
  if (s.app_state === 'background_calibration') {
    const p = s.bg_cal_progress || 0;
    ctx.fillStyle = 'rgba(255,212,59,0.15)';
    ctx.fillRect(fx, fy, fw * p, fh);
    ctx.fillStyle = '#ffd43b';
    ctx.font      = '13px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Background calibration…', fx + fw / 2, fy + fh / 2 - 10);
    ctx.fillText(Math.round(p * 100) + '%', fx + fw / 2, fy + fh / 2 + 12);
    return;
  }

  // --- Corner calibration: recorded pixel positions ---
  const cc = s.corner_cal;
  if (cc && cc.recorded_pixels) {
    cc.recorded_pixels.forEach((p, i) => {
      const [cx, cy] = cam(p[0], p[1]);
      ctx.beginPath(); ctx.arc(cx, cy, 9, 0, Math.PI * 2);
      ctx.fillStyle   = '#51cf66';
      ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.stroke();
      ctx.fillStyle   = '#000';
      ctx.font        = 'bold 9px monospace';
      ctx.textAlign   = 'center';
      ctx.fillText(i, cx, cy + 3);
    });
  }

  // --- Raw touch blobs ---
  (s.raw_touches || []).forEach(touch => {
    const [cx, cy] = cam(touch.px, touch.py);
    const r = Math.max(5, Math.min(22, Math.sqrt(touch.pixel_count / Math.PI)));
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle   = 'rgba(0,212,255,0.35)'; ctx.fill();
    ctx.strokeStyle = '#00d4ff'; ctx.lineWidth = 2; ctx.stroke();
  });

  // Coordinate hint
  ctx.fillStyle = '#333';
  ctx.font      = '9px monospace';
  ctx.textAlign = 'left';
  ctx.fillText('0,0', fx + 2, fy + 10);
  ctx.textAlign = 'right';
  ctx.fillText(camW_px + ',' + camH_px, fx + fw - 2, fy + fh - 2);
}

// ------------------------------------------------------------------ screen panel
function drawScreenPanel(ctx, px, py, pw, ph, s, t) {
  ctx.fillStyle = '#0d0d1a';
  ctx.fillRect(px, py, pw, ph);

  ctx.fillStyle = '#444';
  ctx.font      = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('SCREEN', px + pw / 2, py + 14);

  const pad = 40;
  const sz  = Math.min(pw - pad * 2, ph - pad * 2 - 24);
  const sx  = px + (pw - sz) / 2;
  const sy  = py + (ph - sz) / 2 + 8;

  // Screen border
  ctx.strokeStyle = '#2a2a3a';
  ctx.lineWidth   = 1;
  ctx.strokeRect(sx, sy, sz, sz);

  // Map UV → canvas
  function uv(u, v) { return [sx + u * sz, sy + v * sz]; }

  const grid = s.grid;
  if (!grid) return;

  // === RUNNING: grid cells ===
  if (s.app_state === 'running') {
    const cols = grid.cols || 4;
    const rows = grid.rows || 4;
    const cw   = sz / cols;
    const ch   = sz / rows;
    const confirmed = new Set((grid.confirmed || []).map(([c, r]) => c + ',' + r));

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = sx + c * cw, y = sy + r * ch;
        const on = confirmed.has(c + ',' + r);
        if (on) {
          ctx.fillStyle = 'rgba(0,212,255,0.45)';
          ctx.fillRect(x + 1, y + 1, cw - 2, ch - 2);
        }
        ctx.strokeStyle = on ? '#00d4ff' : '#1e2430';
        ctx.lineWidth   = on ? 1.5 : 1;
        ctx.strokeRect(x, y, cw, ch);

        ctx.fillStyle = on ? '#fff' : '#2a3040';
        ctx.font      = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(c + ',' + r, x + cw / 2, y + ch / 2 + 3);
      }
    }

    // Post-homography touch dots
    (s.screen_touches || []).forEach(st => {
      const [cx, cy] = uv(st.u, st.v);
      ctx.beginPath(); ctx.arc(cx, cy, 7, 0, Math.PI * 2);
      ctx.fillStyle   = 'rgba(0,212,255,0.85)'; ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.stroke();
    });
    return;
  }

  // === CORNER CALIBRATION: corner markers ===
  const cc = s.corner_cal;
  if (!cc || !cc.corner_uvs) return;

  const LABELS = ['TL', 'TR', 'BR', 'BL'];
  const NAMES  = ['top-left', 'top-right', 'bottom-right', 'bottom-left'];
  const recorded = cc.corners_recorded || 0;
  const pulse = 0.65 + 0.35 * Math.sin(t / 380);

  cc.corner_uvs.forEach((cuv, i) => {
    const [cx, cy] = uv(cuv[0], cuv[1]);
    const done   = i < recorded;
    const isNext = i === recorded;
    const r      = isNext ? 14 * pulse : 12;

    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle   = done    ? 'rgba(81,207,102,0.3)'
                    : isNext  ? `rgba(0,212,255,${0.25 * pulse})`
                    :           'rgba(60,60,80,0.2)';
    ctx.fill();
    ctx.strokeStyle = done ? '#51cf66' : isNext ? '#00d4ff' : '#444';
    ctx.lineWidth   = done ? 2 : isNext ? 2 : 1;
    ctx.stroke();

    ctx.fillStyle = done ? '#51cf66' : isNext ? '#00d4ff' : '#444';
    ctx.font      = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(LABELS[i], cx, cy + 4);

    // Name label offset away from screen centre
    const lx = cx + (cuv[0] < 0.5 ? -22 : 22);
    const ly = cy + (cuv[1] < 0.5 ? -18 : 18);
    ctx.fillStyle = done ? '#51cf66' : isNext ? '#aef' : '#333';
    ctx.font      = '9px monospace';
    ctx.fillText(NAMES[i], lx, ly);
  });

  // Instruction banner
  if (cc.next_corner_name) {
    const bannerY = sy + sz + 22;
    ctx.fillStyle = '#ffd43b';
    ctx.font      = '13px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Touch the ' + cc.next_corner_name + ' marker', px + pw / 2, bannerY);
  } else if (recorded === 4) {
    ctx.fillStyle = '#51cf66';
    ctx.font      = '13px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('All corners recorded ✓', px + pw / 2, sy + sz + 22);
  }

  // Raw touches on screen panel during corner cal (helps aim)
  (s.raw_touches || []).forEach(touch => {
    // We don't have a homography yet so just show a warning dot at screen centre
    ctx.beginPath(); ctx.arc(sx + sz / 2, sy + sz / 2, 5, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,212,59,0.5)'; ctx.fill();
  });
}

// ------------------------------------------------------------------ status bar
function updateStatus(s) {
  const state  = (s.app_state || '').replace(/_/g, ' ');
  const frame  = s.frame || 0;
  const grid   = s.grid  || {};
  const nTouch = (s.raw_touches || []).length;
  const nConf  = (grid.confirmed || []).length;
  statusEl.textContent =
    state.toUpperCase() +
    ' | frame ' + frame +
    ' | raw_touches=' + nTouch +
    ' | confirmed=' + nConf +
    ' | grid=' + (grid.cols || '?') + '×' + (grid.rows || '?');
}

// ------------------------------------------------------------------ WebSocket
function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws    = new WebSocket(proto + '://' + location.host + '/ws');

  ws.onopen    = () => { statusEl.textContent = 'connected — waiting for data…'; };
  ws.onclose   = () => {
    statusEl.textContent = 'disconnected — retrying…';
    setTimeout(connect, 2000);
  };
  ws.onerror   = () => ws.close();
  ws.onmessage = ev => { lastState = JSON.parse(ev.data); updateStatus(lastState); };
}

connect();

// Continuous animation loop (enables smooth pulsing even between frames)
function animate() {
  if (lastState) draw(lastState);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI()
_connections: set[WebSocket] = set()
_loop: asyncio.AbstractEventLoop | None = None


@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


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
    """Thread-safe: push a state snapshot to all connected browsers."""
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

def start_server(host: str = "0.0.0.0", port: int = 8766) -> None:
    """Launch the FastAPI / WebSocket server in a background daemon thread."""
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
    print(f"Visualizer: http://{host}:{port}")
