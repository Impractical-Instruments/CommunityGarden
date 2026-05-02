import logging
import math
from dataclasses import dataclass
from enum import Enum

from .base import ChannelFrame, Color, ControllableState, GardenState, LEDControllable, scale_color

log = logging.getLogger("treehouse")


class _State(Enum):
    NORMAL     = "normal"
    BLOWUP     = "blowup"
    AFTERMATH  = "aftermath"


@dataclass
class PorchLightsConfig:
    name: str = "Porch Lights"
    pico_pin: int = 8
    led_count: int = 2
    blowup_duration: float = 3.0
    aftermath_duration: float = 10.0


class PorchLightsDisplay(LEDControllable):
    """
    Two warm exterior light fixtures outside the front door.

    Normal:    warm incandescent glow.
    Triggered by FundingCAPTCHA blow-up (captcha_blowup in GardenState):
      1. Sickly blue flicker for blowup_duration seconds
      2. Dim orange smoulder for aftermath_duration seconds
      3. Fade back to normal
    """

    _WARM_COLOR:      Color = (255, 160,  60, 200)
    _BLOWUP_COLOR:    Color = ( 60, 200, 255,   0)
    _AFTERMATH_COLOR: Color = (255,  80,  20,   0)

    def __init__(self, config: PorchLightsConfig) -> None:
        super().__init__(config.name)
        self.pico_pin = config.pico_pin
        self.led_count = config.led_count
        self.blowup_duration = config.blowup_duration
        self.aftermath_duration = config.aftermath_duration
        self._state = _State.NORMAL
        self._state_time = 0.0
        self._time = 0.0

    def reset(self) -> None:
        log.info("Porch Lights: reset to normal")
        self._state = _State.NORMAL
        self._state_time = 0.0

    def update(self, dt: float, state: GardenState) -> None:
        if not self.enabled:
            return
        if state.captcha_blowup and self._state == _State.NORMAL:
            log.info("Porch Lights: blowup triggered")
            self._state = _State.BLOWUP
            self._state_time = 0.0
        self._time += dt
        self._state_time += dt
        if self._state == _State.BLOWUP and self._state_time >= self.blowup_duration:
            self._state = _State.AFTERMATH
            self._state_time = 0.0
            log.info("Porch Lights: aftermath")
        elif self._state == _State.AFTERMATH and self._state_time >= self.aftermath_duration:
            self._state = _State.NORMAL
            self._state_time = 0.0
            log.info("Porch Lights: back to normal")

    def _compute_color(self) -> Color:
        if self._state == _State.NORMAL:
            noise = (math.sin(self._time * 7.3) + math.sin(self._time * 13.7)) / 2.0
            factor = 1.0 - 0.015 * (1.0 - (noise + 1.0) / 2.0)
            return scale_color(self._WARM_COLOR, factor)

        if self._state == _State.BLOWUP:
            # Erratic high-freq flicker — inharmonic pair well above perceptible flicker threshold
            noise = (math.sin(self._time * 47.1) + math.sin(self._time * 83.7)) / 2.0
            factor = 0.5 + 0.5 * (noise + 1.0) / 2.0
            return scale_color(self._BLOWUP_COLOR, factor)

        # AFTERMATH: dim static orange
        return scale_color(self._AFTERMATH_COLOR, 0.35)

    def get_pixels(self) -> list[ChannelFrame]:
        off: list[Color] = [(0, 0, 0, 0)] * self.led_count
        if not self.enabled:
            return [ChannelFrame(pin=self.pico_pin, pixels=off)]
        color = self._compute_color()
        return [ChannelFrame(pin=self.pico_pin, pixels=[color] * self.led_count)]

    def get_state(self) -> ControllableState:
        return ControllableState(
            name=self.name,
            enabled=self.enabled,
            params={
                "pico_pin": self.pico_pin,
                "led_count": self.led_count,
                "state": self._state.value,
                "state_time": round(self._state_time, 2),
                "blowup_duration": self.blowup_duration,
                "aftermath_duration": self.aftermath_duration,
            },
        )
