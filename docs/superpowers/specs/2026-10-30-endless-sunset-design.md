# Endless Sunset — shader player Setup

A new FundingCAPTCHA shader player Setup (ADR-0021): a storybook sunset that never ends, which wakes up when someone stands in front of it and turns their silhouette into squiggles when they flail.

## Intent

A visual Shepard tone: the sunset seems to keep sinking/zooming forever, but it is a loop of overlapping layers whose resets are hidden. It should feel otherworldly and storybook-like, drawn in the same ink-line style as The Community Garden concept art, not realistic. The payoff for visitors is play: big movement gets a big, silly response.

## Goals

- An endless-motion illusion that never visibly resets.
- Three clear states driven by the Body:
  - **Empty** — low smolder: slow and dim. Light attract mode.
  - **Someone present** (standing) — over ~1–2 s the scene brightens and speeds up; the person appears as a white figure with an ink outline.
  - **Flailing** (big movement) — the person's outline becomes a jittery sine-wave squiggle, the scene speeds up further, and the rings and rays ripple outward around them. More movement → more squiggle. Flailing is rewarded.
  - Leaving eases everything back to the smolder.
- Runs on the show Pi 5 inside the existing shader player, and can be prototyped in Shadertoy with the mouse body painter, like every other Setup.

## Non-goals

- No uploaded art, textures or video (the player doesn't support them). Everything is procedural.
- No distinguishing between individual visitors; several people behave like one bigger Body.
- No sound.

## Anti-goals

- Realistic or photographic sunset (smooth gradients, glow, lens effects). It must read as flat, line-drawn, cartoonish.
- A visible reset or a pulse where the loop wraps.
- A standing visitor getting the same response as a flailing one.

## Reference mockup

[`2026-10-30-endless-sunset-mockup.html`](2026-10-30-endless-sunset-mockup.html) is the approved look and behaviour, as a runnable 2D-canvas sketch (open it in a browser). It loops empty → standing → flailing → leaving with a stand-in figure. It shows three people treatments; **A (wiggly outline) is the chosen one**. Port it to GLSL and match it side by side; its constants (ring base radius, wobble, ray widths, water hatch, ripple falloff, dim wash) are the starting values. It's a sketch, not a spec for code structure.

Concept art style, for anything the mockup doesn't cover: black pen linework with crosshatch shading, flat white fills, flat colour fields, colour used as sparse accents. The concept art itself lives outside the repo and is not to be committed.

## The look (decided, from mockups)

Back to front:

1. **Paper** — warm off-white `#f6f1e4` background.
2. **Rings** — wobbly concentric half-rings centred on the sun, flat colour fills with black ink outlines, growing outward forever. The rim wobbles slightly (~5% of radius, ~9 lobes around the half circle, slowly drifting).
3. **Rays** — squiggly sine-wave rays streaming out from the sun over the rings, warm white `#fffaf0` and pale yellow `#fbe9a0`, **no outline**. Thickness grows a little with distance.
4. **Sun** — flat yellow `#fff200` half-disc on the horizon with a black ink outline, radius 60/360 of the screen height (enlarged from the mockup after testing).
5. **Horizon** — a black ink line 20% of the way up from the bottom (lowered from the mockup after testing).
6. **Water** — below the horizon: wavy hatched ink lines alternating black and deep blue `#2076a3`, spacing increasing toward the viewer, gently undulating; short orange `#e8862f` streaks under the sun as its reflection, narrowing with depth.
7. **People** — white `#fffaf0` fill with a black ink outline (like the figures in the concept art). The outline becomes a sine squiggle with movement (see Behaviour).

Palette: the studio website's colours — slate `#719aad`, deep blue `#2076a3`, rust `#bc4c26`, yellow `#fff200`, black ink — plus orange `#e8862f`, pink `#e8957f` and violet `#6b5b95` added because a sunset needs them. Ring colours in layer order: yellow, orange, pink, rust, violet, slate.

Line weights: ink lines read as hand-drawn pen, roughly 2–3 px at 1080p. Exact widths are the builder's call.

## The endless motion (decided)

Both rings and rays use the same layered phase-wrap scheme:

- N = 6 layers. Layer i's phase: `p_i(t) = fract(t / T + i / N)`, with T ≈ 9 s at full speed.
- Scale: `s_i = 8^p_i` — each layer grows 8× over a cycle.
- Opacity: `a_i = sin²(π · p_i)` — fades in from nothing, peaks mid-cycle, fades out before it wraps.
- Rings: radius = base radius × `s_i`, fill at ~75% of `a_i`, outline at `a_i`. Larger rings draw behind smaller ones.
- Rays: ~17 rays across the half circle; each layer is a ray segment from `r_A = base × s_i` to `1.35 × r_A`, with alternate rays offset by half a layer so they don't move in lockstep. The squiggle is a sine wiggle perpendicular to the ray that travels outward.

`t` is not wall-clock time: it is an accumulated clock whose rate changes with state (below), so speed changes never cause a jump.

## Behaviour (decided)

- **Awake level** (0–1) — whether anyone is in frame, smoothed over ~1–2 s. It saturates at small coverage, so one person standing far back fully wakes the scene; more people don't make it "more awake". 0 = empty. *(Builder-check call.)*
- **Nearness** (`.g`) is not used. *(Builder-check call; can be added later.)*
- **Movement** — the Body only gives presence/nearness, not motion, so motion is derived by comparing each frame of the Body with the previous one, kept as a fading per-pixel trail. It is local: a waving arm squiggles more than a still torso. A global flail level (0–1) is the total amount of that movement, smoothed.
- **Speed**: clock rate ≈ 0.35 when empty → 1.0 when awake → ~1.6 at full flail.
- **Brightness**: empty is dimmed (in the mockup, a ~50% wash of `#1d3550` over everything); awake is full brightness.
- **Squiggle outline**: the outline is pushed in and out by a travelling sine wiggle whose amplitude grows with local movement (small but present when still, large when flailing).
- **Ripples**: ring rims and rays are displaced near people — a sine wave travelling outward from the Body that decays with distance (~45 px falloff at 640 wide in the mockup) — strength small when someone is just standing, full when flailing.

Mockup tuning values above are starting points; they will be tuned by eye on the real display.

**Real camera noise** *(builder-check call)*: on the Pi the Body is a noisy depth mask at ~10 fps (the shader runs at ~30), so a still person's edges flicker, which reads as motion right where the squiggle is measured. The mouse painter can't show this. So:
- Movement uses a noise floor, and changes only register when a new camera frame arrives (not every render frame).
- All the thresholds and gains (noise floor, flail normalisation, awake saturation, speeds, dim amount, wiggle amplitudes, ripple strength) live as named constants together at the top of `common.glsl`, so they can be retuned on site with the player's **R** reload.
- The standing/flailing split is unverified against real camera data until it has been run with the camera (`--camera`, or `--mock-camera` as a first approximation). The plan must include that tuning pass and say so if it couldn't happen.

**Stretch** *(builder-check call)*: the Body is sampled with plain screen UVs, like the other Setups. On the Pi people look wider than in Shadertoy; that is accepted, not corrected.

## Constraints

- Shader player rules (`ShowControl/FundingCAPTCHA/shaders/README.md`): Buffer A is the Body (`.r` presence, `.g` nearness), read via `texture()` with UVs; buffers are RGBA16F (keep stored values small, store positions as UVs); `HW_PERFORMANCE` 0; no textures; linear + clamp filtering; renders at half resolution on the Pi.
- Must be pasteable into Shadertoy with `body_painter.glsl` in Buffer A, and work with its mouse controls.
- Must hold a smooth frame rate on the Pi 5 at half resolution. If something has to give, simplify the rings or the water before the squiggle.
- On the Pi the camera's square view is stretched to the screen, so people look wider than in Shadertoy.
- No show, artist or album names in any file (repo rule).

## Where it goes (decided)

- New Setup folder `ShowControl/FundingCAPTCHA/shaders/endless_sunset/` following the `ripples/` template: `setup.json`, `image.glsl`, plus whichever of `common.glsl` / `buffer_b.glsl`… are needed.
- Added to `shaders/setups.json` alongside `ripples`, `duration_s` 120.
- `make test` already compiles every listed Setup; it must pass.

## Left to the builder

- How state (previous Body, motion trail, smoothed awake/flail levels, the accumulated clock) is split across Buffers B–D, and how global levels are reduced (e.g. one texel doing a sparse sample loop).
- How the outline and the distance-to-Body for ripples are derived from the Body mask (e.g. offset sampling, a blurred/dilated buffer).
- Antialiasing approach for ink lines, and exact line widths.
- Water line count/spacing and ray count, within the look above.
