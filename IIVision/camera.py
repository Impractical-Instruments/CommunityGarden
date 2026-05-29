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

import logging
import struct
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager

import numpy as np

log = logging.getLogger(__name__)
_CAMERA_RETRY_DELAY_S = 5

try:
    import cv2  # type: ignore[import]
except ImportError:
    cv2 = None  # type: ignore[assignment]

from .blob_tracker import CameraIntrinsics, FramePacket


# ---------------------------------------------------------------------------
# RGB frame (used by layout calibrator only)
# ---------------------------------------------------------------------------

class RGBFrame:
    """Single BGR color frame from the Orbbec color sensor."""

    def __init__(self, data: np.ndarray, width: int, height: int,
                 fx: float, fy: float, cx: float, cy: float) -> None:
        self.data = data          # shape (H, W, 3), BGR
        self.width = width
        self.height = height
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy


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
        mirror: bool = False,
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
        self._mirror = mirror

        self._Pipeline = Pipeline
        self._Config = Config
        self._Context = Context
        self._OBSensorType = OBSensorType
        self._OBFormat = OBFormat

        self._pipeline: object | None = None
        self._context: object | None = None

    def __enter__(self) -> "OrbbecCamera":
        while True:
            try:
                if self._serial:
                    self._context = self._Context()
                    device_list = self._context.query_devices()
                    device = device_list.get_device_by_serial_number(self._serial)
                    self._pipeline = self._Pipeline(device)
                else:
                    self._pipeline = self._Pipeline()
                break
            except RuntimeError as exc:
                self._pipeline = None
                self._context = None
                log.warning("Orbbec device not ready (%s) — retrying in %ds…", exc, _CAMERA_RETRY_DELAY_S)
                time.sleep(_CAMERA_RETRY_DELAY_S)
        profile_list = self._pipeline.get_stream_profile_list(self._OBSensorType.DEPTH_SENSOR)
        profile = profile_list.get_video_stream_profile(
            self._width, self._height, self._OBFormat.Y16, self._fps,
        )
        config = self._Config()
        config.enable_stream(profile)
        self._pipeline.start(config)
        self._apply_depth_mirror(self._mirror)
        return self

    def _apply_depth_mirror(self, mirror: bool) -> None:
        """
        Force the device's depth-mirror property to a known value.

        Orbbec depth streams frequently default to horizontally mirrored. A
        mirrored image flips the unprojected camera X axis, which BlobTracker's
        pinhole math (x3d = (xx - cx) * z / fx) assumes is NOT mirrored — so we
        set the property explicitly rather than trusting the device default.
        """
        try:
            from pyorbbecsdk import OBPropertyID, OBPermissionType  # type: ignore[import]

            device = self._pipeline.get_device()
            prop = OBPropertyID.OB_PROP_DEPTH_MIRROR_BOOL
            if not device.is_property_supported(prop, OBPermissionType.OB_PERMISSION_WRITE):
                log.warning("Depth mirror property not writable on this device — leaving as-is")
                return
            device.set_bool_property(prop, mirror)
            log.info("Depth mirror set to %s", mirror)
        except Exception as exc:
            log.warning("Could not set depth mirror (%s) — leaving device default", exc)

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


# ---------------------------------------------------------------------------
# Orbbec color-only camera — used exclusively by the layout calibrator
# ---------------------------------------------------------------------------

class OrbbecRGBCamera:
    """
    Opens only the Orbbec COLOR stream and yields RGBFrame objects.
    Not a BaseCamera subclass — depth pipeline is not involved.

    Typical use:
        with OrbbecRGBCamera(serial=..., width=1280, height=720, fps=15) as cam:
            for frame in cam.frames():
                ...
    """

    def __init__(
        self,
        serial: str | None = None,
        width: int = 1280,
        height: int = 720,
        fps: int = 15,
    ) -> None:
        try:
            from pyorbbecsdk import (  # type: ignore[import]
                Config, Context, OBFormat, OBSensorType, Pipeline,
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

    def __enter__(self) -> "OrbbecRGBCamera":
        while True:
            try:
                if self._serial:
                    self._context = self._Context()
                    device_list = self._context.query_devices()
                    device = device_list.get_device_by_serial_number(self._serial)
                    self._pipeline = self._Pipeline(device)
                else:
                    self._pipeline = self._Pipeline()
                break
            except RuntimeError as exc:
                self._pipeline = None
                self._context = None
                log.warning("Orbbec device not ready (%s) — retrying in %ds…", exc, _CAMERA_RETRY_DELAY_S)
                time.sleep(_CAMERA_RETRY_DELAY_S)

        profile_list = self._pipeline.get_stream_profile_list(
            self._OBSensorType.COLOR_SENSOR
        )
        # Prefer RGB888; fall back to the first available profile.
        try:
            profile = profile_list.get_video_stream_profile(
                self._width, self._height, self._OBFormat.RGB, self._fps
            )
        except Exception:
            profile = profile_list.get_default_video_stream_profile()

        config = self._Config()
        config.enable_stream(profile)
        self._pipeline.start(config)
        return self

    def __exit__(self, *_) -> None:
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None
        self._context = None

    def frames(self) -> Iterator[RGBFrame]:
        assert self._pipeline is not None, "Camera not opened — use as context manager"
        while True:
            frame_set = self._pipeline.wait_for_frames(200)
            if frame_set is None:
                continue
            color_frame = frame_set.get_color_frame()
            if color_frame is None:
                continue

            w = color_frame.get_width()
            h = color_frame.get_height()
            raw = bytes(color_frame.get_data())

            # Intrinsics from the color stream profile
            profile = color_frame.get_stream_profile()
            intr = profile.get_intrinsic()

            # Decode: try raw RGB reshape, fall back to JPEG decode
            arr: np.ndarray | None = None
            if len(raw) == w * h * 3:
                arr = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3)
                arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            else:
                buf = np.frombuffer(raw, dtype=np.uint8)
                arr = cv2.imdecode(buf, cv2.IMREAD_COLOR)

            if arr is None:
                continue

            yield RGBFrame(
                data=arr,
                width=w,
                height=h,
                fx=intr.fx,
                fy=intr.fy,
                cx=intr.cx,
                cy=intr.cy,
            )
