"""MonitoringServer over a real socket: /health, a command path, /logs, 404."""
import json
import logging
import socket
import time
import urllib.error
import urllib.request

import pytest

from monitor import MonitoringServer

pytest.importorskip("websockets")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(port: int, path: str):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2) as r:
        return r.status, json.loads(r.read())


@pytest.fixture
def server():
    called: list[str] = []
    port = _free_port()
    srv = MonitoringServer(port, commands={"/api/restart": lambda: called.append("restart")})
    srv.start()
    for _ in range(200):                       # wait for the port to open
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.1).close()
            break
        except OSError:
            time.sleep(0.02)
    else:
        pytest.fail("monitoring server never opened its port")
    return srv, port, called


def test_health_reports_the_last_status(server):
    srv, port, _ = server
    assert _get(port, "/health") == (200, {"state": "starting"})
    srv.set_status({"state": "game", "fg_pixels": 1234})
    assert _get(port, "/health") == (200, {"state": "game", "fg_pixels": 1234})
    assert _get(port, "/")[1] == {"state": "game", "fg_pixels": 1234}


def test_command_path_calls_the_command(server):
    _, port, called = server
    assert _get(port, "/api/restart") == (200, {"ok": True})
    assert called == ["restart"]


def test_unknown_path_is_404(server):
    _, port, called = server
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(port, "/api/nope")
    assert exc.value.code == 404
    assert called == []


def test_log_records_reach_a_logs_client(server):
    from websockets.sync.client import connect

    srv, port, _ = server
    logger = logging.getLogger("test_monitor.stream")
    logger.setLevel(logging.INFO)
    handler = srv.log_handler()
    logger.addHandler(handler)
    try:
        with connect(f"ws://127.0.0.1:{port}/logs", open_timeout=2) as ws:
            deadline = time.monotonic() + 2
            while not srv._log_clients and time.monotonic() < deadline:
                time.sleep(0.01)               # the server registers the client just after the handshake
            logger.info("hello %s", "dashboard")
            entry = json.loads(ws.recv(timeout=2))
    finally:
        logger.removeHandler(handler)
    assert entry["level"] == "INFO"
    assert entry["msg"] == "hello dashboard"
