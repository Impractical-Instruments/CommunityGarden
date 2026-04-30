"""
Core flower-bed logic: cluster assignment and look-angle calculation.

All positions are in world space (X=right, Y=forward, Z=up, centimetres).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from IIVision.transforms import Rotator, Transform, look_yaw_degrees, rotator_to_matrix

if TYPE_CHECKING:
    from IIVision.blob_stabilizer import TrackedBlob


# ---------------------------------------------------------------------------
# Config types
# ---------------------------------------------------------------------------

@dataclass
class AttractionConfig:
    """
    Utility-based blob attraction weights for a FlowerCluster.

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


@dataclass
class ClusterConfig:
    motor_id: int = 0
    pos_offset_cm: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation_offset: dict = field(default_factory=lambda: {"pitch": 0, "yaw": 0, "roll": 0})


@dataclass
class ModuleConfig:
    registration_point_cm: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: dict = field(default_factory=lambda: {"pitch": 0, "yaw": 0, "roll": 0})
    clusters: list[ClusterConfig] = field(default_factory=list)


@dataclass
class CoordinatorConfig:
    modules: list[ModuleConfig] = field(default_factory=list)
    attraction: AttractionConfig = field(default_factory=AttractionConfig)
    exclusion_radius_cm: float = 0.0


@dataclass
class ControllerConfig:
    ip: str = "192.168.1.50"
    port: int = 9000


@dataclass
class CameraConfig:
    name: str = ""
    pos_cm: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: dict = field(default_factory=lambda: {"pitch": 0, "yaw": 0, "roll": 0})
    serial: str = ""
    width: int = 640
    height: int = 400
    framerate: int = 30


# ---------------------------------------------------------------------------
# Motor command
# ---------------------------------------------------------------------------

@dataclass
class MotorCommand:
    motor_id: int
    rotation_deg: float


# ---------------------------------------------------------------------------
# FlowerCluster
# ---------------------------------------------------------------------------

class FlowerCluster:
    """
    One servo cluster at a fixed world position.

    Each frame, scores every in-range blob with a utility function that weighs
    proximity, how long the visitor has been present, and continuity with the
    previous target.  The highest-scoring blob becomes the look target.
    """

    def __init__(
        self,
        motor_id: int,
        world_pos_cm: np.ndarray,
        attraction: AttractionConfig | None = None,
    ) -> None:
        self.motor_id = motor_id
        self.world_pos_cm = world_pos_cm.copy()
        self.current_yaw_deg: float = 0.0
        self.has_target: bool = False
        self.attraction = attraction or AttractionConfig()

        # Consecutive frames each blob has been within influence_radius_cm.
        self._blob_dwell: dict[int, int] = {}
        # stable_id of the blob targeted last frame (drives inertia bonus).
        self._current_target_id: int | None = None

    def update(self, blobs: list[TrackedBlob]) -> MotorCommand | None:
        """
        Score in-range blobs with the utility function and return a motor command
        for the best target.  Returns None when no blobs are in range.
        """
        cfg = self.attraction
        radius_sq = cfg.influence_radius_cm ** 2

        # Collect blobs that fall within the influence radius.
        in_range: list[tuple[int, np.ndarray, float]] = []  # (id, pos, dist_cm)
        for blob in blobs:
            diff = blob.world_pos_cm[:2] - self.world_pos_cm[:2]  # XY only — ignore height
            dist_sq = float(np.dot(diff, diff))
            if dist_sq <= radius_sq:
                in_range.append((blob.stable_id, blob.world_pos_cm, math.sqrt(dist_sq)))

        # Maintain dwell counters: increment blobs in range, evict those that left.
        in_range_ids = {bid for bid, _, _ in in_range}
        for bid in list(self._blob_dwell):
            if bid not in in_range_ids:
                del self._blob_dwell[bid]
        for bid, _, _ in in_range:
            self._blob_dwell[bid] = self._blob_dwell.get(bid, 0) + 1

        if not in_range:
            self.has_target = False
            self._current_target_id = None
            return None

        # Score every in-range blob and select the highest utility target.
        best_score = -1.0
        best_id: int | None = None
        best_pos: np.ndarray | None = None

        for bid, pos, dist_cm in in_range:
            distance_score = math.exp(-dist_cm / cfg.distance_falloff_cm)
            dwell_score = 1.0 - math.exp(
                -self._blob_dwell.get(bid, 0) / cfg.dwell_halflife_frames
            )
            inertia_score = 1.0 if bid == self._current_target_id else 0.0

            utility = (
                cfg.distance_weight * distance_score
                + cfg.dwell_weight * dwell_score
                + cfg.inertia_weight * inertia_score
            )

            if utility > best_score:
                best_score = utility
                best_id = bid
                best_pos = pos

        self._current_target_id = best_id
        yaw = look_yaw_degrees(self.world_pos_cm, best_pos)
        self.current_yaw_deg = yaw
        self.has_target = True
        return MotorCommand(motor_id=self.motor_id, rotation_deg=yaw)


# ---------------------------------------------------------------------------
# FlowerModule
# ---------------------------------------------------------------------------

class FlowerModule:
    """A physical module containing several clusters."""

    def __init__(self, config: ModuleConfig, attraction: AttractionConfig) -> None:
        rot = Rotator(**config.rotation)
        self.transform = Transform(
            translation=np.array(config.registration_point_cm, dtype=float),
            rotation=rot,
        )
        rot_matrix = rotator_to_matrix(rot)

        self.clusters: list[FlowerCluster] = []
        for cc in config.clusters:
            offset = np.array(cc.pos_offset_cm, dtype=float)
            world_pos = rot_matrix @ offset + self.transform.translation
            self.clusters.append(
                FlowerCluster(
                    motor_id=cc.motor_id,
                    world_pos_cm=world_pos,
                    attraction=attraction,
                )
            )

    def update(self, blobs: list[TrackedBlob]) -> list[MotorCommand]:
        commands: list[MotorCommand] = []
        for cluster in self.clusters:
            cmd = cluster.update(blobs)
            if cmd is not None:
                commands.append(cmd)
        return commands


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class Coordinator:
    """
    Top-level orchestrator.

    Usage:
        coordinator = Coordinator.from_config(coordinator_config)
        commands = coordinator.process_tracked_blobs(tracked)
        for cmd in commands:
            controller.send(cmd)
    """

    def __init__(self, modules: list[FlowerModule], exclusion_radius_cm: float = 0.0) -> None:
        self.modules = modules
        self._exclusion_radius_cm = exclusion_radius_cm

    @classmethod
    def from_config(cls, config: CoordinatorConfig) -> "Coordinator":
        modules = [FlowerModule(mc, config.attraction) for mc in config.modules]
        return cls(modules, config.exclusion_radius_cm)

    def process_tracked_blobs(
        self,
        blobs: list[TrackedBlob],
    ) -> list[MotorCommand]:
        """
        Dispatch stabilized, world-space TrackedBlob objects to all modules.

        This is the primary call path when using BlobStabilizer — blob IDs are
        stable across frames so dwell and inertia scores work correctly.
        """
        commands: list[MotorCommand] = []
        for module in self.modules:
            commands.extend(module.update(blobs))
        return commands

    def cluster_world_positions(self) -> list[np.ndarray]:
        """Return the world position of every cluster."""
        return [cluster.world_pos_cm for module in self.modules for cluster in module.clusters]

    def make_exclusion_filter(self) -> Callable[[list[np.ndarray]], list[np.ndarray]] | None:
        """
        Return a pre-stabilizer filter that suppresses blob positions too close
        to any physical cluster.  Returns None when no exclusion radius is set.
        """
        if self._exclusion_radius_cm <= 0:
            return None
        excl_sq = self._exclusion_radius_cm ** 2
        cluster_positions = self.cluster_world_positions()

        def _filter(positions: list[np.ndarray]) -> list[np.ndarray]:
            return [
                p for p in positions
                if not any(
                    float(np.dot(p[:2] - cp[:2], p[:2] - cp[:2])) < excl_sq
                    for cp in cluster_positions
                )
            ]

        return _filter

    def snapshot(self) -> list[dict]:
        """Return a JSON-serialisable snapshot of all cluster states for the visualizer."""
        result = []
        for module in self.modules:
            for cluster in module.clusters:
                result.append({
                    "motor_id": cluster.motor_id,
                    "x": float(cluster.world_pos_cm[0]),
                    "y": float(cluster.world_pos_cm[1]),
                    "yaw_deg": float(cluster.current_yaw_deg),
                    "has_target": cluster.has_target,
                    "target_id": cluster._current_target_id,
                })
        return result
