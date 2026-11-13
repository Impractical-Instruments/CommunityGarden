"""
Settings dataclasses for FlowerBeds: the shapes of `settings.json` and how they parse.

All positions are in world space (X=right, Y=forward, Z=up, centimetres).
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterator
from dataclasses import dataclass, field, fields as _dc_fields


def load_settings(path: str) -> dict:
    """Read a settings JSON file."""
    with open(path) as f:
        return json.load(f)


def _kwargs_from_dict(cls, raw: dict) -> dict:
    """Return a kwargs dict for cls, keeping only keys that match field names."""
    known = {f.name for f in _dc_fields(cls)}
    return {k: v for k, v in raw.items() if k in known}


@dataclass
class Attraction:
    """
    The policy that governs which visitor a FlowerCluster looks at.

    Each frame, every in-range blob receives a utility score:

        U = distance_weight * exp(-dist_cm / distance_falloff_cm)
          + dwell_weight    * (1 - exp(-dwell_frames / dwell_halflife_frames))
          + inertia_weight  * (1.0 if blob is the current target else 0.0)

    The blob with the highest total utility is selected as the look target.

    Tuning guide:
      - Raise distance_weight / lower distance_falloff_cm  → strongly prefer closer blobs.
      - Raise dwell_weight / lower dwell_halflife_frames   → faster warm-up to lingering visitors.
      - Raise inertia_weight                               → stickier tracking, less switching.
      - Set dwell_weight=0 and inertia_weight=0            → pure soft nearest-neighbour (legacy).
    """
    # Blobs farther than this are ignored entirely (hard gate).
    influence_radius_cm: float = 300.0
    # Distance score contribution.  Higher → closer blobs dominate more strongly.
    distance_weight: float = 1.0
    # Exponential falloff scale.  At this distance the distance score is ~37% of max.
    distance_falloff_cm: float = 150.0
    # Dwell score contribution.  Higher → flowers prefer visitors who linger.
    dwell_weight: float = 0.5
    # Frames for dwell score to reach ~63% of max (1 − 1/e).
    # At 10 fps a halflife of 30 ≈ 3 seconds.
    dwell_halflife_frames: int = 30
    # Inertia bonus for the currently-tracked blob.  Prevents jittery target-switching.
    inertia_weight: float = 0.3

    def score(self, dist_cm: float, dwell_frames: int, is_current_target: bool) -> float:
        """Compute the utility score for a single candidate blob."""
        distance_score = math.exp(-dist_cm / self.distance_falloff_cm)
        dwell_score = 1.0 - math.exp(-dwell_frames / self.dwell_halflife_frames)
        inertia_score = 1.0 if is_current_target else 0.0
        return (
            self.distance_weight * distance_score
            + self.dwell_weight * dwell_score
            + self.inertia_weight * inertia_score
        )

    @classmethod
    def from_dict(cls, raw: dict) -> "Attraction":
        return cls(**_kwargs_from_dict(cls, raw))


@dataclass
class ClusterConfig:
    motor_id: int = 0
    pos_offset_cm: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation_offset: dict = field(default_factory=lambda: {"pitch": 0, "yaw": 0, "roll": 0})
    yaw_limit_deg: float = 60.0  # symmetric ±cap on motor command (local frame)

    @classmethod
    def from_dict(cls, raw: dict) -> "ClusterConfig":
        if "motor_id" not in raw:
            raise ValueError(f"cluster config missing required 'motor_id': {raw}")
        return cls(**_kwargs_from_dict(cls, raw))


@dataclass
class ModuleConfig:
    registration_point_cm: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: dict = field(default_factory=lambda: {"pitch": 0, "yaw": 0, "roll": 0})
    clusters: list[ClusterConfig] = field(default_factory=list)
    name: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> "ModuleConfig":
        kwargs = _kwargs_from_dict(cls, raw)
        kwargs["clusters"] = [ClusterConfig.from_dict(c) for c in raw.get("clusters", [])]
        return cls(**kwargs)


@dataclass
class CoordinatorConfig:
    modules: list[ModuleConfig] = field(default_factory=list)
    attraction: Attraction = field(default_factory=Attraction)
    exclusion_radius_cm: float = 0.0

    @classmethod
    def from_dict(cls, raw: dict) -> "CoordinatorConfig":
        kwargs = _kwargs_from_dict(cls, raw)
        kwargs["modules"] = [ModuleConfig.from_dict(m) for m in raw.get("modules", [])]
        kwargs["attraction"] = Attraction.from_dict(raw.get("attraction", {}))
        # Accept legacy key name from older settings files
        if "exclusion_radius_cm" not in kwargs and "cluster_exclusion_radius_cm" in raw:
            kwargs["exclusion_radius_cm"] = raw["cluster_exclusion_radius_cm"]
        return cls(**kwargs)

    def all_clusters(self) -> Iterator[ClusterConfig]:
        """Every cluster of every module, in config order."""
        for module in self.modules:
            yield from module.clusters


@dataclass
class CameraConfig:
    name: str = ""
    pos_cm: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: dict = field(default_factory=lambda: {"pitch": 0, "yaw": 0, "roll": 0})
    width: int = 640
    height: int = 400
    framerate: int = 30
    # False = un-mirrored depth (correct for BlobDetector's pinhole unproject).
    # Set True only if the device delivers a non-mirrored image by default.
    mirror: bool = False

    @classmethod
    def from_dict(cls, raw: dict) -> "CameraConfig":
        return cls(**_kwargs_from_dict(cls, raw))
