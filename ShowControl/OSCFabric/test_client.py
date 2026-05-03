"""
Tests for FabricClient and load_network_config.

Red-green-refactor: run with `python -m pytest test_client.py` from this directory
or via `make test` from the repo root.
"""
from __future__ import annotations

import json
import pytest

from OSCFabric.client import FabricClient
from OSCFabric.config import load_network_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class SpyTransport:
    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []

    def send(self, address: str, *args) -> None:
        self.calls.append((address, args))

    def sent_addresses(self) -> list[str]:
        return [c[0] for c in self.calls]


def _config(**overrides) -> dict:
    cfg: dict = {"heartbeat_interval_s": 5.0, "change_epsilon": 0.01}
    cfg.update(overrides)
    return cfg


# ---------------------------------------------------------------------------
# report() — on-change semantics
# ---------------------------------------------------------------------------

def test_report_sends_on_first_call():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(), transport=spy)
    client.report("activity", 0.5)
    assert ("/flowerbeds/activity", (0.5,)) in spy.calls


def test_report_uses_element_prefixed_address():
    spy = SpyTransport()
    client = FabricClient("captcha", _config(), transport=spy)
    client.report("intensity", 0.3)
    assert spy.calls[0][0] == "/captcha/intensity"


def test_report_suppresses_if_value_unchanged():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(), transport=spy)
    client.report("activity", 0.5)
    spy.calls.clear()
    client.report("activity", 0.5)
    assert spy.calls == []


def test_report_suppresses_if_delta_below_epsilon():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(change_epsilon=0.01), transport=spy)
    client.report("activity", 0.5)
    spy.calls.clear()
    client.report("activity", 0.505)   # delta 0.005 < epsilon 0.01
    assert spy.calls == []


def test_report_sends_if_delta_exceeds_epsilon():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(change_epsilon=0.01), transport=spy)
    client.report("activity", 0.5)
    spy.calls.clear()
    client.report("activity", 0.52)    # delta 0.02 > epsilon 0.01
    assert ("/flowerbeds/activity", (0.52,)) in spy.calls


def test_report_independent_signals_tracked_separately():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(), transport=spy)
    client.report("activity", 0.5)
    client.report("mood", 0.8)
    spy.calls.clear()
    client.report("activity", 0.5)    # unchanged — suppressed
    client.report("mood", 0.9)        # changed — sent
    assert spy.sent_addresses() == ["/flowerbeds/mood"]


# ---------------------------------------------------------------------------
# send_event() — one-shot semantics
# ---------------------------------------------------------------------------

def test_send_event_sends_immediately():
    spy = SpyTransport()
    client = FabricClient("captcha", _config(), transport=spy)
    client.send_event("blowup")
    assert spy.calls == [("/captcha/blowup", ())]


def test_send_event_carries_no_args():
    spy = SpyTransport()
    client = FabricClient("captcha", _config(), transport=spy)
    client.send_event("game_started")
    assert spy.calls[0][1] == ()


def test_send_event_always_fires():
    spy = SpyTransport()
    client = FabricClient("captcha", _config(), transport=spy)
    client.send_event("blowup")
    client.send_event("blowup")
    assert len([c for c in spy.calls if c[0] == "/captcha/blowup"]) == 2


# ---------------------------------------------------------------------------
# tick() — heartbeat semantics
# ---------------------------------------------------------------------------

def test_tick_does_not_fire_before_interval():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(heartbeat_interval_s=5.0), transport=spy)
    client.report("activity", 0.5)
    spy.calls.clear()
    client.tick(4.9)
    assert spy.calls == []


def test_tick_fires_heartbeat_at_interval():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(heartbeat_interval_s=5.0), transport=spy)
    client.report("activity", 0.5)
    spy.calls.clear()
    client.tick(5.0)
    assert ("/flowerbeds/activity", (0.5,)) in spy.calls


def test_tick_accumulates_across_multiple_calls():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(heartbeat_interval_s=5.0), transport=spy)
    client.report("activity", 0.5)
    spy.calls.clear()
    client.tick(2.0)
    client.tick(2.0)
    client.tick(1.0)   # total = 5.0 → fires
    assert ("/flowerbeds/activity", (0.5,)) in spy.calls


def test_tick_resets_timer_after_heartbeat():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(heartbeat_interval_s=5.0), transport=spy)
    client.report("activity", 0.5)
    client.tick(5.0)
    spy.calls.clear()
    client.tick(4.9)   # timer reset — should not fire again
    assert spy.calls == []


def test_tick_fires_heartbeat_for_all_tracked_signals():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(heartbeat_interval_s=5.0), transport=spy)
    client.report("activity", 0.5)
    client.report("mood", 0.8)
    spy.calls.clear()
    client.tick(5.0)
    addresses = spy.sent_addresses()
    assert "/flowerbeds/activity" in addresses
    assert "/flowerbeds/mood" in addresses


def test_tick_does_nothing_if_no_signals_reported():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(heartbeat_interval_s=5.0), transport=spy)
    client.tick(10.0)
    assert spy.calls == []


def test_heartbeat_sends_most_recent_value():
    spy = SpyTransport()
    client = FabricClient("flowerbeds", _config(heartbeat_interval_s=5.0), transport=spy)
    client.report("activity", 0.5)
    client.report("activity", 0.9)   # update before heartbeat fires
    spy.calls.clear()
    client.tick(5.0)
    assert ("/flowerbeds/activity", (0.9,)) in spy.calls
    assert ("/flowerbeds/activity", (0.5,)) not in spy.calls


# ---------------------------------------------------------------------------
# load_network_config()
# ---------------------------------------------------------------------------

def test_load_network_config_loads_file(tmp_path):
    cfg = {"heartbeat_interval_s": 10, "change_epsilon": 0.02}
    (tmp_path / "network.json").write_text(json.dumps(cfg))
    result = load_network_config(tmp_path / "network.json")
    assert result["heartbeat_interval_s"] == 10
    assert result["change_epsilon"] == 0.02


def test_load_network_config_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_network_config(tmp_path / "nonexistent.json")


def test_load_network_config_finds_canonical_path():
    # The canonical network.json lives one level above this package.
    # This test verifies the file exists at the expected location and parses.
    result = load_network_config()
    assert "elements" in result
    assert "treehouse" in result["elements"]
