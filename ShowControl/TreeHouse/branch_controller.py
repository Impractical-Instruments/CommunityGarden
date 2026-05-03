import json
import logging

import serial

log = logging.getLogger("treehouse")


class BranchController:
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
            log.info("BranchController connected on %s @ %d baud", self._port, self._baud)
        except serial.SerialException as e:
            log.warning("BranchController not available (%s) — branch output disabled", e)

    def set_position(self, motor_id: int, degrees: float) -> None:
        if not self._serial or not self._serial.is_open:
            return
        line = json.dumps({"id": motor_id, "pos": round(degrees, 2)}) + "\n"
        try:
            self._serial.write(line.encode())
        except serial.SerialException as e:
            log.error("BranchController write error: %s — branch output suspended", e)
            self._serial = None

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
            log.info("BranchController disconnected")
