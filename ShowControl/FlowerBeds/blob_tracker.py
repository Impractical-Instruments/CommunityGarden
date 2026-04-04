"""
Port of IIVision FBlobTracker to Python/numpy.

Pipeline per frame:
  1. SubtractBackground  — depth delta threshold
  2. MajorityFilter x2   — 3×3 neighbourhood despeckle
  3. ExtractBlobs        — 8-connected components
  4. Compute3DBlobs      — pinhole unproject + median-Z windowing
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import label as nd_label

# Minimum calibration frames that must be valid before a pixel's background
# depth is trusted.
_MIN_FRAMES_VALID = 10
_MAX_CALIB_FRAMES = 128


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
class CalibrationConfig:
    min_depth_mm: int = 50
    max_depth_mm: int = 6000


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
    # Camera-space position, metres
    cam_pos_m: np.ndarray = field(default_factory=lambda: np.zeros(3))
    cam_half_extents_m: np.ndarray = field(default_factory=lambda: np.zeros(3))
    median_z_m: float = 0.0
    sample_count: int = 0

    def world_pos_cm(self) -> np.ndarray:
        """Convert to UE world space (X=forward, Y=right, Z=up), centimetres."""
        # camera: X=right, Y=down, Z=forward
        # UE:     X=forward, Y=right, Z=up
        return np.array([
            self.cam_pos_m[2] * 100.0,   # UE X ← cam Z
            self.cam_pos_m[0] * 100.0,   # UE Y ← cam X
            -self.cam_pos_m[1] * 100.0,  # UE Z ← -cam Y
        ])

    def world_half_extents_cm(self) -> np.ndarray:
        return np.array([
            self.cam_half_extents_m[2] * 100.0,
            self.cam_half_extents_m[0] * 100.0,
            -self.cam_half_extents_m[1] * 100.0,
        ])


@dataclass
class DetectionResult:
    foreground: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint8))
    screen_blobs: list[Blob2D] = field(default_factory=list)
    world_blobs: list[Blob3D] = field(default_factory=list)


class CalibrationState(enum.Enum):
    NOT_CALIBRATED = "not_calibrated"
    IN_PROGRESS = "in_progress"
    CALIBRATED = "calibrated"


class BlobTracker:
    """
    Stateful depth-frame blob tracker.

    Usage:
        tracker = BlobTracker()
        tracker.begin_calibration(num_frames=60, width=640, height=400)
        for frame in calibration_frames:
            tracker.push_calibration_frame(frame)
        # state transitions to CALIBRATED automatically
        result = tracker.detect(live_frame)
    """

    def __init__(self):
        self.calib_config = CalibrationConfig()
        self.detection_config = DetectionConfig()

        self._state = CalibrationState.NOT_CALIBRATED
        self._width = 0
        self._height = 0
        self._calib_frames: list[np.ndarray] = []
        self._calib_frames_remaining = 0
        self._background: np.ndarray | None = None   # uint16, shape (H*W,)
        self._valid_mask: np.ndarray | None = None   # bool,   shape (H*W,)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> CalibrationState:
        return self._state

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def background_depth_mm(self) -> np.ndarray | None:
        return self._background

    @property
    def valid_mask(self) -> np.ndarray | None:
        return self._valid_mask

    def begin_calibration(self, num_frames: int, width: int, height: int) -> None:
        self._calib_frames = []
        self._calib_frames_remaining = max(1, num_frames)
        self._width = max(1, width)
        self._height = max(1, height)
        self._background = None
        self._valid_mask = None
        self._state = CalibrationState.IN_PROGRESS

    def push_calibration_frame(self, frame: FramePacket) -> None:
        if self._state != CalibrationState.IN_PROGRESS:
            return
        if self._calib_frames_remaining <= 0:
            return
        if frame.width != self._width or frame.height != self._height:
            return

        arr = np.frombuffer(frame.data, dtype=np.uint16).copy()
        self._calib_frames.append(arr)
        self._calib_frames_remaining -= 1

        if self._calib_frames_remaining <= 0:
            self._end_calibration()

    def detect(self, frame: FramePacket) -> DetectionResult:
        if self._state != CalibrationState.CALIBRATED:
            raise RuntimeError("detect() called before calibration is complete")
        if frame.width != self._width or frame.height != self._height:
            raise ValueError(f"Frame size mismatch: expected {self._width}x{self._height}")

        result = DetectionResult()
        result.foreground = self._subtract_background(frame)

        # Double despeckle
        tmp = self._majority_filter(result.foreground)
        result.foreground = self._majority_filter(tmp)

        result.screen_blobs = self._extract_blobs(result.foreground)
        result.world_blobs = self._compute_3d_blobs(frame, result.screen_blobs)
        return result

    # ------------------------------------------------------------------
    # Calibration internals
    # ------------------------------------------------------------------

    def _end_calibration(self) -> None:
        self._compute_background()
        self._calib_frames = []
        self._state = CalibrationState.CALIBRATED

    def _compute_background(self) -> None:
        # Stack into (N, num_pixels)
        frames = np.stack(self._calib_frames, axis=0).astype(np.uint16)  # (N, H*W)
        valid = (
            (frames >= self.calib_config.min_depth_mm)
            & (frames <= self.calib_config.max_depth_mm)
        )  # (N, H*W)

        num_valid = valid.sum(axis=0)  # (H*W,)
        self._valid_mask = num_valid >= _MIN_FRAMES_VALID

        # Replace invalid samples with sentinel (sorts to the end) then sort
        sentinel = np.iinfo(np.uint16).max
        masked = np.where(valid, frames, sentinel)
        masked.sort(axis=0)

        # Median index per pixel
        median_idx = num_valid // 2  # (H*W,)
        self._background = masked[median_idx, np.arange(frames.shape[1])]
        self._background[~self._valid_mask] = 0

    # ------------------------------------------------------------------
    # Detection internals
    # ------------------------------------------------------------------

    def _subtract_background(self, frame: FramePacket) -> np.ndarray:
        depth = np.frombuffer(frame.data, dtype=np.uint16)
        num_pixels = self._width * self._height
        fg = np.zeros(num_pixels, dtype=np.uint8)

        in_range = (depth >= self.detection_config.min_depth_mm) & (
            depth <= self.detection_config.max_depth_mm
        )

        # Pixels where background was valid
        bg_valid = self._valid_mask & in_range
        bg_closer = self._background > depth  # background closer than current → foreground
        delta = self._background.astype(np.int32) - depth.astype(np.int32)
        fg_from_valid = bg_valid & bg_closer & (delta > self.detection_config.depth_delta_mm)

        # Pixels where background was invalid but depth is in range → probably foreground
        fg_from_invalid = (~self._valid_mask) & in_range

        fg[fg_from_valid | fg_from_invalid] = 255
        return fg

    def _majority_filter(self, foreground: np.ndarray) -> np.ndarray:
        """
        A pixel stays foreground if ≥5 of its 3×3 neighbours are foreground.
        Matches the C++ MajorityFilter exactly (border treated as 0).
        """
        fg2d = (foreground.reshape(self._height, self._width) > 0).astype(np.int8)

        # Manual 3×3 sum (avoids scipy import of ndimage.uniform_filter with cval issues)
        count = np.zeros_like(fg2d, dtype=np.int8)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                rolled = np.roll(np.roll(fg2d, dy, axis=0), dx, axis=1)
                # Zero out the wrapped edges
                if dy > 0:
                    rolled[:dy, :] = 0
                elif dy < 0:
                    rolled[dy:, :] = 0
                if dx > 0:
                    rolled[:, :dx] = 0
                elif dx < 0:
                    rolled[:, dx:] = 0
                count += rolled

        result = np.where(count >= 5, np.uint8(255), np.uint8(0))
        return result.ravel()

    def _extract_blobs(self, foreground: np.ndarray) -> list[Blob2D]:
        fg2d = (foreground.reshape(self._height, self._width) > 0)

        # Mask the 1-pixel border (matches C++ starting loop at y=1, x=1)
        fg2d[[0, -1], :] = False
        fg2d[:, [0, -1]] = False

        # 8-connectivity connected components
        structure = np.ones((3, 3), dtype=np.int32)
        labeled, num_features = nd_label(fg2d, structure=structure)

        blobs: list[Blob2D] = []
        for blob_id in range(1, num_features + 1):
            mask = labeled == blob_id
            pixel_count = int(mask.sum())
            if pixel_count < self.detection_config.min_blob_pixels:
                continue
            ys, xs = np.nonzero(mask)
            blobs.append(Blob2D(
                id=len(blobs),
                pixel_count=pixel_count,
                min_x=int(xs.min()),
                max_x=int(xs.max()),
                min_y=int(ys.min()),
                max_y=int(ys.max()),
                centroid_x=float(xs.mean()),
                centroid_y=float(ys.mean()),
            ))

        return blobs

    def _compute_3d_blobs(
        self, frame: FramePacket, blobs_2d: list[Blob2D]
    ) -> list[Blob3D]:
        depth_img = np.frombuffer(frame.data, dtype=np.uint16).reshape(
            self._height, self._width
        )
        fx = frame.intrinsics.fx
        fy = frame.intrinsics.fy
        cx = frame.intrinsics.cx
        cy = frame.intrinsics.cy
        cfg = self.detection_config

        blobs_3d: list[Blob3D] = []

        for blob in blobs_2d:
            min_x = max(0, blob.min_x)
            max_x = min(self._width - 1, blob.max_x)
            min_y = max(0, blob.min_y)
            max_y = min(self._height - 1, blob.max_y)

            # Sample strided patch
            ys = np.arange(min_y, max_y + 1, cfg.stride_pixels)
            xs = np.arange(min_x, max_x + 1, cfg.stride_pixels)
            yy, xx = np.meshgrid(ys, xs, indexing="ij")
            depths = depth_img[yy, xx]

            in_range = (depths >= cfg.min_depth_mm) & (depths <= cfg.max_depth_mm)
            valid_depths = depths[in_range]

            if len(valid_depths) < cfg.min_samples:
                continue

            median_depth_mm = float(np.median(valid_depths))
            depth_lo = median_depth_mm - cfg.z_window_mm
            depth_hi = median_depth_mm + cfg.z_window_mm

            window_mask = (
                in_range
                & (depths >= depth_lo)
                & (depths <= depth_hi)
            )
            valid_yy = yy[window_mask]
            valid_xx = xx[window_mask]
            valid_z = depths[window_mask] * 0.001  # mm → m

            if len(valid_z) < cfg.min_samples // 2:
                continue

            # Pinhole unproject
            x3d = (valid_xx - cx) * valid_z / fx
            y3d = (valid_yy - cy) * valid_z / fy
            points = np.stack([x3d, y3d, valid_z], axis=1)  # (N, 3)

            cam_pos = points.mean(axis=0)
            cam_min = points.min(axis=0)
            cam_max = points.max(axis=0)

            blobs_3d.append(Blob3D(
                id=blob.id,
                valid=True,
                cam_pos_m=cam_pos,
                cam_half_extents_m=(cam_max - cam_min) * 0.5,
                median_z_m=median_depth_mm * 0.001,
                sample_count=len(valid_z),
            ))

        return blobs_3d
