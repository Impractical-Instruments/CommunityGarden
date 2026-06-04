"""Tests for the shared silhouette renderer (depth → colored Play-Zone mask)."""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # headless: no real display

import numpy as np
import pygame

from silhouette import render_silhouette


_FULL_ROI = {"x": 0, "y": 0, "w": 4, "h": 4}
_SLAB = [{"near_mm": 800, "far_mm": 2500, "slab_id": 0}]
_COLOR = (10, 220, 80)


def _identity_surf(fg: np.ndarray, slabs=_SLAB, roi=None, color=_COLOR):
    """Render at 1:1 (w,h == roi w,h) so surface pixels map to fg pixels."""
    roi = roi or _FULL_ROI
    return render_silhouette(fg, slabs, roi, color, roi["w"], roi["h"])


def test_in_slab_pixel_is_colored():
    fg = np.zeros((4, 4), dtype=np.uint16)
    fg[1, 2] = 1500  # inside [800, 2500)
    surf = _identity_surf(fg)
    # fg[row=1, col=2] → surface pixel (x=2, y=1)
    assert surf.get_at((2, 1))[:3] == _COLOR


def test_out_of_slab_pixels_are_black():
    fg = np.zeros((4, 4), dtype=np.uint16)
    fg[1, 2] = 1500
    surf = _identity_surf(fg)
    assert surf.get_at((0, 0))[:3] == (0, 0, 0)  # depth 0 → outside slab
    assert surf.get_at((3, 3))[:3] == (0, 0, 0)


def test_slab_bounds_are_half_open():
    fg = np.zeros((4, 4), dtype=np.uint16)
    fg[0, 0] = 800   # near_mm — inclusive
    fg[1, 1] = 2500  # far_mm  — exclusive
    fg[2, 2] = 799   # just below near — excluded
    surf = _identity_surf(fg)
    assert surf.get_at((0, 0))[:3] == _COLOR        # 800 in
    assert surf.get_at((1, 1))[:3] == (0, 0, 0)     # 2500 out
    assert surf.get_at((2, 2))[:3] == (0, 0, 0)     # 799 out


def test_multiple_slabs_union():
    fg = np.zeros((4, 4), dtype=np.uint16)
    fg[0, 0] = 1500   # slab 0
    fg[3, 3] = 3000   # slab 1
    slabs = _SLAB + [{"near_mm": 2500, "far_mm": 4000, "slab_id": 1}]
    surf = _identity_surf(fg, slabs=slabs)
    assert surf.get_at((0, 0))[:3] == _COLOR
    assert surf.get_at((3, 3))[:3] == _COLOR


def test_roi_crop_and_scale_to_size():
    fg = np.zeros((8, 8), dtype=np.uint16)
    roi = {"x": 2, "y": 2, "w": 4, "h": 4}
    surf = render_silhouette(fg, _SLAB, roi, _COLOR, 200, 120)
    assert surf.get_size() == (200, 120)
