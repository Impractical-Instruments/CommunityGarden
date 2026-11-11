"""The visualizer's /control/* routes, and the Dashboard buttons that call them."""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import visualizer
from controllables import LookingGlassConfig, LookingGlassControllable, ShowMode
from coordinator import BranchConfig, BranchMotorConfig, Coordinator

DASHBOARD_PAGE = Path(__file__).parent.parent / "Dashboard" / "treehouse.html"


@pytest.fixture
def coordinator(monkeypatch):
    coord = Coordinator(
        [LookingGlassControllable(LookingGlassConfig())],
        branch_config=BranchConfig(motors=[BranchMotorConfig(id=1, recoil_pos=-20.0)]),
    )
    monkeypatch.setattr(visualizer, "_coordinator", coord)
    return coord


@pytest.fixture
def client():
    return TestClient(visualizer.app)


@pytest.mark.parametrize("mode", ["active", "dim", "inactive"])
def test_show_mode_sets_the_mode(client, coordinator, mode):
    assert client.post("/control/show/mode", json={"mode": mode}).json() == {"ok": True}
    assert coordinator.mode == ShowMode(mode)


def test_unknown_show_mode_is_ignored(client, coordinator):
    client.post("/control/show/mode", json={"mode": "dim"})
    assert client.post("/control/show/mode", json={"mode": "full"}).status_code == 200
    assert coordinator.mode == ShowMode.DIM


def test_brightness_sets_the_dim_level(client, coordinator):
    client.post("/control/show/mode", json={"mode": "dim"})
    assert client.post("/control/show/brightness", json={"level": 0.4}).json() == {"ok": True}
    assert coordinator.brightness == pytest.approx(0.4)


def test_looking_glass_sets_the_scene(client, coordinator):
    assert client.post("/control/looking-glass", json={"scene": "cosmos"}).json() == {"ok": True}
    assert coordinator.get_all_states()[0].params["scene"] == "cosmos"


def test_blowup_recoils_the_branches_for_one_frame(client, coordinator):
    assert client.post("/control/blowup").json() == {"ok": True}
    coordinator.update(1 / 30)
    assert coordinator.garden_state.captcha_blowup
    assert coordinator.get_branch_positions() == [(1, -20.0)]
    coordinator.update(1 / 30)
    assert not coordinator.garden_state.captcha_blowup


def test_routes_answer_before_the_coordinator_exists(client, monkeypatch):
    monkeypatch.setattr(visualizer, "_coordinator", None)
    assert client.post("/control/show/mode", json={"mode": "dim"}).json() == {"ok": True}
    assert client.post("/control/blowup").json() == {"ok": True}


# ── The Dashboard page ────────────────────────────────────────────────────────

def test_dashboard_show_mode_buttons_send_real_modes():
    sent = re.findall(r'data-show-mode="([^"]+)"', DASHBOARD_PAGE.read_text())
    assert sent == [m.value for m in ShowMode]


def test_dashboard_scene_buttons_send_real_scenes():
    sent = re.findall(r'data-scene="([^"]+)"', DASHBOARD_PAGE.read_text())
    assert tuple(sent) == LookingGlassControllable.SCENES


def test_dashboard_posts_only_to_routes_that_exist():
    posted = set(re.findall(r"ctrlPost\('(/control/[^']+)'", DASHBOARD_PAGE.read_text()))
    routes = {r.path for r in visualizer.app.routes if r.path.startswith("/control/")}
    assert posted and posted <= routes
