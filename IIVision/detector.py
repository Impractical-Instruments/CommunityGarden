"""Detects blobs in a single depth frame against a background model: subtract, despeckle, label, unproject to 3D.

Tracking across frames is BlobStabilizer's job, not this module's.

Pipeline per frame:
  1. SubtractBackground  — depth delta threshold
  2. MajorityFilter x2   — 3×3 neighbourhood despeckle
  3. ExtractBlobs        — 8-connected components
  4. Compute3DBlobs      — pinhole unproject + median-Z windowing
"""

from __future__ import annotations

from typing import Protocol

import numpy as np
from scipy.ndimage import label as nd_label

from .types import Blob2D, Blob3D, DetectionConfig, DetectionResult, FramePacket


class BackgroundModel(Protocol):
    """What BlobDetector reads from a background model.

    Implemented by Calibration (fixed, from Calibrator) and AdaptiveBackground
    (continuously learned, ADR-0023).
    """
    width: int
    height: int

    @property
    def background(self) -> np.ndarray: ...   # uint16 (H*W,), mm

    @property
    def valid_mask(self) -> np.ndarray: ...   # bool (H*W,)

    def threshold(self, depth_delta_mm: float) -> np.ndarray: ...   # int32 (H*W,), mm


class BlobDetector:
    """
    Per-frame blob detector over a background model: a ready Calibration (use
    Calibrator to build one) or an AdaptiveBackground that has had a frame pushed.

    Usage:
        detector = BlobDetector(calibration)
        result = detector.detect(live_frame)
    """

    def __init__(self, calibration: BackgroundModel, config: DetectionConfig | None = None) -> None:
        self._calibration = calibration
        self.detection_config = config or DetectionConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def calibration(self) -> BackgroundModel:
        return self._calibration

    @property
    def threshold_map(self) -> np.ndarray:
        """Per-pixel effective foreground threshold (mm), shape (H, W), dtype uint16.

        The model's threshold(depth_delta_mm). Zero where the background is invalid.
        """
        cal = self._calibration
        t = cal.threshold(self.detection_config.depth_delta_mm)
        t = np.where(cal.valid_mask, t, 0).clip(0, 65535)
        return t.reshape(cal.height, cal.width).astype(np.uint16)

    def detect_foreground(self, frame: FramePacket) -> np.ndarray:
        """uint16 (H, W): foreground pixels = depth_mm, background pixels = 0.

        Double-despeckled, matching detect(). The silhouette consumer reprojects
        this frame and dilates to close the resulting scatter holes, which would
        inflate any surviving stray pixel by the square of the dilation radius —
        so specks have to go before they get there, not after.

        Connected regions smaller than min_blob_pixels are dropped too, as detect()
        drops them from its blob list: camera noise that clumps survives the
        despeckle, and would otherwise show up as small blobs in the silhouette.
        """
        cal = self._calibration
        depth = np.frombuffer(frame.data, dtype=np.uint16).reshape(cal.height, cal.width)
        fg = self._subtract_background(frame)
        fg = self._majority_filter(self._majority_filter(fg))
        fg_mask = fg.reshape(cal.height, cal.width) > 0
        min_pixels = self.detection_config.min_blob_pixels
        if min_pixels > 1 and fg_mask.any():
            labeled, n = nd_label(fg_mask, structure=np.ones((3, 3), dtype=np.int32))
            keep = np.bincount(labeled.ravel(), minlength=n + 1) >= min_pixels
            keep[0] = False
            fg_mask = keep[labeled]
        result = np.zeros((cal.height, cal.width), dtype=np.uint16)
        result[fg_mask] = depth[fg_mask]
        return result

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

        background = cal.background
        bg_valid = cal.valid_mask & in_range
        bg_closer = background > depth
        delta = background.astype(np.int32) - depth.astype(np.int32)
        # Per-pixel threshold: at least depth_delta_mm, raised where the model
        # has measured high sensor noise — keeps noisy pixels from flickering.
        threshold = cal.threshold(self.detection_config.depth_delta_mm)
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

            blobs_3d.append(Blob3D(
                id=blob.id,
                valid=True,
                cam_pos_m=cam_pos,
            ))

        return blobs_3d


# Old name, kept so existing imports keep working. It detects; BlobStabilizer tracks.
BlobTracker = BlobDetector
