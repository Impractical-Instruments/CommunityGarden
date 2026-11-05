"""BlobStabilizer.update_tracks(): every live track, its detection, and expiries."""
from __future__ import annotations

import numpy as np

from IIVision.blob_stabilizer import BlobStabilizer, StabilizerConfig


def _p(x, y=0.0):
    return np.array([x, y, 0.0])


def test_update_tracks_reports_unconfirmed_and_detection_index():
    s = BlobStabilizer(StabilizerConfig(min_confirm_frames=3))
    tracks, expired = s.update_tracks([_p(0), _p(500)])
    assert expired == []
    assert sorted((t.track_id, t.det_idx, t.seen_frames) for t in tracks) == [(0, 0, 1), (1, 1, 1)]
    assert s.update([_p(0), _p(500)]) == []          # update() still hides unconfirmed tracks


def test_update_tracks_matches_by_distance_not_order():
    s = BlobStabilizer(StabilizerConfig(smoothing_alpha=1.0))
    s.update_tracks([_p(0), _p(500)])
    tracks, _ = s.update_tracks([_p(505), _p(3)])
    assert {t.track_id: t.det_idx for t in tracks} == {0: 1, 1: 0}


def test_update_tracks_reports_misses_then_expiry():
    s = BlobStabilizer(StabilizerConfig(max_miss_frames=2))
    s.update_tracks([_p(0)])
    for miss in (1, 2):
        tracks, expired = s.update_tracks([])
        assert [(t.det_idx, t.miss_frames) for t in tracks] == [(None, miss)]
        assert expired == []
    tracks, expired = s.update_tracks([])
    assert tracks == [] and expired == [0]


def test_update_unchanged_for_confirmed_visible_tracks():
    s = BlobStabilizer(StabilizerConfig(min_confirm_frames=2, smoothing_alpha=0.5))
    s.update([_p(0)])
    out = s.update([_p(10)])
    assert [b.stable_id for b in out] == [0]
    assert out[0].world_pos_cm[0] == 5.0
    assert s.update([]) == []                         # missed: tracked, not reported
