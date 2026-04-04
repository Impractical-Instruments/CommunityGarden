"""
OSC client that sends flower rotation commands to the Arduino controller.

OSC address : /cg/ff/rot
Arguments   : [int motor_id, float rotation_deg]

Mirrors UFlowerController in FlowerController.h/.cpp.
"""

from __future__ import annotations

from pythonosc.udp_client import SimpleUDPClient  # type: ignore[import]

from flower_beds import ControllerConfig, MotorCommand

_OSC_ADDRESS = "/cg/ff/rot"


class FlowerController:
    def __init__(self, config: ControllerConfig) -> None:
        self._client = SimpleUDPClient(config.ip, config.port)

    def send(self, cmd: MotorCommand) -> None:
        """Send a single motor rotation command."""
        self._client.send_message(_OSC_ADDRESS, [cmd.motor_id, cmd.rotation_deg])

    def send_all(self, commands: list[MotorCommand]) -> None:
        for cmd in commands:
            self.send(cmd)
