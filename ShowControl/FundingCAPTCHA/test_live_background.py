"""Entry points go live from the first frame: no standback, no calibration (ADR-0023)."""
import json
import time
from pathlib import Path

import numpy as np

from camera_feed import CameraFeed, build_background, build_detection_config
from shadertoy import pack_body

SETTINGS = json.loads((Path(__file__).parent / "captcha-settings.json").read_text())


def test_mock_camera_shows_bodies_within_about_two_seconds():
    # MockCamera has its bodies in view from frame 0. They must not wait for a
    # calibration pass, and must not be baked into the background for good.
    feed = CameraFeed(SETTINGS, "mock")
    feed.start()
    t0 = time.monotonic()
    body_px = 0
    try:
        while time.monotonic() - t0 < 5.0:
            fg = feed.drain()
            if fg is not None:
                body = pack_body(fg, SETTINGS["camera_roi"], SETTINGS["depth_slabs"])
                body_px = int(np.count_nonzero(body[..., 0]))
                if body_px > 200:
                    break
            time.sleep(0.01)
        elapsed = time.monotonic() - t0
    finally:
        feed.stop()
    assert body_px > 200, "no body in the Body texture after 5 s"
    # background.warmup_s (1 s, the Orbbec's bad first frames) + min_valid_frames.
    warmup = SETTINGS["background"]["warmup_s"]
    assert elapsed < warmup + 1.5, f"bodies took {elapsed:.2f}s to appear"


def test_background_settings_build_the_model():
    det = build_detection_config(SETTINGS)
    model = build_background(SETTINGS, det)
    cfg = model.config
    assert cfg.depth_delta_mm == SETTINGS["detection"]["depth_delta_mm"]
    assert cfg.absorb_s > 120, "must outlast Watering can's 120 s stand-still"
    for key, value in SETTINGS["background"].items():
        if not key.startswith("_"):
            assert getattr(cfg, key) == value, key
