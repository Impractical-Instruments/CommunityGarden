"""
Screen calibration — 4-corner homography from camera pixel space to screen UV.

The user physically touches 4 projected corner markers in sequence:
  0: top-left     → screen UV (inset, inset)
  1: top-right    → screen UV (1-inset, inset)
  2: bottom-right → screen UV (1-inset, 1-inset)
  3: bottom-left  → screen UV (inset, 1-inset)

`corner_inset` (default 0.05) is the fraction Godot insets the markers from
the projected image edge so they are easily touchable.  main.py reads
`next_corner_uv` and sends it to Godot so Godot knows where to render the dot.

Once all 4 corners are recorded, `is_complete` becomes True and `to_uv(px, py)`
maps any camera pixel to a screen UV coordinate.

The calibration is serialised to JSON for persistence across runs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_CORNER_NAMES = ["top-left", "top-right", "bottom-right", "bottom-left"]


def _corner_uvs(inset: float) -> list[tuple[float, float]]:
    """Return the 4 UV coordinates that Godot projects markers at."""
    i = inset
    return [
        (i,     i    ),  # top-left
        (1 - i, i    ),  # top-right
        (1 - i, 1 - i),  # bottom-right
        (i,     1 - i),  # bottom-left
    ]


def _compute_homography(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """
    Compute the 3×3 homography H such that dst ~ H * src (homogeneous coords),
    using the Direct Linear Transform with 4 point pairs.

    src, dst: float arrays of shape (4, 2).
    Returns H normalised so H[2, 2] == 1.
    """
    A = np.zeros((8, 9), dtype=np.float64)
    for i, ((x, y), (u, v)) in enumerate(zip(src, dst)):
        A[2 * i]     = [-x, -y, -1,  0,  0,  0, u * x, u * y, u]
        A[2 * i + 1] = [ 0,  0,  0, -x, -y, -1, v * x, v * y, v]
    _, _, Vt = np.linalg.svd(A)
    h = Vt[-1]
    H = h.reshape(3, 3)
    return H / H[2, 2]


class ScreenCalibration:
    """
    Collects 4 corner pixel positions, computes the homography, and maps
    camera pixels → screen UV [0, 1] × [0, 1].

    Usage:
        cal = ScreenCalibration(corner_inset=0.05)

        while not cal.is_complete:
            # Show user: cal.next_corner_name, cal.next_corner_uv
            # Wait for a touch, then:
            cal.add_corner(touch_px, touch_py)

        u, v = cal.to_uv(px, py)   # 0..1 each, or None if outside screen
        cal.save("calibration.json")

        # Later:
        cal = ScreenCalibration.load("calibration.json")
    """

    def __init__(self, corner_inset: float = 0.05) -> None:
        self.corner_inset = corner_inset
        self._target_uvs = _corner_uvs(corner_inset)
        self._recorded_pixels: list[tuple[float, float]] = []
        self._H: np.ndarray | None = None  # set once all 4 corners collected

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    @property
    def corners_recorded(self) -> int:
        return len(self._recorded_pixels)

    @property
    def is_complete(self) -> bool:
        return self._H is not None

    @property
    def next_corner_index(self) -> int | None:
        """Index of the next corner to collect, or None if complete."""
        if self.is_complete:
            return None
        return len(self._recorded_pixels)

    @property
    def next_corner_name(self) -> str | None:
        idx = self.next_corner_index
        return _CORNER_NAMES[idx] if idx is not None else None

    @property
    def next_corner_uv(self) -> tuple[float, float] | None:
        idx = self.next_corner_index
        return self._target_uvs[idx] if idx is not None else None

    @property
    def recorded_pixels(self) -> list[tuple[float, float]]:
        """Camera pixel coordinates that have been recorded so far (0–4 entries)."""
        return list(self._recorded_pixels)

    @property
    def corner_uvs(self) -> list[tuple[float, float]]:
        """The 4 target UV coordinates Godot projects calibration markers at."""
        return list(self._target_uvs)

    def add_corner(self, pixel_x: float, pixel_y: float) -> int:
        """
        Record the camera pixel for the next expected corner.
        Returns the corner index just recorded.
        Raises RuntimeError if already complete.
        """
        if self.is_complete:
            raise RuntimeError("Calibration already complete")
        idx = len(self._recorded_pixels)
        self._recorded_pixels.append((pixel_x, pixel_y))
        if len(self._recorded_pixels) == 4:
            self._finalise()
        return idx

    def _finalise(self) -> None:
        src = np.array(self._recorded_pixels, dtype=np.float64)    # camera pixels
        dst = np.array(self._target_uvs, dtype=np.float64)          # screen UV
        self._H = _compute_homography(src, dst)

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    def to_uv(self, pixel_x: float, pixel_y: float) -> tuple[float, float] | None:
        """
        Map a camera pixel to screen UV.
        Returns None if not yet calibrated or if the point projects outside [0,1]².
        """
        if self._H is None:
            return None
        p = self._H @ np.array([pixel_x, pixel_y, 1.0], dtype=np.float64)
        u = p[0] / p[2]
        v = p[1] / p[2]
        if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
            return None
        return float(u), float(v)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        if self._H is None:
            raise RuntimeError("Cannot save incomplete calibration")
        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "corner_inset": self.corner_inset,
            "recorded_pixels": self._recorded_pixels,
            "homography": self._H.tolist(),
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "ScreenCalibration":
        data = json.loads(Path(path).read_text())
        cal = cls(corner_inset=data.get("corner_inset", 0.05))
        cal._recorded_pixels = [tuple(p) for p in data["recorded_pixels"]]
        cal._H = np.array(data["homography"], dtype=np.float64)
        # Rebuild target UVs in case inset changed between saves.
        cal._target_uvs = _corner_uvs(cal.corner_inset)
        return cal
