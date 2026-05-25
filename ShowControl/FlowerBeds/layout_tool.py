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
import threading
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import uvicorn  # type: ignore[import]
from fastapi import FastAPI  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from fastapi.responses import FileResponse, JSONResponse  # type: ignore[import]
from fastapi.staticfiles import StaticFiles  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]
from pythonosc.udp_client import SimpleUDPClient  # type: ignore[import]

from diag import osc_ping

_OSC_ADDRESS = "/cg/ff/rot"
STATIC_DIR   = Path(__file__).resolve().parent / "layout_tool"

_DEFAULT_CLUSTER_OFFSETS = [
    [30.0,  30.0, 0.0],
    [-30.0,  30.0, 0.0],
    [30.0, -30.0, 0.0],
    [-30.0,  -30.0, 0.0],
]

# Paths set by main() before the server starts
_config_path: Path  = Path("settings.json")
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
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AimBody(BaseModel):
    motor_id: int
    deg: float


class LayoutBody(BaseModel):
    modules: list[dict]


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/defaults")
async def get_defaults():
    return JSONResponse({"cluster_offsets": _DEFAULT_CLUSTER_OFFSETS})


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
        pong = await loop.run_in_executor(None, osc_ping, c["ip"], c["osc_port"])
        entry = {
            "name":       c["name"],
            "ip":         c["ip"],
            "osc_port":   c["osc_port"],
            "online":     pong is not None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        if pong is not None:
            entry.update(pong)
        results.append(entry)
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
