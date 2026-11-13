"""
The per-frame state the visualizer displays: its shape, and its assembly from a frame's results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from IIVision.blob_stabilizer import TrackedBlob
    from config import CameraConfig


class BlobState(TypedDict):
    id: int
    x: float
    y: float


class ClusterState(TypedDict):
    motor_id: int
    x: float
    y: float
    world_yaw_deg: float       # real-world look direction (arrow points here)
    motor_yaw_deg: float       # commanded motor angle in local frame
    clamped: bool              # True when the yaw cap is fighting the target
    has_target: bool
    target_id: int | None


class CameraState(TypedDict):
    name: str
    x: float
    y: float
    yaw_deg: float


class VisualizerState(TypedDict):
    frame: int
    blobs: list[BlobState]
    clusters: list[ClusterState]
    cameras: list[CameraState]
    missing_motor_ids: list[int]


def build_visualizer_state(
    frame: int,
    tracked: list[TrackedBlob],
    clusters: list[ClusterState],
    cam_cfg: CameraConfig,
    missing_motor_ids: list[int],
) -> VisualizerState:
    """Assemble one frame's visualizer state (world-space centimetres)."""
    return {
        "frame": frame,
        "blobs": [
            {
                "id": t.stable_id,
                "x": float(t.world_pos_cm[0]),
                "y": float(t.world_pos_cm[1]),
            }
            for t in tracked
        ],
        "clusters": clusters,
        "cameras": [
            {
                "name": cam_cfg.name,
                "x": float(cam_cfg.pos_cm[0]),
                "y": float(cam_cfg.pos_cm[1]),
                "yaw_deg": float(cam_cfg.rotation.get("yaw", 0)),
            }
        ],
        "missing_motor_ids": missing_motor_ids,
    }
