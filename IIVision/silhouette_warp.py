"""
Reproject a foreground silhouette from physical camera space to a virtual
camera at world origin looking along +Y (screen normal, Z-up).

Used to make the silhouette appear as if the camera were at the projector
screen centre rather than its physical mount position.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import grey_dilation

from .blob_tracker import CameraIntrinsics
from .transforms import Transform, rotator_to_matrix


def reproject_silhouette(
    fg: np.ndarray,
    intrinsics: CameraIntrinsics,
    cam_transform: Transform,
    dilation_px: int = 3,
) -> np.ndarray:
    """
    fg: uint16 (H, W) — foreground pixels = depth_mm, background = 0.
    cam_transform: camera pose in world space (translation in cm).

    Returns uint16 (H, W) in virtual-camera space. Virtual camera is at world
    origin [0,0,0] looking in +Y (screen normal), X=right, Z=up.

    Preserves original depth_mm values so slab ranges stay valid.
    """
    H, W = fg.shape
    R = rotator_to_matrix(cam_transform.rotation)
    t = cam_transform.translation          # (3,) cm

    fx, fy = intrinsics.fx, intrinsics.fy
    cx, cy = intrinsics.cx, intrinsics.cy

    ys, xs = np.nonzero(fg)
    if ys.size == 0:
        return np.zeros_like(fg)

    depths = fg[ys, xs].astype(np.float64)  # mm

    # Unproject to Orbbec camera space (mm): X=right, Y=down, Z=forward
    cam_X = (xs - cx) / fx * depths
    cam_Y = (ys - cy) / fy * depths
    cam_Z = depths

    # Axis-swap to world space (cm): X=right, Y=forward, Z=up
    world_base = np.stack([
        cam_X * 0.1,    # mm→cm, right→right
        cam_Z * 0.1,    # mm→cm, forward→forward
        -cam_Y * 0.1,   # mm→cm, up = -down
    ])  # (3, N)

    # Apply camera rotation and translation
    world_pts = R @ world_base + t[:, np.newaxis]  # (3, N)

    # Project onto virtual camera: at [0,0,0], looking +Y, up=+Z
    #   u = cx + fx * (world_X / world_Y)
    #   v = cy - fy * (world_Z / world_Y)   (Z=up → v decreases upward)
    world_Y = world_pts[1]
    valid = world_Y > 0

    safe_Y = np.where(valid, world_Y, 1.0)
    u_out = np.round(cx + fx * world_pts[0] / safe_Y).astype(np.int32)
    v_out = np.round(cy - fy * world_pts[2] / safe_Y).astype(np.int32)

    in_frame = valid & (u_out >= 0) & (u_out < W) & (v_out >= 0) & (v_out < H)

    out = np.zeros((H, W), dtype=np.uint16)
    out[v_out[in_frame], u_out[in_frame]] = depths[in_frame].astype(np.uint16)

    if dilation_px > 0:
        k = dilation_px * 2 + 1
        out = grey_dilation(out, footprint=np.ones((k, k), dtype=bool)).astype(np.uint16)

    return out
