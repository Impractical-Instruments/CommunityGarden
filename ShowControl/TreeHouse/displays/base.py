from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


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
        """Advance internal state by *dt* seconds and push to hardware."""

    @abstractmethod
    def get_state(self) -> DisplayState:
        """Return a serialisable snapshot (for logging / visualiser)."""
