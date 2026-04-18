import json
import logging
from dataclasses import dataclass, field
from typing import Any

from displays import (
    Display,
    DisplayState,
    LEDDisplay,
    LEDConfig,
    LookingGlassDisplay,
    LookingGlassConfig,
    ForgeAndFloraDisplay,
    ForgeAndFloraConfig,
)

log = logging.getLogger("treehouse")


# ---------------------------------------------------------------------------
# Config dataclasses (mirror settings.json structure)
# ---------------------------------------------------------------------------

@dataclass
class DioramaConfig:
    name: str
    brightness: float = 1.0
    color: tuple[int, int, int] = (255, 255, 255)
    pattern: str = "solid"


@dataclass
class GableWindowConfig:
    name: str
    brightness: float = 1.0
    color: tuple[int, int, int] = (255, 255, 255)
    pattern: str = "solid"


@dataclass
class DormerConfig:
    name: str
    brightness: float = 1.0
    color: tuple[int, int, int] = (255, 255, 255)
    pattern: str = "solid"


@dataclass
class TreehouseConfig:
    dioramas: list[DioramaConfig]
    looking_glass: LookingGlassConfig
    forge_and_flora: ForgeAndFloraConfig
    gable_front: GableWindowConfig
    gable_back: GableWindowConfig
    dormer: DormerConfig


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(path: str) -> TreehouseConfig:
    with open(path) as f:
        raw = json.load(f)

    dioramas = [
        DioramaConfig(
            name=d["name"],
            brightness=d.get("brightness", 1.0),
            color=tuple(d.get("color", [255, 255, 255])),  # type: ignore[arg-type]
            pattern=d.get("pattern", "solid"),
        )
        for d in raw["dioramas"]
    ]

    lg = raw["garage_windows"]["looking_glass"]
    looking_glass = LookingGlassConfig(
        name=lg.get("name", "Looking Glass"),
        scene=lg.get("scene", "bloom"),
        speed=lg.get("speed", 1.0),
        mirror_depth=lg.get("mirror_depth", 6),
    )

    ff = raw["garage_windows"]["forge_and_flora"]
    forge_and_flora = ForgeAndFloraConfig(
        name=ff.get("name", "Forge & Flora"),
        blend=ff.get("blend", 0.0),
        transition_speed=ff.get("transition_speed", 0.1),
        flicker_intensity=ff.get("flicker_intensity", 0.3),
    )

    gf = raw["gable_windows"]["front"]
    gable_front = GableWindowConfig(
        name=gf.get("name", "Front Gable"),
        brightness=gf.get("brightness", 1.0),
        color=tuple(gf.get("color", [255, 255, 255])),  # type: ignore[arg-type]
        pattern=gf.get("pattern", "solid"),
    )

    gb = raw["gable_windows"]["back"]
    gable_back = GableWindowConfig(
        name=gb.get("name", "Back Gable"),
        brightness=gb.get("brightness", 1.0),
        color=tuple(gb.get("color", [255, 255, 255])),  # type: ignore[arg-type]
        pattern=gb.get("pattern", "solid"),
    )

    dw = raw["dormer"]
    dormer = DormerConfig(
        name=dw.get("name", "Dormer"),
        brightness=dw.get("brightness", 1.0),
        color=tuple(dw.get("color", [255, 255, 255])),  # type: ignore[arg-type]
        pattern=dw.get("pattern", "solid"),
    )

    return TreehouseConfig(
        dioramas=dioramas,
        looking_glass=looking_glass,
        forge_and_flora=forge_and_flora,
        gable_front=gable_front,
        gable_back=gable_back,
        dormer=dormer,
    )


# ---------------------------------------------------------------------------
# Display factory
# ---------------------------------------------------------------------------

def build_displays(config: TreehouseConfig) -> list[Display]:
    displays: list[Display] = []

    for d in config.dioramas:
        displays.append(LEDDisplay(LEDConfig(
            name=d.name,
            brightness=d.brightness,
            color=d.color,
            pattern=d.pattern,
        )))

    displays.append(LookingGlassDisplay(config.looking_glass))
    displays.append(ForgeAndFloraDisplay(config.forge_and_flora))

    for gable in (config.gable_front, config.gable_back):
        displays.append(LEDDisplay(LEDConfig(
            name=gable.name,
            brightness=gable.brightness,
            color=gable.color,
            pattern=gable.pattern,
        )))

    displays.append(LEDDisplay(LEDConfig(
        name=config.dormer.name,
        brightness=config.dormer.brightness,
        color=config.dormer.color,
        pattern=config.dormer.pattern,
    )))

    return displays


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class Coordinator:
    """Owns all Display instances and drives the per-frame update loop."""

    def __init__(self, displays: list[Display]) -> None:
        self._displays: dict[str, Display] = {d.name: d for d in displays}

    def get(self, name: str) -> Display:
        """Look up a display by name."""
        return self._displays[name]

    def update(self, dt: float) -> None:
        for display in self._displays.values():
            display.update(dt)

    def get_all_states(self) -> list[DisplayState]:
        return [d.get_state() for d in self._displays.values()]

    @property
    def display_names(self) -> list[str]:
        return list(self._displays.keys())
