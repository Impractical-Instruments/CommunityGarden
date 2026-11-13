"""Turns GardenState into branch motor positions and drives the branch servos over USB serial."""

import json
import logging

import serial

from config import BranchConfig, BranchMotorConfig
from controllables import Controllable, ControllableState, GardenState

log = logging.getLogger("treehouse")


def branch_positions(
    motors: list[BranchMotorConfig], state: GardenState,
) -> list[tuple[int, float]]:
    """(motor_id, degrees) for each motor: the weighted signal blend, or recoil on a Blow-Up."""
    positions: list[tuple[int, float]] = []
    for motor in motors:
        if state.captcha_blowup:
            pos = motor.recoil_pos
        else:
            signal = (
                motor.weight_flowerbeds * state.flowerbeds_activity
                + motor.weight_captcha * state.captcha_intensity
                + motor.weight_pipes * state.pipes_activity
            )
            signal = max(0.0, min(1.0, signal))
            pos = motor.min_pos + signal * (motor.max_pos - motor.min_pos)
        positions.append((motor.id, pos))
    return positions


class BranchDriver:
    """
    Sends servo position commands to the branch OpenRB-150 over USB serial.

    Protocol — one newline-delimited JSON object per command:
        {"id": <int>, "pos": <float>}

    The controller acknowledges each command with:
        {"id": <int>, "ok": true}

    This driver is fire-and-forget: it does not wait for acknowledgements.
    If the serial port is unavailable the driver logs a warning and silently
    drops commands rather than crashing the loop.
    """

    def __init__(self, port: str, baud: int = 115200) -> None:
        self._port = port
        self._baud = baud
        self._serial: serial.Serial | None = None

    def connect(self) -> None:
        try:
            self._serial = serial.Serial(self._port, self._baud, timeout=1)
            log.info("BranchDriver connected on %s @ %d baud", self._port, self._baud)
        except serial.SerialException as e:
            log.warning("BranchDriver not available (%s) — branch output disabled", e)

    def set_position(self, motor_id: int, degrees: float) -> None:
        if not self._serial or not self._serial.is_open:
            return
        line = json.dumps({"id": motor_id, "pos": round(degrees, 2)}) + "\n"
        try:
            self._serial.write(line.encode())
        except serial.SerialException as e:
            log.error("BranchDriver write error: %s — branch output suspended", e)
            self._serial = None

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
            log.info("BranchDriver disconnected")


class BranchController(Controllable):
    """The roof Branches as a Controllable (ADR-0006): maps GardenState to motor positions each frame."""

    def __init__(self, config: BranchConfig, driver: BranchDriver, name: str = "Branches") -> None:
        super().__init__(name)
        self._motors = config.motors
        self._driver = driver
        self._positions: list[tuple[int, float]] = []

    @property
    def positions(self) -> list[tuple[int, float]]:
        """(motor_id, degrees) pairs sent on the most recent update()."""
        return list(self._positions)

    def update(self, dt: float, state: GardenState) -> None:
        self._positions = branch_positions(self._motors, state)
        for motor_id, degrees in self._positions:
            self._driver.set_position(motor_id, degrees)

    def get_state(self) -> ControllableState:
        return ControllableState(
            name=self.name,
            enabled=self.enabled,
            params={"positions": [[motor_id, degrees] for motor_id, degrees in self._positions]},
        )
