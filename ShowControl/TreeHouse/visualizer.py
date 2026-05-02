"""
TreeHouse visualizer — FastAPI WebSocket server.

Pushes show state snapshots to connected browsers via /ws.
Streams log output via /logs.

Access: http://<show-computer-ip>:8766
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import uvicorn  # type: ignore[import]
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from fastapi.responses import JSONResponse  # type: ignore[import]

if TYPE_CHECKING:
    from coordinator import Coordinator

log = logging.getLogger("treehouse")

# ---------------------------------------------------------------------------
# App & shared state
# ---------------------------------------------------------------------------

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

_connections: set[WebSocket] = set()
_log_queues: list[asyncio.Queue] = []
_loop: asyncio.AbstractEventLoop | None = None


# ---------------------------------------------------------------------------
# Log streaming
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return JSONResponse({"ok": True})


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


# ---------------------------------------------------------------------------
# State broadcast — called from the frame loop coroutine
# ---------------------------------------------------------------------------

async def broadcast_state(coordinator: Coordinator) -> None:
    if not _connections:
        return
    state = {
        "mode": coordinator.mode.value,
        "brightness": coordinator.brightness,
        "displays": [
            {"name": s.name, "enabled": s.enabled, "params": s.params}
            for s in coordinator.get_all_states()
        ],
    }
    payload = json.dumps(state)
    dead: set[WebSocket] = set()
    for ws in list(_connections):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

async def serve(host: str = "0.0.0.0", port: int = 8766) -> None:
    """Run the FastAPI server as an asyncio task in the caller's event loop."""
    global _loop
    _loop = asyncio.get_running_loop()
    handler = WebSocketLogHandler()
    logging.getLogger("treehouse").addHandler(handler)
    config = uvicorn.Config(app, host=host, port=port, log_level="warning", loop="asyncio")
    server = uvicorn.Server(config)
    server.install_signal_handlers = False
    log.info("TreeHouse visualizer: http://%s:%d", host, port)
    await server.serve()
