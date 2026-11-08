"""Tests for AdaptiveBackground: synthetic depth arrays plus an injected clock."""
from __future__ import annotations

import numpy as np

from IIVision.adaptive_background import AdaptiveBackground, AdaptiveBackgroundConfig
from IIVision.blob_tracker import (
    BlobTracker,
    Calibration,
    CameraIntrinsics,
    DetectionConfig,
    FramePacket,
)

W, H = 40, 30
FPS = 15.0
FLOOR = 3000          # empty-scene depth, mm
PERSON = 1800         # a visitor, mm
DELTA = 30            # detection.depth_delta_mm
DET = DetectionConfig(min_depth_mm=500, max_depth_mm=6000, depth_delta_mm=DELTA)
BODY = (slice(8, 22), slice(12, 26))     # a visitor-sized patch
INSIDE = (slice(10, 20), slice(14, 24))  # its interior, clear of despeckle edges


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _frame(depth: np.ndarray) -> FramePacket:
    h, w = depth.shape
    return FramePacket(width=w, height=h, data=depth.astype(np.uint16).tobytes(),
                       intrinsics=CameraIntrinsics(fx=100, fy=100, cx=w / 2, cy=h / 2))


def _scene(person: bool = False, floor: int = FLOOR) -> np.ndarray:
    d = np.full((H, W), floor, dtype=np.uint16)
    if person:
        d[BODY] = PERSON
    return d


class Rig:
    """Model + tracker + clock, stepping at FPS."""

    def __init__(self, **cfg) -> None:
        self.clock = Clock()
        cfg.setdefault("stats_log_s", 0)
        cfg.setdefault("warmup_s", 0)
        self.model = AdaptiveBackground(
            AdaptiveBackgroundConfig(depth_delta_mm=DELTA, **cfg), clock=self.clock)
        self.tracker = BlobTracker(self.model, DET)

    def step(self, depth: np.ndarray, n: int = 1) -> np.ndarray:
        """Push n frames of depth; return the last frame's foreground mask (H, W)."""
        for _ in range(n):
            frame = _frame(depth)
            self.model.push(frame)
            fg = self.tracker.detect_foreground(frame) > 0
            self.clock.t += 1.0 / FPS
        return fg

    def run_for(self, depth: np.ndarray, seconds: float) -> np.ndarray:
        return self.step(depth, int(round(seconds * FPS)))

    def bg(self) -> np.ndarray:
        return self.model.background.reshape(H, W)


# ── Boot ──────────────────────────────────────────────────────────────────────

def test_empty_floor_is_live_within_a_second():
    rig = Rig()
    fg = rig.run_for(_scene(), 0.7)
    assert rig.model.valid_mask.all()
    assert not fg.any()
    # A visitor walking on now is foreground straight away.
    assert rig.step(_scene(person=True))[INSIDE].all()


def test_person_present_from_frame_0_is_revealed_when_they_walk_off():
    cfg = AdaptiveBackgroundConfig()
    rig = Rig()
    fg = rig.run_for(_scene(person=True), 5.0)
    assert not fg.any(), "invisible until they move: they are the only depth seen there"
    assert (rig.bg()[INSIDE] == PERSON).all()

    rig.step(_scene(), cfg.reveal_frames - 1)
    assert (rig.bg()[INSIDE] == PERSON).all(), "not before reveal_frames"
    rig.step(_scene())
    assert (rig.bg()[INSIDE] == FLOOR).all(), "revealed within reveal_frames"

    # From then on they're tracked.
    assert rig.step(_scene(person=True))[INSIDE].all()


def test_unseen_pixels_are_never_foreground():
    rig = Rig()
    depth = _scene()
    depth[:, :10] = 0               # no return there, ever
    rig.run_for(depth, 1.0)
    depth[BODY] = PERSON
    depth[:, :10] = PERSON          # something now in front of the unknown region
    fg = rig.step(depth)
    assert not fg[:, :10].any()
    assert fg[INSIDE].all()


def test_startup_frames_reading_too_far_leave_no_ghosts():
    # Measured on the Gemini 336: the first frames of a stream read up to ~400 mm
    # too far (1 frame warm, ~5 cold), then step to the true depth. Seeding from
    # them made the true floor "nearer" — little blobs that lasted absorb_s.
    rig = Rig(warmup_s=1.0)
    too_far = _scene(floor=FLOOR + 400)
    fg = rig.step(too_far, 5)
    assert not fg.any() and not rig.model.valid_mask.any(), "warm-up frames are ignored"
    fg = rig.run_for(_scene(), 2.0)
    assert not fg.any()
    assert (rig.bg() == FLOOR).all()


def test_far_outlier_first_sample_on_a_noisy_pixel_does_not_stick():
    # Measured on the Gemini 336: a pixel at ~3.7 m with σ ≈ 80 mm whose first
    # sample was a far outlier. Seeding bg from that one sample left every later
    # reading "nearer" — foreground, never at bg, too jumpy to be absorbed.
    rng = np.random.default_rng(1)
    rig = Rig()
    first = _scene()
    first[INSIDE] = FLOOR + 400
    rig.step(first)
    fgs = []
    for _ in range(int(20 * FPS)):
        d = _scene()
        d[INSIDE] = rng.normal(FLOOR, 80, d[INSIDE].shape).round()
        fgs.append(rig.step(d)[INSIDE].mean())
    assert np.mean(fgs[int(5 * FPS):]) < 0.001


def test_seed_noise_comes_from_the_seeding_samples():
    rng = np.random.default_rng(2)
    rig = Rig()
    for _ in range(AdaptiveBackgroundConfig().min_valid_frames):
        rig.step(rng.normal(FLOOR, 50, (H, W)).round().astype(np.uint16))
    assert 30 < float(np.median(rig.model.noise)) < 70
    assert abs(float(np.median(rig.model.background.astype(float))) - FLOOR) < 20


# ── Standing still ───────────────────────────────────────────────────────────

def test_person_still_for_120s_stays_foreground():
    rig = Rig()
    rig.run_for(_scene(), 2.0)
    fg = rig.run_for(_scene(person=True), 120.0)
    assert fg[INSIDE].all()


def test_static_object_absorbed_after_absorb_s():
    cfg = AdaptiveBackgroundConfig()
    rig = Rig()
    rig.run_for(_scene(), 2.0)
    bag = _scene(person=True)
    fg = rig.run_for(bag, cfg.absorb_s - 1.0)
    assert fg[INSIDE].all(), "foreground until absorb_s"
    fg = rig.run_for(bag, 2.0)
    assert not fg.any(), "background after absorb_s"
    assert (rig.bg()[INSIDE] == PERSON).all()

    # Someone walks in front of the absorbed object: still detected.
    nearer = bag.copy()
    nearer[INSIDE] = 1000
    assert rig.step(nearer)[12:18, 16:22].all()
    # The object is taken away: the floor behind it is revealed again.
    rig.step(_scene(), cfg.reveal_frames)
    assert (rig.bg()[INSIDE] == FLOOR).all()


def test_fidgeting_restarts_the_absorb_timer():
    cfg = AdaptiveBackgroundConfig()
    rig = Rig()
    rig.run_for(_scene(), 2.0)
    a, b = _scene(person=True), _scene(person=True)
    b[BODY] = PERSON + 200            # shifts by far more than thr
    for _ in range(int(cfg.absorb_s / 50) + 2):
        rig.run_for(a, 25.0)
        fg = rig.run_for(b, 25.0)
    assert rig.clock.t > cfg.absorb_s + 2.0
    assert fg[INSIDE].all()


# ── Noise and spikes ─────────────────────────────────────────────────────────

def test_single_frame_far_spike_leaves_bg_unchanged():
    rig = Rig()
    rig.run_for(_scene(), 1.0)
    before = rig.bg().copy()
    spike = _scene()
    spike[15, 20] = 5500             # flying pixel / multipath
    spike[5:8, 5:30] = 4500
    rig.step(spike)
    rig.step(_scene())
    np.testing.assert_array_equal(rig.bg(), before)


def test_far_spikes_short_of_reveal_frames_do_not_move_bg():
    cfg = AdaptiveBackgroundConfig()
    rig = Rig()
    rig.run_for(_scene(), 1.0)
    spike = _scene(floor=FLOOR + 500)
    for _ in range(20):
        rig.step(spike, cfg.reveal_frames - 1)
        rig.step(_scene())
    assert (rig.bg() == FLOOR).all()


def test_gaussian_noise_on_empty_scene_has_under_0_1_percent_foreground():
    # Orbbec structured light at 3 m: σ on the order of 10–20 mm. Use the top end.
    w, h, sigma = 160, 120, 20.0
    rng = np.random.default_rng(0)
    clock = Clock()
    model = AdaptiveBackground(AdaptiveBackgroundConfig(depth_delta_mm=DELTA, stats_log_s=0,
                                                        warmup_s=0), clock=clock)
    tracker = BlobTracker(model, DET)

    def noisy() -> FramePacket:
        d = rng.normal(FLOOR, sigma, (h, w)).round().clip(0, 65535)
        return _frame(d)

    for _ in range(int(10 * FPS)):          # warm-up
        model.push(noisy())
        clock.t += 1 / FPS

    raw = despeckled = 0
    n = int(20 * FPS)
    for _ in range(n):
        frame = noisy()
        model.push(frame)
        clock.t += 1 / FPS
        raw += np.count_nonzero(tracker._subtract_background(frame))
        despeckled += np.count_nonzero(tracker.detect_foreground(frame))
    assert raw / (n * w * h) < 0.001
    assert despeckled == 0
    # The noise estimate settles near the real σ.
    assert 0.7 * sigma < float(np.median(model.noise)) < 1.3 * sigma
    assert abs(float(np.median(model.background.astype(float))) - FLOOR) < 5


def test_threshold_has_depth_delta_floor():
    rig = Rig()
    rig.run_for(_scene(), 2.0)          # noiseless: σ estimate decays toward 0
    t = rig.model.threshold(DELTA)
    assert (t == DELTA).all()
    assert (rig.tracker.threshold_map == DELTA).all()


# ── Bump guard ───────────────────────────────────────────────────────────────

def test_bump_nearer_reseeds_after_reseed_after_s():
    cfg = AdaptiveBackgroundConfig()
    rig = Rig()
    rig.run_for(_scene(), 2.0)
    bumped = _scene(floor=FLOOR - 400)
    fg = rig.run_for(bumped, cfg.reseed_after_s - 1.0)
    assert rig.model.reseed_count == 0
    assert fg.mean() > 0.5
    fg = rig.run_for(bumped, 2.0)
    assert rig.model.reseed_count == 1
    assert not fg.any()
    assert (rig.bg() == FLOOR - 400).all()
    # After the reseed, people are tracked against the new background.
    assert rig.step(_scene(person=True, floor=FLOOR - 400))[INSIDE].all()


def test_bump_farther_heals_through_reveal_without_reseed():
    cfg = AdaptiveBackgroundConfig()
    rig = Rig()
    rig.run_for(_scene(), 2.0)
    fg = rig.step(_scene(floor=FLOOR + 400), cfg.reveal_frames)
    assert not fg.any()
    assert (rig.bg() == FLOOR + 400).all()
    rig.run_for(_scene(floor=FLOOR + 400), cfg.reseed_after_s + 5)
    assert rig.model.reseed_count == 0


def test_small_crowd_does_not_trigger_bump_guard():
    cfg = AdaptiveBackgroundConfig()
    rig = Rig()
    rig.run_for(_scene(), 2.0)
    fg = rig.run_for(_scene(person=True), cfg.reseed_after_s + 5)   # ~16% of the frame
    assert rig.model.reseed_count == 0
    assert fg[INSIDE].all()


def test_reseed_request_takes_effect_on_next_push():
    rig = Rig()
    rig.run_for(_scene(), 1.0)
    rig.model.reseed()
    fg = rig.step(_scene(person=True))
    assert rig.model.reseed_count == 1
    assert not fg.any()
    assert (rig.bg()[INSIDE] == PERSON).all()
    rig.step(_scene(), AdaptiveBackgroundConfig().reveal_frames)
    assert (rig.bg()[INSIDE] == FLOOR).all()


# ── Interface ────────────────────────────────────────────────────────────────

def test_config_from_dict_ignores_comments_and_takes_overrides():
    cfg = AdaptiveBackgroundConfig.from_dict(
        {"_comment": "x", "absorb_s": 200, "reveal_frames": 3}, depth_delta_mm=25)
    assert cfg.absorb_s == 200 and cfg.reveal_frames == 3 and cfg.depth_delta_mm == 25


def test_frame_size_change_raises():
    rig = Rig()
    rig.step(_scene())
    try:
        rig.model.push(_frame(np.full((10, 10), FLOOR, dtype=np.uint16)))
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_update_time_is_recorded():
    rig = Rig()
    rig.step(_scene())
    assert rig.model.last_update_ms > 0.0


def test_update_time_is_logged(caplog):
    import logging
    rig = Rig(stats_log_s=1e-9)
    with caplog.at_level(logging.INFO, logger="IIVision.adaptive_background"):
        rig.step(_scene(), 2)
    assert any("Background update" in r.getMessage() and " ms" in r.getMessage()
               for r in caplog.records)


def test_calibration_threshold_matches_previous_formula():
    n = 4
    cal = Calibration(width=2, height=2,
                      background=np.full(n, 3000, dtype=np.uint16),
                      valid_mask=np.ones(n, dtype=bool),
                      noise_floor=np.array([0, 5, 20, 100], dtype=np.uint16))
    np.testing.assert_array_equal(cal.threshold(30), [30, 30, 60, 300])
