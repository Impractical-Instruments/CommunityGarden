# FundingCAPTCHA uses three-corner orthographic projection for Screen mapping

Touch detection in FundingCAPTCHA maps raw world-space blob positions (cm, from IIVision) onto the Screen surface so that games can work in normalised UV coordinates and grid cells. The Screen is a vertical projection surface whose physical corners are measured once during installation setup.

## Architecture

**Calibration** (integrated into `app.py`):

Calibration runs automatically at startup if no saved calibration exists, or when the operator presses R. It is a state inside the unified app — not a separate tool. The app enters `BG_CAL` state (solid black frame, camera collects background model), then `CORNER_CAL` state (operator touches three screen corners in order: BOTTOM-LEFT → BOTTOM-RIGHT → TOP-LEFT). When all three corners are accepted, coordinates are written to `captcha-settings.local.json` and the app transitions to `LIVE`. Corner coordinates persist across restarts; the background model is rebuilt on each startup.

**Projection** (`ScreenProjector`):

`ScreenProjector` takes the three calibrated corners and constructs a screen-local coordinate frame: U-axis along the bottom edge, V-axis along the left edge, normal = U × V. Given any world-space blob position, it orthographically projects onto the screen plane and returns (u, v) ∈ [0,1]². Values outside that range are off-screen. This handles tilted or non-axis-aligned screens correctly.

`ScreenProjector` also exposes `plane_distance(xyz) -> float` (signed cm distance from the screen plane; positive = camera side) and `in_bounds_3d(xyz, max_dist) -> bool` (combines UV bounds check with `0 < d <= max_dist`). Callers use these to gate touch registration to blobs physically close to the screen surface, rejecting hovering hands that project to valid UV coordinates but are too far from the plane.

**Grid mapping**:

(u, v) maps to (col, row) with v=1 at the top of the Screen (row 0). Games define their own grid dimensions; `ScreenProjector.uv_to_cell()` does the conversion.

**Pygame games** consume `ScreenProjector` directly — calibrate once, project each frame, map to grid cells. No additional coordinate config needed at the game layer.

## The `screen_rect` field

`captcha-settings.json` previously contained a `screen_rect` (axis-aligned x0/x1/z0/z1 box) consumed only by the browser-game JS layer. The browser games have been replaced by native pygame games that use `ScreenProjector` directly. `screen_rect` has been removed.

## Consequences

- Three physical corner measurements fully define the Screen's geometry for all subsequent runtime projection.
- `ScreenProjector` is the single projection implementation; pygame games import and reuse it rather than duplicating the mapping logic.
- `min_depth_mm` / `max_depth_mm` in the `detection` section bound the depth range the CV pipeline considers; tuned for the ~3-foot projector standoff distance.
- `max_plane_dist_cm` (settings + `--max-plane-dist` CLI arg, default 10 cm) gates touch registration to blobs within that distance in front of the calibrated screen plane. Blobs behind the plane (d ≤ 0) are always rejected.
- If the Screen is physically moved or the camera is remounted, press R in `app.py` to wipe the saved calibration and redo both BG_CAL and CORNER_CAL. This also triggers a background model rebuild.
- The background model is rebuilt on every startup (not persisted to disk). Corner coordinates are persisted. This means the projector must be displaying black at startup — `app.py` handles this automatically.
