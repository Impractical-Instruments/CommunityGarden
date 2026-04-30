"""
Blob stabilizer: cross-frame ID assignment and position de-jittering.

After each BlobTracker.detect() call, transform raw detections to world space
and pass them to BlobStabilizer.update() to get back TrackedBlob objects with
stable integer IDs and EMA-smoothed positions.

Matching uses greedy nearest-neighbour with a configurable maximum distance.
Smoothing uses exponential moving average (EMA).
"""

from __future__ import annotations

from dataclasses import dataclass, fields as _dc_fields

import numpy as np


@dataclass
class StabilizerConfig:
    # Maximum distance (cm) to match a detection to an existing track.
    max_match_dist_cm: float = 80.0
    # EMA smoothing factor applied to position each frame.
    # 1.0 = no smoothing (take new position directly).
    # 0.0 = frozen (ignore new positions entirely).
    # Typical range: 0.2–0.5 — lower is smoother but laggier.
    smoothing_alpha: float = 0.3
    # Frames a track can go unmatched before it is dropped.
    max_miss_frames: int = 8
    # Frames a new track must be seen consecutively before it appears in output.
    # Filters one-shot phantom detections.
    min_confirm_frames: int = 2

    @classmethod
    def from_dict(cls, raw: dict) -> "StabilizerConfig":
        known = {f.name for f in _dc_fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in known})


@dataclass
class TrackedBlob:
    stable_id: int
    world_pos_cm: np.ndarray


class _Track:
    __slots__ = ("track_id", "smoothed_pos", "miss_frames", "seen_frames")

    def __init__(self, track_id: int, pos: np.ndarray) -> None:
        self.track_id = track_id
        self.smoothed_pos = pos.copy()
        self.miss_frames = 0
        self.seen_frames = 1

    def update(self, pos: np.ndarray, alpha: float) -> None:
        self.smoothed_pos = alpha * pos + (1.0 - alpha) * self.smoothed_pos
        self.miss_frames = 0
        self.seen_frames += 1

    def mark_missing(self) -> None:
        self.miss_frames += 1


class BlobStabilizer:
    """
    Maintains cross-frame blob identity and smooths positions with EMA.

    Each call to update() performs three steps:
      1. Associate this frame's raw detections to existing tracks via greedy
         nearest-neighbour matching (within max_match_dist_cm).
      2. Update matched tracks with EMA-smoothed positions; increment miss
         counter on unmatched tracks; spawn new tracks for unmatched detections.
      3. Drop tracks that have been missing for more than max_miss_frames.

    Only tracks that have been confirmed (seen for at least min_confirm_frames
    consecutive frames) are included in the returned list.

    Usage:
        stabilizer = BlobStabilizer(StabilizerConfig())
        # Each detection frame:
        tracked = stabilizer.update(world_positions_cm)
    """

    def __init__(self, config: StabilizerConfig | None = None) -> None:
        self.config = config or StabilizerConfig()
        self._next_id: int = 0
        self._tracks: dict[int, _Track] = {}

    def update(self, detections: list[np.ndarray]) -> list[TrackedBlob]:
        """
        Associate detections to tracks, smooth positions, and return confirmed blobs.

        detections: world-space positions (cm) from this frame, shape (3,) each.
        Returns a list of TrackedBlob with stable IDs and smoothed positions.
        """
        cfg = self.config
        max_dist_sq = cfg.max_match_dist_cm ** 2

        matched: list[tuple[int, int]] = []          # (track_id, det_idx)
        matched_track_ids: set[int] = set()
        matched_det_idxs: set[int] = set()

        if self._tracks and detections:
            track_ids = list(self._tracks.keys())
            track_pos = np.stack(
                [self._tracks[tid].smoothed_pos for tid in track_ids], axis=0
            )  # (T, 3)
            det_pos = np.stack(detections, axis=0)  # (D, 3)

            # Squared Euclidean distance matrix (T × D)
            diff = track_pos[:, np.newaxis, :] - det_pos[np.newaxis, :, :]  # (T, D, 3)
            dist_sq = (diff ** 2).sum(axis=2)  # (T, D)

            # Greedy: repeatedly consume the globally smallest unmatched pair.
            remaining_ti = set(range(len(track_ids)))
            remaining_di = set(range(len(detections)))

            while remaining_ti and remaining_di:
                # Build view with only remaining entries; mask out consumed ones.
                masked = np.full_like(dist_sq, np.inf)
                for ti in remaining_ti:
                    for di in remaining_di:
                        masked[ti, di] = dist_sq[ti, di]

                min_val = float(masked.min())
                if min_val > max_dist_sq:
                    break

                ti, di = np.unravel_index(masked.argmin(), masked.shape)
                ti, di = int(ti), int(di)

                matched.append((track_ids[ti], di))
                matched_track_ids.add(track_ids[ti])
                matched_det_idxs.add(di)
                remaining_ti.discard(ti)
                remaining_di.discard(di)

        # Update matched tracks.
        for track_id, det_idx in matched:
            self._tracks[track_id].update(detections[det_idx], cfg.smoothing_alpha)

        # Mark unmatched tracks as missing.
        for track_id in self._tracks:
            if track_id not in matched_track_ids:
                self._tracks[track_id].mark_missing()

        # Spawn new tracks for unmatched detections.
        for det_idx in range(len(detections)):
            if det_idx not in matched_det_idxs:
                self._tracks[self._next_id] = _Track(self._next_id, detections[det_idx])
                self._next_id += 1

        # Expire stale tracks.
        expired = [
            tid for tid, t in self._tracks.items()
            if t.miss_frames > cfg.max_miss_frames
        ]
        for tid in expired:
            del self._tracks[tid]

        # Return only confirmed, currently-visible tracks.
        return [
            TrackedBlob(stable_id=t.track_id, world_pos_cm=t.smoothed_pos.copy())
            for t in self._tracks.values()
            if t.seen_frames >= cfg.min_confirm_frames and t.miss_frames == 0
        ]
