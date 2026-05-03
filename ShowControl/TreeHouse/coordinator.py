import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from displays import (
    ChannelFrame,
    Color,
    Controllable,
    ControllableState,
    ForgeAndFloraConfig,
    ForgeAndFloraDisplay,
    GardenState,
    LEDConfig,
    LEDControllable,
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
class BranchMotorConfig:
    id: int
    min_pos: float = 0.0
    max_pos: float = 90.0
    recoil_pos: float = -20.0
    weight_flowerbeds: float = 0.6
    weight_captcha: float = 0.2
    weight_pipes: float = 0.2


@dataclass
class BranchConfig:
    port: str = "/dev/ttyACM1"
    baud: int = 115200
    motors: list[BranchMotorConfig] = None

    def __post_init__(self) -> None:
        if self.motors is None:
            self.motors = []


@dataclass
class OSCConfig:
    listen_port: int = 9001
    heartbeat_interval_s: float = 5.0


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
    branch: BranchConfig = None

    def __post_init__(self) -> None:
        if self.branch is None:
            self.branch = BranchConfig()


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

    network_path = Path(path).resolve().parent.parent / "network.json"
    network: dict = {}
    if network_path.exists():
        with open(network_path) as f:
            network = json.load(f)
    else:
        log.warning("network.json not found at %s", network_path)

    pico_raw = raw.get("pico", {})
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
        base_flicker_intensity=ff.get("base_flicker_intensity", 0.1),
        max_flicker_intensity=ff.get("max_flicker_intensity", 0.6),
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

    bc = raw.get("branch_controller", {})
    branch_motors = [
        BranchMotorConfig(
            id=m["id"],
            min_pos=m.get("min_pos", 0.0),
            max_pos=m.get("max_pos", 90.0),
            recoil_pos=m.get("recoil_pos", -20.0),
            weight_flowerbeds=m.get("weights", {}).get("flowerbeds", 0.6),
            weight_captcha=m.get("weights", {}).get("captcha", 0.2),
            weight_pipes=m.get("weights", {}).get("pipes", 0.2),
        )
        for m in bc.get("motors", [])
    ]
    branch = BranchConfig(
        port=bc.get("port", "/dev/ttyACM1"),
        baud=bc.get("baud", 115200),
        motors=branch_motors,
    )

    return TreehouseConfig(
        pico=PicoConfig(
            port=pico_raw.get("port", "/dev/ttyACM0"),
            baud=pico_raw.get("baud", 115200),
        ),
        osc=OSCConfig(
            listen_port=network.get("elements", {}).get("treehouse", {}).get("osc_port", 9001),
            heartbeat_interval_s=float(network.get("heartbeat_interval_s", 5.0)),
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
        branch=branch,
    )


# ---------------------------------------------------------------------------
# Display factory
# ---------------------------------------------------------------------------

def build_displays(config: TreehouseConfig) -> list[Controllable]:
    displays: list[Controllable] = []

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
    """Owns all Controllable instances, drives the frame loop, manages show state."""

    def __init__(
        self,
        displays: list[Controllable],
        branch_config: BranchConfig | None = None,
        heartbeat_interval_s: float = 5.0,
        _clock=None,
    ) -> None:
        self._displays: dict[str, Controllable] = {d.name: d for d in displays}
        self._led_displays: dict[str, LEDDisplay] = {
            d.name: d for d in displays if isinstance(d, LEDDisplay)
        }
        self._looking_glass: LookingGlassDisplay | None = next(
            (d for d in displays if isinstance(d, LookingGlassDisplay)), None
        )
        self._porch_lights: PorchLightsDisplay | None = next(
            (d for d in displays if isinstance(d, PorchLightsDisplay)), None
        )
        self.mode = ShowMode.FULL
        self._dim_level = 0.25
        self._captcha_blowup_pending = False
        self._flowerbeds_activity = 0.0
        self._captcha_intensity = 0.0
        self._pipes_activity = 0.0
        self._branch_motors: list[BranchMotorConfig] = (branch_config.motors if branch_config else [])
        self._branch_positions: list[tuple[int, float]] = []
        self._heartbeat_interval = heartbeat_interval_s
        self._clock = _clock or time.monotonic
        self._last_received: dict[str, float] = {}
        self._stale_warned: set[str] = set()

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
        display = self._led_displays.get(display_name)
        if display:
            display.set_pattern(pattern)
        else:
            log.warning("set_display_pattern: %r not found", display_name)

    def set_looking_glass_scene(self, scene: str) -> None:
        if self._looking_glass:
            self._looking_glass.set_scene(scene)

    def trigger_captcha_blowup(self) -> None:
        log.info("Captcha blowup signalled")
        self._captcha_blowup_pending = True
        self._touch("captcha")

    def set_flowerbeds_activity(self, value: float) -> None:
        self._flowerbeds_activity = max(0.0, min(1.0, value))
        self._touch("flowerbeds")

    def set_captcha_intensity(self, value: float) -> None:
        self._captcha_intensity = max(0.0, min(1.0, value))
        self._touch("captcha")

    def set_pipes_activity(self, value: float) -> None:
        self._pipes_activity = max(0.0, min(1.0, value))
        self._touch("pipes")

    def _touch(self, sender: str) -> None:
        self._last_received[sender] = self._clock()
        self._stale_warned.discard(sender)

    def reset_porch_lights(self) -> None:
        if self._porch_lights:
            self._porch_lights.reset()

    def get(self, name: str) -> Controllable:
        return self._displays[name]

    def _expire_stale_senders(self) -> None:
        now = self._clock()
        timeout = 2.0 * self._heartbeat_interval
        stale_values = {"flowerbeds": 0.0, "captcha": 0.0, "pipes": 0.0}
        for sender, last in self._last_received.items():
            if now - last > timeout:
                if sender not in self._stale_warned:
                    log.warning(
                        "No signal from %s for %.0fs — zeroing contribution",
                        sender, now - last,
                    )
                    self._stale_warned.add(sender)
                if sender in stale_values:
                    if sender == "flowerbeds":
                        self._flowerbeds_activity = 0.0
                    elif sender == "captcha":
                        self._captcha_intensity = 0.0
                    elif sender == "pipes":
                        self._pipes_activity = 0.0

    def update(self, dt: float) -> None:
        self._expire_stale_senders()
        state = GardenState(
            flowerbeds_activity=self._flowerbeds_activity,
            captcha_intensity=self._captcha_intensity,
            captcha_blowup=self._captcha_blowup_pending,
            pipes_activity=self._pipes_activity,
            show_mode=self.mode,
            brightness=self.brightness,
        )
        self._captcha_blowup_pending = False
        for controllable in self._displays.values():
            controllable.update(dt, state)
        self._update_branch_positions(state)

    def _update_branch_positions(self, state: GardenState) -> None:
        positions: list[tuple[int, float]] = []
        for motor in self._branch_motors:
            if state.captcha_blowup:
                pos = motor.recoil_pos
            else:
                signal = (
                    motor.weight_flowerbeds * state.flowerbeds_activity
                    + motor.weight_captcha * state.captcha_intensity
                    + motor.weight_pipes * state.pipes_activity
                )
                signal = max(0.0, min(1.0, signal))
                pos = motor.min_pos + signal * (motor.max_pos - motor.min_pos)
            positions.append((motor.id, pos))
        self._branch_positions = positions

    def get_branch_positions(self) -> list[tuple[int, float]]:
        """Return (motor_id, degrees) pairs for the current frame."""
        return list(self._branch_positions)

    def get_all_frames(self) -> list[ChannelFrame]:
        frames: list[ChannelFrame] = []
        for controllable in self._displays.values():
            if isinstance(controllable, LEDControllable):
                frames.extend(controllable.get_pixels())
        return frames

    def get_all_states(self) -> list[ControllableState]:
        return [d.get_state() for d in self._displays.values()]

    @property
    def display_names(self) -> list[str]:
        return list(self._displays.keys())
