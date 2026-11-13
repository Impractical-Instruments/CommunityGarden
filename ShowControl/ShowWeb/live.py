"""The live-view web server every Element's visualizer shares: /health, a /ws state socket and a /logs socket."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import uvicorn  # type: ignore[import]
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse  # type: ignore[import]

LOG_QUEUE_SIZE = 500


class WebSocketLogHandler(logging.Handler):
    """Streams log records to every connected /logs client of one LiveServer."""

    def __init__(self, server: "LiveServer") -> None:
        super().__init__()
        self._server = server

    def emit(self, record: logging.LogRecord) -> None:
        loop = self._server.loop
        queues = self._server.log_queues
        if loop is None or not queues:
            return
        msg = json.dumps({
            "ts": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
        })
        for q in list(queues):
            try:
                loop.call_soon_threadsafe(q.put_nowait, msg)
            except Exception:
                pass


class LiveServer:
    """
    One Element's live-view server.

    `logger_name` is the logger whose records /logs streams. `port` may be left out here
    if `serve()` or `start_in_thread()` is given it. `html` (a page string or a
    Path to a static file) is served at GET /; leave it out for an API-only server.
    `extra_routes(app)` registers the Element's own routes on the FastAPI app.

    Run it as an asyncio task with `await serve()`, or in a daemon thread with
    `start_in_thread()`. `broadcast(state)` is thread-safe; `await broadcast_async(state)`
    is for callers already on the server's event loop.
    """

    def __init__(
        self,
        logger_name: str,
        port: int | None = None,
        html: str | Path | None = None,
        extra_routes: Callable[[FastAPI], None] | None = None,
        host: str = "0.0.0.0",
    ) -> None:
        self.logger_name = logger_name
        self.port = port
        self.host = host
        self.loop: asyncio.AbstractEventLoop | None = None
        self.connections: set[WebSocket] = set()
        self.log_queues: list[asyncio.Queue] = []
        self._log_handler: WebSocketLogHandler | None = None

        self.app = FastAPI()
        self.app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
        self._add_routes(html)
        if extra_routes is not None:
            extra_routes(self.app)

    # -- routes ------------------------------------------------------------

    def _add_routes(self, html: str | Path | None) -> None:
        app = self.app

        if html is not None:
            @app.get("/", response_class=HTMLResponse)
            async def index():
                if isinstance(html, Path):
                    return FileResponse(html, media_type="text/html")
                return html

        @app.get("/health")
        async def health():
            return JSONResponse({"ok": True})

        @app.websocket("/ws")
        async def ws_endpoint(websocket: WebSocket):
            await websocket.accept()
            self._bind_running_loop()
            self.connections.add(websocket)
            try:
                while True:
                    # Keep the connection alive; state is pushed by broadcast().
                    await asyncio.sleep(10)
            except (WebSocketDisconnect, Exception):
                pass
            finally:
                self.connections.discard(websocket)

        @app.websocket("/logs")
        async def logs_endpoint(websocket: WebSocket):
            await websocket.accept()
            self._bind_running_loop()
            q: asyncio.Queue[str] = asyncio.Queue(maxsize=LOG_QUEUE_SIZE)
            self.log_queues.append(q)
            try:
                while True:
                    msg = await q.get()
                    await websocket.send_text(msg)
            except (WebSocketDisconnect, Exception):
                pass
            finally:
                if q in self.log_queues:
                    self.log_queues.remove(q)

    # -- event loop and log handler ----------------------------------------

    def _bind_running_loop(self) -> None:
        """Adopt the loop serving a client when none was set (a server run by something else)."""
        if self.loop is None:
            self.loop = asyncio.get_running_loop()

    def _attach_log_handler(self) -> None:
        if self._log_handler is None:
            self._log_handler = WebSocketLogHandler(self)
            logging.getLogger(self.logger_name).addHandler(self._log_handler)

    def _uvicorn_server(self, host: str | None, port: int | None) -> uvicorn.Server:
        port = port if port is not None else self.port
        if port is None:
            raise ValueError("LiveServer has no port: pass one to the constructor or to serve()")
        config = uvicorn.Config(
            self.app,
            host=host or self.host,
            port=port,
            log_level="warning",
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        server.install_signal_handlers = False
        return server

    # -- lifecycle ---------------------------------------------------------

    async def serve(self, host: str | None = None, port: int | None = None) -> None:
        """Run the server as a task in the caller's event loop. `host` and `port` override the constructor's."""
        self.loop = asyncio.get_running_loop()
        self._attach_log_handler()
        await self._uvicorn_server(host, port).serve()

    def start_in_thread(self, host: str | None = None, port: int | None = None) -> None:
        """
        Run the server on its own event loop in a daemon thread, for a synchronous caller.
        Returns once the loop exists; the server runs until the process exits.
        """
        ready = threading.Event()

        def _run() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = loop
            ready.set()
            loop.run_until_complete(self._uvicorn_server(host, port).serve())

        threading.Thread(target=_run, daemon=True).start()
        ready.wait()
        self._attach_log_handler()

    @property
    def has_clients(self) -> bool:
        """True while any /ws client is connected, so a caller can skip building a state nobody reads."""
        return bool(self.connections)

    # -- state push --------------------------------------------------------

    async def broadcast_async(self, state: Any) -> None:
        """Send `state` to every connected /ws client, dropping the dead ones. No-op without clients."""
        if not self.connections:
            return
        payload = json.dumps(state)
        dead: set[WebSocket] = set()
        for ws in list(self.connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        self.connections.difference_update(dead)

    def broadcast(self, state: Any) -> None:
        """Thread-safe: schedule `state` for every connected /ws client. No-op without clients."""
        if not self.connections or self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast_async(state), self.loop)
