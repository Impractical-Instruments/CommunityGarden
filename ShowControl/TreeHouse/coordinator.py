import json
import logging
from dataclasses import dataclass

from displays import (
    ChannelFrame,
    Color,
    Display,
    DisplayState,
    ForgeAndFloraConfig,
    ForgeAndFloraDisplay,
    LEDConfig,
    LEDDisplay,
    LookingGlassConfig,
    LookingGlassDisplay,
    PorchLightsConfig,
    PorchLightsDisplay,
    ShowMode,
)

log = logging.getLogger("treehouse")


# ---------------------------------------------------------------------------
# Config dataclasses — mirror settings.json structure
# ---------------------------------------------------------------------------

@dataclass
class PicoConfig:
    port: str = "/dev/ttyACM0"
    baud: int = 115200


@dataclass
class OSCConfig:
    listen_port: int = 9001


@dataclass
class ShowConfig:
    fps: int = 30
    dim_level: float = 0.25


@dataclass
class DioramaConfig:
    name: str
    pico_pin: int
    led_count: int
    brightness: float = 1.0
    color: Color = (0, 0, 0, 255)
    pattern: str = "solid"
    pulse_period: float = 20.0
    pulse_min: float = 0.5


@dataclass
class GableWindowConfig:
    name: str
    pico_pin: int
    led_count: int
    brightness: float = 1.0
    color: Color = (0, 0, 0, 255)
    pattern: str = "solid"


@dataclass
class DormerConfig:
    name: str
    pico_pin: int
    led_count: int
    brightness: float = 1.0
    color: Color = (0, 0, 0, 255)
    pattern: str = "solid"


@dataclass
class TreehouseConfig:
    pico: PicoConfig
    osc: OSCConfig
    show: ShowConfig
    dioramas: list[DioramaConfig]
    looking_glass: LookingGlassConfig
    forge_and_flora: ForgeAndFloraConfig
    gable_front: GableWindowConfig
    gable_back: GableWindowConfig
    dormer: DormerConfig
    porch_lights: PorchLightsConfig


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _color(raw: list[int]) -> Color:
    if len(raw) != 4:
        raise ValueError(f"Color must be [R, G, B, W], got {raw!r}")
    return (raw[0], raw[1], raw[2], raw[3])


def load_config(path: str) -> TreehouseConfig:
    with open(path) as f:
        raw = json.load(f)

    pico_raw = raw.get("pico", {})
    osc_raw  = raw.get("osc", {})
    show_raw = raw.get("show", {})

    dioramas = [
        DioramaConfig(
            name=d["name"],
            pico_pin=d["pico_pin"],
            led_count=d["led_count"],
            brightness=d.get("brightness", 1.0),
            color=_color(d.get("color", [0, 0, 0, 255])),
            pattern=d.get("pattern", "solid"),
            pulse_period=d.get("pulse_period", 20.0),
            pulse_min=d.get("pulse_min", 0.5),
        )
        for d in raw.get("dioramas", [])
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
        arc_pin=ff["arc_pin"],
        bloom_pin=ff["bloom_pin"],
        led_count=ff.get("led_count", 48),
        blend=ff.get("blend", 0.0),
        transition_speed=ff.get("transition_speed", 0.1),
        flicker_intensity=ff.get("flicker_intensity", 0.3),
    )

    gf = raw["gable_windows"]["front"]
    gable_front = GableWindowConfig(
        name=gf.get("name", "Front Gable"),
        pico_pin=gf["pico_pin"],
        led_count=gf["led_count"],
        brightness=gf.get("brightness", 1.0),
        color=_color(gf.get("color", [0, 0, 0, 255])),
        pattern=gf.get("pattern", "solid"),
    )

    gb = raw["gable_windows"]["back"]
    gable_back = GableWindowConfig(
        name=gb.get("name", "Back Gable"),
        pico_pin=gb["pico_pin"],
        led_count=gb["led_count"],
        brightness=gb.get("brightness", 1.0),
        color=_color(gb.get("color", [0, 0, 0, 255])),
        pattern=gb.get("pattern", "solid"),
    )

    dw = raw["dormer"]
    dormer = DormerConfig(
        name=dw.get("name", "Dormer"),
        pico_pin=dw["pico_pin"],
        led_count=dw["led_count"],
        brightness=dw.get("brightness", 1.0),
        color=_color(dw.get("color", [0, 0, 0, 255])),
        pattern=dw.get("pattern", "solid"),
    )

    pl = raw.get("porch_lights", {})
    porch_lights = PorchLightsConfig(
        name=pl.get("name", "Porch Lights"),
        pico_pin=pl.get("pico_pin", 8),
        led_count=pl.get("led_count", 2),
        blowup_duration=pl.get("blowup_duration", 3.0),
        aftermath_duration=pl.get("aftermath_duration", 10.0),
    )

    return TreehouseConfig(
        pico=PicoConfig(
            port=pico_raw.get("port", "/dev/ttyACM0"),
            baud=pico_raw.get("baud", 115200),
        ),
        osc=OSCConfig(
            listen_port=osc_raw.get("listen_port", 9001),
        ),
        show=ShowConfig(
            fps=show_raw.get("fps", 30),
            dim_level=show_raw.get("dim_level", 0.25),
        ),
        dioramas=dioramas,
        looking_glass=looking_glass,
        forge_and_flora=forge_and_flora,
        gable_front=gable_front,
        gable_back=gable_back,
        dormer=dormer,
        porch_lights=porch_lights,
    )


# ---------------------------------------------------------------------------
# Display factory
# ---------------------------------------------------------------------------

def build_displays(config: TreehouseConfig) -> list[Display]:
    displays: list[Display] = []

    for d in config.dioramas:
        displays.append(LEDDisplay(LEDConfig(
            name=d.name,
            pico_pin=d.pico_pin,
            led_count=d.led_count,
            brightness=d.brightness,
            color=d.color,
            pattern=d.pattern,
            pulse_period=d.pulse_period,
            pulse_min=d.pulse_min,
        )))

    displays.append(LookingGlassDisplay(config.looking_glass))
    displays.append(ForgeAndFloraDisplay(config.forge_and_flora))

    for gable in (config.gable_front, config.gable_back):
        displays.append(LEDDisplay(LEDConfig(
            name=gable.name,
            pico_pin=gable.pico_pin,
            led_count=gable.led_count,
            brightness=gable.brightness,
            color=gable.color,
            pattern=gable.pattern,
        )))

    displays.append(LEDDisplay(LEDConfig(
        name=config.dormer.name,
        pico_pin=config.dormer.pico_pin,
        led_count=config.dormer.led_count,
        brightness=config.dormer.brightness,
        color=config.dormer.color,
        pattern=config.dormer.pattern,
    )))

    displays.append(PorchLightsDisplay(config.porch_lights))

    return displays


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class Coordinator:
    """Owns all Display instances, drives the frame loop, manages show state."""

    def __init__(self, displays: list[Display]) -> None:
        self._displays: dict[str, Display] = {d.name: d for d in displays}
        self.mode = ShowMode.FULL
        self._dim_level = 0.25

    @property
    def brightness(self) -> float:
        if self.mode == ShowMode.OFF:
            return 0.0
        if self.mode == ShowMode.DIM:
            return self._dim_level
        return 1.0

    def set_mode(self, mode_str: str) -> None:
        try:
            self.mode = ShowMode(mode_str)
            log.info("Show mode → %s (brightness %.2f)", self.mode.value, self.brightness)
        except ValueError:
            log.warning("Unknown show mode %r; valid: %s", mode_str, [m.value for m in ShowMode])

    def set_dim_level(self, level: float) -> None:
        self._dim_level = max(0.0, min(1.0, level))
        log.info("Dim level → %.2f", self._dim_level)

    def set_display_pattern(self, display_name: str, pattern: str) -> None:
        display = self._displays.get(display_name)
        if isinstance(display, LEDDisplay):
            display.set_pattern(pattern)
        else:
            log.warning("set_display_pattern: %r not found or not an LEDDisplay", display_name)

    def set_looking_glass_scene(self, scene: str) -> None:
        display = self._displays.get("Looking Glass")
        if isinstance(display, LookingGlassDisplay):
            display.set_scene(scene)

    def set_forge_mode(self, mode: str) -> None:
        display = self._displays.get("Forge & Flora")
        if isinstance(display, ForgeAndFloraDisplay):
            display.set_mode(mode)

    def trigger_captcha_blowup(self) -> None:
        display = self._displays.get("Porch Lights")
        if isinstance(display, PorchLightsDisplay):
            display.trigger_blowup()

    def reset_porch_lights(self) -> None:
        display = self._displays.get("Porch Lights")
        if isinstance(display, PorchLightsDisplay):
            display.reset()

    def get(self, name: str) -> Display:
        return self._displays[name]

    def update(self, dt: float) -> None:
        for display in self._displays.values():
            display.update(dt)

    def get_all_frames(self) -> list[ChannelFrame]:
        frames: list[ChannelFrame] = []
        for display in self._displays.values():
            frames.extend(display.get_frames())
        return frames

    def get_all_states(self) -> list[DisplayState]:
        return [d.get_state() for d in self._displays.values()]

    @property
    def display_names(self) -> list[str]:
        return list(self._displays.keys())
