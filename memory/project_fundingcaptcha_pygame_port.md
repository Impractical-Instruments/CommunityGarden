---
name: FundingCAPTCHA silhouette interaction pivot
description: Interaction model, architecture, and TODO state after 2026-05-11 pivot to body silhouette input
type: project
---

Camera now faces Players (mounted on kiosk, pointing outward). Silhouette body interaction replaces touch detection entirely.

**Why:** Touch detection via co-mounted projector camera was impractical (IR interference, calibration fragility). Body silhouette interaction is more legible and thematically stronger.

**Architecture (ADR-0013, supersedes ADR-0004 + ADR-0011):**
- `screen_projector.py` deleted
- `CORNER_CAL` state removed from `app.py`
- Camera thread emits raw foreground depth frames (numpy), not blob tracks
- `run_pipeline()` (blob detection + stabilisation) not called
- Grid cells activate per-pixel: ≥ `cell_activation_threshold` coverage by a Depth Slab → active
- Depth Slabs: `[{near_mm, far_mm, slab_id}]` in `captcha-settings.json`; `slab_styles` maps slab_id → color
- BG_CAL still runs at startup (background model still needed)
- New `camera_roi` + horizontal flip config replaces corner calibration

**Arc state machine:**
- Screensaver → player detected for `attract_dwell_s` → Arc starts (Level 1)
- Win Level → next Level (harder: more cells, multi-slab, shorter timer)
- Timer expires → Blow-Up → Screensaver

**Level format (bodycaptcha-levels.json):**
`[{"timer_s": 30, "hold_s": 0.8, "grid": [4,4], "cells": [[col, row, slab_id], ...]}]`

**Difficulty axes:** cell count, pose complexity (single body can't cover), multi-slab requirement, timer duration.
**Stretch goal:** moving cells / distorting grid (Space Team-style) — log as issue when BodyCaptcha ships.

**Status (2026-05-11):** Docs done. Code TODO:
- [ ] Implement `BodyCaptcha` game (`games/bodycaptcha.py` + `bodycaptcha-levels.json`)
- [ ] Rewrite camera thread in `app.py` (raw depth frames, skip `run_pipeline`)
- [ ] Remove `CornerCal`, `CORNER_CAL` state, `ScreenProjector` from `app.py`
- [ ] Update `games/grid.py` (replace `blob_to_cell` with pixel-to-cell from slab mask)
- [ ] Update `captcha-settings.json` (add depth_slabs, slab_styles, cell_activation_threshold, attract_dwell_s, camera_roi; remove screen_corners fields)
- [ ] Delete `screen_projector.py`
- [ ] Delete `games/upsidedown.py`, `games/rhythm.py`, `games/keepaway.py` (design docs in `docs/games/`)
- [ ] Port UpsideDown to silhouette dwell interaction
- [ ] Port Rhythm to silhouette edge-detection interaction
- [ ] Port Keepaway to silhouette dwell interaction

**How to apply:** When working on FundingCAPTCHA, interaction is silhouette-based (depth pixels → slab mask → grid coverage), not touch/blob-track based. `ScreenProjector` is gone. `run_pipeline()` is not called. Design docs for old games in `docs/games/`.
