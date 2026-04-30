"""
IIVision — shared computer-vision pipeline for Impractical Instruments installations.

Public API:
    run_pipeline(camera, camera_transform, calib_frames, stabilizer_config,
                 pre_stabilize_filter=None) -> Iterator[list[TrackedBlob]]

    Camera classes:    MockCamera, OrbbecCamera
    Config types:      StabilizerConfig, Transform, Rotator
    Output type:       TrackedBlob
"""

from .pipeline import PreStabilizeFilter, run_pipeline
from .blob_stabilizer import BlobStabilizer, StabilizerConfig, TrackedBlob
from .blob_tracker import BlobTracker, CalibrationState
from .camera import MockCamera, OrbbecCamera
from .transforms import Rotator, Transform, look_yaw_degrees, orbbec_to_world, rotator_to_matrix, transform_position

__all__ = [
    "run_pipeline",
    "PreStabilizeFilter",
    "BlobStabilizer",
    "StabilizerConfig",
    "TrackedBlob",
    "BlobTracker",
    "CalibrationState",
    "MockCamera",
    "OrbbecCamera",
    "Rotator",
    "Transform",
    "look_yaw_degrees",
    "orbbec_to_world",
    "rotator_to_matrix",
    "transform_position",
]
