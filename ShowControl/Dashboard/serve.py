#!/usr/bin/env python3
"""
Show dashboard — FastAPI server for the static dashboard pages.

The pages talk to each Element's own monitoring port from the browser; this
server relays nothing. It serves the ports from network.json at /api/network,
so the pages hold no addresses of their own.

Usage:
  python serve.py           # default port 9000
  python serve.py 9001      # custom port
"""

import argparse
import logging
import socket
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from OSCFabric import load_network_config_or_empty

DIR = Path(__file__).resolve().parent

log = logging.getLogger("dashboard")

app = FastAPI()


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return JSONResponse({"ok": True})


@app.get("/api/network")
async def network():
    """The `elements` block of network.json: {name: {ip, osc_port, http_port}}."""
    return JSONResponse({"elements": load_network_config_or_empty(log).get("elements", {})})


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
