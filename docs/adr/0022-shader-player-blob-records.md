# ADR 0022 — Shader player blob records: boxes, stable IDs, lifecycle

**Status:** Accepted
**Amends:** [ADR-0021](0021-fundingcaptcha-shader-player.md)

## Context

ADR-0021 gives Setups the Body (Buffer A: `.r` presence, `.g` nearness) and nothing else about the people in it. Some Setups want to draw *the tracker itself*: a box per person, a stable number that follows them, and whether the tracker is unsure, sure, guessing, or has given up on them. The first is a debug view of the tracker, styled as a bird hunting visitors (the `hunter_bird` Setup). A shader can't recover identity across frames from a mask. Faking it in a buffer would show tracking bugs the real tracker doesn't have, and would hide the ones it does.

## Decision

1. **A new channel source, `"blobs"`.** It's bound like any other source in `setup.json`. On the Pi it's a `BLOB_SLOTS` × `BLOB_ROWS` (8 × 3) RGBA32F texture (constants in `blobs_contract.py`) with `NEAREST` filtering, read with `texelFetch(iChannelN, ivec2(slot, row), 0)`. This is the exception to "never `texelFetch`": records have a fixed layout, not a resolution.

   | Row | `.x` | `.y` | `.z` | `.w` |
   |---|---|---|---|---|
   | 0 — box | x0 | y0 | x1 | y1 |
   | 1 — motion | cx | cy | vx | vy |
   | 2 — identity | id | state | age_s | nearness |

   Positions are Body UV (y up, the same space as sampling Buffer A); velocity is UV per second. `id` is 1–999, exact even if a Setup copies it into a 16-bit buffer. `state` is 0 empty, 1 tentative, 2 confirmed, 3 coasting, 4 lost. `age_s` is seconds in the current state. `nearness` is the blob's mean `.g`.

2. **Slots are stable.** A track keeps its slot from birth to the end of its lost hold, so a Setup can keep per-slot state (trails, interest, lock) in its own buffers. When all eight slots are taken, further tracks aren't shown until a slot frees.

3. **Blobs come from the Body, not the camera frame.** `body_blobs.py` finds 8-connected regions in the packed Body (after reprojection and ROI crop) and runs IIVision's `BlobStabilizer` on their centroids in Body pixels. Boxes line up with the silhouette Setups see by construction. `BlobStabilizer` gains `update_tracks()`, which reports every live track (unconfirmed and missed ones included) with its matched detection and the IDs that expired. `update()` is unchanged.

4. **Lifecycle:** tentative until `min_confirm_frames` → confirmed → coasting while missed (the box drifts on its last velocity, slowing) → lost when the stabilizer drops it, held `lost_hold_s` → empty. A tentative track that expires goes straight to empty: it never was anyone.

5. **Camera rate in, render rate out.** Tracking runs once per camera frame (about 10 fps). Records are rebuilt every render frame, with box and centroid eased toward the latest camera estimate over `ease_s`, so boxes don't step at 10 Hz. Tunables are in `captcha-settings.json` → `shader_app.blobs`.

6. **Only while needed.** Tracking runs only while the current Setup binds `"blobs"`, and resets when a Setup that doesn't is playing.

7. **Prototyping.** In Shadertoy, `shaders/blob_painter.glsl` in a spare buffer stands in for the tracker. It mirrors `body_painter.glsl`'s people and controls, with the same layout and lifecycle. On the Pi, `--test-input` reads the painted Body back from the GPU at camera rate and runs the real tracker on it, so the boxes there are the real tracker's. `shaders/blob_debug/` is the reference reader.

## Consequences

- `scipy` is now always required by `shader_app.py`, not only with a camera.
- The blob painter's stand-in boxes are analytic (the painter's person shape), so in Shadertoy overlapping people get separate boxes where the real tracker would merge them into one blob.
- In Shadertoy the records are read from a buffer tab the Setup folder doesn't contain; `setup.json` names `"blobs"` where Shadertoy names that buffer. Setups that already use all of Buffers B–D can't prototype blobs in Shadertoy.
- Fixed with this change: the keyboard texture was created as an integer texture and read as 0 by every shader, so the painter's Shift, Space and C never worked in `--test-input`.
- Not yet measured on the Pi 5: tracking cost per camera frame (about 2.5 ms on a desktop x86 at 480 × 480), and how often mask flicker splits or merges a still person into new IDs. Tune `min_blob_pixels`, `max_match_dist_px` and the frame counts on site.
