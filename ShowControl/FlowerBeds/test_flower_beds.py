"""Tests for FlowerCluster yaw transform + per-cluster limit (ADR-style behavior)."""
from __future__ import annotations

import numpy as np
import pytest

from IIVision.blob_stabilizer import TrackedBlob

from flower_beds import (
    Attraction,
    ClusterConfig,
    Coordinator,
    CoordinatorConfig,
    FlowerCluster,
    ModuleConfig,
)


def _blob(stable_id: int, x: float, y: float) -> TrackedBlob:
    return TrackedBlob(stable_id=stable_id, world_pos_cm=np.array([x, y, 0.0]))


# ---------------------------------------------------------------------------
# Tracer: clamp splits motor_yaw (limited) from world_yaw (unclamped)
# ---------------------------------------------------------------------------

def test_world_yaw_unclamped_motor_yaw_clamped_at_default_limit():
    """Cluster facing forward (+Y). Blob 90° to the right in world frame.
    Default yaw_limit_deg=60 → motor clipped to +60° while world stays at +90°."""
    c = FlowerCluster(
        motor_id=1,
        world_pos_cm=np.array([0.0, 0.0, 0.0]),
        attraction=Attraction(),
    )
    cmd = c.update([_blob(1, 200.0, 0.0)])
    assert cmd is not None
    assert cmd.motor_id == 1
    assert cmd.rotation_deg == pytest.approx(60.0)
    assert c.current_motor_yaw_deg == pytest.approx(60.0)
    assert c.current_world_yaw_deg == pytest.approx(90.0)


def test_coordinator_from_config_passes_yaw_limit_and_module_yaw_into_cluster():
    """ClusterConfig.yaw_limit_deg + ModuleConfig.rotation.yaw + ClusterConfig.rotation_offset.yaw
    all reach the FlowerCluster so the clamp + transform apply at runtime."""
    cfg = CoordinatorConfig(
        modules=[
            ModuleConfig(
                registration_point_cm=[0.0, 0.0, 0.0],
                rotation={"pitch": 0, "yaw": 90, "roll": 0},
                clusters=[
                    ClusterConfig(
                        motor_id=7,
                        pos_offset_cm=[0.0, 0.0, 0.0],
                        rotation_offset={"pitch": 0, "yaw": 15, "roll": 0},
                        yaw_limit_deg=30.0,
                    ),
                ],
            ),
        ],
        attraction=Attraction(),
    )
    coord = Coordinator.from_config(cfg)
    cluster = coord.modules[0].clusters[0]
    assert cluster.yaw_limit_deg == pytest.approx(30.0)
    assert cluster.module_yaw_deg == pytest.approx(90.0)
    assert cluster.cluster_yaw_offset_deg == pytest.approx(15.0)

    # Blob directly to the right (world yaw 90°): motor_yaw = 90 − 90 − 15 = −15 (under cap).
    cmd = cluster.update([_blob(1, 200.0, 0.0)])
    assert cmd is not None
    assert cluster.current_world_yaw_deg == pytest.approx(90.0)
    assert cluster.current_motor_yaw_deg == pytest.approx(-15.0)


def test_snapshot_exposes_world_motor_and_clamped_state():
    """Coordinator snapshot must expose world_yaw_deg, motor_yaw_deg, clamped
    so the visualizer can draw look direction independently of motor command."""
    cfg = CoordinatorConfig(
        modules=[
            ModuleConfig(
                clusters=[
                    ClusterConfig(motor_id=1, pos_offset_cm=[0.0, 0.0, 0.0], yaw_limit_deg=30.0),
                    ClusterConfig(motor_id=2, pos_offset_cm=[0.0, 0.0, 0.0], yaw_limit_deg=120.0),
                ],
            ),
        ],
        attraction=Attraction(),
    )
    coord = Coordinator.from_config(cfg)
    # Blob 90° to the right of both clusters (which share position).
    coord.process_tracked_blobs([_blob(1, 200.0, 0.0)])
    snap = coord.snapshot()
    assert len(snap) == 2
    # Cluster with 30° limit — gets clamped from world 90°.
    s1 = snap[0]
    assert s1["motor_id"] == 1
    assert s1["world_yaw_deg"] == pytest.approx(90.0)
    assert s1["motor_yaw_deg"] == pytest.approx(30.0)
    assert s1["clamped"] is True
    # Cluster with 120° limit — never reaches cap, motor_yaw == world_yaw.
    s2 = snap[1]
    assert s2["motor_id"] == 2
    assert s2["world_yaw_deg"] == pytest.approx(90.0)
    assert s2["motor_yaw_deg"] == pytest.approx(90.0)
    assert s2["clamped"] is False


def test_cluster_yaw_offset_composes_with_module_yaw():
    """A cluster mounted with an additional 45° yaw offset on an unrotated module.
    Blob at 45° world yaw should yield motor_yaw=0 (45 − 0 − 45)."""
    c = FlowerCluster(
        motor_id=1,
        world_pos_cm=np.array([0.0, 0.0, 0.0]),
        attraction=Attraction(),
        module_yaw_deg=0.0,
        cluster_yaw_offset_deg=45.0,
    )
    # Blob in the direction (sin45, cos45) ≈ (70.7, 70.7) lies at world yaw 45°.
    cmd = c.update([_blob(1, 70.7, 70.7)])
    assert cmd is not None
    assert c.current_world_yaw_deg == pytest.approx(45.0, abs=0.1)
    assert c.current_motor_yaw_deg == pytest.approx(0.0, abs=0.1)


def test_module_yaw_180_subtracts_from_world_yaw():
    """Cluster on a module rotated 180°. A blob at world (0, -100) sits 'in front of'
    the cluster's physical orientation, so the motor should command 0°.
    World yaw to that blob is 180°; motor yaw = 180° − 180° (module) = 0°."""
    c = FlowerCluster(
        motor_id=1,
        world_pos_cm=np.array([0.0, 0.0, 0.0]),
        attraction=Attraction(),
        module_yaw_deg=180.0,
    )
    cmd = c.update([_blob(1, 0.0, -100.0)])
    assert cmd is not None
    assert c.current_world_yaw_deg == pytest.approx(180.0)
    assert c.current_motor_yaw_deg == pytest.approx(0.0)
    assert cmd.rotation_deg == pytest.approx(0.0)
