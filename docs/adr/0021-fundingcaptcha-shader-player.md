# FundingCAPTCHA shader player — Shadertoy Setups driven by the depth camera

## Context

Some events want the FundingCAPTCHA screen to show procedural visuals that visitors bend by moving, instead of the Game Arc. Several people need to prototype those visuals in parallel, without the show hardware, and the results must run on the show Pi 5 unchanged.

The existing app draws with pygame surfaces in software. Per-pixel procedural work there is too slow at projector resolution, and an OpenGL display can't be shared with that pygame drawing.

## Decision

1. **Prototype in Shadertoy; play GLSL on the Pi.** Shadertoy is WebGL2 / GLSL ES 3.00; the Pi 5 runs GL 3.3 core under Mesa (as ADR-0018). Shadertoy tabs are pasted verbatim into a **Setup** folder (`shaders/<name>/`) and wrapped with the Shadertoy uniform set at load time.

2. **Buffer A is the Body.** Every Setup reserves Buffer A. In Shadertoy it runs `shaders/body_painter.glsl`, where the mouse stands in for a visitor. On the Pi the Orbbec silhouette replaces it. Texel contract: `.r` presence 0/1, `.g` nearness 0 (far, `max far_mm` of the Depth Slabs) to 1 (near, `min near_mm`). Setups sample it with `texture()` — it is camera-ROI resolution on the Pi.

3. **`iMouse` follows the Body.** On the Pi, `iMouse.xy` is the presence centroid and `zw` follows Shadertoy's click semantics (positive while someone is present, `w` positive on the first frame). A mouse-driven prototype still responds to people.

4. **Separate entry point.** `shader_app.py` opens an OpenGL display and reuses `app.py`'s settings, camera thread, and calibration; it does not run Games. Passes render at `shader_app.render_scale` of the display and are upscaled.

5. **Rotation.** `shaders/setups.json` lists the Setups; each plays for its `duration_s`, shuffle-bag order (`arc.ShuffleBag`). A Setup that fails to compile is logged and skipped.

## Consequences

- Shadertoy can't take uploaded media; Setups are procedural plus the Body.
- Unsupported Shadertoy features: cubemaps, sound, video/texture inputs, per-channel filter/wrap settings (always linear + clamp), Buffer A code.
- Calibration has no on-screen countdown: shaders play with an empty Body for `calibration_standback_s` plus collection. Keep people out of frame at startup.
- Not yet measured on the Pi 5: frame rate per Setup. `shader_app.py` logs fps every 10 s.
