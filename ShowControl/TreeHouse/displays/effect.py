import logging
import math
from dataclasses import dataclass

from .base import ChannelFrame, Color, ControllableState, GardenState, LEDControllable, scale_color

log = logging.getLogger("treehouse")


@dataclass
class ForgeAndFloraConfig:
    name: str = "Forge & Flora"
    arc_pin: int = 2
    bloom_pin: int = 3
    led_count: int = 48      # same count on both strips
    blend: float = 0.0       # 0.0 = welding arc, 1.0 = magical gardening
    transition_speed: float = 0.1  # blend units per second
    base_flicker_intensity: float = 0.1   # flicker when garden is quiet
    max_flicker_intensity: float = 0.6    # flicker at peak captcha+flowerbeds activity


class ForgeAndFloraDisplay(LEDControllable):
    """
    Two-strip LED effect transitioning between welding arc and magical gardening.

    Arc strip (arc_pin)     — cold blue-white with high-freq flicker + orange spatter bursts
    Bloom strip (bloom_pin) — warm bioluminescent green with slow sinusoidal pulse

    blend = 0.0  →  arc at full, bloom off
    blend = 1.0  →  bloom at full, arc off
    Intermediate values cross-fade both strips simultaneously.
    """

    _ARC_COLOR: Color   = (180, 210, 255, 200)  # cold blue-white arc
    _SPARK_COLOR: Color = (255, 140,  20,   0)  # hot orange spatter
    _BLOOM_COLOR: Color = ( 60, 255, 100,  50)  # bioluminescent green

    def __init__(self, config: ForgeAndFloraConfig) -> None:
        super().__init__(config.name)
        self.arc_pin = config.arc_pin
        self.bloom_pin = config.bloom_pin
        self.led_count = config.led_count
        self.blend = config.blend
        self.transition_speed = config.transition_speed
        self._base_flicker = config.base_flicker_intensity
        self._max_flicker = config.max_flicker_intensity
        self.flicker_intensity = self._base_flicker
        self._target_blend = config.blend
        self._time = 0.0

    def set_mode(self, mode: str) -> None:
        modes = {"welding": 0.0, "gardening": 1.0}
        if mode not in modes:
            raise ValueError(f"Unknown mode {mode!r}; use {list(modes)}")
        log.info("Forge & Flora mode → %s", mode)
        self._target_blend = modes[mode]

    def set_blend(self, blend: float) -> None:
        self._target_blend = max(0.0, min(1.0, blend))

    def set_transition_speed(self, speed: float) -> None:
        self.transition_speed = max(0.0, speed)

    def _flicker(self) -> float:
        """Inharmonic high-freq noise for arc simulation."""
        raw = (math.sin(self._time * 73.0) + math.sin(self._time * 137.0)) / 2.0
        return 1.0 - self.flicker_intensity * (1.0 - (raw + 1.0) / 2.0)

    def _spark(self) -> float:
        """Occasional sharp orange burst riding on top of the arc."""
        return max(0.0, math.sin(self._time * 29.0) ** 8)

    def update(self, dt: float, state: GardenState) -> None:
        if not self.enabled:
            return
        self._time += dt

        # pipes_activity drives the arc→bloom crossfade
        self._target_blend = state.pipes_activity

        # combined captcha + flowerbeds activity drives how dramatic the effects are
        intensity = min(1.0, (state.captcha_intensity + state.flowerbeds_activity) / 2.0)
        self.flicker_intensity = self._base_flicker + intensity * (self._max_flicker - self._base_flicker)

        delta = self._target_blend - self.blend
        step = self.transition_speed * dt
        if abs(delta) <= step:
            self.blend = self._target_blend
        else:
            self.blend += step * (1.0 if delta > 0 else -1.0)

    def get_pixels(self) -> list[ChannelFrame]:
        empty: list[Color] = [(0, 0, 0, 0)] * self.led_count
        if not self.enabled:
            return [
                ChannelFrame(pin=self.arc_pin,   pixels=list(empty)),
                ChannelFrame(pin=self.bloom_pin, pixels=list(empty)),
            ]

        # Arc strip: base arc colour with flicker, occasional spark overlay
        arc_base  = scale_color(self._ARC_COLOR,   (1.0 - self.blend) * self._flicker())
        spark     = scale_color(self._SPARK_COLOR, (1.0 - self.blend) * self._spark())
        arc_color: Color = (
            min(255, arc_base[0] + spark[0]),
            min(255, arc_base[1] + spark[1]),
            min(255, arc_base[2] + spark[2]),
            min(255, arc_base[3] + spark[3]),
        )

        # Bloom strip: slow sinusoidal breathing
        bloom_pulse = (math.sin(self._time * 0.8) + 1.0) / 2.0
        bloom_color = scale_color(self._BLOOM_COLOR, self.blend * (0.7 + 0.3 * bloom_pulse))

        return [
            ChannelFrame(pin=self.arc_pin,   pixels=[arc_color]   * self.led_count),
            ChannelFrame(pin=self.bloom_pin, pixels=[bloom_color]  * self.led_count),
        ]

    def get_state(self) -> ControllableState:
        return ControllableState(
            name=self.name,
            enabled=self.enabled,
            params={
                "blend": round(self.blend, 3),
                "target_blend": round(self._target_blend, 3),
                "flicker_intensity": round(self.flicker_intensity, 3),
                "transition_speed": self.transition_speed,
                "arc_pin": self.arc_pin,
                "bloom_pin": self.bloom_pin,
                "led_count": self.led_count,
                "time": round(self._time, 2),
            },
        )
