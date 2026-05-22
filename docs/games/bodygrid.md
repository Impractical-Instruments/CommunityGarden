# Body Grid — input layer

Body Grid is the depth-camera input mechanism used by FundingCAPTCHA. It maps a Player's silhouette to a grid of boolean cell states. Any Game or tester that needs grid-based body input uses Body Grid.

## How it works

1. An Orbbec depth camera captures a raw depth frame.
2. Background subtraction + denoising (IIVision) produces a foreground depth frame.
3. `BodyGridActivator` partitions the frame into a configurable grid and evaluates each cell.
4. A cell is **active** when ≥ `cell_activation_threshold` (default 0.30) of its pixels are covered by a foreground pixel within any configured Depth Slab.

Cell states are boolean. Games and the tester consume the active-cell set each frame.

## BodyGridActivator

The `BodyGridActivator` class (in `games/grid.py`) owns cell activation:

- Takes a foreground depth frame and a slab mask.
- Returns a set of `(col, row)` pairs for active cells each frame.
- Grid dimensions and `cell_activation_threshold` are configurable per-Level (or game-wide via `captcha-settings.json`).

## Grid overlay

A reusable grid overlay abstraction (separate from any Game) renders the grid on screen. It draws cell boundaries and exposes raw active-cell state to its caller — no game-specific coloring. Games and the tester apply their own visual treatment on top.

## Depth Slabs

The Play Zone is defined as one or more Depth Slabs (`depth_slabs` in `captcha-settings.json`). Each slab has `near_mm`, `far_mm`, and `slab_id`. Pixels within a slab contribute to the silhouette. Pixels below the nearest slab's `near_mm` are discarded (too-close exclusion zone).

Two slabs may share a `slab_id` (non-contiguous bands, identical behavior).

Config shape:

```json
"depth_slabs": [
  {"near_mm": 800, "far_mm": 2500, "slab_id": 0}
],
"slab_styles": {
  "0": {"color": [0, 220, 100]}
},
"cell_activation_threshold": 0.30
```

## Standalone tester

`body_grid_tester.py` runs Body Grid in isolation — no Game context. Useful for tuning depth slabs, verifying activation thresholds, and checking camera reprojection. Displays the live silhouette with the grid overlay; logs active cells each frame.
