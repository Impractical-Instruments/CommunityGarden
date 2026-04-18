import logging
from dataclasses import dataclass, field

from .base import Display, DisplayState

log = logging.getLogger("treehouse")

Color = tuple[int, int, int]  # RGB 0–255


@dataclass
class LEDConfig:
    name: str
    brightness: float = 1.0
    color: Color = (255, 255, 255)
    pattern: str = "solid"


class LEDDisplay(Display):
    """
    Generic LED panel — used for diorama boxes, gable windows, and the dormer.

    Patterns
    --------
    solid   – static colour at set brightness
    breathe – sinusoidal fade in/out
    strobe  – rapid on/off flash
    chase   – sweeping pixel movement (hardware-dependent)
    """

    PATTERNS = ("solid", "breathe", "strobe", "chase")

    def __init__(self, config: LEDConfig) -> None:
        super().__init__(config.name)
        self.brightness = config.brightness
        self.color: Color = config.color
        self.pattern = config.pattern
        self._time = 0.0

    # ------------------------------------------------------------------
    # Control interface
    # ------------------------------------------------------------------

    def set_color(self, color: Color) -> None:
        self.color = color

    def set_brightness(self, brightness: float) -> None:
        self.brightness = max(0.0, min(1.0, brightness))

    def set_pattern(self, pattern: str) -> None:
        if pattern not in self.PATTERNS:
            raise ValueError(f"Unknown pattern {pattern!r}; choices: {self.PATTERNS}")
        self.pattern = pattern

    # ------------------------------------------------------------------
    # Display lifecycle
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if not self.enabled:
            return
        self._time += dt
        # TODO: compute effective brightness from pattern and push to hardware
        # (e.g. via sACN/DMX, serial, or OSC)

    def get_state(self) -> DisplayState:
        return DisplayState(
            name=self.name,
            enabled=self.enabled,
            params={
                "color": self.color,
                "brightness": round(self.brightness, 3),
                "pattern": self.pattern,
                "time": round(self._time, 2),
            },
        )
