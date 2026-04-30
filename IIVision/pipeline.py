"""
CV pipeline: calibrate → detect → transform → filter → stabilize.

Typical usage:
    calibration = build_calibration(camera, num_frames=60)
    calibration.save("calibration.npz")          # optional — skip recalibration on restart
    for tracked in run_pipeline(camera, transform, calibration, stab_cfg):
        ...

Warm restart (people present, skip recalibration):
    calibration = Calibration.load("calibration.npz")
    for tracked in run_pipeline(camera, transform, calibration, stab_cfg):
        ...

Force recalibration:
    Calibration.delete("calibration.npz")
    calibration = build_calibration(camera, num_frames=60)
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import Any

import numpy as np

from .blob_stabilizer import BlobStabilizer, StabilizerConfig, TrackedBlob
from .blob_tracker import BlobTracker, Calibration, Calibrator
from .transforms import Transform, orbbec_to_world, transform_position

log = logging.getLogger(__name__)

PreStabilizeFilter = Callable[[list[np.ndarray]], list[np.ndarray]]


def build_calibration(camera: Any, num_frames: int) -> Calibration:
    """
    Open camera, collect num_frames depth frames, and return a Calibration.
    The camera is opened and closed by this function.
    """
    log.info("Calibrating (%d frames)…", num_frames)
    calibrator = Calibrator(num_frames)
    with camera:
        for frame in camera.frames():
            if calibrator.push_frame(frame):
                break
    calibration = calibrator.build()
    log.info("Calibration complete")
    return calibration


def run_pipeline(
    camera: Any,
    camera_transform: Transform,
    calibration: Calibration,
    stabilizer_config: StabilizerConfig,
    pre_stabilize_filter: PreStabilizeFilter | None = None,
) -> Iterator[list[TrackedBlob]]:
    """
    Run the blob-detection pipeline for one camera.

    Opens the camera, then yields one list[TrackedBlob] per frame until the
    generator is exhausted or closed.

    pre_stabilize_filter is applied to raw world-space positions after
    coordinate transform but before the stabilizer — useful for discarding
    positions inside physical obstacles (e.g. flower clusters).
    """
    tracker = BlobTracker(calibration)
    stabilizer = BlobStabilizer(stabilizer_config)

    with camera:
        for frame in camera.frames():
            result = tracker.detect(frame)
            raw_positions = [
                transform_position(camera_transform, orbbec_to_world(blob.cam_pos_m))
                for blob in result.world_blobs
                if blob.valid
            ]
            if pre_stabilize_filter is not None:
                raw_positions = pre_stabilize_filter(raw_positions)
            yield stabilizer.update(raw_positions)
