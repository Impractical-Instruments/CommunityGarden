"""CV path on synthetic frames: Calibrator, detect, the 2D -> 3D step, orbbec_to_world, run_pipeline."""
from __future__ import annotations

import itertools

import numpy as np
import pytest

from IIVision import MockCamera, StabilizerConfig, build_calibration, run_pipeline
from IIVision.blob_tracker import (
    BlobTracker,
    Calibrator,
    CameraIntrinsics,
    DetectionConfig,
    FramePacket,
)
from IIVision.transforms import Rotator, Transform, orbbec_to_world

W, H = 64, 48
BG_MM = 3000
BODY_MM = 1500
INTRINSICS = CameraIntrinsics(fx=50.0, fy=50.0, cx=32.0, cy=24.0)
# Tiny frames: min_blob_pixels and min_samples are far below the defaults, and stride 1
# samples every pixel of a blob's bounding box.
CFG = DetectionConfig(min_depth_mm=100, max_depth_mm=5000, depth_delta_mm=50,
                      min_blob_pixels=20, stride_pixels=1, min_samples=10)


def _frame(depth: np.ndarray, width: int = W, height: int = H) -> FramePacket:
    return FramePacket(width=width, height=height, timestamp_us=0,
                       data=depth.astype(np.uint16).tobytes(), intrinsics=INTRINSICS)


def _scene(*bodies: tuple[slice, slice]) -> np.ndarray:
    depth = np.full((H, W), BG_MM, dtype=np.uint16)
    for rows, cols in bodies:
        depth[rows, cols] = BODY_MM
    return depth


def _calibration(frames: int = 12):
    cal = Calibrator(frames)
    for _ in range(frames):
        cal.push_frame(_frame(_scene()))
    return cal.build()


# --- Calibrator -------------------------------------------------------------

def test_calibrator_reports_ready_only_after_n_frames():
    cal = Calibrator(3)
    assert [cal.push_frame(_frame(_scene())) for _ in range(3)] == [False, False, True]
    assert cal.is_ready


def test_calibrator_build_before_ready_raises():
    cal = Calibrator(3)
    cal.push_frame(_frame(_scene()))
    with pytest.raises(RuntimeError):
        cal.build()


def test_calibrator_background_is_median_of_frames():
    cal = Calibrator(11)
    for i in range(11):
        # One frame in 11 has a person at the top-left; the median ignores it.
        cal.push_frame(_frame(_scene((slice(0, 10), slice(0, 10))) if i == 0 else _scene()))
    model = cal.build()
    assert (model.width, model.height) == (W, H)
    assert (model.background == BG_MM).all()
    assert model.valid_mask.all()
    assert (model.noise_floor == 0).all()


def test_calibrator_marks_pixels_without_enough_depth_readings_invalid():
    cal = Calibrator(12)
    for _ in range(12):
        depth = _scene()
        depth[0, 0] = 0   # sensor dropout, every frame
        cal.push_frame(_frame(depth))
    model = cal.build()
    assert not model.valid_mask[0]
    assert model.background[0] == 0
    assert model.valid_mask[1:].all()


def test_calibrator_ignores_frames_of_another_size():
    cal = Calibrator(2)
    cal.push_frame(_frame(_scene()))
    assert cal.push_frame(_frame(np.full((10, 10), BG_MM), 10, 10)) is False
    assert cal.push_frame(_frame(_scene())) is True


# --- detect -----------------------------------------------------------------

def test_detect_empty_scene_has_no_blobs():
    result = BlobTracker(_calibration(), CFG).detect(_frame(_scene()))
    assert result.screen_blobs == [] and result.world_blobs == []


def test_detect_planted_body_gives_one_blob_with_its_bounds():
    body = (slice(22, 38), slice(40, 56))
    result = BlobTracker(_calibration(), CFG).detect(_frame(_scene(body)))
    assert len(result.screen_blobs) == 1
    blob = result.screen_blobs[0]
    assert (blob.min_x, blob.max_x, blob.min_y, blob.max_y) == (40, 55, 22, 37)
    assert blob.centroid_x == pytest.approx(47.5, abs=0.1)
    assert blob.centroid_y == pytest.approx(29.5, abs=0.1)
    assert 200 <= blob.pixel_count <= 256   # the despeckle trims the corners
    assert len(result.world_blobs) == 1 and result.world_blobs[0].id == blob.id


def test_detect_two_bodies_gives_two_blobs():
    left = (slice(10, 26), slice(4, 20))
    right = (slice(24, 40), slice(40, 56))
    result = BlobTracker(_calibration(), CFG).detect(_frame(_scene(left, right)))
    assert sorted(b.min_x for b in result.screen_blobs) == [4, 40]


def test_detect_drops_blob_smaller_than_min_blob_pixels():
    speck = (slice(20, 23), slice(20, 23))
    assert BlobTracker(_calibration(), CFG).detect(_frame(_scene(speck))).screen_blobs == []


def test_detect_rejects_frame_of_another_size():
    with pytest.raises(ValueError):
        BlobTracker(_calibration(), CFG).detect(_frame(np.full((10, 10), BG_MM), 10, 10))


# --- the 2D -> 3D step ------------------------------------------------------

def test_3d_step_unprojects_known_pixel_and_depth_to_camera_space():
    # Body bounding box is centred on pixel (47.5, 29.5) at 1.5 m.
    body = (slice(22, 38), slice(40, 56))
    result = BlobTracker(_calibration(), CFG).detect(_frame(_scene(body)))
    blob = result.world_blobs[0]
    assert blob.valid
    expected_x = (47.5 - INTRINSICS.cx) * 1.5 / INTRINSICS.fx    # right of the optical axis
    expected_y = (29.5 - INTRINSICS.cy) * 1.5 / INTRINSICS.fy    # below it
    np.testing.assert_allclose(blob.cam_pos_m, [expected_x, expected_y, 1.5], atol=1e-6)


def test_3d_step_skips_blob_with_too_few_depth_samples():
    cfg = DetectionConfig(min_depth_mm=100, max_depth_mm=5000, depth_delta_mm=50,
                          min_blob_pixels=20, stride_pixels=1, min_samples=10_000)
    body = (slice(22, 38), slice(40, 56))
    result = BlobTracker(_calibration(), cfg).detect(_frame(_scene(body)))
    assert len(result.screen_blobs) == 1 and result.world_blobs == []


# --- orbbec_to_world --------------------------------------------------------

def test_orbbec_to_world_maps_axes_and_units():
    # camera: 1 m right, 2 m down, 3 m forward
    np.testing.assert_allclose(orbbec_to_world(np.array([1.0, 2.0, 3.0])), [100.0, 300.0, -200.0])


def test_orbbec_to_world_up_is_negative_camera_y():
    assert orbbec_to_world(np.array([0.0, -0.5, 0.0]))[2] == pytest.approx(50.0)


def test_orbbec_to_world_origin_is_origin():
    np.testing.assert_allclose(orbbec_to_world(np.zeros(3)), np.zeros(3))


# --- run_pipeline -----------------------------------------------------------

def test_run_pipeline_with_mock_camera_tracks_blobs_in_world_space():
    calibration = build_calibration(MockCamera(fps=1000, num_blobs=0), num_frames=12)
    camera = MockCamera(fps=1000, num_blobs=2)
    transform = Transform(translation=np.zeros(3), rotation=Rotator())
    gen = run_pipeline(camera, transform, calibration, StabilizerConfig(min_confirm_frames=2))
    try:
        batches = list(itertools.islice(gen, 6))
    finally:
        gen.close()
    assert len(batches) == 6
    assert batches[0] == []                 # nothing is confirmed on the first frame
    confirmed = batches[-1]
    assert confirmed, "no blob confirmed after 6 frames"
    for tracked in confirmed:
        x, y, z = tracked.world_pos_cm
        # Mock blobs stand 500-1200 mm in front of a 3000 mm wall: world Y is forward.
        assert 150.0 <= y <= 250.0
        assert abs(x) < 300.0 and abs(z) < 300.0
    assert len({t.stable_id for t in confirmed}) == len(confirmed)
