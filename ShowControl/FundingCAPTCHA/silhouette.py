"""Camera-space silhouette correction and rendering for FundingCAPTCHA.

Camera-space correction:
  build_cam_transform(settings) → Transform | None
  apply_cam_transform(fg, intrinsics, transform) → np.ndarray

Display rendering:
  render_silhouette(fg, slabs_cfg, roi, color, w, h) → pygame.Surface

Grow to a class if state or additional config is needed.
"""
from __future__ import annotations

import numpy as np
import pygame


def render_silhouette(foreground: np.ndarray, slabs_cfg: list[dict],
                      roi: dict, color: tuple, w: int, h: int) -> pygame.Surface:
    """Render a foreground depth frame as a colored Play-Zone silhouette.

    Crops to the camera ROI, masks pixels inside any Depth Slab
    [near_mm, far_mm), paints them `color`, and scales to (w, h).
    Single source of truth for the depth→silhouette mapping shared by the
    attract overlay (app.py) and the in-game backdrops (games/).
    """
    cropped = foreground[roi["y"]:roi["y"] + roi["h"], roi["x"]:roi["x"] + roi["w"]]
    H, W    = cropped.shape
    mask    = np.zeros((H, W), dtype=bool)
    for s in slabs_cfg:
        mask |= (cropped >= s["near_mm"]) & (cropped < s["far_mm"])
    rgb = np.zeros((W, H, 3), dtype=np.uint8)
    rgb[mask.T, 0] = color[0]
    rgb[mask.T, 1] = color[1]
    rgb[mask.T, 2] = color[2]
    surf = pygame.surfarray.make_surface(rgb)
    return pygame.transform.scale(surf, (w, h))


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
