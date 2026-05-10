"""
Depth-frame blob tracker.

Pipeline per frame:
  1. SubtractBackground  — depth delta threshold
  2. MajorityFilter x2   — 3×3 neighbourhood despeckle
  3. ExtractBlobs        — 8-connected components
  4. Compute3DBlobs      — pinhole unproject + median-Z windowing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.ndimage import label as nd_label

# Minimum calibration frames that must be valid before a pixel's background
# depth is trusted.
_MIN_FRAMES_VALID = 10

# Multiplier applied to per-pixel IQR to form the noise-adaptive threshold.
# IQR ≈ 1.35σ, so 3×IQR ≈ 4σ — eliminates sensor noise false positives while
# still catching real foreground objects.
_NOISE_SIGMA = 3


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
    cam_pos_m: np.ndarray = field(default_factory=lambda: np.zeros(3))
    cam_half_extents_m: np.ndarray = field(default_factory=lambda: np.zeros(3))
    median_z_m: float = 0.0
    sample_count: int = 0


@dataclass
class DetectionResult:
    foreground: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint8))
    screen_blobs: list[Blob2D] = field(default_factory=list)
    world_blobs: list[Blob3D] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

@dataclass
class Calibration:
    """
    Background model: per-pixel median depth, validity mask, and noise floor.
    Produced by Calibrator; consumed by BlobTracker.
    Serializable to disk to skip recalibration on warm restart.
    """
    width: int
    height: int
    background: np.ndarray   # uint16, shape (H*W,)
    valid_mask: np.ndarray   # bool,   shape (H*W,)
    noise_floor: np.ndarray  # uint16, shape (H*W,) — per-pixel IQR from calibration frames

    def save(self, path: Path | str) -> None:
        """Save to a .npz file."""
        np.savez(
            path,
            background=self.background,
            valid_mask=self.valid_mask,
            noise_floor=self.noise_floor,
            meta=np.array([self.width, self.height], dtype=np.int32),
        )

    @classmethod
    def load(cls, path: Path | str) -> "Calibration":
        """Load from a .npz file. Raises FileNotFoundError if missing."""
        data = np.load(path)
        width, height = int(data["meta"][0]), int(data["meta"][1])
        n = width * height
        noise_floor = (
            data["noise_floor"] if "noise_floor" in data
            else np.zeros(n, dtype=np.uint16)
        )
        return cls(
            width=width,
            height=height,
            background=data["background"],
            valid_mask=data["valid_mask"].astype(bool),
            noise_floor=noise_floor,
        )

    @staticmethod
    def delete(path: Path | str) -> None:
        """Delete a saved calibration file to force recalibration on next start."""
        Path(path).unlink(missing_ok=True)


class Calibrator:
    """
    Collects depth frames and computes a Calibration (background model).

    Usage:
        cal = Calibrator(num_frames=60)
        for frame in camera.frames():
            if cal.push_frame(frame):
                break
        calibration = cal.build()
    """

    def __init__(self, num_frames: int, config: CalibrationConfig | None = None) -> None:
        self._num_frames = max(1, num_frames)
        self._config = config or CalibrationConfig()
        self._frames: list[np.ndarray] = []
        self._width: int = 0
        self._height: int = 0

    def push_frame(self, frame: FramePacket) -> bool:
        """Accept a frame. Returns True when enough frames have been collected."""
        if self.is_ready:
            return True
        if not self._frames:
            self._width = frame.width
            self._height = frame.height
        if frame.width != self._width or frame.height != self._height:
            return False
        self._frames.append(np.frombuffer(frame.data, dtype=np.uint16).copy())
        return self.is_ready

    @property
    def is_ready(self) -> bool:
        return len(self._frames) >= self._num_frames

    def build(self) -> Calibration:
        """Compute and return the Calibration. Raises RuntimeError if not enough frames."""
        if not self.is_ready:
            raise RuntimeError(
                f"Calibrator needs {self._num_frames} frames, has {len(self._frames)}"
            )
        frames = np.stack(self._frames, axis=0).astype(np.uint16)  # (N, H*W)
        valid = (
            (frames >= self._config.min_depth_mm)
            & (frames <= self._config.max_depth_mm)
        )
        num_valid = valid.sum(axis=0)  # (H*W,)
        valid_mask = num_valid >= _MIN_FRAMES_VALID

        sentinel = np.iinfo(np.uint16).max
        masked = np.where(valid, frames, sentinel)
        masked.sort(axis=0)   # valid values first (sentinel=max floats to end)

        arange = np.arange(frames.shape[1])
        median_idx = num_valid // 2
        background = masked[median_idx, arange]
        background[~valid_mask] = 0

        # Per-pixel IQR from already-sorted frames — noise floor for adaptive threshold.
        p25_idx = (num_valid * 25 // 100).clip(0, len(self._frames) - 1)
        p75_idx = (num_valid * 75 // 100).clip(0, len(self._frames) - 1)
        iqr = (masked[p75_idx, arange].astype(np.int32)
               - masked[p25_idx, arange].astype(np.int32)).clip(0, 65535)
        noise_floor = np.where(valid_mask, iqr, 0).astype(np.uint16)

        return Calibration(
            width=self._width,
            height=self._height,
            background=background,
            valid_mask=valid_mask,
            noise_floor=noise_floor,
        )


# ---------------------------------------------------------------------------
# BlobTracker
# ---------------------------------------------------------------------------

class BlobTracker:
    """
    Per-frame blob detector. Requires a ready Calibration — use Calibrator to build one.

    Usage:
        tracker = BlobTracker(calibration)
        result = tracker.detect(live_frame)
    """

    def __init__(self, calibration: Calibration, config: DetectionConfig | None = None) -> None:
        self._calibration = calibration
        self.detection_config = config or DetectionConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: FramePacket) -> DetectionResult:
        cal = self._calibration
        if frame.width != cal.width or frame.height != cal.height:
            raise ValueError(f"Frame size mismatch: expected {cal.width}x{cal.height}")

        result = DetectionResult()
        result.foreground = self._subtract_background(frame)

        # Double despeckle
        tmp = self._majority_filter(result.foreground)
        result.foreground = self._majority_filter(tmp)

        result.screen_blobs = self._extract_blobs(result.foreground)
        result.world_blobs = self._compute_3d_blobs(frame, result.screen_blobs)
        return result

    # ------------------------------------------------------------------
    # Detection internals
    # ------------------------------------------------------------------

    def _subtract_background(self, frame: FramePacket) -> np.ndarray:
        cal = self._calibration
        depth = np.frombuffer(frame.data, dtype=np.uint16)
        num_pixels = cal.width * cal.height
        fg = np.zeros(num_pixels, dtype=np.uint8)

        in_range = (depth >= self.detection_config.min_depth_mm) & (
            depth <= self.detection_config.max_depth_mm
        )

        bg_valid = cal.valid_mask & in_range
        bg_closer = cal.background > depth
        delta = cal.background.astype(np.int32) - depth.astype(np.int32)
        # Per-pixel threshold: at least depth_delta_mm, raised to 3×IQR where
        # sensor noise is high — prevents noisy pixels from flickering as foreground.
        threshold = np.maximum(
            self.detection_config.depth_delta_mm,
            cal.noise_floor.astype(np.int32) * _NOISE_SIGMA,
        )
        fg_from_valid = bg_valid & bg_closer & (delta > threshold)

        fg[fg_from_valid] = 255
        return fg

    def _majority_filter(self, foreground: np.ndarray) -> np.ndarray:
        """
        A pixel stays foreground if ≥5 of its 3×3 neighbours are foreground.
        Matches the C++ MajorityFilter exactly (border treated as 0).
        """
        cal = self._calibration
        fg2d = (foreground.reshape(cal.height, cal.width) > 0).astype(np.int8)

        count = np.zeros_like(fg2d, dtype=np.int8)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                rolled = np.roll(np.roll(fg2d, dy, axis=0), dx, axis=1)
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
        cal = self._calibration
        fg2d = (foreground.reshape(cal.height, cal.width) > 0)

        # Mask the 1-pixel border (matches C++ starting loop at y=1, x=1)
        fg2d[[0, -1], :] = False
        fg2d[:, [0, -1]] = False

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
        cal = self._calibration
        depth_img = np.frombuffer(frame.data, dtype=np.uint16).reshape(cal.height, cal.width)
        fx = frame.intrinsics.fx
        fy = frame.intrinsics.fy
        cx = frame.intrinsics.cx
        cy = frame.intrinsics.cy
        cfg = self.detection_config

        blobs_3d: list[Blob3D] = []

        for blob in blobs_2d:
            min_x = max(0, blob.min_x)
            max_x = min(cal.width - 1, blob.max_x)
            min_y = max(0, blob.min_y)
            max_y = min(cal.height - 1, blob.max_y)

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

            window_mask = in_range & (depths >= depth_lo) & (depths <= depth_hi)
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
