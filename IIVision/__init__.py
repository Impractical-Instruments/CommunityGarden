"""
IIVision — shared computer-vision pipeline for Impractical Instruments installations.

Public API:
    build_calibration(camera, num_frames) -> Calibration
    run_pipeline(camera, camera_transform, calibration, stabilizer_config,
                 pre_stabilize_filter=<identity>) -> Iterator[list[TrackedBlob]]

    Background models:   Calibration + Calibrator (fixed, FlowerBeds),
                         AdaptiveBackground (self-learning, FundingCAPTCHA — ADR-0023)
    Camera classes:      MockCamera, OrbbecCamera
    Config types:        StabilizerConfig, Transform, Rotator
    Output type:         TrackedBlob
"""

from .pipeline import build_calibration, filter_positions_near_points, run_pipeline
from .blob_stabilizer import BlobStabilizer, StabilizerConfig, TrackedBlob
from .types import DetectionConfig, FramePacket
from .calibration import Calibration, Calibrator
from .detector import BackgroundModel, BlobDetector, BlobTracker
from .adaptive_background import AdaptiveBackground, AdaptiveBackgroundConfig
from .camera import MockCamera, OrbbecCamera
from .transforms import Rotator, Transform, look_yaw_degrees, orbbec_to_world, rotator_to_matrix, transform_position
from .silhouette_warp import reproject_silhouette

__all__ = [
    "build_calibration",
    "filter_positions_near_points",
    "run_pipeline",
    "BlobStabilizer",
    "StabilizerConfig",
    "TrackedBlob",
    "AdaptiveBackground",
    "AdaptiveBackgroundConfig",
    "BackgroundModel",
    "BlobDetector",
    "BlobTracker",   # alias of BlobDetector, kept for old imports
    "Calibration",
    "Calibrator",
    "DetectionConfig",
    "FramePacket",
    "MockCamera",
    "OrbbecCamera",
    "Rotator",
    "Transform",
    "look_yaw_degrees",
    "orbbec_to_world",
    "rotator_to_matrix",
    "transform_position",
    "reproject_silhouette",
]
