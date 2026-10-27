# Shader Setups — prototyping guide

Make visuals in [Shadertoy](https://www.shadertoy.com) that visitors bend by moving. The show Pi plays them, with the depth camera standing in for your mouse.

## Start a prototype in Shadertoy

1. New shader. Click **+** next to the tabs → **Buffer A**.
2. Paste [`body_painter.glsl`](body_painter.glsl) into Buffer A. Set Buffer A's **iChannel0 = Buffer A**, **iChannel1 = Keyboard**. Don't change it.
3. In **Image**, set **iChannel0 = Buffer A**. That's the Body:
   ```glsl
   vec4 body = texture(iChannel0, fragCoord / iResolution.xy);
   // body.r  1 inside a person, 0 outside — test with body.r > 0.5 (edges blend)
   // body.g  nearness: 0 far … 1 close to the camera
   ```
4. Use Buffers B–D and Common freely (trails, simulations, feedback).

Mouse controls in Buffer A: **hold left button** = a person at the cursor · **hold Shift** = they step close · **Space** = leave a person standing there · **C** = clear.

## Rules (so it runs on the Pi)

- Read the Body with `texture()` and normalised UVs, never `texelFetch` — on the Pi it's camera resolution.
- Only `.r` and `.g` of the Body mean anything. On the Pi the camera's square view is stretched to the screen, so people look wider than the painter's.
- Buffers are 16-bit float on the Pi (Shadertoy uses 32-bit). Keep stored values small: past ~2048, whole numbers start rounding. Store positions as UVs (0–1), not pixels.
- `HW_PERFORMANCE` is 0 on the Pi — the low-quality branch.
- `iMouse` works: on the Pi it's the centre of everyone in frame, "pressed" while anyone is there.
- No textures, videos, sound, cubemaps, or webcam — procedural + Body only.
- Channel filter/wrap settings are ignored: always linear, clamp.
- The Pi renders at half resolution by default. Keep it cheap; avoid long raymarch loops.

## Hand it in

Copy [`ripples/`](ripples/) to `shaders/<your-setup>/` and replace:

| Shadertoy tab | File |
|---|---|
| Common | `common.glsl` (optional) |
| Buffer B / C / D | `buffer_b.glsl` … (optional) |
| Image | `image.glsl` |
| Buffer A | — don't copy; it's the Body |

`setup.json` records the iChannel bindings per tab and how long it plays:

```json
{
  "duration_s": 120,
  "channels": {
    "buffer_b": ["A", "B"],
    "image":    ["A", "B", null, "keyboard"]
  }
}
```

Sources: `"A"` (Body), `"B"`, `"C"`, `"D"`, `"keyboard"`, or `null`. List position = iChannel number.

Add the folder name to [`setups.json`](setups.json) to put it in the rotation. `make test` compiles every listed Setup.

## Run it locally

From `ShowControl/FundingCAPTCHA/` (`pip install -r requirements.txt`):

```
python3 shader_app.py --test-input --windowed --setup <your-setup>   # mouse paints the Body, same as Shadertoy
python3 shader_app.py --mock-camera --windowed                       # fake drifting visitors
```

Keys: **N** / **→** next Setup · **R** reload from disk (edit, save, press R) · **Esc** quit. Compile errors are logged with your tab's line numbers (`0:LINE` = the tab, `1:LINE` = common).
