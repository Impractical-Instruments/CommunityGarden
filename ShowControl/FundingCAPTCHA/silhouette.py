"""Camera-space silhouette correction for FundingCAPTCHA.

Two functions cover the full pipeline:
  build_cam_transform(settings) → Transform | None
  apply_cam_transform(fg, intrinsics, transform) → np.ndarray

Grow to a class if state or additional config is needed.
"""
from __future__ import annotations

import numpy as np


def build_cam_transform(settings: dict):
    """Return a camera Transform from settings, or None if IIVision unavailable."""
    try:
        from IIVision import Rotator, Transform
    except ImportError:
        return None
    cam = settings.get("camera", {})
    pos = cam.get("pos_cm", [0, 0, 0])
    rot = cam.get("rotation", {})
    return Transform(
        translation=np.array(pos, dtype=float),
        rotation=Rotator(
            pitch=rot.get("pitch", 0.0),
            yaw=rot.get("yaw", 0.0),
            roll=rot.get("roll", 0.0),
        ),
    )


def apply_cam_transform(fg: np.ndarray, intrinsics, transform) -> np.ndarray:
    """Correct fg for camera mounting: reproject if possible, always mirror.

    Always mirrors horizontally — camera faces players, mirror gives natural view.
    Reprojects only when both intrinsics and transform are non-None.
    """
    if intrinsics is not None and transform is not None:
        from IIVision import reproject_silhouette
        fg = reproject_silhouette(fg, intrinsics, transform)
    return fg[:, ::-1]
