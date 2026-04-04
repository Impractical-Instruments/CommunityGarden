"""
Camera abstraction for the touch-screen detector.

Self-contained — does not depend on any other module in this package.

Usage:
    cam = OrbbecCamera(serial="...", width=640, height=400, fps=30)
    # or
    cam = MockCamera(width=640, height=400, fps=30)

    with cam:
        for frame in cam.frames():
            ...  # frame is a FramePacket
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
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
    # Raw uint16 depth data, row-major, length == width * height
    data: bytes = b""
    intrinsics: CameraIntrinsics = field(default_factory=CameraIntrinsics)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

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
    Thin wrapper around the Orbbec Python SDK (pyorbbecsdk2).

    Install with:  pip install pyorbbecsdk2
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
            profile = depth_frame.get_stream_profile()
            intr = profile.get_intrinsic()
            yield FramePacket(
                width=depth_frame.get_width(),
                height=depth_frame.get_height(),
                timestamp_us=depth_frame.get_timestamp(),
                data=bytes(depth_frame.get_data()),
                intrinsics=CameraIntrinsics(
                    fx=intr.fx, fy=intr.fy, cx=intr.cx, cy=intr.cy,
                ),
            )


# ---------------------------------------------------------------------------
# Mock implementation — for laptop testing without hardware
# ---------------------------------------------------------------------------

class MockCamera(BaseCamera):
    """
    Generates synthetic depth frames that simulate a flat projection surface
    with drifting "touch" blobs very close to that surface.

    Background: uniform plane at `background_mm`.
    Touch blobs: small elliptical patches at `background_mm - touch_depth_mm`,
    simulating fingers hovering just above / touching the screen surface.
    """

    def __init__(
        self,
        width: int = 640,
        height: int = 400,
        fps: int = 30,
        background_mm: int = 1500,
        num_touches: int = 2,
        touch_depth_mm: int = 40,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.background_mm = background_mm
        self.num_touches = num_touches
        self.touch_depth_mm = touch_depth_mm

        # Typical Orbbec intrinsics at 640×400
        self.intrinsics = CameraIntrinsics(fx=480.0, fy=480.0, cx=320.0, cy=200.0)

        rng = np.random.default_rng(42)
        self._cx = rng.uniform(100, width - 100, num_touches)
        self._cy = rng.uniform(80, height - 80, num_touches)
        self._vx = rng.uniform(-30, 30, num_touches)  # px/s
        self._vy = rng.uniform(-20, 20, num_touches)
        self._rx = rng.integers(15, 35, num_touches)   # half-width in pixels
        self._ry = rng.integers(10, 25, num_touches)   # half-height in pixels

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

            # Drift touch blobs
            self._cx += self._vx * dt
            self._cy += self._vy * dt
            for i in range(self.num_touches):
                if self._cx[i] < self._rx[i] or self._cx[i] > self.width - self._rx[i]:
                    self._vx[i] *= -1
                if self._cy[i] < self._ry[i] or self._cy[i] > self.height - self._ry[i]:
                    self._vy[i] *= -1

            depth = np.full(self.height * self.width, self.background_mm, dtype=np.uint16)
            img = depth.reshape(self.height, self.width)

            touch_mm = self.background_mm - self.touch_depth_mm
            for i in range(self.num_touches):
                cx, cy = int(self._cx[i]), int(self._cy[i])
                rx, ry = int(self._rx[i]), int(self._ry[i])
                y0, y1 = max(0, cy - ry), min(self.height, cy + ry)
                x0, x1 = max(0, cx - rx), min(self.width, cx + rx)
                img[y0:y1, x0:x1] = touch_mm

            yield FramePacket(
                width=self.width,
                height=self.height,
                timestamp_us=int(now * 1e6),
                data=depth.tobytes(),
                intrinsics=self.intrinsics,
            )

            elapsed = time.monotonic() - now
            sleep_s = (1.0 / self.fps) - elapsed
            if sleep_s > 0:
                time.sleep(sleep_s)
