"""
Touch detector — background calibration and per-frame touch-blob extraction.

Pipeline per frame:
  1. SubtractBackground  — pixels significantly closer than calibrated background
  2. MajorityFilter x2   — 3×3 neighbourhood despeckle
  3. ExtractTouches      — 8-connected components → centroids in camera pixel space

Mirrors the BlobTracker pattern from FlowerBeds but works entirely in 2-D
pixel space (no 3-D unprojection needed for a flat projection surface).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import label as nd_label

from camera import FramePacket

_MIN_FRAMES_VALID = 10
_MAX_CALIB_FRAMES = 128


@dataclass
class CalibrationConfig:
    min_depth_mm: int = 50
    max_depth_mm: int = 6000


@dataclass
class DetectionConfig:
    # Depth range within which foreground is considered valid.
    min_depth_mm: int = 200
    max_depth_mm: int = 4000
    # A pixel is foreground if the background is this much farther away.
    touch_threshold_mm: int = 25
    # Connected-component size gates (pixels).
    min_touch_pixels: int = 30
    max_touch_pixels: int = 8000


@dataclass
class TouchPoint:
    """A detected touch contact in camera pixel space."""
    pixel_x: float
    pixel_y: float
    pixel_count: int


class CalibrationState(enum.Enum):
    NOT_CALIBRATED = "not_calibrated"
    IN_PROGRESS = "in_progress"
    CALIBRATED = "calibrated"


class TouchDetector:
    """
    Stateful depth-frame touch detector.

    Usage:
        detector = TouchDetector()
        detector.begin_calibration(num_frames=90, width=640, height=400)
        for frame in calibration_frames:
            detector.push_calibration_frame(frame)
        # state transitions to CALIBRATED automatically
        touches = detector.detect(live_frame)  # list[TouchPoint]
    """

    def __init__(self) -> None:
        self.calib_config = CalibrationConfig()
        self.detection_config = DetectionConfig()

        self._state = CalibrationState.NOT_CALIBRATED
        self._width = 0
        self._height = 0
        self._calib_frames: list[np.ndarray] = []
        self._calib_frames_remaining = 0
        self._background: np.ndarray | None = None  # uint16, shape (H*W,)
        self._valid_mask: np.ndarray | None = None  # bool,   shape (H*W,)

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

    def detect(self, frame: FramePacket) -> list[TouchPoint]:
        if self._state != CalibrationState.CALIBRATED:
            raise RuntimeError("detect() called before calibration is complete")
        if frame.width != self._width or frame.height != self._height:
            raise ValueError(f"Frame size mismatch: expected {self._width}×{self._height}")

        fg = self._subtract_background(frame)
        fg = self._majority_filter(fg)
        fg = self._majority_filter(fg)
        return self._extract_touches(fg)

    # ------------------------------------------------------------------
    # Calibration internals
    # ------------------------------------------------------------------

    def _end_calibration(self) -> None:
        self._compute_background()
        self._calib_frames = []
        self._state = CalibrationState.CALIBRATED

    def _compute_background(self) -> None:
        frames = np.stack(self._calib_frames, axis=0).astype(np.uint16)  # (N, H*W)
        valid = (
            (frames >= self.calib_config.min_depth_mm)
            & (frames <= self.calib_config.max_depth_mm)
        )
        num_valid = valid.sum(axis=0)
        self._valid_mask = num_valid >= _MIN_FRAMES_VALID

        sentinel = np.iinfo(np.uint16).max
        masked = np.where(valid, frames, sentinel)
        masked.sort(axis=0)

        median_idx = num_valid // 2
        self._background = masked[median_idx, np.arange(frames.shape[1])]
        self._background[~self._valid_mask] = 0

    # ------------------------------------------------------------------
    # Detection internals
    # ------------------------------------------------------------------

    def _subtract_background(self, frame: FramePacket) -> np.ndarray:
        depth = np.frombuffer(frame.data, dtype=np.uint16)
        cfg = self.detection_config
        fg = np.zeros(self._width * self._height, dtype=np.uint8)

        in_range = (depth >= cfg.min_depth_mm) & (depth <= cfg.max_depth_mm)

        # Pixels where background was valid and something is closer by threshold.
        bg_valid = self._valid_mask & in_range
        delta = self._background.astype(np.int32) - depth.astype(np.int32)
        fg_from_valid = bg_valid & (delta > cfg.touch_threshold_mm)

        fg[fg_from_valid] = 255
        return fg

    def _majority_filter(self, foreground: np.ndarray) -> np.ndarray:
        """
        A pixel stays foreground if ≥5 of its 3×3 neighbours are foreground.
        Border pixels are always treated as background.
        """
        fg2d = (foreground.reshape(self._height, self._width) > 0).astype(np.int8)
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

    def _extract_touches(self, foreground: np.ndarray) -> list[TouchPoint]:
        cfg = self.detection_config
        fg2d = (foreground.reshape(self._height, self._width) > 0)

        # Zero 1-pixel border (avoids spurious edge detections).
        fg2d[[0, -1], :] = False
        fg2d[:, [0, -1]] = False

        structure = np.ones((3, 3), dtype=np.int32)
        labeled, num_features = nd_label(fg2d, structure=structure)

        touches: list[TouchPoint] = []
        for label_id in range(1, num_features + 1):
            mask = labeled == label_id
            pixel_count = int(mask.sum())
            if pixel_count < cfg.min_touch_pixels:
                continue
            if pixel_count > cfg.max_touch_pixels:
                continue
            ys, xs = np.nonzero(mask)
            touches.append(TouchPoint(
                pixel_x=float(xs.mean()),
                pixel_y=float(ys.mean()),
                pixel_count=pixel_count,
            ))

        return touches
