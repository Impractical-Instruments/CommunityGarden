"""
Camera abstraction with an Orbbec implementation and a mock for laptop testing.

Usage:
    # Real hardware
    cam = OrbbecCamera(serial="CPCG85300095", width=640, height=400, fps=30)

    # Mock (random blobs, no hardware needed)
    cam = MockCamera(width=640, height=400, fps=30)

    with cam:
        for frame in cam.frames():
            ...  # frame is a blob_tracker.FramePacket
"""

from __future__ import annotations

import struct
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager

import numpy as np

from .blob_tracker import CameraIntrinsics, FramePacket


class BaseCamera(ABC):
    @abstractmethod
    def __enter__(self) -> "BaseCamera": ...

    @abstractmethod
    def __exit__(self, *_) -> None: ...

    @abstractmethod
    def frames(self) -> Iterator[FramePacket]: ...


# ---------------------------------------------------------------------------
# Orbbec implementation
# ---------------------------------------------------------------------------

class OrbbecCamera(BaseCamera):
    """
    Thin wrapper around the Orbbec Python SDK (pyorbbecsdk).

    Install with:
        pip install pyorbbecsdk
    or build from source: https://github.com/orbbec/pyorbbecsdk

    If pyorbbecsdk is not installed this raises ImportError at construction time.
    """

    def __init__(
        self,
        serial: str | None = None,
        width: int = 640,
        height: int = 400,
        fps: int = 30,
    ) -> None:
        try:
            from pyorbbecsdk import (  # type: ignore[import]
                Config,
                Context,
                OBAlignMode,
                OBFormat,
                OBSensorType,
                Pipeline,
            )
        except ImportError as exc:
            raise ImportError(
                "pyorbbecsdk2 is not installed. Run: pip install pyorbbecsdk2"
            ) from exc

        self._serial = serial
        self._width = width
        self._height = height
        self._fps = fps

        self._Pipeline = Pipeline
        self._Config = Config
        self._Context = Context
        self._OBSensorType = OBSensorType
        self._OBFormat = OBFormat

        self._pipeline: object | None = None
        self._context: object | None = None

    def __enter__(self) -> "OrbbecCamera":
        if self._serial:
            self._context = self._Context()
            device_list = self._context.query_devices()
            device = device_list.get_device_by_serial_number(self._serial)
            self._pipeline = self._Pipeline(device)
        else:
            self._pipeline = self._Pipeline()
        profile_list = self._pipeline.get_stream_profile_list(self._OBSensorType.DEPTH_SENSOR)
        profile = profile_list.get_video_stream_profile(
            self._width, self._height, self._OBFormat.Y16, self._fps,
        )
        config = self._Config()
        config.enable_stream(profile)
        self._pipeline.start(config)
        return self

    def __exit__(self, *_) -> None:
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None
        self._context = None

    def frames(self) -> Iterator[FramePacket]:
        while True:
            frame_set = self._pipeline.wait_for_frames(100)
            if frame_set is None:
                continue

            depth_frame = frame_set.get_depth_frame()
            if depth_frame is None:
                continue

            # Get intrinsics from the camera profile
            profile = depth_frame.get_stream_profile()
            intr = profile.get_intrinsic()

            raw_data = bytes(depth_frame.get_data())

            yield FramePacket(
                width=depth_frame.get_width(),
                height=depth_frame.get_height(),
                timestamp_us=depth_frame.get_timestamp(),
                data=raw_data,
                intrinsics=CameraIntrinsics(
                    fx=intr.fx,
                    fy=intr.fy,
                    cx=intr.cx,
                    cy=intr.cy,
                ),
            )


# ---------------------------------------------------------------------------
# Mock implementation — generates synthetic depth frames for laptop testing
# ---------------------------------------------------------------------------

class MockCamera(BaseCamera):
    """
    Generates synthetic 16-bit depth frames with configurable fake blobs.

    The background is a flat plane at `background_mm`.  Each blob is a
    rectangular region placed in camera space that is `blob_depth_mm`
    closer than the background, simulating a person standing in front of the
    camera.

    Blob positions drift slowly so the visualizer shows interesting movement.
    """

    def __init__(
        self,
        width: int = 640,
        height: int = 400,
        fps: int = 30,
        background_mm: int = 3000,
        num_blobs: int = 2,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.background_mm = background_mm
        self.num_blobs = num_blobs

        # Fake intrinsics matching a typical Orbbec depth camera at 640×400
        self.intrinsics = CameraIntrinsics(fx=480.0, fy=480.0, cx=320.0, cy=200.0)

        # Blob centre positions (pixel coords), will drift over time
        rng = np.random.default_rng(42)
        self._blob_cx = rng.uniform(120, width - 120, num_blobs)
        self._blob_cy = rng.uniform(80, height - 80, num_blobs)
        self._blob_vx = rng.uniform(-20, 20, num_blobs)  # px/s
        self._blob_vy = rng.uniform(-10, 10, num_blobs)

        self._blob_depth_mm = rng.integers(500, 1200, num_blobs)
        self._blob_radius_px = rng.integers(40, 80, num_blobs)

        self._last_time = time.monotonic()
        self._running = False

    def __enter__(self) -> "MockCamera":
        self._running = True
        self._last_time = time.monotonic()
        return self

    def __exit__(self, *_) -> None:
        self._running = False

    def frames(self) -> Iterator[FramePacket]:
        while self._running:
            now = time.monotonic()
            dt = now - self._last_time
            self._last_time = now

            # Drift blobs
            self._blob_cx += self._blob_vx * dt
            self._blob_cy += self._blob_vy * dt

            # Bounce off edges
            for i in range(self.num_blobs):
                r = self._blob_radius_px[i]
                if self._blob_cx[i] < r or self._blob_cx[i] > self.width - r:
                    self._blob_vx[i] *= -1
                if self._blob_cy[i] < r or self._blob_cy[i] > self.height - r:
                    self._blob_vy[i] *= -1

            depth = np.full(self.height * self.width, self.background_mm, dtype=np.uint16)
            img = depth.reshape(self.height, self.width)

            for i in range(self.num_blobs):
                cx = int(self._blob_cx[i])
                cy = int(self._blob_cy[i])
                r = int(self._blob_radius_px[i])
                y0 = max(0, cy - r)
                y1 = min(self.height, cy + r)
                x0 = max(0, cx - r)
                x1 = min(self.width, cx + r)
                img[y0:y1, x0:x1] = self.background_mm - int(self._blob_depth_mm[i])

            yield FramePacket(
                width=self.width,
                height=self.height,
                timestamp_us=int(now * 1e6),
                data=depth.tobytes(),
                intrinsics=self.intrinsics,
            )

            # Pace to target framerate
            elapsed = time.monotonic() - now
            sleep_s = (1.0 / self.fps) - elapsed
            if sleep_s > 0:
                time.sleep(sleep_s)
