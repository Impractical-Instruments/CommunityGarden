"""Tests for BodyGridActivator."""
from __future__ import annotations

import numpy as np
import pytest

from body_grid import BodyGridActivator, BodyGridConfig, SlabConfig


SLAB_0 = SlabConfig(near_mm=800, far_mm=2500, slab_id=0)
SLAB_1 = SlabConfig(near_mm=2500, far_mm=4000, slab_id=1)

_FULL_ROI = {"x": 0, "y": 0, "w": 100, "h": 100}


def _cfg(
    cols: int = 4,
    rows: int = 4,
    roi: dict | None = None,
    slabs: list[SlabConfig] | None = None,
    threshold: float = 0.30,
    rule: str = "additive",
) -> BodyGridConfig:
    return BodyGridConfig(
        cols=cols,
        rows=rows,
        camera_roi=roi or _FULL_ROI,
        slabs=slabs or [SLAB_0],
        cell_activation_threshold=threshold,
        activation_rule=rule,
    )


def _fg(h: int = 100, w: int = 100, fill: int = 0) -> np.ndarray:
    return np.full((h, w), fill, dtype=np.uint16)


# ── Basic activation ───────────────────────────────────────────────────────────

def test_empty_frame_no_activations():
    fg = _fg()
    result = BodyGridActivator(_cfg()).activate(fg)
    assert result == {}


def test_full_coverage_all_cells_active():
    fg = _fg(fill=1000)  # 1000mm, inside SLAB_0 (800–2500)
    result = BodyGridActivator(_cfg(cols=4, rows=4)).activate(fg)
    assert len(result) == 16
    for (col, row), slabs in result.items():
        assert len(slabs) == 1
        slab_id, coverage = slabs[0]
        assert slab_id == 0
        assert abs(coverage - 1.0) < 0.01


def test_coverage_below_threshold_no_activation():
    fg = _fg()
    # Fill top 20 rows → 20% coverage; threshold=0.30
    fg[:20, :] = 1000
    result = BodyGridActivator(_cfg(cols=1, rows=1, threshold=0.30)).activate(fg)
    assert result == {}


def test_coverage_above_threshold_activates():
    fg = _fg()
    fg[:40, :] = 1000  # 40% > 0.30
    result = BodyGridActivator(_cfg(cols=1, rows=1, threshold=0.30)).activate(fg)
    assert (0, 0) in result


def test_coverage_fraction_accuracy():
    fg = _fg()
    fg[:50, :] = 1000  # exactly 50%
    result = BodyGridActivator(_cfg(cols=1, rows=1, threshold=0.30)).activate(fg)
    assert (0, 0) in result
    _, coverage = result[(0, 0)][0]
    assert abs(coverage - 0.50) < 0.02


def test_pixels_outside_all_slabs_not_counted():
    fg = _fg(fill=5000)  # 5000mm, above SLAB_0 far_mm (2500)
    result = BodyGridActivator(_cfg()).activate(fg)
    assert result == {}


def test_zero_pixels_background_not_counted():
    fg = _fg(fill=0)  # all zeros = background
    result = BodyGridActivator(_cfg()).activate(fg)
    assert result == {}


# ── Multi-slab ─────────────────────────────────────────────────────────────────

def test_multiple_slabs_both_reported():
    fg = _fg()
    fg[:50, :] = 1000   # slab 0 (800–2500): 50%
    fg[50:, :] = 3000   # slab 1 (2500–4000): 50%
    result = BodyGridActivator(_cfg(cols=1, rows=1, slabs=[SLAB_0, SLAB_1])).activate(fg)
    assert (0, 0) in result
    slab_ids = {sid for sid, _ in result[(0, 0)]}
    assert slab_ids == {0, 1}


def test_additive_rule_sums_coverages():
    # Each slab: 20% coverage; additive = 40% > 30% threshold
    fg = _fg()
    fg[:20, :] = 1000  # slab 0: 20%
    fg[20:40, :] = 3000  # slab 1: 20%
    result = BodyGridActivator(_cfg(
        cols=1, rows=1, slabs=[SLAB_0, SLAB_1], threshold=0.30, rule="additive",
    )).activate(fg)
    assert (0, 0) in result


def test_max_rule_takes_maximum():
    # Each slab: 20% coverage; max = 20% < 30% threshold → no activation
    fg = _fg()
    fg[:20, :] = 1000  # slab 0: 20%
    fg[20:40, :] = 3000  # slab 1: 20%
    result = BodyGridActivator(_cfg(
        cols=1, rows=1, slabs=[SLAB_0, SLAB_1], threshold=0.30, rule="max",
    )).activate(fg)
    assert result == {}


def test_max_rule_activates_when_one_slab_exceeds_threshold():
    fg = _fg()
    fg[:40, :] = 1000   # slab 0: 40% > 30%
    fg[40:60, :] = 3000  # slab 1: 20%
    result = BodyGridActivator(_cfg(
        cols=1, rows=1, slabs=[SLAB_0, SLAB_1], threshold=0.30, rule="max",
    )).activate(fg)
    assert (0, 0) in result


# ── Spatial mapping ────────────────────────────────────────────────────────────

def test_horizontal_flip_moves_left_to_right():
    # Blob on left half of frame → after flip → right column active
    fg = _fg()
    fg[:, :50] = 1000  # left half (x=0..49) in camera space
    result = BodyGridActivator(_cfg(cols=2, rows=1)).activate(fg)
    # After flip: left→right; col 1 = right half of display
    assert (1, 0) in result
    assert (0, 0) not in result


def test_horizontal_flip_moves_right_to_left():
    fg = _fg()
    fg[:, 50:] = 1000  # right half in camera space
    result = BodyGridActivator(_cfg(cols=2, rows=1)).activate(fg)
    assert (0, 0) in result
    assert (1, 0) not in result


def test_roi_excludes_pixels_outside():
    # Blob at top of frame; ROI covers bottom half only
    fg = _fg()
    fg[:20, :] = 1000  # rows 0–19, outside ROI
    roi = {"x": 0, "y": 50, "w": 100, "h": 50}
    result = BodyGridActivator(_cfg(cols=1, rows=1, roi=roi)).activate(fg)
    assert result == {}


def test_roi_includes_pixels_inside():
    fg = _fg()
    fg[60:90, :] = 1000  # inside ROI (y=50..100)
    roi = {"x": 0, "y": 50, "w": 100, "h": 50}
    result = BodyGridActivator(_cfg(cols=1, rows=1, roi=roi)).activate(fg)
    assert (0, 0) in result


def test_only_active_cells_in_result():
    fg = _fg()
    # Activate only top-left quarter of a 2×2 grid
    fg[:50, :50] = 1000  # after flip → top-right quarter (col=1, row=0)
    result = BodyGridActivator(_cfg(cols=2, rows=2)).activate(fg)
    assert len(result) == 1
    assert (1, 0) in result
