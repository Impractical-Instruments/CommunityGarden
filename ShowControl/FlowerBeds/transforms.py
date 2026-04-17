"""
Minimal UE coordinate-system helpers.

UE world space:
  X = Forward
  Y = Right
  Z = Up
  Units: centimetres

Rotation convention (FRotator):
  Pitch = rotation around Y axis
  Yaw   = rotation around Z axis
  Roll  = rotation around X axis
  Application order: Roll first, then Pitch, then Yaw (intrinsic XYZ).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation


@dataclass
class UERotator:
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0


@dataclass
class UETransform:
    translation: np.ndarray  # shape (3,), centimetres
    rotation: UERotator


def rotator_to_matrix(r: UERotator) -> np.ndarray:
    """Return a 3×3 rotation matrix for a UE FRotator."""
    # Intrinsic XYZ ≡ extrinsic ZYX.
    # UE pitch is left-handed (positive = nose up rotates +X toward +Z), which
    # is the opposite sense to scipy's right-handed R_y, so pitch is negated.
    rot = Rotation.from_euler("XYZ", [r.roll, -r.pitch, r.yaw], degrees=True)
    return rot.as_matrix()


def transform_position(transform: UETransform, point: np.ndarray) -> np.ndarray:
    """Apply a UE transform to a point (no scale)."""
    m = rotator_to_matrix(transform.rotation)
    return m @ point + transform.translation


def look_yaw_degrees(from_pos: np.ndarray, to_pos: np.ndarray) -> float:
    """
    Return the yaw angle (degrees) that faces from_pos toward to_pos,
    ignoring elevation (projects onto the XY plane).

    Matches FBlobTracker::GetLookRotation / FlowerCluster::UpdateClusterTargets.
    """
    direction = to_pos - from_pos
    direction = direction.copy()
    direction[2] = 0.0  # project onto XY plane
    norm = float(np.linalg.norm(direction))
    if norm < 1e-6:
        return 0.0
    direction /= norm
    # UE yaw: atan2(Y, X)  (rotation from X-forward toward Y-right)
    return float(np.degrees(np.arctan2(direction[1], direction[0])))
