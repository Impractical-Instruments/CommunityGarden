import logging
import math
from dataclasses import dataclass

from .base import ChannelFrame, Color, Display, DisplayState, scale_color

log = logging.getLogger("treehouse")


@dataclass
class LEDConfig:
    name: str
    pico_pin: int
    led_count: int
    brightness: float = 1.0
    color: Color = (0, 0, 0, 255)  # pure white via the W channel
    pattern: str = "solid"
    pulse_period: float = 20.0   # seconds per cycle (mycelium pattern)
    pulse_min: float = 0.5       # minimum brightness fraction (mycelium pattern)


class LEDDisplay(Display):
    """
    Generic SK6812 LED strip — diorama boxes, gable windows, dormer.

    Patterns
    --------
    solid        – static colour at set brightness
    breathe      – sinusoidal fade in/out (~4 s cycle)
    strobe       – 10 Hz on/off flash
    chase        – lit head travels the strip with a fading 6-pixel trail
    incandescent – barely-perceptible flicker simulating a warm bulb
    mycelium     – very slow pulse between pulse_min and 1.0 (default 20 s, 50–100%)
    """

    PATTERNS = ("solid", "breathe", "strobe", "chase", "incandescent", "mycelium")

    def __init__(self, config: LEDConfig) -> None:
        super().__init__(config.name)
        self.pico_pin = config.pico_pin
        self.led_count = config.led_count
        self.brightness = config.brightness
        self.color: Color = config.color
        self.pattern = config.pattern
        self.pulse_period = config.pulse_period
        self.pulse_min = config.pulse_min
        self._time = 0.0

    def set_color(self, color: Color) -> None:
        self.color = color

    def set_brightness(self, brightness: float) -> None:
        self.brightness = max(0.0, min(1.0, brightness))

    def set_pattern(self, pattern: str) -> None:
        if pattern not in self.PATTERNS:
            raise ValueError(f"Unknown pattern {pattern!r}; choices: {self.PATTERNS}")
        self.pattern = pattern

    def update(self, dt: float) -> None:
        if not self.enabled:
            return
        self._time += dt

    def _base_color(self) -> Color:
        return scale_color(self.color, self.brightness)

    def _compute_pixels(self) -> list[Color]:
        base = self._base_color()

        if self.pattern == "breathe":
            factor = (math.sin(self._time * math.pi / 2.0) + 1.0) / 2.0
            return [scale_color(base, factor)] * self.led_count

        if self.pattern == "strobe":
            on = (int(self._time * 10) % 2 == 0)
            return [base if on else (0, 0, 0, 0)] * self.led_count

        if self.pattern == "chase":
            pixels: list[Color] = [(0, 0, 0, 0)] * self.led_count
            head = int(self._time * 20) % self.led_count
            trail = 6
            for i in range(trail):
                idx = (head - i) % self.led_count
                pixels[idx] = scale_color(base, 1.0 - i / trail)
            return pixels

        if self.pattern == "incandescent":
            # Two inharmonic sines produce irregular flicker without obvious periodicity
            noise = (math.sin(self._time * 7.3) + math.sin(self._time * 13.7)) / 2.0
            factor = 1.0 - 0.015 * (noise + 1.0) / 2.0
            return [scale_color(base, factor)] * self.led_count

        if self.pattern == "mycelium":
            phase = (math.sin(self._time * 2 * math.pi / self.pulse_period) + 1.0) / 2.0
            factor = self.pulse_min + (1.0 - self.pulse_min) * phase
            return [scale_color(base, factor)] * self.led_count

        return [base] * self.led_count  # solid

    def get_frames(self) -> list[ChannelFrame]:
        off: list[Color] = [(0, 0, 0, 0)] * self.led_count
        if not self.enabled:
            return [ChannelFrame(pin=self.pico_pin, pixels=off)]
        return [ChannelFrame(pin=self.pico_pin, pixels=self._compute_pixels())]

    def get_state(self) -> DisplayState:
        return DisplayState(
            name=self.name,
            enabled=self.enabled,
            params={
                "pico_pin": self.pico_pin,
                "led_count": self.led_count,
                "color": self.color,
                "brightness": round(self.brightness, 3),
                "pattern": self.pattern,
                "time": round(self._time, 2),
            },
        )
