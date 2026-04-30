"""
Coordinate-system helpers for the CommunityGarden show control.

World space (installation frame):
  X = Right
  Y = Forward (depth direction from the camera)
  Z = Up
  Units: centimetres

This is a right-handed system and aligns naturally with the Orbbec depth
camera's output axes (X=right, Y=down, Z=forward in camera space).

Camera space (Orbbec native output):
  X = Right
  Y = Down
  Z = Forward
  Units: metres

Rotation convention (Rotator):
  Pitch = rotation around X axis (right); positive = nose up
  Yaw   = rotation around Z axis (up);   positive = rotate from forward toward right
  Roll  = rotation around Y axis (forward)
  Application order: Roll first, then Pitch, then Yaw (intrinsic YXZ).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation


@dataclass
class Rotator:
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0


@dataclass
class Transform:
    translation: np.ndarray  # shape (3,), centimetres
    rotation: Rotator


def rotator_to_matrix(r: Rotator) -> np.ndarray:
    """Return a 3×3 rotation matrix for a Rotator."""
    # Intrinsic yxz: roll around Y, then pitch around body X, then yaw around body Z.
    # Yaw is negated because positive yaw (from +Y toward +X) is clockwise
    # when viewed from +Z, which is -R_Z in scipy's right-handed convention.
    rot = Rotation.from_euler("yxz", [r.roll, r.pitch, -r.yaw], degrees=True)
    return rot.as_matrix()


def transform_position(transform: Transform, point: np.ndarray) -> np.ndarray:
    """Apply a Transform to a point (no scale)."""
    m = rotator_to_matrix(transform.rotation)
    return m @ point + transform.translation


def look_yaw_degrees(from_pos: np.ndarray, to_pos: np.ndarray) -> float:
    """
    Return the yaw angle (degrees) that faces from_pos toward to_pos,
    ignoring elevation (projects onto the XY plane).

    Yaw = 0 means facing +Y (forward).
    Positive yaw rotates from +Y (forward) toward +X (right).
    """
    direction = to_pos - from_pos
    direction = direction.copy()
    direction[2] = 0.0  # project onto XY plane
    norm = float(np.linalg.norm(direction))
    if norm < 1e-6:
        return 0.0
    direction /= norm
    # atan2(X, Y): angle from +Y (forward) toward +X (right)
    return float(np.degrees(np.arctan2(direction[0], direction[1])))
