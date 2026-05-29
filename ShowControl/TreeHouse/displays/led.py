import logging
import math
from dataclasses import dataclass

from .base import (
    ChannelFrame, Color, ControllableState, GardenState,
    GPIOFrame, PWMFrame, LEDControllable, PWMControllable, scale_color,
)

log = logging.getLogger("treehouse")


@dataclass
class LEDConfig:
    name: str
    pico_pin: int
    led_count: int
    pico_id: str = "dioramas"
    brightness: float = 1.0
    color: Color = (0, 0, 0, 255)  # pure white via the W channel
    pattern: str = "solid"
    pulse_period: float = 20.0   # seconds per cycle (mycelium pattern)
    pulse_min: float = 0.5       # minimum brightness fraction (mycelium pattern)
    transistor_pin: int = -1     # -1 = no transistor; set to Pico GPIO pin for switch
    transistor_pico_id: str = "dioramas"
    transistor_threshold: float = 0.6  # pipes_activity level that triggers the switch


class LEDDisplay(LEDControllable):
    """
    Generic SK6812 LED strip — diorama boxes, dormer, attic.

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
        self.pico_id = config.pico_id
        self.led_count = config.led_count
        self.brightness = config.brightness
        self.color: Color = config.color
        self.pattern = config.pattern
        self.pulse_period = config.pulse_period
        self.pulse_min = config.pulse_min
        self.transistor_pin = config.transistor_pin
        self.transistor_pico_id = config.transistor_pico_id
        self.transistor_threshold = config.transistor_threshold
        self._gpio_value = False
        self._time = 0.0

    def set_color(self, color: Color) -> None:
        self.color = color

    def set_brightness(self, brightness: float) -> None:
        self.brightness = max(0.0, min(1.0, brightness))

    def set_pattern(self, pattern: str) -> None:
        if pattern not in self.PATTERNS:
            raise ValueError(f"Unknown pattern {pattern!r}; choices: {self.PATTERNS}")
        self.pattern = pattern

    def update(self, dt: float, state: GardenState) -> None:
        if not self.enabled:
            return
        self._time += dt
        if self.transistor_pin >= 0:
            self._gpio_value = state.pipes_activity >= self.transistor_threshold

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

    def get_pixels(self) -> list[ChannelFrame]:
        off: list[Color] = [(0, 0, 0, 0)] * self.led_count
        if not self.enabled:
            return [ChannelFrame(pin=self.pico_pin, pixels=off, pico_id=self.pico_id)]
        return [ChannelFrame(pin=self.pico_pin, pixels=self._compute_pixels(), pico_id=self.pico_id)]

    def get_gpio_frames(self) -> list[GPIOFrame]:
        if self.transistor_pin < 0 or not self.enabled:
            return []
        return [GPIOFrame(pin=self.transistor_pin, value=self._gpio_value, pico_id=self.transistor_pico_id)]

    def get_state(self) -> ControllableState:
        return ControllableState(
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


@dataclass
class PWMConfig:
    name: str
    pico_pin: int
    pico_id: str = "dioramas"
    min_value: int = 8000   # 0–65535; floor glow when garden is quiet
    max_value: int = 65535
    pulse_period: float = 8.0
    signal_weight_captcha: float = 0.0
    signal_weight_flowerbeds: float = 0.5
    signal_weight_pipes: float = 0.5


class PWMDisplay(PWMControllable):
    """
    PWM-driven LED filament or dim circuit.

    Combines a slow sinusoidal ambient pulse with a GardenState signal bag
    to produce a single duty-cycle value each frame.
    """

    def __init__(self, config: PWMConfig) -> None:
        super().__init__(config.name)
        self._pin = config.pico_pin
        self._pico_id = config.pico_id
        self._min = config.min_value
        self._max = config.max_value
        self._period = config.pulse_period
        self._w_captcha = config.signal_weight_captcha
        self._w_flowerbeds = config.signal_weight_flowerbeds
        self._w_pipes = config.signal_weight_pipes
        self._time = 0.0
        self._value = config.min_value

    def update(self, dt: float, state: GardenState) -> None:
        if not self.enabled:
            self._value = 0
            return
        self._time += dt
        pulse = (math.sin(self._time * 2 * math.pi / self._period) + 1.0) / 2.0
        w_total = self._w_captcha + self._w_flowerbeds + self._w_pipes
        if w_total > 0:
            signal = (
                self._w_captcha * state.captcha_intensity
                + self._w_flowerbeds * state.flowerbeds_activity
                + self._w_pipes * state.pipes_activity
            ) / w_total
        else:
            signal = 0.0
        drive = 0.5 + 0.3 * pulse + 0.2 * signal
        drive = max(0.0, min(1.0, drive))
        if state.show_mode.value == "inactive":
            drive = 0.0
        elif state.show_mode.value == "dim":
            drive *= state.brightness
        self._value = int(self._min + drive * (self._max - self._min))

    def get_pwm_frames(self) -> list[PWMFrame]:
        return [PWMFrame(pin=self._pin, value=self._value, pico_id=self._pico_id)]

    def get_state(self) -> ControllableState:
        return ControllableState(
            name=self.name,
            enabled=self.enabled,
            params={
                "pico_pin": self._pin,
                "pico_id": self._pico_id,
                "value": self._value,
                "time": round(self._time, 2),
            },
        )
