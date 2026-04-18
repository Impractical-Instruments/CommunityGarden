from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# SK6812 RGBW — four channels, each 0-255
Color = tuple[int, int, int, int]


class ShowMode(Enum):
    FULL = "full"
    DIM = "dim"
    OFF = "off"


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
class DisplayState:
    """Serialisable snapshot of one display's current state."""
    name: str
    enabled: bool
    params: dict[str, Any] = field(default_factory=dict)


class Display(ABC):
    """Abstract base for every controllable element in the TreeHouse."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.enabled = True

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance internal state by *dt* seconds."""

    @abstractmethod
    def get_frames(self) -> list[ChannelFrame]:
        """Return pixel data for all LED channels owned by this display.
        Returns an empty list for non-LED displays (e.g. HDMI video)."""

    @abstractmethod
    def get_state(self) -> DisplayState:
        """Return a serialisable snapshot for logging / visualiser."""
