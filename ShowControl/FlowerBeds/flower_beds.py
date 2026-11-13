"""
Core flower-bed logic: which visitor each cluster looks at, and the motor angle that follows.

All positions are in world space (X=right, Y=forward, Z=up, centimetres).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from config import Attraction, CoordinatorConfig, ModuleConfig
from IIVision.pipeline import filter_positions_near_points
from IIVision.transforms import Rotator, Transform, look_yaw_degrees, rotator_to_matrix

if TYPE_CHECKING:
    from IIVision.blob_stabilizer import TrackedBlob
    from state import ClusterState


# ---------------------------------------------------------------------------
# Motor command
# ---------------------------------------------------------------------------

@dataclass
class MotorCommand:
    motor_id: int
    rotation_deg: float  # software convention, CCW positive from above; ControllerBus.send flips it


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
        attraction: Attraction | None = None,
        yaw_limit_deg: float = 60.0,
        module_yaw_deg: float = 0.0,
        cluster_yaw_offset_deg: float = 0.0,
    ) -> None:
        self.motor_id = motor_id
        self.world_pos_cm = world_pos_cm.copy()
        self.yaw_limit_deg = float(yaw_limit_deg)
        self.module_yaw_deg = float(module_yaw_deg)
        self.cluster_yaw_offset_deg = float(cluster_yaw_offset_deg)
        # Direction the cluster is trying to look (world frame, unclamped).
        self.current_world_yaw_deg: float = 0.0
        # Angle commanded to the motor (local frame, clamped to ±yaw_limit_deg).
        self.current_motor_yaw_deg: float = 0.0
        self.has_target: bool = False
        self.clamped: bool = False
        self.attraction = attraction or Attraction()

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
            utility = cfg.score(
                dist_cm=dist_cm,
                dwell_frames=self._blob_dwell.get(bid, 0),
                is_current_target=(bid == self._current_target_id),
            )
            if utility > best_score:
                best_score = utility
                best_id = bid
                best_pos = pos

        self._current_target_id = best_id
        world_yaw = look_yaw_degrees(self.world_pos_cm, best_pos)
        # Transform world look direction into the motor's local frame: subtract
        # the module's yaw (cluster mounts rotate with the module) and wrap to
        # (-180, 180].
        local_yaw = world_yaw - self.module_yaw_deg - self.cluster_yaw_offset_deg
        local_yaw = ((local_yaw + 180.0) % 360.0) - 180.0
        motor_yaw = max(-self.yaw_limit_deg, min(self.yaw_limit_deg, local_yaw))
        self.current_world_yaw_deg = world_yaw
        self.current_motor_yaw_deg = motor_yaw
        self.clamped = motor_yaw != local_yaw
        self.has_target = True
        return MotorCommand(motor_id=self.motor_id, rotation_deg=motor_yaw)


# ---------------------------------------------------------------------------
# FlowerModule
# ---------------------------------------------------------------------------

class FlowerModule:
    """A physical module containing several clusters."""

    def __init__(self, config: ModuleConfig, attraction: Attraction) -> None:
        rot = Rotator(**config.rotation)
        self.transform = Transform(
            translation=np.array(config.registration_point_cm, dtype=float),
            rotation=rot,
        )
        rot_matrix = rotator_to_matrix(rot)
        module_yaw_deg = float(config.rotation.get("yaw", 0))

        self.clusters: list[FlowerCluster] = []
        for cc in config.clusters:
            offset = np.array(cc.pos_offset_cm, dtype=float)
            world_pos = rot_matrix @ offset + self.transform.translation
            self.clusters.append(
                FlowerCluster(
                    motor_id=cc.motor_id,
                    world_pos_cm=world_pos,
                    attraction=attraction,
                    yaw_limit_deg=cc.yaw_limit_deg,
                    module_yaw_deg=module_yaw_deg,
                    cluster_yaw_offset_deg=float(cc.rotation_offset.get("yaw", 0)),
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
        cluster_positions = self.cluster_world_positions()
        radius_cm = self._exclusion_radius_cm
        return lambda positions: filter_positions_near_points(positions, cluster_positions, radius_cm)

    def snapshot(self) -> list[ClusterState]:
        """Return a JSON-serialisable snapshot of all cluster states for the visualizer."""
        result: list[ClusterState] = []
        for module in self.modules:
            for cluster in module.clusters:
                result.append({
                    "motor_id": cluster.motor_id,
                    "x": float(cluster.world_pos_cm[0]),
                    "y": float(cluster.world_pos_cm[1]),
                    "world_yaw_deg": float(cluster.current_world_yaw_deg),
                    "motor_yaw_deg": float(cluster.current_motor_yaw_deg),
                    "clamped": bool(cluster.clamped),
                    "has_target": cluster.has_target,
                    "target_id": cluster._current_target_id,
                })
        return result
