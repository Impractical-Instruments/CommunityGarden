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

- Read the Body with `texture()` and normalised UVs, never `texelFetch` — on the Pi it's camera resolution. (Blob records are the exception: always `texelFetch`.)
- Only `.r` and `.g` of the Body mean anything. On the Pi the camera's square view is stretched to the screen, so people look wider than the painter's.
- Buffers are 16-bit float on the Pi (Shadertoy uses 32-bit). Keep stored values small: past ~2048, whole numbers start rounding. Store positions as UVs (0–1), not pixels.
- `HW_PERFORMANCE` is 0 on the Pi — the low-quality branch.
- `iMouse` works: on the Pi it's the centre of everyone in frame, "pressed" while anyone is there.
- No textures, videos, sound, cubemaps, or webcam — procedural + Body only.
- Channel filter/wrap settings are ignored: always linear, clamp.
- The Pi renders at half resolution by default. Keep it cheap; avoid long raymarch loops.

## Blobs: boxes, IDs and lifecycle (optional)

To draw the tracker itself (a box per person, a number that follows them, whether the tracker is sure of them), read the **blobs** source ([ADR-0022](../../../docs/adr/0022-shader-player-blob-records.md)).

In Shadertoy: paste [`blob_painter.glsl`](blob_painter.glsl) into a spare buffer (D unless you use it). Set that buffer's **iChannel0 = itself**, **iChannel1 = Keyboard**, and don't change it. Bind it to any tab that reads blobs. It tracks the painter's people: the held mouse is one person, and each **Space** parks another.

Read records with `texelFetch` (the one exception to the rule below), slot 0–7:

```glsl
vec4 box = texelFetch(iChannel1, ivec2(slot, 0), 0);  // x0, y0, x1, y1      Body UV
vec4 mot = texelFetch(iChannel1, ivec2(slot, 1), 0);  // cx, cy, vx, vy      UV, UV per second
vec4 idn = texelFetch(iChannel1, ivec2(slot, 2), 0);  // id, state, age_s, nearness
// state: 0 empty, 1 tentative, 2 confirmed, 3 coasting (missed, drifting), 4 lost (about to go)
// id: 1–999, follows the person · age_s: seconds in this state
```

Slots are stable: a person keeps their slot until their record empties, so per-slot state in your own buffers stays theirs. UV is the Body's space, so `box * iResolution.xyxy` lines up with the silhouette. [`blob_debug/`](blob_debug/) is a minimal reader.

When handing in, don't copy the blob painter tab. In `setup.json`, write `"blobs"` where Shadertoy has that buffer:

```json
"channels": { "image": ["A", "blobs"] }
```

## Hand it in

Copy [`ripples/`](ripples/) to `shaders/<your-setup>/` and replace:

| Shadertoy tab | File |
|---|---|
| Common | `common.glsl` (optional) |
| Buffer B / C / D | `buffer_b.glsl` … (optional) |
| Image | `image.glsl` |
| Buffer A | — don't copy; it's the Body |
| The blob painter's buffer | — don't copy; it's `"blobs"` |

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

Sources: `"A"` (Body), `"B"`, `"C"`, `"D"`, `"keyboard"`, `"blobs"` (blob records, above), or `null`. List position = iChannel number.

Add the folder name to [`setups.json`](setups.json) to put it in the rotation. `make test` compiles every listed Setup.

## Run it locally

From `ShowControl/FundingCAPTCHA/` (`pip install -r requirements.txt`):

```
python3 shader_app.py --test-input --windowed --setup <your-setup>   # mouse paints the Body, same as Shadertoy
python3 shader_app.py --mock-camera --windowed                       # fake drifting visitors
```

Keys: **N** / **→** next Setup · **R** reload from disk (edit, save, press R) · **Esc** quit. Compile errors are logged with your tab's line numbers (`0:LINE` = the tab, `1:LINE` = common).
