"""Plain data types shared by camera, calibration and detection: frames, intrinsics, config, blobs."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class CameraIntrinsics:
    fx: float = 0.0
    fy: float = 0.0
    cx: float = 0.0
    cy: float = 0.0


@dataclass
class FramePacket:
    width: int = 0
    height: int = 0
    timestamp_us: int = 0
    # Raw uint16 depth data in row-major order, length == width * height
    data: bytes = b""
    intrinsics: CameraIntrinsics = field(default_factory=CameraIntrinsics)


@dataclass
class DetectionConfig:
    min_depth_mm: int = 500
    max_depth_mm: int = 6000
    depth_delta_mm: int = 80
    min_blob_pixels: int = 500
    stride_pixels: int = 3
    min_samples: int = 40
    z_window_mm: int = 150


@dataclass
class Blob2D:
    id: int = -1
    pixel_count: int = 0
    min_x: int = 0
    max_x: int = 0
    min_y: int = 0
    max_y: int = 0
    centroid_x: float = 0.0
    centroid_y: float = 0.0


@dataclass
class Blob3D:
    """3-D blob in camera coordinate space (X=right, Y=down, Z=forward), metres."""
    id: int = -1
    valid: bool = False
    cam_pos_m: np.ndarray = field(default_factory=lambda: np.zeros(3))


@dataclass
class DetectionResult:
    foreground: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint8))
    screen_blobs: list[Blob2D] = field(default_factory=list)
    world_blobs: list[Blob3D] = field(default_factory=list)
