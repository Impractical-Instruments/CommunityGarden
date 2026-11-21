"""The Dashboard server hands the pages each Element's address; the pages hold none."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
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


def test_no_page_or_script_holds_an_element_ip():
    ips = {el["ip"] for el in NETWORK["elements"].values()}
    for page in sorted(DIR.glob("*.html")) + sorted(DIR.glob("*.js")):
        found = sorted(ip for ip in ips if ip in page.read_text())
        assert not found, f"{page.name} hardcodes {found}; get it from elementBase() in network.js"


def test_no_page_builds_an_element_url_from_its_own_hostname():
    """Elements run on their own hosts; only network.js may ask where the Dashboard was loaded from."""
    for page in sorted(DIR.glob("*.html")) + sorted(DIR.glob("*.js")):
        if page.name == "network.js":
            continue
        found = re.findall(r"location\s*\.\s*(?:host(?:name)?|origin|href)\b|document\.domain", page.read_text())
        assert not found, f"{page.name} uses {found[0]}; get the Element's URL from elementBase() in network.js"


def test_every_page_gets_element_urls_from_element_base():
    for page in sorted(DIR.glob("*.html")):
        text = page.read_text()
        assert "elementBase(" in text, f"{page.name} does not call elementBase()"
        assert "/api/network" not in text, f"{page.name} reads /api/network itself; use network.js"


def element_bases(page_url: str) -> dict[str, str]:
    """What network.js's elementBase() returns for each Element, on a page at `page_url`."""
    script = """
      const fs = require('fs');
      const [file, pageUrl, elements] = process.argv.slice(1);
      globalThis.location = new URL(pageUrl);
      globalThis.fetch = async () => ({ ok: true, json: async () => ({ elements: JSON.parse(elements) }) });
      (0, eval)(fs.readFileSync(file, 'utf8'));
      (async () => {
        const out = {};
        for (const id of Object.keys(JSON.parse(elements))) out[id] = await elementBase(id);
        console.log(JSON.stringify(out));
      })();
    """
    run = subprocess.run(
        ["node", "-e", script, str(DIR / "network.js"), page_url, json.dumps(NETWORK["elements"])],
        capture_output=True, text=True, timeout=30,
    )
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="needs node to run network.js")


@needs_node
def test_element_base_is_the_elements_own_address_on_the_show_network():
    dashboard = f"http://{NETWORK['elements']['treehouse']['ip']}:9000/index.html"
    assert element_bases(dashboard) == {
        name: f"http://{el['ip']}:{el['http_port']}" for name, el in NETWORK["elements"].items()
    }


@needs_node
@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "127.0.1.1", "[::1]"])
def test_element_base_is_the_local_host_when_the_dashboard_is_opened_locally(host):
    assert element_bases(f"http://{host}:9000/index.html") == {
        name: f"http://{host}:{el['http_port']}" for name, el in NETWORK["elements"].items()
    }


@needs_node
def test_an_element_id_in_the_query_string_overrides_that_element_only():
    bases = element_bases("http://localhost:9000/playingthepipes.html?pipes=example.test:1234")
    assert bases["pipes"] == "http://example.test:1234"
    flowerbeds = NETWORK["elements"]["flowerbeds"]
    assert bases["flowerbeds"] == f"http://localhost:{flowerbeds['http_port']}"


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
