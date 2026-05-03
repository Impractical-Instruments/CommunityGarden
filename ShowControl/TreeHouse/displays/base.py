from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# SK6812 RGBW — four channels, each 0-255
Color = tuple[int, int, int, int]


class ShowMode(Enum):
    ACTIVE = "active"
    DIM = "dim"
    INACTIVE = "inactive"


def scale_color(color: Color, factor: float) -> Color:
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
        max(0, min(255, int(color[3] * factor))),
    )


@dataclass
class ChannelFrame:
    """One LED strip's worth of pixel data bound to a specific Pico GPIO pin."""
    pin: int
    pixels: list[Color]


@dataclass
class GardenState:
    """Live signals from all Elements, assembled by the Coordinator each frame."""
    flowerbeds_activity: float = 0.0
    captcha_intensity: float = 0.0
    captcha_blowup: bool = False
    pipes_activity: float = 0.0
    show_mode: ShowMode = ShowMode.ACTIVE
    brightness: float = 1.0


@dataclass
class ControllableState:
    """Serialisable snapshot of one Controllable's current state."""
    name: str
    enabled: bool
    params: dict[str, Any] = field(default_factory=dict)


class Controllable(ABC):
    """Abstract base for every output in the TreeHouse."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.enabled = True

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    @abstractmethod
    def update(self, dt: float, state: GardenState) -> None:
        """Advance internal state by *dt* seconds given the current GardenState."""

    @abstractmethod
    def get_state(self) -> ControllableState:
        """Return a serialisable snapshot for logging / visualiser."""


class LEDControllable(Controllable):
    """Controllable subclass for anything that drives SK6812 RGBW LED strips via the Pico."""

    @abstractmethod
    def get_pixels(self) -> list[ChannelFrame]:
        """Return pixel data for all LED channels owned by this Controllable."""
