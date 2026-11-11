import json
import logging
import time
from dataclasses import dataclass

from OSCFabric import load_network_config_or_empty

from location_sender import LocationTarget
from controllables import (
    Controllable,
    ControllableState,
    GardenState,
    LookingGlassConfig,
    LookingGlassControllable,
    ShowMode,
)

log = logging.getLogger("treehouse")


# ---------------------------------------------------------------------------
# Config dataclasses — mirror settings.json structure
# ---------------------------------------------------------------------------

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
class LocationsConfig:
    """ESP32-S3 location controllers (ADR-0020). Addresses come from network.json."""
    targets: list = None
    send_hz: float = 20.0
    heartbeat_interval_s: float = 5.0
    change_epsilon: float = 0.01

    def __post_init__(self) -> None:
        if self.targets is None:
            self.targets = []


@dataclass
class ShowConfig:
    fps: int = 30
    dim_level: float = 0.25


@dataclass
class TreehouseConfig:
    osc: OSCConfig
    show: ShowConfig
    looking_glass: LookingGlassConfig
    branch: BranchConfig = None
    locations: LocationsConfig = None

    def __post_init__(self) -> None:
        if self.branch is None:
            self.branch = BranchConfig()
        if self.locations is None:
            self.locations = LocationsConfig()


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _load_locations(raw: dict, network: dict) -> LocationsConfig:
    """
    Resolves each named controller against network.json.

    settings.json names controllers; it never carries their addresses
    (AGENTS.md constraint #3).  A name with no matching firmware entry is
    skipped with a warning rather than raising — the other controllers should
    still come up.
    """
    firmware = network.get("firmware", {})
    targets: list[LocationTarget] = []

    for name in raw.get("controllers", []):
        entry = firmware.get(name)
        if not entry or not entry.get("ip") or not entry.get("osc_port"):
            log.warning("locations: no usable network.json firmware entry for %r", name)
            continue
        targets.append(LocationTarget(name=name, ip=entry["ip"], port=int(entry["osc_port"])))

    return LocationsConfig(
        targets=targets,
        send_hz=float(raw.get("send_hz", 20.0)),
        heartbeat_interval_s=float(network.get("heartbeat_interval_s", 5.0)),
        change_epsilon=float(network.get("change_epsilon", 0.01)),
    )


def load_config(path: str) -> TreehouseConfig:
    with open(path) as f:
        raw = json.load(f)

    network = load_network_config_or_empty(log)

    show_raw = raw.get("show", {})

    lg = raw.get("looking_glass", {})
    looking_glass = LookingGlassConfig(
        name=lg.get("name", "Looking Glass"),
        scene=lg.get("scene", "bloom"),
        speed=lg.get("speed", 1.0),
        renderer_port=lg.get("renderer_port", 9002),
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

    locations = _load_locations(raw.get("locations", {}), network)

    return TreehouseConfig(
        osc=OSCConfig(
            listen_port=network.get("elements", {}).get("treehouse", {}).get("osc_port", 9001),
            heartbeat_interval_s=float(network.get("heartbeat_interval_s", 5.0)),
        ),
        show=ShowConfig(
            fps=show_raw.get("fps", 30),
            dim_level=show_raw.get("dim_level", 0.25),
        ),
        looking_glass=looking_glass,
        branch=branch,
        locations=locations,
    )


# ---------------------------------------------------------------------------
# Controllable factory
# ---------------------------------------------------------------------------

def build_controllables(config: TreehouseConfig) -> list[Controllable]:
    """The Controllables the Pi drives itself. The LED locations are ESP32-S3
    controllers reached through LocationSender (ADR-0020), not Controllables."""
    return [LookingGlassControllable(config.looking_glass)]


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class Coordinator:
    """Owns all Controllable instances, drives the frame loop, manages show state."""

    def __init__(
        self,
        controllables: list[Controllable],
        branch_config: BranchConfig | None = None,
        heartbeat_interval_s: float = 5.0,
        _clock=None,
    ) -> None:
        self._controllables: dict[str, Controllable] = {c.name: c for c in controllables}
        self._looking_glass: LookingGlassControllable | None = next(
            (c for c in controllables if isinstance(c, LookingGlassControllable)), None
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
        self._last_state = GardenState()

    @property
    def garden_state(self) -> GardenState:
        """The GardenState the most recent update() ran on."""
        return self._last_state

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
        # Held for LocationSender, which reads it after update() returns and
        # needs to see the one-shot blowup flag this frame was built with.
        self._last_state = state
        for controllable in self._controllables.values():
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

    def get_all_states(self) -> list[ControllableState]:
        return [c.get_state() for c in self._controllables.values()]

    @property
    def controllable_names(self) -> list[str]:
        return list(self._controllables.keys())
