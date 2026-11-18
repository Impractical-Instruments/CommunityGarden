"""LiveServer: /health, the /ws state socket, the /logs socket, the page at /, and a clean shutdown of its log handler."""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ShowWeb import LiveServer

SHOW_CONTROL = Path(__file__).resolve().parent.parent
DASHBOARD = SHOW_CONTROL / "Dashboard"


@pytest.fixture
def server():
    s = LiveServer("test_live_server")
    yield s
    if s._log_handler is not None:
        logging.getLogger(s.logger_name).removeHandler(s._log_handler)


def test_health(server):
    assert TestClient(server.app).get("/health").json() == {"ok": True}


def test_ws_receives_a_broadcast(server):
    with TestClient(server.app).websocket_connect("/ws") as ws:
        server.broadcast({"frame": 7, "blobs": []})
        assert ws.receive_json() == {"frame": 7, "blobs": []}


def test_ws_broadcast_reaches_every_client(server):
    client = TestClient(server.app)
    with client.websocket_connect("/ws") as a, client.websocket_connect("/ws") as b:
        server.broadcast({"n": 1})
        assert a.receive_json() == {"n": 1}
        assert b.receive_json() == {"n": 1}


def test_broadcast_with_no_clients_is_a_no_op(server):
    server.broadcast({"n": 1})
    assert not server.has_clients


def test_logs_streams_a_record(server):
    server._attach_log_handler()
    with TestClient(server.app).websocket_connect("/logs") as ws:
        logging.getLogger("test_live_server").warning("hello %s", "garden")
        entry = ws.receive_json()
    assert entry["level"] == "WARNING"
    assert entry["msg"] == "hello garden"
    assert re.fullmatch(r"\d\d:\d\d:\d\d", entry["ts"])


def test_logs_ignores_other_loggers(server):
    server._attach_log_handler()
    with TestClient(server.app).websocket_connect("/logs") as ws:
        logging.getLogger("some_other_logger").warning("not for the panel")
        logging.getLogger("test_live_server").warning("for the panel")
        assert ws.receive_json()["msg"] == "for the panel"


def test_a_closed_log_client_is_forgotten(server):
    with TestClient(server.app).websocket_connect("/logs"):
        pass
    assert server.log_queues == []


def test_extra_routes_are_registered():
    def routes(app: FastAPI) -> None:
        @app.get("/mine")
        async def mine():
            return {"mine": True}

    assert TestClient(LiveServer("x", extra_routes=routes).app).get("/mine").json() == {"mine": True}


def test_html_string_is_served_at_root():
    resp = TestClient(LiveServer("x", html="<p>hi</p>").app).get("/")
    assert resp.text == "<p>hi</p>"
    assert resp.headers["content-type"].startswith("text/html")


def test_html_path_is_served_at_root(tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<p>from a file</p>")
    assert TestClient(LiveServer("x", html=page).app).get("/").text == "<p>from a file</p>"


def test_no_page_without_html():
    assert TestClient(LiveServer("x").app).get("/").status_code == 404


def test_serving_without_a_port_is_an_error():
    import asyncio

    with pytest.raises(ValueError, match="no port"):
        asyncio.run(LiveServer("x").serve())


# -- one copy of each piece of plumbing ----------------------------------------

def test_one_definition_of_the_log_handler_and_socket_handlers():
    # The FundingCAPTCHA monitor is a different server (the websockets library), not a copy of this one.
    for name in ("class WebSocketLogHandler", '.websocket("/ws")', '.websocket("/logs")'):
        defining = [p for p in SHOW_CONTROL.rglob("*.py") if name in p.read_text() and "test_" not in p.name]
        assert defining == [SHOW_CONTROL / "ShowWeb" / "live.py"], name


def test_no_html_page_in_a_python_file():
    for path in SHOW_CONTROL.rglob("*.py"):
        if path.name.startswith("test_"):
            continue
        text = path.read_text().lower()
        assert "<!doctype" not in text and "<html" not in text, path


def test_one_copy_of_the_log_panel_javascript():
    holders = [p.name for p in DASHBOARD.glob("*.html") if "function appendLog" in p.read_text()]
    assert holders == []
    assert "function appendLog" in (DASHBOARD / "log-panel.js").read_text()
    for page in ("flowerbeds.html", "fundingcaptcha.html", "treehouse.html"):
        assert '<script src="log-panel.js">' in (DASHBOARD / page).read_text(), page
