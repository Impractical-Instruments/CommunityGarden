# FundingCAPTCHA uses body silhouette interaction, not touch detection

**Supersedes:** ADR-0004 (depth-primary touch detection), ADR-0011 (screen calibration and projection)

## Context

The original FundingCAPTCHA design assumed Players touch a projected Screen. The depth camera was co-mounted with the projector, detecting finger contacts close to the projection surface. Field testing showed the camera-to-screen-plane calibration and the projector IR interference problem (ADR-0004) made reliable touch detection impractical as a show-day interaction.

## Decision

The camera is remounted to face outward toward Players rather than at the Screen. Players interact by making shapes with their bodies — their silhouettes, captured via depth background subtraction, activate cells on a projected grid overlay.

Key consequences:

**ScreenProjector is removed.** There is no screen plane to project onto. Camera pixels map to display pixels via a camera-mounting correction: the camera thread calls `apply_cam_transform()` (see `silhouette.py`) which reprojects the depth frame to appear as though the camera is centred on the screen — compensating for physical mounting position and orientation — then mirrors horizontally so players see a natural mirror view. ROI crop is applied downstream in `BodyGridActivator`. Games and screensavers receive a fully corrected, display-space frame and must not flip.

**CORNER_CAL is removed.** The per-installation corner-touch calibration step (operator touching three screen corners) is eliminated. BG_CAL (background model collection at startup) remains.

**Blob detection is not used by FundingCAPTCHA.** The camera thread calls IIVision's `Calibrator` and background subtraction, then emits raw foreground depth frames. The `run_pipeline()` call (blob detection + stabilisation) is skipped. Grid cell activation is computed directly from per-pixel depth values.

**Grid activation is per-pixel, not per-blob.** A cell activates when ≥ `cell_activation_threshold` (configurable, default 0.30) of its pixels are covered by a given Depth Slab. This produces smooth, intuitive silhouette-fills rather than point-contact events.

## Play Zone and Depth Slabs

The depth range in front of the camera is partitioned into Depth Slabs. Each slab has a `near_mm`, `far_mm`, and `slab_id`. Pixels in a slab contribute to the silhouette with that slab's color and game role. Pixels below the nearest slab's `near_mm` (the implicit "too close" exclusion zone) are discarded — this prevents a Player standing directly in front of the camera from filling the entire frame.

Two slabs may share a `slab_id` (non-contiguous bands, identical behavior). Games may use `slab_id` to distinguish foreground depth layers with different visual or gameplay functions.

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

## Arc state machine

```
Screensaver
  → (foreground pixel count ≥ min_foreground_pixels for attract_dwell_s)
  → Arc begins — Level drawn from difficulty-1 pool
    → (valid_cells covered exactly, held for hold_s)
      → Level drawn from same-difficulty or +1 pool (shuffle-bag)
    → (timer expires)
      → Blow-Up (random taunt + confetti animation)
      → Screensaver
```

`attract_dwell_s` and `min_foreground_pixels` are global config values. The Arc starts on the first frame after the dwell countdown completes. There is no win condition — the Arc always ends in a Blow-Up.

**Hold mechanic:** A Level is beaten when the Player's silhouette covers all `valid_cells` and no non-target cells simultaneously for a continuous `hold_s` duration. Covering any extra cell resets the hold timer.

**Screensaver:** Rotates generative visual modules from `ScreenSavers/`. Each module is a Python file in that directory with a `create(settings)` factory and `update(dt, foreground_frame)` / `draw(surf)` interface. When a Player is detected during the Screensaver, their silhouette is rendered at configurable opacity with a "Game starts in…" countdown overlay. `foreground_frame` is always passed to screensaver modules (None when no camera) so modules may incorporate live depth data.

**Blow-Up:** On timer expiry the current game image shatters into a confetti particle animation. A randomly selected taunt string (from `taunts.json`) is displayed. Defaults to "Too Slow! You're not a robot."

## Level format

Levels are authored as a JSON array in a per-Game config file. Each entry:

```json
{
  "prompt": "Select all motorcycles",
  "image": "motorcycles.jpg",
  "difficulty": 3,
  "grid": [4, 4],
  "valid_cells": [[col, row], ...],
  "timer_s": 30,
  "hold_s": 1.0,
  "hint_opacity": 0.1
}
```

`timer_s`, `hold_s`, and `hint_opacity` are optional per-Level overrides; game-wide defaults apply when absent. `difficulty` is designer-assigned 1–5 and drives both Arc progression and the Intensity signal.

Arc progression uses a shuffle-bag over eligible Levels: after beating a Level, the next Level is drawn from all Levels whose `difficulty` equals the current Level's difficulty or is one higher. There is no fixed ordering and no overall win condition — the Arc always ends in a Blow-Up when a Level's timer expires.

## Alternatives considered

**Keep touch detection, fix the IR interference problem.** IR amplitude masking (ADR-0004) was the next step. Rejected because the physical interaction — reaching toward a projected surface — was observed to be confusing and awkward for festival visitors. The body-silhouette interaction is more immediately legible and more thematically resonant (the machine is watching your whole body, not just your fingertip).

**Use blob centroids for grid activation.** Centroid-based activation was considered and rejected. A blob centroid is a single point; filling a grid cell requires area coverage. Per-pixel threshold gives natural, spatially-intuitive results: you fill cells by physically occupying them with your body.

## Consequences

- `screen_projector.py` is deleted.
- `CornerCal` and `CORNER_CAL` state are removed from `app.py`.
- Camera thread outputs foreground depth frames (numpy arrays) instead of blob track lists.
- `captcha-settings.json` gains `depth_slabs`, `slab_styles`, `cell_activation_threshold`, `attract_dwell_s`, and `camera_roi` (crop, display-space coordinates). `camera.pos_cm` and `camera.rotation` (pitch/yaw/roll) drive the reprojection. Screen corner fields are removed.
- `silhouette.py` provides `build_cam_transform(settings)` and `apply_cam_transform(fg, intrinsics, transform)`. Both camera entry points (`app.py`, `body_grid_tester.py`) use these. Games must not flip or reproject — frames arrive display-ready.
- `games/grid.py` `blob_to_cell()` is replaced by pixel-to-cell logic operating on the slab mask.
- UpsideDown, Rhythm, and Keepaway must be ported to the silhouette interaction model. Design docs in `docs/games/`. Code deleted pending port.
- BodyGrid is the first Game built for this interaction model.
