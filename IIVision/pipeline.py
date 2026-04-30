"""
CV pipeline generator: calibrate → detect → transform → filter → stabilize.

Yields one list[TrackedBlob] per calibrated frame. No values are yielded
during calibration. The caller controls threading; this is a plain generator.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import Any

import numpy as np

from .blob_stabilizer import BlobStabilizer, StabilizerConfig, TrackedBlob
from .blob_tracker import BlobTracker, CalibrationState
from .transforms import Transform, orbbec_to_world, transform_position

log = logging.getLogger(__name__)

PreStabilizeFilter = Callable[[list[np.ndarray]], list[np.ndarray]]


def run_pipeline(
    camera: Any,
    camera_transform: Transform,
    calib_frames: int,
    stabilizer_config: StabilizerConfig,
    pre_stabilize_filter: PreStabilizeFilter | None = None,
) -> Iterator[list[TrackedBlob]]:
    """
    Run the full blob-detection pipeline for one camera.

    Opens the camera, calibrates, then yields a list[TrackedBlob] each frame.
    Closes the camera when the generator is exhausted or closed.

    pre_stabilize_filter is applied to raw world-space positions after
    coordinate transform but before the stabilizer sees them — useful for
    discarding positions inside physical obstacles (e.g. flower clusters).
    """
    tracker = BlobTracker()
    stabilizer = BlobStabilizer(stabilizer_config)

    with camera:
        for frame in camera.frames():
            if tracker.state == CalibrationState.NOT_CALIBRATED:
                log.info("Calibrating (%d frames)…", calib_frames)
                tracker.begin_calibration(calib_frames, frame.width, frame.height)
                tracker.push_calibration_frame(frame)

            elif tracker.state == CalibrationState.IN_PROGRESS:
                tracker.push_calibration_frame(frame)
                if tracker.state == CalibrationState.CALIBRATED:
                    log.info("Calibration complete")

            else:
                result = tracker.detect(frame)
                raw_positions = [
                    transform_position(camera_transform, orbbec_to_world(blob.cam_pos_m))
                    for blob in result.world_blobs
                    if blob.valid
                ]
                if pre_stabilize_filter is not None:
                    raw_positions = pre_stabilize_filter(raw_positions)
                yield stabilizer.update(raw_positions)
