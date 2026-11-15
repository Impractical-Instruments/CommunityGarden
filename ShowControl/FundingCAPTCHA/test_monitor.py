"""monitor.py: /health, commands, CORS for the Dashboard, and the reseed reaching the camera."""
import argparse
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from monitor import MonitoringServer, monitor_port

NETWORK = json.loads((Path(__file__).parents[1] / "network.json").read_text())
SETTINGS = json.loads((Path(__file__).parent / "captcha-settings.json").read_text())


def _server() -> tuple[MonitoringServer, threading.Event]:
    reseed = threading.Event()
    return MonitoringServer(0, {"/api/reseed": reseed}), reseed


# ── Routing ───────────────────────────────────────────────────────────────────

def test_post_to_a_command_sets_its_event():
    server, reseed = _server()
    assert server.handle("POST", "/api/reseed") == (200, {"ok": True})
    assert reseed.is_set()


def test_get_does_not_fire_a_command():
    # A link preview or a prefetch must not reset the background.
    server, reseed = _server()
    code, _ = server.handle("GET", "/api/reseed")
    assert code == 405
    assert not reseed.is_set()


def test_health_reports_the_last_status():
    server, _ = _server()
    server.set_status({"state": "playlist", "fg_pixels": 12})
    assert server.handle("GET", "/health") == (200, {"state": "playlist", "fg_pixels": 12})
    assert server.handle("GET", "/") == (200, {"state": "playlist", "fg_pixels": 12})


def test_unknown_path_is_404_and_preflight_is_204():
    server, _ = _server()
    assert server.handle("GET", "/nope") == (404, None)
    assert server.handle("OPTIONS", "/api/reseed") == (204, None)


def test_port_comes_from_network_json_unless_overridden():
    assert monitor_port() == NETWORK["elements"]["captcha"]["http_port"]
    assert monitor_port(9999) == 9999


# ── Over a real socket ────────────────────────────────────────────────────────

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(port: int) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return
        except OSError:
            time.sleep(0.05)
    pytest.fail("monitoring server did not start")


def test_dashboard_can_post_reseed_and_read_health_cross_origin():
    reseed = threading.Event()
    port   = _free_port()
    server = MonitoringServer(port, {"/api/reseed": reseed})
    server.start()
    _wait_for(port)
    base = f"http://127.0.0.1:{port}"
    origin = {"Origin": "http://192.168.1.10:9000"}

    # As the Dashboard sends it: POST, no body (a CORS "simple" request).
    req = urllib.request.Request(base + "/api/reseed", method="POST", headers=origin)
    with urllib.request.urlopen(req, timeout=2) as resp:
        assert resp.status == 200
        assert resp.headers["Access-Control-Allow-Origin"] == "*"
    assert reseed.is_set()

    server.set_status({"state": "playlist"})
    with urllib.request.urlopen(urllib.request.Request(base + "/health", headers=origin),
                                timeout=2) as resp:
        assert resp.headers["Access-Control-Allow-Origin"] == "*"
        assert json.load(resp) == {"state": "playlist"}

    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(base + "/api/reseed", timeout=2)          # GET
    assert err.value.code == 405


# ── The reseed reaches the background model ───────────────────────────────────

def test_reseed_event_is_consumed_by_the_camera_thread():
    pytest.importorskip("IIVision")
    from shader_app import drain_camera, start_camera

    args   = argparse.Namespace(camera=False, mock_camera=True, test_input=False)
    reseed = threading.Event()
    cam_q, stop = start_camera(args, SETTINGS, reseed)
    try:
        reseed.set()
        deadline = time.monotonic() + 5.0
        while reseed.is_set() and time.monotonic() < deadline:
            drain_camera(cam_q)          # the camera thread blocks when its queue is full
            time.sleep(0.01)
    finally:
        stop.set()
    assert not reseed.is_set(), "the camera thread never picked up the reseed"
