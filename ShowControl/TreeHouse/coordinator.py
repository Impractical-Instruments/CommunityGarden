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
    GPIOFrame,
    LEDConfig,
    LEDControllable,
    LEDDisplay,
    LookingGlassConfig,
    LookingGlassDisplay,
    PWMConfig,
    PWMControllable,
    PWMDisplay,
    PWMFrame,
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
class PWMDisplayConfig:
    name: str
    pico_pin: int
    pico_id: str = "dioramas"
    min_value: int = 8000
    max_value: int = 65535
    pulse_period: float = 8.0
    signal_weight_captcha: float = 0.0
    signal_weight_flowerbeds: float = 0.5
    signal_weight_pipes: float = 0.5


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
    pico_id: str = "dioramas"
    brightness: float = 1.0
    color: Color = (0, 0, 0, 255)
    pattern: str = "solid"
    pulse_period: float = 20.0
    pulse_min: float = 0.5
    transistor_pin: int = -1
    transistor_pico_id: str = "dioramas"
    transistor_threshold: float = 0.6


@dataclass
class TreehouseConfig:
    pico_dioramas: PicoConfig
    pico_structure: PicoConfig
    osc: OSCConfig
    show: ShowConfig
    dioramas: list[DioramaConfig]
    pwm_displays: list[PWMDisplayConfig]
    looking_glass: LookingGlassConfig
    forge_and_flora: ForgeAndFloraConfig
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

    show_raw = raw.get("show", {})

    pd_raw = raw.get("pico_dioramas", {})
    ps_raw = raw.get("pico_structure", {})

    dioramas = [
        DioramaConfig(
            name=d["name"],
            pico_pin=d["pico_pin"],
            led_count=d["led_count"],
            pico_id=d.get("pico_id", "dioramas"),
            brightness=d.get("brightness", 1.0),
            color=_color(d.get("color", [0, 0, 0, 255])),
            pattern=d.get("pattern", "solid"),
            pulse_period=d.get("pulse_period", 20.0),
            pulse_min=d.get("pulse_min", 0.5),
            transistor_pin=d.get("transistor_pin", -1),
            transistor_pico_id=d.get("transistor_pico_id", "dioramas"),
            transistor_threshold=d.get("transistor_threshold", 0.6),
        )
        for d in raw.get("dioramas", [])
    ]

    pwm_displays = [
        PWMDisplayConfig(
            name=p["name"],
            pico_pin=p["pico_pin"],
            pico_id=p.get("pico_id", "dioramas"),
            min_value=p.get("min_value", 8000),
            max_value=p.get("max_value", 65535),
            pulse_period=p.get("pulse_period", 8.0),
            signal_weight_captcha=p.get("signal_weight_captcha", 0.0),
            signal_weight_flowerbeds=p.get("signal_weight_flowerbeds", 0.5),
            signal_weight_pipes=p.get("signal_weight_pipes", 0.5),
        )
        for p in raw.get("pwm_displays", [])
    ]

    lg = raw["garage_windows"]["looking_glass"]
    looking_glass = LookingGlassConfig(
        name=lg.get("name", "Looking Glass"),
        scene=lg.get("scene", "bloom"),
        speed=lg.get("speed", 1.0),
        mirror_depth=lg.get("mirror_depth", 6),
        renderer_port=lg.get("renderer_port", 9002),
    )

    ff = raw["garage_windows"]["forge_and_flora"]
    forge_and_flora = ForgeAndFloraConfig(
        name=ff.get("name", "Forge & Flora"),
        arc_pin=ff["arc_pin"],
        bloom_pin=ff["bloom_pin"],
        led_count=ff.get("led_count", 20),
        blend=ff.get("blend", 0.0),
        transition_speed=ff.get("transition_speed", 0.1),
        base_flicker_intensity=ff.get("base_flicker_intensity", 0.1),
        max_flicker_intensity=ff.get("max_flicker_intensity", 0.6),
        arc_flash_pin=ff.get("arc_flash_pin", -1),
        arc_flash_pico_id=ff.get("arc_flash_pico_id", "dioramas"),
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
        pico_dioramas=PicoConfig(
            port=pd_raw.get("port", "/dev/treehouse-pico-a"),
            baud=pd_raw.get("baud", 115200),
        ),
        pico_structure=PicoConfig(
            port=ps_raw.get("port", "/dev/treehouse-pico-b"),
            baud=ps_raw.get("baud", 115200),
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
        pwm_displays=pwm_displays,
        looking_glass=looking_glass,
        forge_and_flora=forge_and_flora,
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
            pico_id=d.pico_id,
            brightness=d.brightness,
            color=d.color,
            pattern=d.pattern,
            pulse_period=d.pulse_period,
            pulse_min=d.pulse_min,
            transistor_pin=d.transistor_pin,
            transistor_pico_id=d.transistor_pico_id,
            transistor_threshold=d.transistor_threshold,
        )))

    for p in config.pwm_displays:
        displays.append(PWMDisplay(PWMConfig(
            name=p.name,
            pico_pin=p.pico_pin,
            pico_id=p.pico_id,
            min_value=p.min_value,
            max_value=p.max_value,
            pulse_period=p.pulse_period,
            signal_weight_captcha=p.signal_weight_captcha,
            signal_weight_flowerbeds=p.signal_weight_flowerbeds,
            signal_weight_pipes=p.signal_weight_pipes,
        )))

    displays.append(LookingGlassDisplay(config.looking_glass))
    displays.append(ForgeAndFloraDisplay(config.forge_and_flora))

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

        self.mode = ShowMode.ACTIVE
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
        if self.mode == ShowMode.INACTIVE:
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

    def get_all_pwm_frames(self) -> list[PWMFrame]:
        frames: list[PWMFrame] = []
        for controllable in self._displays.values():
            if isinstance(controllable, PWMControllable):
                frames.extend(controllable.get_pwm_frames())
        return frames

    def get_all_gpio_frames(self) -> list[GPIOFrame]:
        frames: list[GPIOFrame] = []
        for controllable in self._displays.values():
            if hasattr(controllable, "get_gpio_frames"):
                frames.extend(controllable.get_gpio_frames())
        return frames

    def get_all_states(self) -> list[ControllableState]:
        return [d.get_state() for d in self._displays.values()]

    @property
    def display_names(self) -> list[str]:
        return list(self._displays.keys())
