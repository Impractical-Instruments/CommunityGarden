# FundingCAPTCHA uses three-corner orthographic projection for Screen mapping

Touch detection in FundingCAPTCHA maps raw world-space blob positions (cm, from IIVision) onto the Screen surface so that games can work in normalised UV coordinates and grid cells. The Screen is a vertical projection surface whose physical corners are measured once during installation setup.

## Architecture

**Calibration** (`touch_calibration.py --camera` or `--mock-camera`):

The calibration tool enters corner-capture mode when `screen_corners` in `captcha-settings.json` are null or `--recalibrate` is passed. A Player touches each of three Screen corners in order (BOTTOM-LEFT → BOTTOM-RIGHT → TOP-LEFT); the tool detects the blob, waits for dwell stability, then writes the world-space coordinates directly to `captcha-settings.json`. No manual transcription required.

**Projection** (`ScreenProjector`):

`ScreenProjector` takes the three calibrated corners and constructs a screen-local coordinate frame: U-axis along the bottom edge, V-axis along the left edge, normal = U × V. Given any world-space blob position, it orthographically projects onto the screen plane and returns (u, v) ∈ [0,1]². Values outside that range are off-screen. This handles tilted or non-axis-aligned screens correctly.

`ScreenProjector` also exposes `plane_distance(xyz) -> float` (signed cm distance from the screen plane; positive = camera side) and `in_bounds_3d(xyz, max_dist) -> bool` (combines UV bounds check with `0 < d <= max_dist`). Callers use these to gate touch registration to blobs physically close to the screen surface, rejecting hovering hands that project to valid UV coordinates but are too far from the plane.

**Grid mapping**:

(u, v) maps to (col, row) with v=1 at the top of the Screen (row 0). Games define their own grid dimensions; `ScreenProjector.uv_to_cell()` does the conversion.

**Pygame games** consume `ScreenProjector` directly via `touch_input.py` — calibrate once, project each frame, map to grid cells. No additional coordinate config needed at the game layer.

## The `screen_rect` field

`captcha-settings.json` contains a legacy `screen_rect` (axis-aligned x0/x1/z0/z1 box). It was consumed only by the now-removed browser JS `TouchInput` layer. It is safe to delete from `captcha-settings.json`; the pygame client ignores it.

## Consequences

- Three physical corner measurements fully define the Screen's geometry for all subsequent runtime projection.
- `ScreenProjector` is the single projection implementation; pygame games should import and reuse it rather than duplicating the mapping logic.
- `min_depth_mm` / `max_depth_mm` in the `detection` section bound the depth range the CV pipeline considers; tuned for the ~3-foot projector standoff distance.
- `max_plane_dist_cm` (settings + `--max-plane-dist` CLI arg, default 30 cm) gates touch registration to blobs within that distance in front of the calibrated screen plane. Tune toward 5–10 cm once the calibration plane aligns with the physical screen surface. Blobs behind the plane (d ≤ 0) are always rejected. Pygame games that import `ScreenProjector` opt in to this filter by calling `in_bounds_3d(xyz, max_dist)` instead of `in_bounds(u, v)`.
- If the Screen is physically moved or the camera is remounted, run `touch_calibration.py --recalibrate`. This sends `/captcha/restart` via OSC (port 9003) to trigger a hard camera restart and background re-calibration in server.py without restarting the service. The OSC message can also be sent from any OSC sender on the local network.
