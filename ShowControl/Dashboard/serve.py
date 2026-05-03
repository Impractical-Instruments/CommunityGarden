#!/usr/bin/env python3
"""
Show dashboard — FastAPI server with mode-relay OSC endpoint.

Usage:
  python serve.py           # default port 9000
  python serve.py 9001      # custom port
"""

import argparse
import json
import logging
import socket
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DIR = Path(__file__).resolve().parent
NETWORK_JSON = DIR.parent / "network.json"

VALID_ELEMENTS = {"treehouse", "flowerbeds", "captcha", "pipes"}
VALID_MODES = {"active", "dim", "inactive"}

log = logging.getLogger("dashboard")

app = FastAPI()


def _load_network() -> dict:
    if not NETWORK_JSON.exists():
        raise FileNotFoundError(f"network.json not found at {NETWORK_JSON}")
    return json.loads(NETWORK_JSON.read_text())


def _send_osc(ip: str, port: int, address: str, value: str) -> None:
    from pythonosc.udp_client import SimpleUDPClient
    SimpleUDPClient(ip, port).send_message(address, value)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return JSONResponse({"ok": True})


class ModeRequest(BaseModel):
    element: str
    mode: str


@app.post("/api/mode")
async def post_mode(req: ModeRequest):
    if req.element not in VALID_ELEMENTS:
        raise HTTPException(400, f"Unknown element {req.element!r}; valid: {sorted(VALID_ELEMENTS)}")
    if req.mode not in VALID_MODES:
        raise HTTPException(400, f"Unknown mode {req.mode!r}; valid: {sorted(VALID_MODES)}")

    try:
        network = _load_network()
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc))

    el = network.get("elements", {}).get(req.element, {})
    ip = el.get("ip")
    port = el.get("osc_port")
    if not ip or not port:
        raise HTTPException(503, f"No OSC address configured for {req.element!r} in network.json")

    try:
        _send_osc(ip, int(port), f"/{req.element}/mode", req.mode)
        log.info("mode relay → /%s/mode %r to %s:%d", req.element, req.mode, ip, port)
    except Exception as exc:
        raise HTTPException(502, f"OSC send failed: {exc}")

    return {"ok": True, "element": req.element, "mode": req.mode}


# Static files — registered last so API routes take priority
app.mount("/", StaticFiles(directory=str(DIR), html=True), name="static")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Show dashboard server")
    parser.add_argument("port", type=int, nargs="?", default=9000)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    print(f"Show Dashboard:  http://{local_ip}:{args.port}/")
    print("Press Ctrl+C to stop.\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
