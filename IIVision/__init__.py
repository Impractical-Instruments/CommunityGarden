"""
IIVision — shared computer-vision pipeline for Impractical Instruments installations.

Public API:
    build_calibration(camera, num_frames) -> Calibration
    run_pipeline(camera, camera_transform, calibration, stabilizer_config,
                 pre_stabilize_filter=<identity>) -> Iterator[list[TrackedBlob]]

    Calibration classes: Calibration, Calibrator
    Camera classes:      MockCamera, OrbbecCamera
    Config types:        StabilizerConfig, Transform, Rotator
    Output type:         TrackedBlob
"""

from .pipeline import PreStabilizeFilter, build_calibration, filter_positions_near_points, run_pipeline
from .blob_stabilizer import BlobStabilizer, StabilizerConfig, TrackedBlob
from .blob_tracker import BlobTracker, Calibration, Calibrator
from .camera import MockCamera, OrbbecCamera
from .transforms import Rotator, Transform, look_yaw_degrees, orbbec_to_world, rotator_to_matrix, transform_position

__all__ = [
    "build_calibration",
    "filter_positions_near_points",
    "run_pipeline",
    "PreStabilizeFilter",
    "BlobStabilizer",
    "StabilizerConfig",
    "TrackedBlob",
    "BlobTracker",
    "Calibration",
    "Calibrator",
    "MockCamera",
    "OrbbecCamera",
    "Rotator",
    "Transform",
    "look_yaw_degrees",
    "orbbec_to_world",
    "rotator_to_matrix",
    "transform_position",
]
