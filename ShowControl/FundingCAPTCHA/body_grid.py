"""
BodyGridActivator: foreground depth frame → activated grid cells with slab coverage.

Usage:
    config = BodyGridConfig(
        cols=4, rows=4,
        camera_roi={"x": 0, "y": 0, "w": 640, "h": 400},
        slabs=[SlabConfig(near_mm=800, far_mm=2500, slab_id=0)],
        cell_activation_threshold=0.30,
        activation_rule="additive",
    )
    activator = BodyGridActivator(config)

    # Each frame (foreground: uint16 H×W from BlobTracker.detect_foreground):
    activations = activator.activate(foreground_frame)
    # activations: {(col, row): [(slab_id, coverage_fraction), ...]}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np


@dataclass
class SlabConfig:
    near_mm: int
    far_mm: int
    slab_id: int


@dataclass
class BodyGridConfig:
    cols: int
    rows: int
    camera_roi: dict  # {"x": int, "y": int, "w": int, "h": int}
    slabs: list[SlabConfig]
    cell_activation_threshold: float = 0.30
    activation_rule: Literal["additive", "max"] = "additive"


# {(col, row): [(slab_id, coverage_fraction), ...]} — active cells only
CellActivations = dict[tuple[int, int], list[tuple[int, float]]]


class BodyGridActivator:
    def __init__(self, config: BodyGridConfig) -> None:
        self._cfg = config

    def activate(self, foreground: np.ndarray) -> CellActivations:
        """
        foreground: uint16 (H, W) from BlobTracker.detect_foreground()
                    0 = background, depth_mm = foreground pixel

        Returns active cells with per-slab coverage fractions.
        Only cells whose effective coverage (per activation_rule) meets
        cell_activation_threshold are included.
        """
        cfg = self._cfg
        roi = cfg.camera_roi

        flipped = foreground[:, ::-1]
        cropped = flipped[roi["y"]:roi["y"] + roi["h"], roi["x"]:roi["x"] + roi["w"]]

        roi_h, roi_w = cropped.shape
        result: CellActivations = {}

        for row in range(cfg.rows):
            y0 = int(row * roi_h / cfg.rows)
            y1 = int((row + 1) * roi_h / cfg.rows)
            for col in range(cfg.cols):
                x0 = int(col * roi_w / cfg.cols)
                x1 = int((col + 1) * roi_w / cfg.cols)
                cell = cropped[y0:y1, x0:x1]
                total = cell.size
                if total == 0:
                    continue

                slab_coverages: list[tuple[int, float]] = []
                for slab in cfg.slabs:
                    mask = (cell > 0) & (cell >= slab.near_mm) & (cell < slab.far_mm)
                    coverage = float(mask.sum()) / total
                    if coverage > 0:
                        slab_coverages.append((slab.slab_id, coverage))

                if not slab_coverages:
                    continue

                if cfg.activation_rule == "additive":
                    effective = sum(c for _, c in slab_coverages)
                else:
                    effective = max(c for _, c in slab_coverages)

                if effective >= cfg.cell_activation_threshold:
                    result[(col, row)] = slab_coverages

        return result
