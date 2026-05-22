# FundingCAPTCHA `--test-input` mode for camera-free game development

## Context

FundingCAPTCHA games are difficult to develop and iterate on without a real Orbbec depth camera attached. `--mock-camera` exists but uses IIVision's `MockCamera`, which generates synthetic noise — the game runs but receives random foreground data, making it impossible to test Level completion, Blow-Up timing, silhouette UX, or multi-slab behaviour.

## Decision

Add `--test-input [--test-depth N]` flags to `app.py`. When active:

1. **Camera thread not started.** `BG_CAL` phase is skipped — a `cal_done` signal is injected into `cam_q` immediately on startup. Game goes straight to `SCREENSAVER`.

2. **Paint canvas maintained.** A `uint16` numpy array at camera resolution (`cam_height × cam_width`, all zeros) acts as the live foreground frame.

3. **Mouse input paints the canvas.** Left-drag sets pixels under the cursor to `test_depth_mm`; right-drag sets them to 0 (erase). `C` key clears the entire canvas. Brush radius is fixed (a small disc, ~20px in camera space).

4. **Canvas pushed to `cam_q` each tick.** At the top of the main loop, before draining the queue, the current paint canvas is pushed as `{"type": "foreground", "frame": paint_canvas}`. This is byte-for-byte identical to what the camera thread produces.

5. **Paint overlay rendered on game surface.** Paint canvas is scaled to screen resolution and composited over the game at ~50% opacity in a distinct colour (cyan) so the developer can see what the game is receiving.

6. **`--test-depth N`** sets the depth value (mm) written by left-drag. Defaults to midpoint of the first configured Depth Slab. Lets developers test specific slab behaviour when multiple slabs are configured.

Zero changes to game code — every Game receives foreground frames through the normal `cam_q` path and calls `BodyGridActivator.activate()` as usual.

## Injection point: foreground frame level, not cell activation level

The alternative was to bypass `BodyGridActivator` entirely and let the developer toggle grid cells directly (click cell → active/inactive). This would be simpler to implement but would skip the `cell_activation_threshold`, slab filtering, and ROI masking logic — the exact code most likely to contain tuning bugs. Injecting at foreground frame level exercises the full pipeline.

## Mouse coordinate mapping

The paint canvas is in camera space (`cam_width × cam_height`). The game renders at screen resolution. Mouse positions must be mapped:

```
cam_x = int(mouse_x / screen_width  * cam_width)
cam_y = int(mouse_y / screen_height * cam_height)
```

No perspective correction needed — the injected frame represents a post-`apply_cam_transform` display-space frame, same as real camera output.

## Alternatives considered

**Separate tool (parallel to `body_grid_tester.py`):** Would keep `app.py` clean but splits the entry point. Developers debugging game feel need the full app context (shuffle-bag, Screensaver transition, OSC fabric, Blow-Up animation). A flag on `app.py` provides all of this with no duplication.

**Inject at cell activation level:** Simpler, but bypasses `BodyGridActivator` — can't catch threshold or slab edge cases. Also requires modifying game code to accept pre-cooked activations.

**Keyboard cell hotkeys:** Considered alongside mouse painting. Rejected — too awkward to express body shapes with hotkeys, and painting maps more naturally to what the camera sees.

## Consequences

- `app.py` gains a `TestInputHandler` class (~80–100 LOC): canvas state, mouse event handling, `cam_q` injection, overlay rendering.
- `--test-input` is mutually exclusive with `--camera` and `--mock-camera`.
- `--test-depth` is only meaningful with `--test-input`; silently ignored otherwise.
- `--mock-camera` is unaffected.
- `body_grid_tester.py` is unaffected.
