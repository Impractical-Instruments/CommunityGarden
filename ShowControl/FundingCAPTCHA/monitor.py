"""The kiosk's monitoring port, for the Dashboard: status, live logs, and remote commands.

    monitor = MonitoringServer(8080, commands={"/api/restart": restart_event.set})
    logging.getLogger().addHandler(monitor.log_handler())
    monitor.start()
    monitor.set_status({"state": "screensaver"})

One port serves:
  GET /health (or /)   the last status payload, as JSON
  WS  /logs            every log record, as {"ts", "level", "msg"}
  any path in `commands`   calls it, answers {"ok": true}

It runs its own asyncio loop on a daemon thread. A command is called on that
thread, so give it something thread-safe, such as an Event's `set`.
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any, Callable

log = logging.getLogger("captcha.monitor")


class MonitoringServer:
    def __init__(self, port: int, commands: dict[str, Callable[[], None]] | None = None) -> None:
        self._port     = port
        self._commands = dict(commands or {})
        self._status: dict[str, Any] = {"state": "starting"}
        self._log_clients: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_status(self, payload: dict) -> None:
        """Record the status GET /health reports."""
        self._status = payload

    def log_handler(self) -> logging.Handler:
        """A logging handler that streams records to the /logs clients."""
        return _LogHandler(self)

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    # ── On the server thread ──────────────────────────────────────────────────

    def _run(self) -> None:
        from websockets.asyncio.server import serve as ws_serve

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        async def _serve() -> None:
            async with ws_serve(self._ws_handler, "0.0.0.0", self._port,
                                process_request=self._process_request):
                log.info("Monitoring on 0.0.0.0:%d  (WS /logs  GET /health  %s)",
                         self._port, "  ".join(self._commands) or "no commands")
                await asyncio.Future()

        loop.run_until_complete(_serve())

    async def _ws_handler(self, ws: Any) -> None:
        if ws.request.path == "/logs":
            self._log_clients.add(ws)
            try:
                await ws.wait_closed()
            finally:
                self._log_clients.discard(ws)

    async def _process_request(self, connection: Any, request: Any) -> Any:
        from websockets.datastructures import Headers
        from websockets.http11 import Response

        def _json(body: bytes) -> Any:
            return Response(200, "OK",
                            Headers([("Content-Type", "application/json"),
                                     ("Content-Length", str(len(body)))]),
                            body)

        path = request.path
        if path == "/logs":
            return None                       # let the WebSocket handshake proceed
        if path in self._commands:
            self._commands[path]()
            return _json(b'{"ok":true}')
        if path in ("/", "/health"):
            return _json(json.dumps(self._status).encode())
        return Response(404, "Not Found", Headers([("Content-Length", "0")]), b"")

    async def _send_log(self, msg: str) -> None:
        dead = set()
        for ws in list(self._log_clients):
            try:
                await ws.send(msg)
            except Exception:
                dead.add(ws)
        self._log_clients.difference_update(dead)


class _LogHandler(logging.Handler):
    def __init__(self, server: MonitoringServer) -> None:
        super().__init__()
        self._server = server

    def emit(self, record: logging.LogRecord) -> None:
        server = self._server
        if server._loop is None or not server._log_clients:
            return
        msg = json.dumps({
            "ts":    time.strftime("%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "msg":   record.getMessage(),
        })
        asyncio.run_coroutine_threadsafe(server._send_log(msg), server._loop)
