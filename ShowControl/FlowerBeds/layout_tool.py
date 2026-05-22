"""
FlowerBeds layout tool — pre-show module placement and verification.

Run on your Windows laptop before show:
    cd ShowControl/FlowerBeds
    python layout_tool.py

Opens http://localhost:8764
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import socket
import threading
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import uvicorn  # type: ignore[import]
from fastapi import FastAPI  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]
from pythonosc.udp_client import SimpleUDPClient  # type: ignore[import]

_OSC_ADDRESS = "/cg/ff/rot"

_DEFAULT_CLUSTER_OFFSETS = [
    [10, 10, 0.0],
    [-10, 10, 0.0],
    [10, -10, 0.0],
    [-10, -10.0, 0.0],
]

# Paths set by main() before the server starts
_config_path: Path = Path("settings.json")
_network_path: Path = Path(__file__).resolve().parents[1] / "network.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _flowerbeds_controllers(network: dict) -> list[dict]:
    """Return [{name, ip, osc_port}] for all flowerbeds_controller_* firmware entries."""
    out = []
    for name, fw in network.get("firmware", {}).items():
        if name.startswith("flowerbeds_controller_") and fw.get("ip") and fw.get("osc_port"):
            out.append({"name": name, "ip": fw["ip"], "osc_port": fw["osc_port"]})
    return out


def _tcp_ping(ip: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def _osc_clients(network: dict) -> list[SimpleUDPClient]:
    return [
        SimpleUDPClient(c["ip"], c["osc_port"])
        for c in _flowerbeds_controllers(network)
    ]


def _send_osc(network: dict, motor_id: int, deg_software: float) -> None:
    """Send /cg/ff/rot to all flowerbeds controllers. Negates deg (CCW+ → CW+)."""
    osc_deg = -deg_software
    for client in _osc_clients(network):
        client.send_message(_OSC_ADDRESS, [motor_id, osc_deg])


def _default_module(index: int) -> dict:
    n = index + 1
    return {
        "name": f"Module {n}",
        "registration_point_cm": [0.0, 0.0, 0.0],
        "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
        "clusters": [
            {
                "motor_id": (index * 4) + i + 1,
                "pos_offset_cm": list(_DEFAULT_CLUSTER_OFFSETS[i]),
                "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0},
            }
            for i in range(4)
        ],
    }


# ---------------------------------------------------------------------------
# Embedded HTML/JS client
# ---------------------------------------------------------------------------

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FlowerBeds Layout Tool</title>
<style>
* { box-sizing: border-box; }
body { background:#111; color:#ddd; font-family:monospace; font-size:13px;
       margin:0; display:flex; flex-direction:column; height:100vh; overflow:hidden; }
#toolbar { display:flex; align-items:center; gap:8px; padding:6px 10px;
           background:#1a1a2e; border-bottom:1px solid #333; flex-shrink:0; flex-wrap:wrap; }
#toolbar h1 { margin:0; font-size:1em; color:#aaa; margin-right:4px; }
button { background:#2a2a4a; color:#ddd; border:1px solid #444; border-radius:3px;
         padding:3px 10px; cursor:pointer; font-family:monospace; font-size:12px; }
button:hover { background:#3a3a6a; }
button.active { background:#3a5fa0; border-color:#6090d0; color:#fff; }
button:disabled { opacity:.4; cursor:default; }
.btn-danger { background:#5a2020; border-color:#904040; }
.btn-danger:hover { background:#7a2020; }
.btn-green { background:#1a4a2a; border-color:#3a8a4a; }
.btn-green:hover { background:#2a5a3a; }
#ctrl-status { margin-left:auto; display:flex; gap:8px; align-items:center; font-size:11px; }
.ctrl-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#555; }
.ctrl-dot.online { background:#51cf66; }
.ctrl-dot.offline { background:#ff6b6b; }
#save-msg { font-size:11px; color:#888; }
#main { display:flex; flex:1; min-height:0; }
#canvas-wrap { flex:1; min-width:0; position:relative; overflow:hidden; }
canvas { display:block; width:100%; height:100%; cursor:default; }
canvas.aim-mode { cursor:crosshair; }
#sidebar { width:280px; flex-shrink:0; overflow-y:auto; background:#161622;
           border-left:1px solid #333; padding:8px; }
#no-sel { color:#555; text-align:center; margin-top:30px; }
.field-row { display:flex; align-items:center; gap:4px; margin-bottom:4px; }
.field-row label { width:60px; color:#999; flex-shrink:0; }
.field-row input[type=text], .field-row input[type=number] {
  flex:1; background:#1e1e38; color:#ddd; border:1px solid #444; border-radius:3px;
  padding:2px 5px; font-family:monospace; font-size:12px; min-width:0; }
.field-row input[type=number] { width:70px; flex:unset; }
.cluster-card { background:#1c1c30; border:1px solid #333; border-radius:4px;
                padding:6px; margin-bottom:6px; }
.cluster-card.selected-aim { border-color:#ffd43b; }
.cluster-header { display:flex; align-items:center; gap:4px; margin-bottom:4px; font-weight:bold; }
.cluster-btns { display:flex; gap:4px; margin-top:4px; flex-wrap:wrap; }
.hold-row { display:flex; align-items:center; gap:4px; margin-top:4px; }
.hold-row input[type=number] { width:60px; }
h3 { margin:0 0 8px; font-size:.9em; color:#aaa; }
.sep { border:none; border-top:1px solid #333; margin:8px 0; }
</style>
</head>
<body>
<div id="toolbar">
  <h1>🌸 Layout Tool</h1>
  <button id="btn-edit" class="active" onclick="setMode('edit')">Place/Edit</button>
  <button id="btn-aim" onclick="setMode('aim')">Aim</button>
  <button onclick="addModule()">+ Add Module</button>
  <button onclick="fitView()">Fit View</button>
  <button class="btn-green" onclick="saveLayout()" id="btn-save">Save settings.json</button>
  <span id="save-msg"></span>
  <div id="ctrl-status">
    <span id="ctrl-dots"></span>
    <button onclick="refreshControllerStatus()" style="padding:2px 6px;font-size:11px">Refresh</button>
  </div>
</div>
<div id="main">
  <div id="canvas-wrap"><canvas id="canvas"></canvas></div>
  <div id="sidebar">
    <div id="no-sel">Click a module to select it</div>
    <div id="mod-panel" style="display:none">
      <h3 id="mod-title">Module</h3>
      <div class="field-row">
        <label>Name</label>
        <input type="text" id="mod-name" oninput="onModNameInput()">
        <button class="btn-danger" onclick="deleteSelectedModule()" style="padding:2px 6px">Delete</button>
      </div>
      <div class="field-row">
        <label>X (cm)</label><input type="number" id="mod-x" step="1" oninput="onModPosInput()">
        <label style="width:auto">Y</label><input type="number" id="mod-y" step="1" oninput="onModPosInput()">
      </div>
      <div class="field-row">
        <label>Yaw (°)</label><input type="number" id="mod-yaw" step="1" oninput="onModYawInput()">
      </div>
      <hr class="sep">
      <h3>Clusters</h3>
      <div id="cluster-list"></div>
    </div>
  </div>
</div>
<script>
// ================================================================ state
const state = {
  modules: [],
  sel: -1,           // selected module index
  aimCluster: -1,    // selected cluster index (within sel module) for aim
  mode: 'edit',
  controllers: [],
  viewCX: 0, viewCY: 0,
  scale: 1.5,        // px/cm
  drag: null,        // {type:'module'|'rotate', idx, startWX, startWY, startModX, startModY}
  pan: null,         // {startX, startY, startVCX, startVCY}
  holdTimers: {},    // motor_id → setInterval handle
};

// ================================================================ canvas
const canvas  = document.getElementById('canvas');
const ctx     = canvas.getContext('2d');
const wrap    = document.getElementById('canvas-wrap');

function resize() {
  canvas.width  = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
  render();
}
window.addEventListener('resize', resize);

// world ↔ canvas
function w2c(wx, wy) {
  return [
    canvas.width  / 2 + (wx - state.viewCX) * state.scale,
    canvas.height / 2 + (wy - state.viewCY) * state.scale,
  ];
}
function c2w(cx, cy) {
  return [
    state.viewCX + (cx - canvas.width  / 2) / state.scale,
    state.viewCY + (cy - canvas.height / 2) / state.scale,
  ];
}

// cluster world pos (applies module yaw rotation, pitch/roll always 0)
function clusterWorldPos(mod, cl) {
  const yaw = (mod.rotation.yaw || 0) * Math.PI / 180;
  const cos = Math.cos(yaw), sin = Math.sin(yaw);
  const ox = cl.pos_offset_cm[0], oy = cl.pos_offset_cm[1];
  return [
    mod.registration_point_cm[0] + cos * ox + sin * oy,
    mod.registration_point_cm[1] - sin * ox + cos * oy,
  ];
}

// ================================================================ render
const MOD_R  = 10;   // module dot radius px
const ROT_R  = 7;    // rotate handle radius px
const CLU_R  = 6;    // cluster dot radius px
const ARROW_LEN_CM = 60; // yaw arrow length in world cm

function render() {
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  // Grid (100cm)
  const gridCm = 100;
  const step = gridCm * state.scale;
  const [ox, oy] = w2c(0, 0);
  ctx.strokeStyle = '#1e1e3e'; ctx.lineWidth = 1;
  for (let x = ((ox % step) + step) % step; x < W; x += step) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }
  for (let y = ((oy % step) + step) % step; y < H; y += step) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }
  // Origin cross
  ctx.strokeStyle = '#3a3a5a'; ctx.lineWidth = 1.5;
  if (ox >= 0 && ox <= W) { ctx.beginPath(); ctx.moveTo(ox, 0); ctx.lineTo(ox, H); ctx.stroke(); }
  if (oy >= 0 && oy <= H) { ctx.beginPath(); ctx.moveTo(0, oy); ctx.lineTo(W, oy); ctx.stroke(); }

  // Modules
  for (let i = 0; i < state.modules.length; i++) {
    const m   = state.modules[i];
    const sel = i === state.sel;
    const [mx, my] = w2c(m.registration_point_cm[0], m.registration_point_cm[1]);
    const yawRad   = (m.rotation.yaw || 0) * Math.PI / 180;
    const arrowPx  = ARROW_LEN_CM * state.scale;

    // Yaw arrow
    const axTip = mx + Math.sin(yawRad) * arrowPx;
    const ayTip = my + Math.cos(yawRad) * arrowPx;
    ctx.strokeStyle = sel ? '#ffd43b' : '#5577aa';
    ctx.lineWidth = sel ? 2 : 1.5;
    ctx.beginPath(); ctx.moveTo(mx, my); ctx.lineTo(axTip, ayTip); ctx.stroke();

    // Clusters
    for (let j = 0; j < m.clusters.length; j++) {
      const cl = m.clusters[j];
      const [cwx, cwy] = clusterWorldPos(m, cl);
      const [ccx, ccy] = w2c(cwx, cwy);
      const isAimSel = sel && j === state.aimCluster;
      ctx.beginPath(); ctx.arc(ccx, ccy, CLU_R, 0, Math.PI * 2);
      ctx.fillStyle = isAimSel ? '#ffd43b' : (sel ? '#6699cc' : '#44558a');
      ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.5; ctx.stroke();
      ctx.fillStyle = '#bbb'; ctx.font = '9px monospace'; ctx.textAlign = 'center';
      ctx.fillText('M' + cl.motor_id, ccx, ccy - 8);
    }

    // Module dot
    ctx.beginPath(); ctx.arc(mx, my, MOD_R, 0, Math.PI * 2);
    ctx.fillStyle = sel ? '#ffd43b' : '#aab0cc';
    ctx.fill();
    ctx.strokeStyle = sel ? '#fff' : '#888'; ctx.lineWidth = 1.5; ctx.stroke();

    // Rotate handle
    ctx.beginPath(); ctx.arc(axTip, ayTip, ROT_R, 0, Math.PI * 2);
    ctx.fillStyle = sel ? '#ffaa22' : '#667799';
    ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.stroke();

    // Label
    ctx.fillStyle = sel ? '#ffd43b' : '#888';
    ctx.font = sel ? 'bold 11px monospace' : '10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(m.name || `M${i+1}`, mx, my + MOD_R + 12);
  }

  // Aim cursor indicator
  if (state.mode === 'aim' && state.sel >= 0 && state.aimCluster >= 0) {
    ctx.fillStyle = '#ffd43b66';
    ctx.font = '11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('AIM MODE — click canvas to aim selected cluster', W / 2, 18);
  }
}

// ================================================================ fit view
function fitView() {
  if (state.modules.length === 0) {
    state.viewCX = 0; state.viewCY = 0; state.scale = 1.5;
    render(); return;
  }
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const m of state.modules) {
    const [rx, ry] = m.registration_point_cm;
    minX = Math.min(minX, rx); maxX = Math.max(maxX, rx);
    minY = Math.min(minY, ry); maxY = Math.max(maxY, ry);
    for (const c of m.clusters) {
      const [wx, wy] = clusterWorldPos(m, c);
      minX = Math.min(minX, wx); maxX = Math.max(maxX, wx);
      minY = Math.min(minY, wy); maxY = Math.max(maxY, wy);
    }
  }
  const pad = 150;
  const wW  = maxX - minX + 2 * pad || 300;
  const wH  = maxY - minY + 2 * pad || 300;
  state.viewCX = (minX + maxX) / 2;
  state.viewCY = (minY + maxY) / 2;
  state.scale  = Math.min(canvas.width / wW, canvas.height / wH);
  render();
}

// ================================================================ mouse
function mouseEventPos(e) {
  const r = canvas.getBoundingClientRect();
  return [e.clientX - r.left, e.clientY - r.top];
}
function hitModule(cx, cy) {
  const HIT = MOD_R + 4;
  for (let i = state.modules.length - 1; i >= 0; i--) {
    const m = state.modules[i];
    const [mx, my] = w2c(m.registration_point_cm[0], m.registration_point_cm[1]);
    if ((cx - mx) ** 2 + (cy - my) ** 2 < HIT ** 2) return {type: 'module', idx: i};
    // Rotate handle
    const yawRad = (m.rotation.yaw || 0) * Math.PI / 180;
    const arrowPx = ARROW_LEN_CM * state.scale;
    const rhx = mx + Math.sin(yawRad) * arrowPx;
    const rhy = my + Math.cos(yawRad) * arrowPx;
    if ((cx - rhx) ** 2 + (cy - rhy) ** 2 < (ROT_R + 4) ** 2) return {type: 'rotate', idx: i};
  }
  return null;
}

canvas.addEventListener('mousedown', e => {
  const [cx, cy] = mouseEventPos(e);
  if (e.button === 1 || (e.button === 0 && e.altKey)) {
    // Pan
    state.pan = {startX: cx, startY: cy, startVCX: state.viewCX, startVCY: state.viewCY};
    e.preventDefault();
    return;
  }
  if (e.button === 2) {
    state.pan = {startX: cx, startY: cy, startVCX: state.viewCX, startVCY: state.viewCY};
    return;
  }
  if (e.button !== 0) return;

  if (state.mode === 'aim') {
    if (state.sel < 0 || state.aimCluster < 0) return;
    const m  = state.modules[state.sel];
    const cl = m.clusters[state.aimCluster];
    const [wx, wy]    = c2w(cx, cy);
    const [cmx, cmy]  = clusterWorldPos(m, cl);
    const dx = wx - cmx, dy = wy - cmy;
    const yaw = Math.atan2(dx, dy) * 180 / Math.PI;
    sendAim(cl.motor_id, yaw);
    return;
  }

  // Edit mode
  const hit = hitModule(cx, cy);
  if (hit) {
    if (hit.idx !== state.sel) {
      state.sel = hit.idx;
      state.aimCluster = -1;
      updateSidebar();
    }
    const m   = state.modules[hit.idx];
    const [wx, wy] = c2w(cx, cy);
    state.drag = {
      type:     hit.type,
      idx:      hit.idx,
      startWX:  wx,
      startWY:  wy,
      startModX: m.registration_point_cm[0],
      startModY: m.registration_point_cm[1],
    };
  } else {
    state.sel = -1;
    state.aimCluster = -1;
    updateSidebar();
  }
  render();
});

canvas.addEventListener('mousemove', e => {
  const [cx, cy] = mouseEventPos(e);
  if (state.pan) {
    state.viewCX = state.pan.startVCX - (cx - state.pan.startX) / state.scale;
    state.viewCY = state.pan.startVCY - (cy - state.pan.startY) / state.scale;
    render(); return;
  }
  if (!state.drag) return;
  const [wx, wy] = c2w(cx, cy);
  const m = state.modules[state.drag.idx];
  if (state.drag.type === 'module') {
    m.registration_point_cm[0] = state.drag.startModX + (wx - state.drag.startWX);
    m.registration_point_cm[1] = state.drag.startModY + (wy - state.drag.startWY);
    if (state.drag.idx === state.sel) syncSidebarPos();
  } else {
    // Rotate: angle from registration point to current mouse world pos
    const dx = wx - m.registration_point_cm[0];
    const dy = wy - m.registration_point_cm[1];
    m.rotation.yaw = Math.atan2(dx, dy) * 180 / Math.PI;
    if (state.drag.idx === state.sel) syncSidebarYaw();
  }
  render();
});

canvas.addEventListener('mouseup', () => { state.drag = null; state.pan = null; });
canvas.addEventListener('mouseleave', () => { state.drag = null; state.pan = null; });
canvas.addEventListener('contextmenu', e => e.preventDefault());

canvas.addEventListener('wheel', e => {
  e.preventDefault();
  const [cx, cy] = mouseEventPos(e);
  const [wx, wy] = c2w(cx, cy);
  const factor   = e.deltaY < 0 ? 1.15 : (1 / 1.15);
  state.scale   *= factor;
  state.scale    = Math.max(0.05, Math.min(state.scale, 20));
  // Keep the point under the cursor fixed
  state.viewCX   = wx - (cx - canvas.width  / 2) / state.scale;
  state.viewCY   = wy - (cy - canvas.height / 2) / state.scale;
  render();
}, {passive: false});

// ================================================================ mode
function setMode(m) {
  state.mode = m;
  document.getElementById('btn-edit').classList.toggle('active', m === 'edit');
  document.getElementById('btn-aim').classList.toggle('active',  m === 'aim');
  canvas.classList.toggle('aim-mode', m === 'aim');
  // Stop any hold timers when changing mode
  for (const id of Object.keys(state.holdTimers)) stopHold(parseInt(id));
  render();
}

// ================================================================ sidebar
function updateSidebar() {
  const panel = document.getElementById('mod-panel');
  const noSel = document.getElementById('no-sel');
  if (state.sel < 0) {
    panel.style.display = 'none';
    noSel.style.display = '';
    return;
  }
  noSel.style.display = 'none';
  panel.style.display = '';
  const m = state.modules[state.sel];
  document.getElementById('mod-title').textContent = `Module ${state.sel + 1}`;
  document.getElementById('mod-name').value = m.name || '';
  syncSidebarPos();
  syncSidebarYaw();
  buildClusterList();
}

function syncSidebarPos() {
  if (state.sel < 0) return;
  const m = state.modules[state.sel];
  document.getElementById('mod-x').value = m.registration_point_cm[0].toFixed(1);
  document.getElementById('mod-y').value = m.registration_point_cm[1].toFixed(1);
}
function syncSidebarYaw() {
  if (state.sel < 0) return;
  const m = state.modules[state.sel];
  document.getElementById('mod-yaw').value = (m.rotation.yaw || 0).toFixed(1);
}

function onModNameInput() {
  if (state.sel < 0) return;
  state.modules[state.sel].name = document.getElementById('mod-name').value;
  render();
}
function onModPosInput() {
  if (state.sel < 0) return;
  const m = state.modules[state.sel];
  m.registration_point_cm[0] = parseFloat(document.getElementById('mod-x').value) || 0;
  m.registration_point_cm[1] = parseFloat(document.getElementById('mod-y').value) || 0;
  render();
}
function onModYawInput() {
  if (state.sel < 0) return;
  state.modules[state.sel].rotation.yaw = parseFloat(document.getElementById('mod-yaw').value) || 0;
  render();
}

function buildClusterList() {
  const m    = state.modules[state.sel];
  const list = document.getElementById('cluster-list');
  list.innerHTML = '';
  m.clusters.forEach((cl, j) => {
    const isAim = j === state.aimCluster;
    const card  = document.createElement('div');
    card.className = 'cluster-card' + (isAim ? ' selected-aim' : '');
    card.id = `cl-card-${j}`;
    card.innerHTML = `
      <div class="cluster-header">
        <span>Cluster ${j + 1}</span>
        <button onclick="selectAimCluster(${j})" style="margin-left:auto;font-size:11px;padding:1px 6px"
                class="${isAim ? 'active' : ''}">Aim</button>
      </div>
      <div class="field-row">
        <label>Motor ID</label>
        <input type="number" value="${cl.motor_id}" step="1" min="1"
               onchange="onClusterField(${j},'motor_id',this.value,'int')">
      </div>
      <div class="field-row">
        <label>Offset X</label>
        <input type="number" value="${cl.pos_offset_cm[0].toFixed(1)}" step="1"
               onchange="onClusterField(${j},'ox',this.value,'float')">
        <label style="width:auto">Y</label>
        <input type="number" value="${cl.pos_offset_cm[1].toFixed(1)}" step="1"
               onchange="onClusterField(${j},'oy',this.value,'float')">
      </div>
      <div class="cluster-btns">
        <button onclick="testMove(${cl.motor_id})" class="btn-green">Test Move</button>
      </div>
      <div class="hold-row" id="hold-row-${j}">
        <span style="color:#999">Hold at</span>
        <input type="number" id="hold-deg-${j}" value="0" step="5" style="width:60px">
        <span style="color:#999">°</span>
        <button id="hold-btn-${j}" onclick="toggleHold(${j})" class="btn-green">Hold</button>
      </div>`;
    list.appendChild(card);
  });
}

function onClusterField(j, field, rawVal, type) {
  if (state.sel < 0) return;
  const cl  = state.modules[state.sel].clusters[j];
  const val = type === 'int' ? parseInt(rawVal) : parseFloat(rawVal);
  if (isNaN(val)) return;
  if      (field === 'motor_id') cl.motor_id = val;
  else if (field === 'ox')       cl.pos_offset_cm[0] = val;
  else if (field === 'oy')       cl.pos_offset_cm[1] = val;
  render();
}

function selectAimCluster(j) {
  state.aimCluster = (state.aimCluster === j) ? -1 : j;
  buildClusterList();
  render();
}

// ================================================================ module ops
function addModule() {
  const idx = state.modules.length;
  state.modules.push({
    name: `Module ${idx + 1}`,
    registration_point_cm: [0.0, 0.0, 0.0],
    rotation: {pitch: 0, yaw: 0, roll: 0},
    clusters: [0,1,2,3].map(i => ({
      motor_id: idx * 4 + i + 1,
      pos_offset_cm: [[40,-30,0],[40,-75,0],[100,-25,0],[95,-70,0]][i].slice(),
      rotation_offset: {pitch:0,yaw:0,roll:0},
    })),
  });
  state.sel = idx;
  state.aimCluster = -1;
  updateSidebar();
  render();
}

function deleteSelectedModule() {
  if (state.sel < 0) return;
  if (!confirm(`Delete ${state.modules[state.sel].name}?`)) return;
  state.modules.splice(state.sel, 1);
  state.sel = Math.min(state.sel, state.modules.length - 1);
  state.aimCluster = -1;
  updateSidebar();
  render();
}

// ================================================================ OSC
async function sendAim(motorId, degSoftware) {
  try {
    const r = await fetch('/api/aim', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({motor_id: motorId, deg: degSoftware}),
    });
    if (!r.ok) console.error('aim failed', await r.text());
  } catch (err) { console.error('aim error', err); }
}

async function testMove(motorId) {
  await sendAim(motorId, 30);
  setTimeout(() => sendAim(motorId, 0), 500);
}

function toggleHold(j) {
  if (state.sel < 0) return;
  const cl    = state.modules[state.sel].clusters[j];
  const mid   = cl.motor_id;
  const btn   = document.getElementById(`hold-btn-${j}`);
  if (state.holdTimers[mid] !== undefined) {
    stopHold(mid);
    btn.textContent = 'Hold';
    btn.classList.remove('active');
  } else {
    const degInput = document.getElementById(`hold-deg-${j}`);
    const fire = () => sendAim(mid, parseFloat(degInput.value) || 0);
    fire();
    state.holdTimers[mid] = setInterval(fire, 500);
    btn.textContent = 'Stop';
    btn.classList.add('active');
  }
}
function stopHold(mid) {
  if (state.holdTimers[mid] !== undefined) {
    clearInterval(state.holdTimers[mid]);
    delete state.holdTimers[mid];
  }
}

// ================================================================ load/save
async function loadLayout() {
  try {
    const r = await fetch('/api/layout');
    const d = await r.json();
    state.modules = d.modules;
    if (state.modules.length === 0) {
      // Bootstrap 12 default modules
      for (let i = 0; i < 12; i++) {
        state.modules.push({
          name: `Module ${i+1}`,
          registration_point_cm: [0.0, 0.0, 0.0],
          rotation: {pitch:0, yaw:0, roll:0},
          clusters: [0,1,2,3].map(k => ({
            motor_id: i*4+k+1,
            pos_offset_cm: [[40,-30,0],[40,-75,0],[100,-25,0],[95,-70,0]][k].slice(),
            rotation_offset: {pitch:0,yaw:0,roll:0},
          })),
        });
      }
    }
    fitView();
  } catch (err) { console.error('load error', err); }
}

async function saveLayout() {
  const btn = document.getElementById('btn-save');
  const msg = document.getElementById('save-msg');
  btn.disabled = true;
  msg.textContent = 'saving…';
  try {
    const r = await fetch('/api/layout', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({modules: state.modules}),
    });
    const d = await r.json();
    msg.textContent = d.ok ? 'Saved ✓' : ('Error: ' + d.error);
    msg.style.color = d.ok ? '#51cf66' : '#ff6b6b';
  } catch (err) {
    msg.textContent = 'Request failed';
    msg.style.color = '#ff6b6b';
  }
  btn.disabled = false;
  setTimeout(() => { msg.textContent = ''; msg.style.color = '#888'; }, 4000);
}

// ================================================================ controller status
async function refreshControllerStatus() {
  try {
    const r = await fetch('/api/controller-status');
    const d = await r.json();
    const el = document.getElementById('ctrl-dots');
    el.innerHTML = d.controllers.map(c =>
      `<span class="ctrl-dot ${c.online ? 'online' : 'offline'}" title="${c.name}"></span> `
      + `<span title="${c.ip}" style="color:${c.online ? '#51cf66' : '#ff6b6b'}">`
      + `${c.name.replace('flowerbeds_controller_','ctrl ')} ${c.online ? 'ONLINE' : 'OFFLINE'}`
      + `</span>`
    ).join('&nbsp;&nbsp;');
    if (d.controllers.length === 0) el.textContent = '(no controllers in network.json)';
  } catch (err) {
    document.getElementById('ctrl-dots').textContent = 'status unavailable';
  }
}

// ================================================================ boot
loadLayout();
refreshControllerStatus();
setInterval(refreshControllerStatus, 10000);
resize();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AimBody(BaseModel):
    motor_id: int
    deg: float


class LayoutBody(BaseModel):
    modules: list[dict]


@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


@app.get("/api/layout")
async def get_layout():
    try:
        settings = _load_json(_config_path)
        modules  = settings.get("coordinator", {}).get("modules", [])
        return JSONResponse({"modules": modules})
    except FileNotFoundError:
        return JSONResponse({"modules": []})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/layout")
async def post_layout(body: LayoutBody):
    try:
        settings = _load_json(_config_path)
    except FileNotFoundError:
        return JSONResponse({"ok": False, "error": f"{_config_path} not found"}, status_code=404)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

    bak = _config_path.with_suffix(_config_path.suffix + ".bak")
    shutil.copy2(_config_path, bak)

    if "coordinator" not in settings:
        settings["coordinator"] = {}
    settings["coordinator"]["modules"] = body.modules

    try:
        with open(_config_path, "w") as f:
            json.dump(settings, f, indent=2)
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@app.get("/api/network")
async def get_network():
    try:
        network     = _load_json(_network_path)
        controllers = _flowerbeds_controllers(network)
        return JSONResponse({"controllers": controllers})
    except FileNotFoundError:
        return JSONResponse({"controllers": [], "error": f"{_network_path} not found"})
    except Exception as exc:
        return JSONResponse({"controllers": [], "error": str(exc)})


@app.get("/api/controller-status")
async def controller_status():
    try:
        network     = _load_json(_network_path)
        controllers = _flowerbeds_controllers(network)
    except Exception:
        controllers = []

    results = []
    loop = asyncio.get_event_loop()
    for c in controllers:
        online = await loop.run_in_executor(None, _tcp_ping, c["ip"], c["osc_port"])
        results.append({
            "name":       c["name"],
            "ip":         c["ip"],
            "osc_port":   c["osc_port"],
            "online":     online,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        })
    return JSONResponse({"controllers": results})


@app.post("/api/aim")
async def aim(body: AimBody):
    try:
        network = _load_json(_network_path)
    except Exception:
        network = {}
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_osc, network, body.motor_id, body.deg)
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    global _config_path, _network_path

    ap = argparse.ArgumentParser(description="FlowerBeds layout tool")
    ap.add_argument("--config",  default="settings.json",
                    help="Path to settings.json (default: settings.json)")
    ap.add_argument("--network", default=None,
                    help="Path to network.json (default: ../../network.json relative to this script)")
    ap.add_argument("--port",    type=int, default=8764, help="HTTP port (default: 8764)")
    ap.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = ap.parse_args()

    _config_path  = Path(args.config).resolve()
    _network_path = (
        Path(args.network).resolve()
        if args.network
        else Path(__file__).resolve().parents[1] / "network.json"
    )

    url = f"http://localhost:{args.port}"
    print(f"Layout tool: {url}")
    print(f"Config:      {_config_path}")
    print(f"Network:     {_network_path}")

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
