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
