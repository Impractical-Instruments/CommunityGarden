import logging
import math
from dataclasses import dataclass

from .base import Display, DisplayState

log = logging.getLogger("treehouse")

Color = tuple[int, int, int]


@dataclass
class ForgeAndFloraConfig:
    name: str = "Forge & Flora"
    # 0.0 = pure welding arc, 1.0 = pure magical gardening
    blend: float = 0.0
    transition_speed: float = 0.1  # blend units per second
    flicker_intensity: float = 0.3  # random intensity for the welding flicker


class ForgeAndFloraDisplay(Display):
    """
    LED effect window blending between two distinct visual states.

    Welding (blend=0.0)
    -------------------
    Harsh blue-white electric arc with high-frequency UV flicker and orange
    spatter sparks. Evokes a welder at work.

    Magical Gardening (blend=1.0)
    -----------------------------
    Soft bioluminescent bloom — warm green-gold pulses and slow colour washes.
    Evokes phosphorescent plants growing in the dark.

    The transition is a smooth EMA-driven lerp so intermediate values produce
    a coherent cross-fade rather than an abrupt switch.
    """

    _WELDING_BASE: Color = (180, 210, 255)    # cold blue-white arc
    _WELDING_SPARK: Color = (255, 140, 20)    # hot orange spatter
    _GARDENING_GLOW: Color = (60, 255, 100)   # bioluminescent green
    _GARDENING_BLOOM: Color = (200, 255, 80)  # warm gold-lime bloom

    def __init__(self, config: ForgeAndFloraConfig) -> None:
        super().__init__(config.name)
        self.blend = config.blend
        self.transition_speed = config.transition_speed
        self.flicker_intensity = config.flicker_intensity
        self._target_blend = config.blend
        self._time = 0.0

    # ------------------------------------------------------------------
    # Control interface
    # ------------------------------------------------------------------

    def set_mode(self, mode: str) -> None:
        """Snap target blend to a named mode."""
        modes = {"welding": 0.0, "gardening": 1.0}
        if mode not in modes:
            raise ValueError(f"Unknown mode {mode!r}; use {list(modes)}")
        log.info("Forge & Flora mode → %s", mode)
        self._target_blend = modes[mode]

    def set_blend(self, blend: float) -> None:
        """Set target blend directly (0.0–1.0)."""
        self._target_blend = max(0.0, min(1.0, blend))

    def set_transition_speed(self, speed: float) -> None:
        self.transition_speed = max(0.0, speed)

    # ------------------------------------------------------------------
    # Colour helpers
    # ------------------------------------------------------------------

    def _lerp_color(self, a: Color, b: Color, t: float) -> Color:
        return tuple(int(ca + (cb - ca) * t) for ca, cb in zip(a, b))  # type: ignore[return-value]

    def primary_color(self) -> Color:
        """Main output colour for the current blend position."""
        return self._lerp_color(self._WELDING_BASE, self._GARDENING_GLOW, self.blend)

    def accent_color(self) -> Color:
        """Accent / secondary colour for the current blend position."""
        return self._lerp_color(self._WELDING_SPARK, self._GARDENING_BLOOM, self.blend)

    def flicker_value(self) -> float:
        """
        Welding side: rapid high-frequency noise.
        Gardening side: slow sinusoidal breathing.
        Blended between the two so the character of light changes with the mode.
        """
        # Fast flicker present when in welding mode
        weld_flicker = (math.sin(self._time * 73.0) + math.sin(self._time * 137.0)) * 0.5
        # Slow breathe present when in gardening mode
        garden_breathe = math.sin(self._time * 0.8) * 0.5 + 0.5
        raw = weld_flicker * (1.0 - self.blend) + garden_breathe * self.blend
        return 1.0 - self.flicker_intensity * (1.0 - self.blend) + raw * self.flicker_intensity

    # ------------------------------------------------------------------
    # Display lifecycle
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if not self.enabled:
            return
        self._time += dt

        # Smooth blend toward target
        delta = self._target_blend - self.blend
        step = self.transition_speed * dt
        if abs(delta) <= step:
            self.blend = self._target_blend
        else:
            self.blend += step * (1.0 if delta > 0 else -1.0)

        # TODO: map primary_color(), accent_color(), flicker_value() to LED hardware
        # (e.g. two independently addressable LED channels via sACN/DMX or serial)

    def get_state(self) -> DisplayState:
        return DisplayState(
            name=self.name,
            enabled=self.enabled,
            params={
                "blend": round(self.blend, 3),
                "target_blend": round(self._target_blend, 3),
                "transition_speed": self.transition_speed,
                "primary_color": self.primary_color(),
                "accent_color": self.accent_color(),
                "flicker_value": round(self.flicker_value(), 3),
                "time": round(self._time, 2),
            },
        )
