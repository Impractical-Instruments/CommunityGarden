"""Entry points go live from the first frame: no standback, no calibration (ADR-0023)."""
import argparse
import json
import time
from pathlib import Path

import numpy as np

import app
import body_grid_tester
from shader_app import drain_camera, start_camera
from shadertoy import pack_body

SETTINGS = json.loads((Path(__file__).parent / "captcha-settings.json").read_text())


def test_mock_camera_shows_bodies_within_about_two_seconds():
    # MockCamera has its bodies in view from frame 0. They must not wait for a
    # calibration pass, and must not be baked into the background for good.
    args = argparse.Namespace(camera=False, mock_camera=True, test_input=False)
    cam_q, stop = start_camera(args, SETTINGS)
    t0 = time.monotonic()
    body_px = 0
    try:
        while time.monotonic() - t0 < 5.0:
            fg = drain_camera(cam_q)
            if fg is not None:
                body = pack_body(fg, SETTINGS["camera_roi"], SETTINGS["depth_slabs"])
                body_px = int(np.count_nonzero(body[..., 0]))
                if body_px > 200:
                    break
            time.sleep(0.01)
        elapsed = time.monotonic() - t0
    finally:
        stop.set()
    assert body_px > 200, "no body in the Body texture after 5 s"
    # background.warmup_s (1 s, the Orbbec's bad first frames) + min_valid_frames.
    warmup = SETTINGS["background"]["warmup_s"]
    assert elapsed < warmup + 1.5, f"bodies took {elapsed:.2f}s to appear"


def test_no_calibration_settings_or_states_remain():
    for key in ("calibration_frames", "calibration_countdown_s", "calibration_standback_s"):
        assert key not in SETTINGS
    assert "background" in SETTINGS
    assert {s.name for s in app.AppState} == {"SCREENSAVER", "GAME"}
    assert not hasattr(body_grid_tester, "AppState")


def test_background_settings_build_the_model():
    det = app.build_detection_config(SETTINGS)
    model = app.build_background(SETTINGS, det)
    cfg = model.config
    assert cfg.depth_delta_mm == SETTINGS["detection"]["depth_delta_mm"]
    assert cfg.absorb_s > 120, "must outlast Watering can's 120 s stand-still"
    for key, value in SETTINGS["background"].items():
        if not key.startswith("_"):
            assert getattr(cfg, key) == value, key
