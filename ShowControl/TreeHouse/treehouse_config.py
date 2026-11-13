"""Loads settings.json and network.json into the typed config the TreeHouse runs on."""

import json
import logging
from dataclasses import dataclass

from OSCFabric import load_network_config_or_empty

from location_sender import LocationTarget
from controllables import LookingGlassConfig

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

    @classmethod
    def from_dict(cls, raw: dict) -> "BranchMotorConfig":
        weights = raw.get("weights", {})
        return cls(
            id=raw["id"],
            min_pos=raw.get("min_pos", 0.0),
            max_pos=raw.get("max_pos", 90.0),
            recoil_pos=raw.get("recoil_pos", -20.0),
            weight_flowerbeds=weights.get("flowerbeds", 0.6),
            weight_captcha=weights.get("captcha", 0.2),
            weight_pipes=weights.get("pipes", 0.2),
        )


@dataclass
class BranchConfig:
    port: str = "/dev/ttyACM1"
    baud: int = 115200
    motors: list[BranchMotorConfig] = None

    def __post_init__(self) -> None:
        if self.motors is None:
            self.motors = []

    @classmethod
    def from_dict(cls, raw: dict) -> "BranchConfig":
        return cls(
            port=raw.get("port", "/dev/ttyACM1"),
            baud=raw.get("baud", 115200),
            motors=[BranchMotorConfig.from_dict(m) for m in raw.get("motors", [])],
        )


@dataclass
class OSCConfig:
    listen_port: int = 9001
    heartbeat_interval_s: float = 5.0

    @classmethod
    def from_network(cls, network: dict) -> "OSCConfig":
        """Both fields come from network.json (AGENTS.md constraint #3)."""
        return cls(
            listen_port=network.get("elements", {}).get("treehouse", {}).get("osc_port", 9001),
            heartbeat_interval_s=float(network.get("heartbeat_interval_s", 5.0)),
        )


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

    @classmethod
    def from_dict(cls, raw: dict, network: dict) -> "LocationsConfig":
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

        return cls(
            targets=targets,
            send_hz=float(raw.get("send_hz", 20.0)),
            heartbeat_interval_s=float(network.get("heartbeat_interval_s", 5.0)),
            change_epsilon=float(network.get("change_epsilon", 0.01)),
        )


@dataclass
class ShowConfig:
    fps: int = 30
    dim_level: float = 0.25

    @classmethod
    def from_dict(cls, raw: dict) -> "ShowConfig":
        return cls(fps=raw.get("fps", 30), dim_level=raw.get("dim_level", 0.25))


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

    @classmethod
    def from_dict(cls, raw: dict, network: dict) -> "TreehouseConfig":
        lg = raw.get("looking_glass", {})
        return cls(
            osc=OSCConfig.from_network(network),
            show=ShowConfig.from_dict(raw.get("show", {})),
            looking_glass=LookingGlassConfig(
                name=lg.get("name", "Looking Glass"),
                scene=lg.get("scene", "bloom"),
                speed=lg.get("speed", 1.0),
                renderer_port=lg.get("renderer_port", 9002),
            ),
            branch=BranchConfig.from_dict(raw.get("branch_controller", {})),
            locations=LocationsConfig.from_dict(raw.get("locations", {}), network),
        )


def load_config(path: str) -> TreehouseConfig:
    with open(path) as f:
        raw = json.load(f)
    return TreehouseConfig.from_dict(raw, load_network_config_or_empty(log))
