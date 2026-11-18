# Architecture & Pipeline

The directory tree is in [the repo map](../repo-map.md). The shared vision library's modules are in [`IIVision/README.md`](../../IIVision/README.md).

## OSCFabric — cross-element messaging

`ShowControl/OSCFabric/` wraps `python-osc` and reads addresses from `network.json`. Use `FabricClient` for any outbound OSC that crosses Element boundaries (e.g. FlowerBeds → TreeHouse). Every address is in [`docs/osc-fabric.md`](../osc-fabric.md).

## Blob detection (BlobDetector)

Runs per frame once calibrated:

1. **Background subtraction** — per-pixel depth delta vs median background
2. **Majority filter ×2** — 3×3 neighbourhood despeckle
3. **Connected components** — 8-connected blobs via `scipy.ndimage.label`
4. **3D unproject** — pinhole model, median-Z windowing, camera → world coordinates

`BlobDetector` reads any background model with `background`, `valid_mask` and `threshold()`. FlowerBeds uses `Calibration`: `Calibrator` collects `calibration_frames` frames (from `settings.json`) to build a per-pixel median background and validity mask. FundingCAPTCHA uses `AdaptiveBackground` (`adaptive_background.py`, ADR-0023), learned continuously from the first frame — the farthest steady depth wins.

## Blob stabilisation (BlobStabilizer)

- Greedy nearest-neighbour matching within `max_match_dist_cm`
- EMA smoothing: `pos = alpha * new + (1 - alpha) * prev`
- Drops tracks missing for more than `max_miss_frames` frames
- Suppresses new tracks until seen for `min_confirm_frames` consecutive frames

The FlowerBeds pipeline, files and tools are in [`docs/FlowerBeds.md`](../FlowerBeds.md).
