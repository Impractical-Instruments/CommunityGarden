"""Monitoring server shared by app.py, shader_app.py and playlist_app.py.

One port (network.json elements.captcha.http_port) serves:
  GET  /health   the status dict the app last set (JSON)
  WS   /logs     every log record, as {"ts", "level", "msg"} JSON
  POST /api/...  one command per path; each sets a threading.Event the main
                 loop polls, so nothing here touches app state directly.

Every response carries Access-Control-Allow-Origin: * so the Dashboard,
served from another port, can read it.
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any

log = logging.getLogger("captcha.monitor")

DEFAULT_PORT = 8080


def monitor_port(override: int | None = None) -> int:
    """The port to serve on: --port if given, else network.json, else 8080."""
    if override is not None:
        return override
    try:
        from OSCFabric import load_network_config_or_empty
    except ImportError:
        return DEFAULT_PORT
    captcha = load_network_config_or_empty(log).get("elements", {}).get("captcha", {})
    return int(captcha.get("http_port", DEFAULT_PORT))


class MonitoringServer:
    """Health, logs and commands on one port, on a daemon thread.

    commands maps a path ("/api/reseed") to the Event a POST to it sets.
    """

    def __init__(self, port: int, commands: dict[str, threading.Event] | None = None) -> None:
        self.port     = port
        self.commands = dict(commands or {})
        self._status: dict[str, Any] = {"state": "starting"}
        self._clients: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.log_handler = _LogHandler(self)

    def set_status(self, payload: dict) -> None:
        """Replace the dict GET /health reports."""
        self._status = payload

    def start(self) -> None:
        """Serve on a daemon thread and stream the root logger to /logs."""
        logging.getLogger().addHandler(self.log_handler)
        # websockets logs every plain-HTTP request at INFO: the Dashboard's
        # 2 s /health poll would flood the journal and the log stream.
        logging.getLogger("websockets").setLevel(logging.WARNING)
        threading.Thread(target=self._run, daemon=True, name="monitor").start()

    # ── HTTP ──────────────────────────────────────────────────────────────────

    def handle(self, method: str | None, path: str) -> tuple[int, dict | None]:
        """Route one plain-HTTP request → (status code, JSON body or None).

        method is None when the websockets version doesn't report it.
        """
        path = path.split("?", 1)[0]
        if method == "OPTIONS":
            return 204, None
        if path in self.commands:
            if method not in (None, "POST"):
                return 405, {"ok": False, "error": "POST only"}
            self.commands[path].set()
            return 200, {"ok": True}
        if path in ("/", "/health"):
            return 200, self._status
        return 404, None

    async def _process_request(self, connection: Any, request: Any) -> Any:
        from websockets.datastructures import Headers
        from websockets.http11 import Response

        if request.path == "/logs":
            return None                                   # the WebSocket handshake
        code, payload = self.handle(getattr(request, "method", None), request.path)
        body = b"" if payload is None else json.dumps(payload).encode()
        headers = [("Access-Control-Allow-Origin", "*"),
                   ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                   ("Content-Length", str(len(body)))]
        if payload is not None:
            headers.append(("Content-Type", "application/json"))
        reason = {200: "OK", 204: "No Content", 404: "Not Found",
                  405: "Method Not Allowed"}[code]
        return Response(code, reason, Headers(headers), body)

    # ── Logs WebSocket ────────────────────────────────────────────────────────

    async def _ws_handler(self, ws: Any) -> None:
        if ws.request.path != "/logs":
            return
        self._clients.add(ws)
        try:
            await ws.wait_closed()
        finally:
            self._clients.discard(ws)

    def _emit(self, msg: str) -> None:
        if self._loop is not None and self._clients:
            asyncio.run_coroutine_threadsafe(self._send(msg), self._loop)

    async def _send(self, msg: str) -> None:
        dead = set()
        for ws in list(self._clients):
            try:
                await ws.send(msg)
            except Exception:
                dead.add(ws)
        self._clients.difference_update(dead)

    def _run(self) -> None:
        from websockets.asyncio.server import serve

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def _serve() -> None:
            async with serve(self._ws_handler, "0.0.0.0", self.port,
                             process_request=self._process_request):
                log.info("Monitoring on 0.0.0.0:%d  (GET /health  WS /logs  POST %s)",
                         self.port, " ".join(sorted(self.commands)) or "-")
                await asyncio.Future()

        try:
            self._loop.run_until_complete(_serve())
        except OSError as exc:
            log.error("Monitoring server could not start on port %d: %s", self.port, exc)


class _LogHandler(logging.Handler):
    def __init__(self, server: MonitoringServer) -> None:
        super().__init__()
        self._server = server

    def emit(self, record: logging.LogRecord) -> None:
        self._server._emit(json.dumps({
            "ts":    time.strftime("%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "msg":   record.getMessage(),
        }))
