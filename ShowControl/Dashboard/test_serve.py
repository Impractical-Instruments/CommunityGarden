"""The Dashboard server hands the pages their ports; the pages hold none."""
from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

import serve

DIR = Path(__file__).resolve().parent
NETWORK = json.loads((DIR.parent / "network.json").read_text())


def test_api_network_serves_the_elements_block():
    body = TestClient(serve.app).get("/api/network").json()
    assert body == {"elements": NETWORK["elements"]}


def test_api_network_is_empty_when_network_json_is_missing(monkeypatch):
    monkeypatch.setattr(serve, "load_network_config_or_empty", lambda log: {})
    assert TestClient(serve.app).get("/api/network").json() == {"elements": {}}


def test_no_page_hardcodes_a_port():
    ports = {str(el[key]) for el in NETWORK["elements"].values() for key in ("http_port", "osc_port")}
    for page in sorted(DIR.glob("*.html")) + [DIR / "network.js"]:
        found = set(re.findall(r"\b\d{4,5}\b", page.read_text())) & ports
        assert not found, f"{page.name} hardcodes {sorted(found)}; read it from /api/network"


def test_every_dashboard_element_is_in_network_json():
    ids = re.findall(r"\{ id: '(\w+)' \}", (DIR / "index.html").read_text())
    assert ids and set(ids) <= set(NETWORK["elements"])


# ── What a page asks an Element for (#303) ───────────────────────────────────

# A URL a page builds for an Element: a path straight after a `${…}` expression,
# as in `http://${HOST}:${PORT}/health`. Dashboard-relative links have no `${…}`.
ELEMENT_PATH = re.compile(r"\$\{[^}]+\}(/[\w./-]*)")


def test_no_page_asks_an_element_port_for_an_html_file():
    # The Elements serve JSON, sockets and (FlowerBeds) a visualizer at `/`; none serves
    # a named .html file. The Dashboard's own pages are linked relatively, without `${…}`.
    for page in sorted(DIR.glob("*.html")) + [DIR / "log-panel.js"]:
        found = [p for p in ELEMENT_PATH.findall(page.read_text()) if p.endswith(".html")]
        assert not found, f"{page.name} asks an Element port for {found}; no Element serves a page there"


def test_the_kiosk_serves_every_path_the_fundingcaptcha_page_asks_for():
    """Start the kiosk's real MonitoringServer and ask it for each path the page uses."""
    import importlib.util
    import socket
    import time
    import urllib.error
    import urllib.request

    import pytest

    pytest.importorskip("websockets")
    # Loaded by path: FundingCAPTCHA/ is not a package, and `monitor` is too plain a name to put on sys.path.
    spec = importlib.util.spec_from_file_location("captcha_monitor", DIR.parent / "FundingCAPTCHA" / "monitor.py")
    captcha_monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(captcha_monitor)

    page = (DIR / "fundingcaptcha.html").read_text()
    paths = set(ELEMENT_PATH.findall(page))
    if "connectLogs(" in page:
        paths |= set(ELEMENT_PATH.findall((DIR / "log-panel.js").read_text()))
    assert {"/health", "/logs"} <= paths, f"the page should read status and logs; it asks for {sorted(paths)}"

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    captcha_monitor.MonitoringServer(port).start()
    for _ in range(200):                       # wait for the port to open
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.1).close()
            break
        except OSError:
            time.sleep(0.02)
    else:
        pytest.fail("monitoring server never opened its port")

    for path in sorted(paths):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:    # /logs is a WebSocket: a plain GET is refused, but not with 404
            status = e.code
        assert status != 404, f"fundingcaptcha.html asks the kiosk for {path}, which it does not serve"
