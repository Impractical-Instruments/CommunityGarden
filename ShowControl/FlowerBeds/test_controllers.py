"""ControllerBus: discovery from network.json, the one yaw sign flip, and diagnostics."""
from __future__ import annotations

import pytest

import controllers
from controllers import OSC_ROT_ADDRESS, ControllerBus, controllers_from_network

NETWORK = {
    "firmware": {
        "flowerbeds_controller_1": {"ip": "10.0.0.1", "osc_port": 9000},
        "flowerbeds_controller_2": {"ip": "10.0.0.2", "osc_port": 9001},
        "flowerbeds_controller_3": {"ip": "10.0.0.3"},          # no port: skipped
        "treehouse_controller_1": {"ip": "10.0.0.9", "osc_port": 9000},
    },
}


class _FakeClient:
    def __init__(self, ip, port):
        self.ip, self.port = ip, port
        self.sent: list[tuple[str, list]] = []

    def send_message(self, address, args):
        self.sent.append((address, list(args)))


def _bus(network=NETWORK) -> tuple[ControllerBus, list[_FakeClient]]:
    made: list[_FakeClient] = []

    def factory(ip, port):
        made.append(_FakeClient(ip, port))
        return made[-1]

    return ControllerBus.from_network(network, client_factory=factory), made


def test_address_is_the_firmware_contract():
    assert OSC_ROT_ADDRESS == "/cg/ff/rot"


def test_discovery_keeps_only_complete_flowerbeds_entries():
    assert controllers_from_network(NETWORK) == [
        {"name": "flowerbeds_controller_1", "ip": "10.0.0.1", "osc_port": 9000},
        {"name": "flowerbeds_controller_2", "ip": "10.0.0.2", "osc_port": 9001},
    ]
    assert controllers_from_network({}) == []


@pytest.mark.parametrize("deg", [0.0, 12.5, -45.0, 90.0])
def test_send_negates_yaw_for_every_controller(deg):
    """Software CCW+ becomes Dynamixel CW+ on the wire (the same values the two old copies produced)."""
    bus, clients = _bus()
    bus.send(7, deg)
    assert len(bus) == 2
    for c in clients:
        assert c.sent == [(OSC_ROT_ADDRESS, [7, -deg])]


def test_diagnose_reports_motors_no_controller_saw(monkeypatch):
    pongs = {
        "10.0.0.1": {"found_ids": "1,2", "baud": 1000000, "found_count": 2,
                     "pkt_rx_count": 5, "pkt_drop_count": 0},
        "10.0.0.2": None,
    }
    monkeypatch.setattr(controllers, "osc_ping", lambda ip, port, timeout: pongs[ip])
    bus, _ = _bus()
    assert bus.diagnose({1, 2, 3}) == [3]
    assert bus.diagnose({1}) == []
