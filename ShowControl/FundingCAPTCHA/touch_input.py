"""
Blob-to-grid touch input for pygame games.

Wraps ScreenProjector + DwellTracker from touch_calibration.py.
Call update(blobs) each frame; on_tap(col, row) fires once per dwell.
"""
from __future__ import annotations

from touch_calibration import DwellTracker, ScreenProjector


class TouchInput:
    def __init__(
        self,
        cols: int,
        rows: int,
        screen_corners: dict,
        dwell_frames: int = 3,
        max_plane_dist_cm: float = 30.0,
        on_tap=None,
    ) -> None:
        self._cols           = cols
        self._rows           = rows
        self._dwell_frames   = dwell_frames
        self._max_dist       = max_plane_dist_cm
        self.on_tap          = on_tap  # callable(col, row) — set by orchestrator
        self._projector      = ScreenProjector(
            screen_corners["bottom_left"],
            screen_corners["bottom_right"],
            screen_corners["top_left"],
        )
        self._dwell          = DwellTracker(dwell_frames)
        self._prev_flashing: set[tuple[int, int]] = set()

    def resize(self, cols: int, rows: int) -> None:
        self._cols  = cols
        self._rows  = rows
        self._dwell = DwellTracker(self._dwell_frames)
        self._prev_flashing = set()

    def update(self, blobs: list[dict]) -> None:
        live: list[tuple[int, int, int]] = []
        for b in blobs:
            xyz = [b["x"], b["y"], b["z"]]
            if not self._projector.in_bounds_3d(xyz, self._max_dist):
                continue
            u, v = self._projector.project(xyz)
            if not ScreenProjector.in_bounds(u, v):
                continue
            col, row = ScreenProjector.uv_to_cell(u, v, self._cols, self._rows)
            live.append((int(b["id"]), col, row))

        prev = self._prev_flashing
        self._dwell.update(live)
        self._prev_flashing = self._dwell.flashing.copy()

        if self.on_tap:
            for cell in self._prev_flashing - prev:
                self.on_tap(cell[0], cell[1])
