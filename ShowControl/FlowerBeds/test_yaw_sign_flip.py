"""The yaw sign flip (software CCW+ -> Dynamixel CW+) on the wire to /cg/ff/rot."""
from __future__ import annotations

import pytest

import layout_tool
from flower_beds import MotorCommand

NETWORK = {
    "firmware": {
        "flowerbeds_controller_1": {"ip": "10.0.0.1", "osc_port": 9000},
    },
}


class _FakeClient:
    sent: list[tuple[str, str, list]] = []

    def __init__(self, ip, port):
        self.ip = ip

    def send_message(self, address, args):
        _FakeClient.sent.append((self.ip, address, list(args)))


@pytest.mark.parametrize("deg", [0.0, 12.5, -45.0, 90.0])
def test_both_copies_negate_the_same_way(monkeypatch, deg):
    """Characterisation of the two pre-refactor copies: they must agree."""
    _FakeClient.sent = []
    monkeypatch.setattr(layout_tool, "SimpleUDPClient", _FakeClient)
    layout_tool._send_osc(NETWORK, 7, deg)
    (_, address, layout_args), = _FakeClient.sent
    assert address == "/cg/ff/rot"
    assert layout_args == MotorCommand(motor_id=7, rotation_deg=deg).to_osc_args()
    assert layout_args == [7, -deg]
