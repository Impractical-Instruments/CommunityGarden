"""
Core flower-bed logic: cluster assignment and look-angle calculation.

Mirrors the C++ classes:
  AFlowerCluster  → FlowerCluster
  AFlowerModule   → FlowerModule
  (coordinator loop lives in main.py / Coordinator)

All positions are in UE world space (X=forward, Y=right, Z=up, centimetres).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from transforms import UERotator, UETransform, look_yaw_degrees, rotator_to_matrix


# ---------------------------------------------------------------------------
# Config types  (mirror FFlowerClusterConfig / FFlowerModuleConfig /
#                FFlowerControllerConfig from FlowerBedSettings.h)
# ---------------------------------------------------------------------------

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
    """One servo cluster at a fixed world position, rotates to face the nearest blob."""

    def __init__(self, motor_id: int, world_pos_cm: np.ndarray) -> None:
        self.motor_id = motor_id
        self.world_pos_cm = world_pos_cm.copy()
        self.current_yaw_deg: float = 0.0
        self.has_target: bool = False

    def update(self, blob_world_positions: list[np.ndarray]) -> MotorCommand | None:
        """
        Find the nearest blob and return the motor command needed to face it.
        Returns None if there are no blobs.

        Mirrors AFlowerCluster::UpdateClusterTargets.
        """
        if not blob_world_positions:
            self.has_target = False
            return None

        best_dist_sq = float("inf")
        best_pos: np.ndarray | None = None

        for pos in blob_world_positions:
            diff = pos - self.world_pos_cm
            dist_sq = float(np.dot(diff, diff))
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_pos = pos

        yaw = look_yaw_degrees(self.world_pos_cm, best_pos)
        self.current_yaw_deg = yaw
        self.has_target = True
        return MotorCommand(motor_id=self.motor_id, rotation_deg=yaw)


# ---------------------------------------------------------------------------
# FlowerModule
# ---------------------------------------------------------------------------

class FlowerModule:
    """
    A physical module containing several clusters.

    Mirrors AFlowerModule::Init + UpdateClusterTargets.
    """

    def __init__(self, config: ModuleConfig) -> None:
        rot = UERotator(**config.rotation)
        self.transform = UETransform(
            translation=np.array(config.registration_point_cm, dtype=float),
            rotation=rot,
        )
        rot_matrix = rotator_to_matrix(rot)

        self.clusters: list[FlowerCluster] = []
        for cc in config.clusters:
            offset = np.array(cc.pos_offset_cm, dtype=float)
            world_pos = rot_matrix @ offset + self.transform.translation
            self.clusters.append(FlowerCluster(motor_id=cc.motor_id, world_pos_cm=world_pos))

    def update(self, blob_world_positions: list[np.ndarray]) -> list[MotorCommand]:
        commands: list[MotorCommand] = []
        for cluster in self.clusters:
            cmd = cluster.update(blob_world_positions)
            if cmd is not None:
                commands.append(cmd)
        return commands


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class Coordinator:
    """
    Top-level orchestrator.  Mirrors AFlowerBedCoordinator::OnBlobDetectionResult.

    Usage:
        coordinator = Coordinator.from_config(settings)
        commands = coordinator.process_blobs(camera_transform, blobs_3d)
        for cmd in commands:
            controller.send(cmd)
    """

    def __init__(self, modules: list[FlowerModule]) -> None:
        self.modules = modules

    @classmethod
    def from_config(cls, module_configs: list[ModuleConfig]) -> "Coordinator":
        return cls([FlowerModule(mc) for mc in module_configs])

    def process_blobs(
        self,
        camera_transform: UETransform,
        blobs_3d: list,  # list[blob_tracker.Blob3D]
    ) -> list[MotorCommand]:
        """
        Transform blobs from camera-local UE space to world space, then
        dispatch to all modules.
        """
        from transforms import transform_position

        world_positions = [
            transform_position(camera_transform, blob.world_pos_cm())
            for blob in blobs_3d
        ]
        return self.process_world_positions(world_positions)

    def process_world_positions(
        self,
        world_positions: list[np.ndarray],
    ) -> list[MotorCommand]:
        """
        Dispatch pre-transformed world-space positions to all modules.

        Use this instead of process_blobs when positions have already been
        transformed (e.g. after running through BlobStabilizer).
        """
        commands: list[MotorCommand] = []
        for module in self.modules:
            commands.extend(module.update(world_positions))
        return commands

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
                })
        return result
