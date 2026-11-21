"""The Dashboard server hands the pages their ports; the pages hold none."""
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


def test_no_page_builds_an_element_url_from_its_own_hostname():
    """Elements run on their own hosts; only network.js may ask where the Dashboard was loaded from."""
    for page in sorted(DIR.glob("*.html")) + sorted(DIR.glob("*.js")):
        if page.name == "network.js":
            continue
        found = re.findall(r"location\s*\.\s*host(?:name)?\b", page.read_text())
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
@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
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
