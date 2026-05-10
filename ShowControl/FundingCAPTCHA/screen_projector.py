"""Orthographic screen-plane projection for FundingCAPTCHA (ADR-0011)."""

from __future__ import annotations
import numpy as np


class ScreenProjector:
    """
    Maps world-space blob positions (cm) onto the Screen plane using
    three calibrated corners (bottom-left, bottom-right, top-left).

    Returns (u, v) ∈ [0,1]²; values outside that range are off-screen.
    v=0 is the bottom of the Screen, v=1 is the top.
    """

    def __init__(
        self,
        bottom_left:  list[float],
        bottom_right: list[float],
        top_left:     list[float],
    ) -> None:
        bl = np.array(bottom_left,  dtype=float)
        br = np.array(bottom_right, dtype=float)
        tl = np.array(top_left,     dtype=float)
        U        = br - bl
        V        = tl - bl
        self._w  = float(np.linalg.norm(U))
        self._h  = float(np.linalg.norm(V))
        self._U  = U / self._w
        self._V  = V / self._h
        n        = np.cross(self._U, self._V)
        self._n  = n / np.linalg.norm(n)
        self._bl = bl

    @property
    def aspect(self) -> float:
        return self._w / self._h

    def project(self, xyz: list[float]) -> tuple[float, float]:
        p       = np.array(xyz, dtype=float)
        p_plane = p - np.dot(p - self._bl, self._n) * self._n
        u = float(np.dot(p_plane - self._bl, self._U) / self._w)
        v = float(np.dot(p_plane - self._bl, self._V) / self._h)
        return u, v

    def plane_distance(self, xyz: list[float]) -> float:
        """Signed cm distance from point to screen plane. Positive = camera side."""
        return float(np.dot(np.array(xyz, dtype=float) - self._bl, self._n))

    def in_bounds_3d(self, xyz: list[float], max_dist: float) -> bool:
        """True if point is within screen UV rect and ≤ max_dist cm in front."""
        d = self.plane_distance(xyz)
        if not (0.0 < d <= max_dist):
            return False
        u, v = self.project(xyz)
        return 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0

    @staticmethod
    def uv_to_cell(u: float, v: float, cols: int, rows: int) -> tuple[int, int]:
        """Map (u,v) to (col, row). v=1 → row 0 (top of screen)."""
        col = int(u * cols)
        row = int((1.0 - v) * rows)
        return max(0, min(cols - 1, col)), max(0, min(rows - 1, row))
