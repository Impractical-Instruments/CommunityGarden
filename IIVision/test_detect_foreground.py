"""Tests for BlobTracker.detect_foreground()."""
from __future__ import annotations

import numpy as np
import pytest

from IIVision.blob_tracker import (
    BlobTracker,
    Calibration,
    CameraIntrinsics,
    DetectionConfig,
    FramePacket,
)


def _calibration(width: int, height: int, background_mm: int) -> Calibration:
    n = width * height
    return Calibration(
        width=width,
        height=height,
        background=np.full(n, background_mm, dtype=np.uint16),
        valid_mask=np.ones(n, dtype=bool),
        noise_floor=np.zeros(n, dtype=np.uint16),
    )


def _frame(width: int, height: int, depth: np.ndarray) -> FramePacket:
    return FramePacket(
        width=width,
        height=height,
        timestamp_us=0,
        data=depth.astype(np.uint16).flatten().tobytes(),
        intrinsics=CameraIntrinsics(),
    )


_CFG = DetectionConfig(min_depth_mm=100, max_depth_mm=5000, depth_delta_mm=50)


def test_returns_uint16_hwshape():
    W, H = 20, 20
    cal = _calibration(W, H, 2000)
    depth = np.full((H, W), 2000, dtype=np.uint16)
    result = BlobTracker(cal, _CFG).detect_foreground(_frame(W, H, depth))
    assert result.dtype == np.uint16
    assert result.shape == (H, W)


def test_matching_background_all_zero():
    W, H = 20, 20
    cal = _calibration(W, H, 2000)
    depth = np.full((H, W), 2000, dtype=np.uint16)
    result = BlobTracker(cal, _CFG).detect_foreground(_frame(W, H, depth))
    assert (result == 0).all()


def test_foreground_pixels_nonzero():
    W, H = 40, 40
    BG, FG = 3000, 1000
    cal = _calibration(W, H, BG)
    depth = np.full((H, W), BG, dtype=np.uint16)
    depth[10:30, 10:30] = FG
    result = BlobTracker(cal, _CFG).detect_foreground(_frame(W, H, depth))
    # Interior well away from borders should be detected as foreground
    assert (result[12:28, 12:28] > 0).all()


def test_background_pixels_remain_zero():
    W, H = 40, 40
    BG, FG = 3000, 1000
    cal = _calibration(W, H, BG)
    depth = np.full((H, W), BG, dtype=np.uint16)
    depth[10:30, 10:30] = FG
    result = BlobTracker(cal, _CFG).detect_foreground(_frame(W, H, depth))
    assert (result[:5, :5] == 0).all()
    assert (result[35:, 35:] == 0).all()


def test_foreground_depth_values_match_frame():
    W, H = 40, 40
    BG, FG = 3000, 1200
    cal = _calibration(W, H, BG)
    depth = np.full((H, W), BG, dtype=np.uint16)
    depth[10:30, 10:30] = FG
    result = BlobTracker(cal, _CFG).detect_foreground(_frame(W, H, depth))
    fg_values = result[result > 0]
    assert (fg_values == FG).all()


def test_pixels_below_min_depth_not_foreground():
    W, H = 40, 40
    BG = 3000
    cfg = DetectionConfig(min_depth_mm=500, max_depth_mm=5000, depth_delta_mm=50)
    cal = _calibration(W, H, BG)
    depth = np.full((H, W), BG, dtype=np.uint16)
    depth[10:30, 10:30] = 200  # below min_depth_mm
    result = BlobTracker(cal, cfg).detect_foreground(_frame(W, H, depth))
    assert (result == 0).all()
