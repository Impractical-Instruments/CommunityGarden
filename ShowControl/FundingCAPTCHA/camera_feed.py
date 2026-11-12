"""The depth camera as a stream of foreground frames, for every FundingCAPTCHA entry point.

    feed = CameraFeed(settings, "camera")     # or "mock", or None for no camera
    feed.start()
    fg = feed.drain()                         # each tick: newest foreground frame, or None

A background thread reads the camera, keeps the self-learning depth background
(ADR-0023) and puts camera-corrected foreground frames on `feed.queue`. There
is no calibration step: frames flow from the first one.

The thread blocks once the queue is full, so drain it every tick. With no
camera (source None) the queue is still there for something else to fill;
--test-input paints into it.
"""
from __future__ import annotations

import logging
import queue
import sys
import threading
from typing import Any

import numpy as np

from settings import with_defaults
from silhouette import apply_cam_transform, build_cam_transform

try:
    from IIVision import (AdaptiveBackground, AdaptiveBackgroundConfig, BlobTracker,
                          DetectionConfig, MockCamera, OrbbecCamera)
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

log = logging.getLogger("captcha.camera")

QUEUE_FRAMES = 32


def source_from_args(args) -> str | None:
    """--camera → "camera", --mock-camera → "mock", neither → None."""
    if args.camera:
        return "camera"
    if args.mock_camera:
        return "mock"
    return None


def make_camera(settings: dict, source: str) -> Any:
    """The Orbbec ("camera") or the drifting fake bodies ("mock"), sized from settings["camera"]."""
    cam = settings["camera"]
    size = dict(width=cam["width"], height=cam["height"], fps=cam["fps"])
    if source == "mock":
        return MockCamera(**size)
    return OrbbecCamera(serial=cam["serial"] or None, **size)


def build_detection_config(settings: dict) -> "DetectionConfig":
    det = settings["detection"]
    return DetectionConfig(
        depth_delta_mm  = det["depth_delta_mm"],
        min_depth_mm    = det["min_depth_mm"],
        max_depth_mm    = det["max_depth_mm"],
        min_blob_pixels = det["min_blob_pixels"],
    )


def build_background(settings: dict, detection_config: "DetectionConfig") -> "AdaptiveBackground":
    """The self-learning depth background (ADR-0023), from settings["background"].

    detection.depth_delta_mm is the lower bound on its per-pixel threshold.
    """
    cfg = AdaptiveBackgroundConfig.from_dict(
        settings["background"], depth_delta_mm=detection_config.depth_delta_mm)
    return AdaptiveBackground(cfg)


def _read_camera(camera: Any, settings: dict, out: queue.Queue,
                 stop: threading.Event, reseed: threading.Event) -> None:
    """Thread body. Every frame updates the background model and emits foreground, from frame 1.

    Setting `reseed` makes the model relearn the background from the next frame.
    A crash is reported on the queue as {"type": "error"}.
    """
    try:
        detection_config = build_detection_config(settings)
        background       = build_background(settings, detection_config)
        tracker          = BlobTracker(background, detection_config)
        cam_transform    = build_cam_transform(settings)
        dilation_px      = int(settings["silhouette_dilation_px"])

        with camera:
            for frame in camera.frames():
                if stop.is_set():
                    break
                if reseed.is_set():
                    reseed.clear()
                    background.reseed()
                background.push(frame)
                foreground = tracker.detect_foreground(frame)
                corrected  = apply_cam_transform(
                    foreground, getattr(frame, "intrinsics", None), cam_transform,
                    dilation_px=dilation_px,
                )
                out.put({"type": "foreground", "frame": corrected})
    except Exception as exc:
        log.error("Camera thread crashed: %s", exc, exc_info=True)
        out.put({"type": "error", "msg": str(exc)})


class CameraFeed:
    """Owns the camera thread and its queue. start / drain every tick / stop."""

    def __init__(self, settings: dict, source: str | None) -> None:
        if source and not CV_AVAILABLE:
            sys.exit("ERROR: CV libraries not available — from the repo root: "
                     "pip install -e \".[fundingcaptcha,camera]\"")
        self._settings = with_defaults(settings)
        self._source   = source
        self._thread: threading.Thread | None = None
        self._stop     = threading.Event()
        self._reseed   = threading.Event()
        self.queue: queue.Queue = queue.Queue(maxsize=QUEUE_FRAMES)
        self.error: str | None  = None      # the camera thread's crash message, once drained

    def start(self) -> None:
        """Begin a fresh run: a new queue, and a new camera thread if there is a camera."""
        self.queue   = queue.Queue(maxsize=QUEUE_FRAMES)
        self._stop   = threading.Event()
        self._reseed = threading.Event()
        self.error   = None
        if not self._source:
            return
        self._thread = threading.Thread(
            target=_read_camera,
            args=(make_camera(self._settings, self._source), self._settings,
                  self.queue, self._stop, self._reseed),
            daemon=True,
        )
        self._thread.start()
        log.info("Camera started (%s) — background learns from the first frame",
                 "mock" if self._source == "mock" else "Orbbec")

    def stop(self) -> None:
        """Tell the camera thread to finish. Does not wait for it."""
        self._stop.set()

    def restart(self) -> None:
        """Stop the camera thread, wait for it (up to 5 s), start a fresh one.

        The background relearns from the first frame. Touches no settings file:
        captcha-settings.local.json is the operator's.
        """
        self.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self.start()
        log.info("Camera restarted — background relearning from the first frame")

    def reseed(self) -> None:
        """Relearn the depth background from the next camera frame."""
        self._reseed.set()

    def drain(self) -> np.ndarray | None:
        """Empty the queue. Returns the newest foreground frame, or None if none arrived.

        A camera crash is logged and kept in `self.error`.
        """
        newest = None
        while True:
            try:
                msg = self.queue.get_nowait()
            except queue.Empty:
                return newest
            if msg["type"] == "foreground":
                newest = msg["frame"]
            elif msg["type"] == "error":
                log.error("Camera: %s", msg["msg"])
                self.error = msg["msg"]
