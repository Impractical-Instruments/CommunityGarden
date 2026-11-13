"""Builds and stores the fixed per-pixel background model (median depth, validity, noise floor) from depth frames."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .types import FramePacket

# Minimum calibration frames that must be valid before a pixel's background
# depth is trusted.
_MIN_FRAMES_VALID = 10

# Multiplier applied to per-pixel IQR to form the noise-adaptive threshold.
# IQR ≈ 1.35σ, so 3×IQR ≈ 4σ — eliminates sensor noise false positives while
# still catching real foreground objects.
_NOISE_SIGMA = 3

_CAL_MIN_DEPTH_MM = 50      # calibration ignores readings nearer than this


@dataclass
class Calibration:
    """
    Background model: per-pixel median depth, validity mask, and noise floor.
    Produced by Calibrator; consumed by BlobDetector.
    Serializable to disk to skip recalibration on warm restart.
    """
    width: int
    height: int
    background: np.ndarray   # uint16, shape (H*W,)
    valid_mask: np.ndarray   # bool,   shape (H*W,)
    noise_floor: np.ndarray  # uint16, shape (H*W,) — per-pixel IQR from calibration frames

    def threshold(self, depth_delta_mm: float) -> np.ndarray:
        """int32 (H*W,): per-pixel foreground threshold, mm.

        At least depth_delta_mm, raised to 3×IQR where sensor noise is high —
        prevents noisy pixels from flickering as foreground.
        """
        return np.maximum(depth_delta_mm, self.noise_floor.astype(np.int32) * _NOISE_SIGMA)

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

    def __init__(self, num_frames: int) -> None:
        self._num_frames = max(1, num_frames)
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
        # No upper cap: a far wall past DetectionConfig.max_depth_mm is still
        # a real background — clipping it here makes those pixels invalid and
        # punches holes in the foreground when people stand in front. Flaky
        # pixels are handled downstream by the noise_floor (IQR) threshold.
        valid = frames >= _CAL_MIN_DEPTH_MM
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
