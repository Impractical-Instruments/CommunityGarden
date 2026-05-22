#!/usr/bin/env python3
"""
Playing the Pipes — health server.

Serves GET /health on port 8767 so the Dashboard can monitor this machine.
Run via NSSM as a Windows background service; see docs/operations.md.

Usage:
  python health_server.py           # port 8767
  python health_server.py 8768      # custom port
"""

import argparse
import logging
import socket
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

log = logging.getLogger("pipes-health")


@app.get("/health")
async def health():
    return JSONResponse({"ok": True})


def main() -> None:
    parser = argparse.ArgumentParser(description="Playing the Pipes health server")
    parser.add_argument("port", type=int, nargs="?", default=8767)
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

    print(f"Pipes health server:  http://{local_ip}:{args.port}/health")
    print("Press Ctrl+C to stop.\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
