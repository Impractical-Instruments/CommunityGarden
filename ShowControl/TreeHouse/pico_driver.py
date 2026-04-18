import json
import logging

import serial

from displays.base import ChannelFrame, Color, scale_color

log = logging.getLogger("treehouse")


class PicoDriver:
    """
    Sends LED frame data to the Pi Pico over USB serial.

    Protocol — one newline-delimited JSON object per strip per frame:

        {"pin": <int>, "pixels": [[r, g, b, w], ...]}

    The Pico firmware reads each line, identifies the SK6812 strip on that
    GPIO pin, and writes the pixel data out via PIO DMA.  The Pi 5 does not
    wait for an acknowledgement; frames are fire-and-forget at 30 fps.

    If the serial port is unavailable (dev mode, cable unplugged) the driver
    logs a warning and silently drops frames rather than crashing the loop.
    """

    def __init__(self, port: str, baud: int = 115200) -> None:
        self._port = port
        self._baud = baud
        self._serial: serial.Serial | None = None

    def connect(self) -> None:
        try:
            self._serial = serial.Serial(self._port, self._baud, timeout=1)
            log.info("Pico connected on %s @ %d baud", self._port, self._baud)
        except serial.SerialException as e:
            log.warning("Pico not available (%s) — LED output disabled", e)

    def send_frames(self, frames: list[ChannelFrame], brightness: float = 1.0) -> None:
        if not self._serial or not self._serial.is_open:
            return
        for frame in frames:
            scaled: list[list[int]] = [list(scale_color(p, brightness)) for p in frame.pixels]
            line = json.dumps({"pin": frame.pin, "pixels": scaled}) + "\n"
            try:
                self._serial.write(line.encode())
            except serial.SerialException as e:
                log.error("Pico write error: %s — LED output suspended", e)
                self._serial = None
                return

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
            log.info("Pico disconnected")
