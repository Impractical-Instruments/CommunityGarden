"""Tests for layout_tool.py Python API layer."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import layout_tool
from layout_tool import app, _default_module, _flowerbeds_controllers


@pytest.fixture
def tmp_settings(tmp_path):
    settings = {
        "calibration_frames": 60,
        "stabilizer": {"max_match_dist_cm": 80.0},
        "coordinator": {
            "exclusion_radius_cm": 40.0,
            "modules": [
                {
                    "name": "Module 1",
                    "registration_point_cm": [-40.0, -84.0, 0.0],
                    "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
                    "clusters": [
                        {"motor_id": 14, "pos_offset_cm": [40.0, -30.0, 0.0],
                         "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}},
                    ],
                }
            ],
        },
    }
    p = tmp_path / "settings.json"
    p.write_text(json.dumps(settings, indent=2))
    layout_tool._config_path = p
    yield p


@pytest.fixture
def tmp_network(tmp_path):
    network = {
        "firmware": {
            "flowerbeds_controller_1": {"ip": "192.168.1.50", "mac": "DE:AD:BE:EF:15:00", "osc_port": 9000},
            "flowerbeds_controller_2": {"ip": "192.168.1.51", "mac": "DE:AD:BE:EF:15:01", "osc_port": 9000},
            "treehouse_branch":        {"ip": None, "mac": None, "osc_port": None},
        }
    }
    p = tmp_path / "network.json"
    p.write_text(json.dumps(network))
    layout_tool._network_path = p
    yield p


@pytest.fixture
def client(tmp_settings, tmp_network):
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_index_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "FlowerBeds Layout Tool" in r.text


# ---------------------------------------------------------------------------
# GET /api/defaults
# ---------------------------------------------------------------------------

def test_get_defaults_returns_cluster_offsets(client):
    r = client.get("/api/defaults")
    assert r.status_code == 200
    d = r.json()
    assert "cluster_offsets" in d
    offsets = d["cluster_offsets"]
    assert len(offsets) == 4
    assert offsets[0] == [30.0, 30.0, 0.0]
    assert offsets[1] == [-30.0, 30.0, 0.0]
    assert offsets[2] == [30.0, -30.0, 0.0]
    assert offsets[3] == [-30.0, -30.0, 0.0]


def test_defaults_match_default_module(client):
    r = client.get("/api/defaults")
    offsets = r.json()["cluster_offsets"]
    m = _default_module(0)
    for i, cluster in enumerate(m["clusters"]):
        assert cluster["pos_offset_cm"] == offsets[i]


# ---------------------------------------------------------------------------
# GET /api/layout
# ---------------------------------------------------------------------------

def test_get_layout_returns_modules(client, tmp_settings):
    r = client.get("/api/layout")
    assert r.status_code == 200
    data = r.json()
    assert "modules" in data
    assert len(data["modules"]) == 1
    assert data["modules"][0]["name"] == "Module 1"


def test_get_layout_missing_file(tmp_path, tmp_network):
    layout_tool._config_path = tmp_path / "nonexistent.json"
    c = TestClient(app)
    r = c.get("/api/layout")
    assert r.status_code == 200
    assert r.json()["modules"] == []


# ---------------------------------------------------------------------------
# POST /api/layout
# ---------------------------------------------------------------------------

def test_post_layout_writes_modules(client, tmp_settings):
    new_modules = [
        {
            "name": "Test Module",
            "registration_point_cm": [100.0, 200.0, 0.0],
            "rotation": {"pitch": 0, "yaw": 45, "roll": 0},
            "clusters": [
                {"motor_id": 99, "pos_offset_cm": [40.0, -30.0, 0.0],
                 "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}},
            ],
        }
    ]
    r = client.post("/api/layout", json={"modules": new_modules})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    written = json.loads(tmp_settings.read_text())
    mods = written["coordinator"]["modules"]
    assert len(mods) == 1
    assert mods[0]["name"] == "Test Module"
    assert mods[0]["rotation"]["yaw"] == 45


def test_post_layout_creates_backup(client, tmp_settings):
    client.post("/api/layout", json={"modules": []})
    bak = tmp_settings.with_suffix(".json.bak")
    assert bak.exists()


def test_post_layout_preserves_other_settings(client, tmp_settings):
    client.post("/api/layout", json={"modules": []})
    written = json.loads(tmp_settings.read_text())
    assert written["calibration_frames"] == 60
    assert "stabilizer" in written


def test_post_layout_missing_file(tmp_path, tmp_network):
    layout_tool._config_path = tmp_path / "nonexistent.json"
    c = TestClient(app)
    r = c.post("/api/layout", json={"modules": []})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/network
# ---------------------------------------------------------------------------

def test_get_network_returns_controllers(client, tmp_network):
    r = client.get("/api/network")
    assert r.status_code == 200
    d = r.json()
    assert len(d["controllers"]) == 2
    names = {c["name"] for c in d["controllers"]}
    assert "flowerbeds_controller_1" in names
    assert "flowerbeds_controller_2" in names
    # treehouse_branch (null ip) excluded
    assert all(c["ip"] for c in d["controllers"])


def test_get_network_missing_file(tmp_path, tmp_settings):
    layout_tool._network_path = tmp_path / "nonexistent.json"
    c = TestClient(app)
    r = c.get("/api/network")
    assert r.status_code == 200
    d = r.json()
    assert d["controllers"] == []


# ---------------------------------------------------------------------------
# GET /api/controller-status
# ---------------------------------------------------------------------------

def test_controller_status_returns_structure(client, tmp_network):
    r = client.get("/api/controller-status")
    assert r.status_code == 200
    d = r.json()
    assert "controllers" in d
    for ctrl in d["controllers"]:
        assert "name" in ctrl
        assert "ip" in ctrl
        assert "online" in ctrl
        assert "checked_at" in ctrl
    # Both should be offline (no real hardware in test environment)
    assert all(not c["online"] for c in d["controllers"])


# ---------------------------------------------------------------------------
# POST /api/aim
# ---------------------------------------------------------------------------

def test_aim_endpoint_exists(client):
    # We can't test actual OSC without hardware, but endpoint should accept the request
    # (it will try to send to non-existent hosts, which should fail gracefully)
    r = client.post("/api/aim", json={"motor_id": 1, "deg": 45.0})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Helper: _flowerbeds_controllers
# ---------------------------------------------------------------------------

def test_flowerbeds_controllers_filters_nulls():
    network = {
        "firmware": {
            "flowerbeds_controller_1": {"ip": "192.168.1.50", "osc_port": 9000, "mac": "AA"},
            "flowerbeds_controller_2": {"ip": "192.168.1.51", "osc_port": 9000, "mac": "BB"},
            "treehouse_branch":        {"ip": None, "mac": None, "osc_port": None},
        }
    }
    result = _flowerbeds_controllers(network)
    assert len(result) == 2
    assert all(c["ip"] for c in result)


def test_flowerbeds_controllers_excludes_non_flowerbeds():
    network = {
        "firmware": {
            "treehouse_branch": {"ip": "192.168.1.20", "osc_port": 9001, "mac": "CC"},
        }
    }
    assert _flowerbeds_controllers(network) == []


# ---------------------------------------------------------------------------
# Helper: _default_module
# ---------------------------------------------------------------------------

def test_default_module_structure():
    m = _default_module(0)
    assert m["name"] == "Module 1"
    assert len(m["clusters"]) == 4
    assert m["clusters"][0]["motor_id"] == 1
    assert m["clusters"][3]["motor_id"] == 4


def test_default_module_sequential_ids():
    m5 = _default_module(4)  # 5th module (0-indexed)
    assert m5["name"] == "Module 5"
    assert m5["clusters"][0]["motor_id"] == 17  # 4*4+1
