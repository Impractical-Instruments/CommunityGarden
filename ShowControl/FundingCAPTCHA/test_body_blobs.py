"""Blob records for the shader player's "blobs" source (body_blobs.py, ADR-0022)."""
from __future__ import annotations

import numpy as np
import pytest

from body_blobs import BlobConfig, BodyBlobs, display_id, find_blobs
from blobs_contract import (BLOB_COASTING, BLOB_CONFIRMED, BLOB_EMPTY, BLOB_LOST, BLOB_ROWS,
                            BLOB_SLOTS, BLOB_TENTATIVE)

W, H = 64, 40
CFG = dict(min_blob_pixels=10, min_confirm_frames=3, max_miss_frames=2,
           max_match_dist_px=20.0, smoothing_alpha=1.0, lost_hold_s=0.5, ease_s=0.0)


def _body(*rects):
    """rects: (x0, y0, x1, y1, nearness) in Body pixels, row 0 = bottom."""
    pres = np.zeros((H, W), dtype=bool)
    near = np.zeros((H, W), dtype=np.float32)
    for x0, y0, x1, y1, n in rects:
        pres[y0:y1, x0:x1] = True
        near[y0:y1, x0:x1] = n
    return pres, near


def _run(bb, frames, t0=0.0, dt=0.1):
    t = t0
    for rects in frames:
        bb.update(*_body(*rects), now=t)
        t += dt
    return t


def _slot(rec, s):
    return {"box": tuple(rec[0, s]), "mot": tuple(rec[1, s]),
            "id": rec[2, s, 0], "state": rec[2, s, 1], "age": rec[2, s, 2], "near": rec[2, s, 3]}


def test_find_blobs_boxes_centroids_nearness():
    pres, near = _body((2, 3, 12, 23, 0.5), (40, 0, 50, 10, 1.0), (60, 30, 62, 32, 1.0))
    blobs = sorted(find_blobs(pres, near, min_pixels=10), key=lambda b: b.bbox[0])
    assert len(blobs) == 2                            # the 2×2 speck is below min_pixels
    assert tuple(blobs[0].bbox) == (2, 3, 12, 23)
    assert tuple(blobs[0].centroid) == pytest.approx((7.0, 13.0))
    assert blobs[0].nearness == pytest.approx(0.5)
    assert blobs[1].pixels == 100


def test_find_blobs_diagonal_touch_is_one_blob():
    pres, near = _body((0, 0, 5, 5, 1.0), (5, 5, 10, 10, 1.0))
    assert len(find_blobs(pres, near, 1)) == 1


def test_records_layout_in_uv():
    bb = BodyBlobs(BlobConfig(**CFG))
    bb.update(*_body((16, 0, 32, 20, 0.25)), now=0.0)
    r = _slot(bb.records(now=0.0), 0)
    assert r["box"] == pytest.approx((0.25, 0.0, 0.5, 0.5))
    assert r["mot"][:2] == pytest.approx((24 / W, 10 / H))
    assert r["near"] == pytest.approx(0.25)
    assert r["state"] == BLOB_TENTATIVE
    assert bb.records(now=0.0).shape == (BLOB_ROWS, BLOB_SLOTS, 4)


def test_lifecycle_tentative_confirmed_coasting_lost_empty():
    bb = BodyBlobs(BlobConfig(**CFG))
    seen = [[(10, 10, 20, 30, 0.5)]] * 3
    t = _run(bb, seen)
    assert _slot(bb.records(now=t - 0.1), 0)["state"] == BLOB_CONFIRMED
    t = _run(bb, [[]], t0=t)
    assert _slot(bb.records(now=t - 0.1), 0)["state"] == BLOB_COASTING
    t = _run(bb, [[], []], t0=t)                      # third miss > max_miss_frames
    lost = _slot(bb.records(now=t - 0.1), 0)
    assert lost["state"] == BLOB_LOST and lost["age"] == pytest.approx(0.0)
    assert _slot(bb.records(now=t - 0.1 + 0.5), 0)["state"] == BLOB_EMPTY


def test_tentative_that_expires_is_never_lost():
    bb = BodyBlobs(BlobConfig(**CFG))
    t = _run(bb, [[(10, 10, 20, 30, 0.5)], [], [], []])
    assert _slot(bb.records(now=t), 0)["state"] == BLOB_EMPTY


def test_age_counts_seconds_in_state():
    bb = BodyBlobs(BlobConfig(**CFG))
    _run(bb, [[(10, 10, 20, 30, 0.5)]] * 3)           # confirmed at t=0.2
    assert _slot(bb.records(now=0.75), 0)["age"] == pytest.approx(0.55)


def test_slots_are_stable_and_reused_after_lost_hold():
    bb = BodyBlobs(BlobConfig(**CFG))
    a, b = (2, 2, 10, 20, 0.5), (40, 2, 48, 20, 0.5)
    t = _run(bb, [[a, b]] * 3)
    ids = {s: _slot(bb.records(now=t), s)["id"] for s in (0, 1)}
    t = _run(bb, [[b]] * 3, t0=t)                     # a leaves: slot 0 lost, b stays in 1
    rec = bb.records(now=t)
    assert _slot(rec, 0)["state"] == BLOB_LOST
    assert _slot(rec, 1)["state"] == BLOB_CONFIRMED and _slot(rec, 1)["id"] == ids[1]
    c = (20, 2, 28, 20, 0.5)
    _run(bb, [[b, c]], t0=t)                          # slot 0 still held for the lost record
    assert _slot(bb.records(now=t), 2)["state"] == BLOB_TENTATIVE
    t = _run(bb, [[b], [b], [b], [b], [b], [b]], t0=t + 0.1)
    _run(bb, [[b, c]], t0=t)
    assert _slot(bb.records(now=t), 0)["state"] == BLOB_TENTATIVE   # freed, reused


def test_velocity_and_coasting_drift():
    bb = BodyBlobs(BlobConfig(**{**CFG, "max_miss_frames": 5}))
    t = _run(bb, [[(10 + 4 * i, 10, 20 + 4 * i, 30, 0.5)] for i in range(4)])
    vx = _slot(bb.records(now=t), 0)["mot"][2]
    assert vx > 0                                     # moving right (UV/s)
    box_before = _slot(bb.records(now=t), 0)["box"][0]
    _run(bb, [[]], t0=t)
    assert _slot(bb.records(now=t), 0)["box"][0] > box_before


def test_y_up_matches_body_rows():
    bb = BodyBlobs(BlobConfig(**CFG))
    bb.update(*_body((0, 30, 10, 40, 1.0)), now=0.0)  # rows 30–39: the top in GL terms
    assert _slot(bb.records(now=0.0), 0)["box"][1] == pytest.approx(0.75)


def test_easing_moves_shown_box_toward_target():
    bb = BodyBlobs(BlobConfig(**{**CFG, "ease_s": 0.1}))
    bb.update(*_body((0, 0, 10, 20, 1.0)), now=0.0)
    bb.records(now=0.0)
    bb.update(*_body((20, 0, 30, 20, 1.0)), now=0.1)
    x0 = _slot(bb.records(now=0.05), 0)["box"][0] * W
    assert 0 < x0 < 20


def test_display_id_range():
    assert display_id(0) == 1 and display_id(998) == 999 and display_id(999) == 1


def test_overflow_beyond_slots_is_dropped():
    bb = BodyBlobs(BlobConfig(**CFG))
    rects = [(i * 7, 0, i * 7 + 5, 5, 1.0) for i in range(BLOB_SLOTS + 1)]
    bb.update(*_body(*rects), now=0.0)
    assert np.count_nonzero(bb.records(now=0.0)[2, :, 1]) == BLOB_SLOTS


def test_reset_clears_everything():
    bb = BodyBlobs(BlobConfig(**CFG))
    bb.update(*_body((0, 0, 10, 20, 1.0)), now=0.0)
    assert bb.records(now=0.0).any()
    bb.reset()
    assert not bb.records(now=0.0).any()
