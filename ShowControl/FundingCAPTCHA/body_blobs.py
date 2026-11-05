"""Blob records for the shader player's "blobs" source (ADR-0022).

Blobs are found in the Body itself — the mask Setups see in Buffer A — so a
box always lines up with the silhouette it belongs to, whatever reprojection
and ROI crop made that Body. IDs come from IIVision's BlobStabilizer, run in
Body pixels rather than world cm.

  blobs = BodyBlobs(BlobConfig.from_dict(settings["shader_app"].get("blobs", {})))
  blobs.update(presence, nearness)   # per camera frame; arrays row 0 = bottom
  renderer.upload_blobs(blobs.records())   # per render frame

Lifecycle per slot: tentative (seen < min_confirm_frames) → confirmed →
coasting (missed; the box drifts on its last velocity) → lost (held for
lost_hold_s, then the slot empties). A tentative track that expires empties
its slot without passing through lost.
"""
from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass, fields as _dc_fields
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # IIVision, as app.py

from IIVision.blob_stabilizer import BlobStabilizer, StabilizerConfig
from shadertoy import (BLOB_COASTING, BLOB_CONFIRMED, BLOB_LOST, BLOB_ROWS,
                       BLOB_SLOTS, BLOB_TENTATIVE)

_VEL_ALPHA   = 0.5     # EMA on velocity, per camera frame
_COAST_DECAY = 0.85    # velocity kept per missed camera frame, so coasting boxes slow down


@dataclass
class BlobConfig:
    min_blob_pixels:    int   = 500     # smaller connected regions are ignored (Body pixels)
    min_confirm_frames: int   = 4       # camera frames a track stays tentative
    max_miss_frames:    int   = 8       # camera frames a track coasts before it is lost
    max_match_dist_px:  float = 80.0    # furthest a centroid may jump between frames (Body pixels)
    smoothing_alpha:    float = 0.5     # EMA on the centroid, per camera frame
    lost_hold_s:        float = 1.0     # how long a lost record stays in its slot
    ease_s:             float = 0.08    # render-rate easing between camera frames; 0 = raw

    @classmethod
    def from_dict(cls, raw: dict) -> "BlobConfig":
        known = {f.name for f in _dc_fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in known})


@dataclass
class Detection:
    bbox:     np.ndarray    # x0, y0, x1, y1 in Body pixels, max exclusive
    centroid: np.ndarray    # x, y in Body pixels
    nearness: float         # mean .g over the blob, 0–1
    pixels:   int


def find_blobs(presence: np.ndarray, nearness: np.ndarray, min_pixels: int) -> list[Detection]:
    """8-connected regions of `presence` with at least `min_pixels` texels."""
    labeled, n = ndimage.label(presence, structure=np.ones((3, 3), dtype=np.int32))
    if n == 0:
        return []
    counts = np.bincount(labeled.ravel(), minlength=n + 1)
    out = []
    # Stats inside each kept blob's own slice: ndimage's whole-image measurements
    # cost ~10 ms a frame at camera resolution.
    for i, sl in enumerate(ndimage.find_objects(labeled), start=1):
        if sl is None or counts[i] < min_pixels:
            continue
        sy, sx = sl
        mask   = labeled[sl] == i
        ys, xs = np.nonzero(mask)
        out.append(Detection(
            bbox     = np.array([sx.start, sy.start, sx.stop, sy.stop], dtype=np.float64),
            centroid = np.array([xs.mean() + sx.start + 0.5, ys.mean() + sy.start + 0.5]),
            nearness = float(nearness[sl][mask].mean()),
            pixels   = int(counts[i]),
        ))
    return out


def display_id(track_id: int) -> int:
    """Stable IDs grow all day; Setups get 1–999, exact in a 16-bit float buffer."""
    return 1 + track_id % 999


class _Record:
    __slots__ = ("slot", "id", "state", "since", "target", "shown", "centroid", "shown_c",
                 "vel", "nearness")

    def __init__(self, slot: int, track_id: int, now: float, det: Detection) -> None:
        self.slot     = slot
        self.id       = display_id(track_id)
        self.state    = BLOB_TENTATIVE
        self.since    = now
        self.target   = det.bbox.copy()
        self.shown    = det.bbox.copy()
        self.centroid = det.centroid.copy()
        self.shown_c  = det.centroid.copy()
        self.vel      = np.zeros(2)
        self.nearness = det.nearness


class BodyBlobs:
    def __init__(self, config: BlobConfig | None = None, clock=time.monotonic) -> None:
        self.config = config or BlobConfig()
        self._clock = clock
        self.reset()

    def reset(self) -> None:
        cfg = self.config
        self._stab = BlobStabilizer(StabilizerConfig(
            max_match_dist_cm  = cfg.max_match_dist_px,     # unit-agnostic: Body pixels here
            smoothing_alpha    = cfg.smoothing_alpha,
            max_miss_frames    = cfg.max_miss_frames,
            min_confirm_frames = cfg.min_confirm_frames,
        ))
        self._recs: dict[int, _Record] = {}            # track id → record
        self._size = (1, 1)
        self._last_update: float | None = None
        self._last_records: float | None = None

    @property
    def active(self) -> bool:
        return bool(self._recs) or self._last_update is not None

    def update(self, presence: np.ndarray, nearness: np.ndarray, now: float | None = None) -> None:
        """One camera frame of Body: presence bool (h, w), nearness 0–1 (h, w), row 0 = bottom."""
        now = self._clock() if now is None else now
        cfg = self.config
        h, w = presence.shape
        self._size = (w, h)
        dt = now - self._last_update if self._last_update is not None else 0.0
        self._last_update = now

        dets = find_blobs(presence, nearness, cfg.min_blob_pixels)
        tracks, expired = self._stab.update_tracks([d.centroid for d in dets])

        for t in tracks:
            r = self._recs.get(t.track_id)
            if r is None:
                if t.det_idx is None:
                    continue                            # never got a slot; nothing to show
                slot = self._free_slot()
                if slot is None:
                    continue                            # all slots taken; it may get one later
                r = self._recs[t.track_id] = _Record(slot, t.track_id, now, dets[t.det_idx])
            elif t.det_idx is not None:
                d = dets[t.det_idx]
                if dt > 0:
                    r.vel = r.vel + _VEL_ALPHA * ((t.smoothed_pos - r.centroid) / dt - r.vel)
                r.centroid = t.smoothed_pos.copy()
                r.target   = d.bbox.copy()
                r.nearness = d.nearness
            else:                                       # missed: drift on the last velocity
                step = r.vel * dt
                r.centroid = r.centroid + step
                r.target   = r.target + np.concatenate([step, step])
                r.vel      = r.vel * _COAST_DECAY

            state = (BLOB_TENTATIVE if t.seen_frames < cfg.min_confirm_frames
                     else BLOB_COASTING if t.miss_frames else BLOB_CONFIRMED)
            if state != r.state:
                r.state, r.since = state, now

        for tid in expired:
            r = self._recs.get(tid)
            if r is None:
                continue
            if r.state == BLOB_TENTATIVE:
                del self._recs[tid]
            else:
                r.state, r.since, r.vel = BLOB_LOST, now, np.zeros(2)
        self._drop_lost(now)

    def records(self, now: float | None = None) -> np.ndarray:
        """(BLOB_ROWS, BLOB_SLOTS, 4) float32 for Renderer.upload_blobs(); call per render frame."""
        now = self._clock() if now is None else now
        dt = now - self._last_records if self._last_records is not None else 0.0
        self._last_records = now
        ease = self.config.ease_s
        k = 1.0 if ease <= 0 else 1.0 - math.exp(-max(dt, 0.0) / ease)
        self._drop_lost(now)

        w, h = self._size
        out = np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32)
        for r in self._recs.values():
            r.shown   += (r.target - r.shown) * k
            r.shown_c += (r.centroid - r.shown_c) * k
            out[0, r.slot] = r.shown / (w, h, w, h)
            out[1, r.slot] = (r.shown_c[0] / w, r.shown_c[1] / h, r.vel[0] / w, r.vel[1] / h)
            out[2, r.slot] = (r.id, r.state, now - r.since, r.nearness)
        return out

    def _free_slot(self) -> int | None:
        used = {r.slot for r in self._recs.values()}
        return next((s for s in range(BLOB_SLOTS) if s not in used), None)

    def _drop_lost(self, now: float) -> None:
        hold = self.config.lost_hold_s
        for tid in [t for t, r in self._recs.items()
                    if r.state == BLOB_LOST and now - r.since >= hold]:
            del self._recs[tid]
