"""
Self-learning depth background: "the farthest steady depth wins" (ADR-0023).

A person can only make a depth pixel nearer, never farther. So each pixel's
background is the farthest depth it has held steadily, learned continuously
from the first frame — with or without people in view. No standback, no
calibration pass, nothing saved to disk.

Per frame, for each pixel with a valid sample d (thr = max(depth_delta_mm,
noise_k × noise)):

  seed     first valid sample sets bg; valid after min_valid_frames samples
  at bg    |d − bg| ≤ thr  → slow EMA of bg and of the noise σ estimate
  farther  d > bg + thr for reveal_frames in a row → bg = mean of those samples
  nearer   d < bg − thr held steady (within thr) for absorb_s → bg = d
  bump     > reseed_fg_fraction of valid pixels nearer for reseed_after_s
           → reseed bg from the current frame

Exposes the same background / valid_mask / threshold() interface as
Calibration, so BlobTracker works with either.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, fields
from typing import Callable

import numpy as np

from .blob_tracker import FramePacket

log = logging.getLogger("IIVision.adaptive_background")

# Mean absolute deviation of a Gaussian ≈ 0.8σ.
_MAD_TO_SIGMA = 1.0 / 0.8


@dataclass
class AdaptiveBackgroundConfig:
    depth_delta_mm: float = 80        # lower bound on thr (DetectionConfig.depth_delta_mm)
    min_depth_mm: int = 50            # samples below this are invalid (0 = no return)
    min_valid_frames: int = 10        # valid samples before a pixel's bg is trusted
    reveal_frames: int = 5            # consecutive farther frames to move bg out
    noise_k: float = 4.0              # thr = max(depth_delta_mm, noise_k × σ)
    bg_alpha: float = 0.01            # per-frame EMA of bg at background
    noise_alpha: float = 0.05         # per-frame EMA of σ at background
    absorb_s: float = 300.0           # steady nearer reading becomes bg after this
    reseed_fg_fraction: float = 0.4   # bump guard: fraction of valid pixels in fg …
    reseed_after_s: float = 30.0      # … for this long → reseed
    stats_log_s: float = 30.0         # how often to log update timing (0 = never)

    @classmethod
    def from_dict(cls, d: dict, **overrides) -> "AdaptiveBackgroundConfig":
        """Build from a settings block; unknown keys (e.g. _comment) are ignored."""
        names = {f.name for f in fields(cls)}
        kw = {k: v for k, v in d.items() if k in names}
        kw.update(overrides)
        return cls(**kw)


class AdaptiveBackground:
    """
    Continuously learned background model.

    Usage:
        model   = AdaptiveBackground(AdaptiveBackgroundConfig(depth_delta_mm=30))
        tracker = BlobTracker(model, detection_config)
        for frame in camera.frames():
            model.push(frame)
            fg = tracker.detect_foreground(frame)

    Before the first push() width/height are 0; BlobTracker needs one push first.
    reseed() may be called from another thread: it takes effect on the next push.
    """

    def __init__(self, config: AdaptiveBackgroundConfig | None = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.config = config or AdaptiveBackgroundConfig()
        self._clock = clock
        self.width = 0
        self.height = 0
        self._reseed_pending = False
        self._crowd_since: float | None = None
        self.reseed_count = 0
        # Timing stats (wall-clock, independent of the injected clock).
        self.last_update_ms = 0.0
        self._stats_n = 0
        self._stats_sum_ms = 0.0
        self._stats_max_ms = 0.0
        self._stats_t0 = time.monotonic()

    # ------------------------------------------------------------------
    # Interface read by BlobTracker
    # ------------------------------------------------------------------

    @property
    def background(self) -> np.ndarray:
        """uint16 (H*W,): background depth in mm, 0 where not valid."""
        bg = np.rint(self._bg).astype(np.uint16)
        bg[~self.valid_mask] = 0
        return bg

    @property
    def valid_mask(self) -> np.ndarray:
        """bool (H*W,): pixel has had ≥ min_valid_frames valid samples."""
        return self._n_valid >= self.config.min_valid_frames

    @property
    def noise(self) -> np.ndarray:
        """float32 (H*W,): running σ estimate at background, mm."""
        return self._noise

    def threshold(self, depth_delta_mm: float) -> np.ndarray:
        """int32 (H*W,): per-pixel foreground threshold, mm."""
        return np.maximum(depth_delta_mm,
                          self.config.noise_k * self._noise).astype(np.int32)

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------

    def reseed(self) -> None:
        """Reseed the background from the next pushed frame."""
        self._reseed_pending = True

    def push(self, frame: FramePacket) -> None:
        """Update the model with one depth frame."""
        t_start = time.perf_counter()
        if self.width == 0:
            self._init_state(frame.width, frame.height)
        elif frame.width != self.width or frame.height != self.height:
            raise ValueError(
                f"Frame size {frame.width}x{frame.height} != model {self.width}x{self.height}")

        d = np.frombuffer(frame.data, dtype=np.uint16).astype(np.float32)
        self._update(d, self._clock())

        self.last_update_ms = (time.perf_counter() - t_start) * 1000.0
        self._record_stats()

    def _init_state(self, width: int, height: int) -> None:
        n = width * height
        self.width, self.height = width, height
        self._bg = np.zeros(n, dtype=np.float32)
        self._noise = np.zeros(n, dtype=np.float32)
        self._n_valid = np.zeros(n, dtype=np.uint16)
        self._reveal_n = np.zeros(n, dtype=np.uint16)
        self._reveal_sum = np.zeros(n, dtype=np.float32)
        self._absorb_ref = np.zeros(n, dtype=np.float32)
        self._absorb_t0 = np.zeros(n, dtype=np.float64)
        self._absorb_on = np.zeros(n, dtype=bool)

    def _update(self, d: np.ndarray, now: float) -> None:
        cfg = self.config
        ok = d >= cfg.min_depth_mm

        if self._reseed_pending:
            self._reseed_pending = False
            self._reseed(d, ok, "requested")
            return

        # 1. Seed: a pixel's first valid sample. Skip the other rules this frame.
        seeded = self._n_valid > 0
        new = ok & ~seeded
        self._bg[new] = d[new]
        self._noise[new] = cfg.depth_delta_mm
        self._n_valid[ok & (self._n_valid < cfg.min_valid_frames)] += 1

        live = ok & seeded
        thr = np.maximum(cfg.depth_delta_mm, cfg.noise_k * self._noise)
        diff = d - self._bg
        at_bg = live & (np.abs(diff) <= thr)
        farther = live & (diff > thr)
        nearer = live & (diff < -thr)

        # 2. At background: track slow drift and the noise level.
        self._bg[at_bg] += cfg.bg_alpha * diff[at_bg]
        sigma_sample = np.abs(diff[at_bg]) * _MAD_TO_SIGMA
        self._noise[at_bg] += cfg.noise_alpha * (sigma_sample - self._noise[at_bg])

        # Any valid sample that isn't farther breaks a reveal run; any that isn't
        # nearer breaks an absorb run.
        not_farther = live & ~farther
        self._reveal_n[not_farther] = 0
        self._reveal_sum[not_farther] = 0.0
        self._absorb_on[live & ~nearer] = False

        # 3. Farther: background revealed once it holds for reveal_frames.
        self._reveal_n[farther] += 1
        self._reveal_sum[farther] += d[farther]
        revealed = farther & (self._reveal_n >= cfg.reveal_frames)
        if revealed.any():
            self._bg[revealed] = self._reveal_sum[revealed] / self._reveal_n[revealed]
            self._reveal_n[revealed] = 0
            self._reveal_sum[revealed] = 0.0

        # 4. Nearer: steady for absorb_s → absorbed (a dropped bag, a moved table).
        steady = nearer & self._absorb_on & (np.abs(d - self._absorb_ref) <= thr)
        restart = nearer & ~steady
        self._absorb_ref[restart] = d[restart]
        self._absorb_t0[restart] = now
        self._absorb_on[restart] = True
        absorbed = steady & (now - self._absorb_t0 >= cfg.absorb_s)
        if absorbed.any():
            self._bg[absorbed] = d[absorbed]
            self._absorb_on[absorbed] = False

        # 5. Bump guard: most of the scene suddenly nearer and staying there.
        valid = self._n_valid >= cfg.min_valid_frames
        n_valid = int(np.count_nonzero(valid))
        fg_frac = (np.count_nonzero(nearer & valid) / n_valid) if n_valid else 0.0
        if fg_frac > cfg.reseed_fg_fraction:
            if self._crowd_since is None:
                self._crowd_since = now
            elif now - self._crowd_since >= cfg.reseed_after_s:
                log.warning("Background reseeded: %.0f%% of the scene has been foreground "
                            "for %.0fs (camera bumped?)", fg_frac * 100,
                            now - self._crowd_since)
                self._reseed(d, ok, "bump guard")
        else:
            self._crowd_since = None

    def _reseed(self, d: np.ndarray, ok: np.ndarray, reason: str) -> None:
        self._bg[ok] = d[ok]
        self._reveal_n[:] = 0
        self._reveal_sum[:] = 0.0
        self._absorb_on[:] = False
        self._crowd_since = None
        self.reseed_count += 1
        log.info("Background reseeded from current frame (%s)", reason)

    def _record_stats(self) -> None:
        ms = self.last_update_ms
        self._stats_n += 1
        self._stats_sum_ms += ms
        self._stats_max_ms = max(self._stats_max_ms, ms)
        if self.config.stats_log_s <= 0:
            return
        now = time.monotonic()
        if now - self._stats_t0 >= self.config.stats_log_s:
            log.info("Background update %dx%d: mean %.1f ms, max %.1f ms over %d frames; "
                     "%.0f%% of pixels valid",
                     self.width, self.height, self._stats_sum_ms / self._stats_n,
                     self._stats_max_ms, self._stats_n,
                     100.0 * np.count_nonzero(self.valid_mask) / max(1, self._n_valid.size))
            self._stats_t0 = now
            self._stats_n = 0
            self._stats_sum_ms = 0.0
            self._stats_max_ms = 0.0
