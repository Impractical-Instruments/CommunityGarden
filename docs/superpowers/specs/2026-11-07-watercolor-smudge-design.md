# Watercolor Smudge — shader player Setup

A new FundingCAPTCHA shader player Setup (ADR-0021), from issue #164. The screen shows a watercolor painting. When visitors come into range, the thin moving parts of their silhouette (hands, arms, feet, head) smear the paint like fingers dragged through wet watercolor. Once the room empties, the painting slowly heals.

The work has two parts:

1. **A player change**: Setups can bind an image as a channel source, and the player shuffles images from the Setup's folder on each load.
2. **The Setup**: the smear and heal behaviour, with a procedurally painted watercolor sunset standing in until real images are committed.

## Intent

The piece is a nice painting you discover you can touch. Nothing on screen says it's interactive. People find out by walking past and seeing the paint move where their hands and feet go. The smear should feel physical: paint is pushed in the direction a limb moves, streaks, and mixes like wet pigment. Then it quietly mends itself once everyone has gone, so the next visitor finds a fresh painting.

The rotation will eventually shuffle interactive Setups and baked videos together. That system isn't part of this work. This Setup only needs to be self-contained: choose its image when it loads and play for its `duration_s`.

## Goals

- **Empty room:** a calm, full-screen watercolor painting.
- **Only the extremities smear.** The thin parts of the silhouette smear the paint when they move: arms, hands, legs and feet, and the head. The broad torso passes through without smearing. Thin vs. broad is judged from the silhouette alone, since there's no skeleton. Concretely, it's how much of a ring around each point is Body (see the mockup's `extremity()`).
- **The smear follows the movement.** Paint is pushed in the direction the edge of the silhouette moves, at roughly the limb's speed times a strength. It breaks into finger-drag streaks across the stroke, and colours mix the way pigments do (multiplicatively, darkening a little) rather than averaging to grey.
- **Wet look:** freshly smeared paint reads slightly darker while wet and dries back over a few seconds.
- **Standing still does nothing.** A still person causes no smear and no bleed.
- **Heal:** once nobody has been in range for about **2 s**, the canvas eases back to the original painting over about **10 s**. While anyone is present, healing is negligible, so smears persist while people play.
- **Images:** the Setup paints whichever image the player bound. On each load the player picks the next image from a shuffle of the Setup's `images/` folder. If the folder is empty or missing, the Setup paints the procedural watercolor sunset instead.
- **Tunable:** smear strength, the thin/broad threshold, heal time and the heal delay are named constants at the top of `common.glsl`, with comments, matching how the other Setups expose tuning. Defaults come from the approved sketch.
- Runs in the shader player on the show's Intel Core Ultra 9 Linux machine, and can be prototyped in Shadertoy with the body painter.

## Non-goals

- No bleed or soak around a standing person. It was tried in the first sketch and dropped.
- No drawing of the person: no silhouette, outline or ghost.
- Nearness (`.g`) isn't used.
- No sound.
- No procedural "watercolor filter" over the images. The images are painted as watercolors already; see "Images" below.
- Playing baked videos and mixing them into the rotation are out of scope.

## Anti-goals

- **A still person smearing because of the camera.** Depth-edge flicker, dropout holes and grain on a stationary silhouette must not move paint. The smear must come from real movement. With the real camera this is the main risk of the frame-difference motion signal; see "Motion signal".
- **The torso bulldozing the painting.** If walking through drags a body-wide band of paint across the screen, the extremity idea is lost. The first sketch did this, and it was rejected as "too broad".
- **Grey mud.** Mixing must stay pigment-like and colourful, never average to grey.
- **Popping.** Healing is a smooth ease back, never a cut.
- **Hard, graphic stroke outlines.** An early v2 iteration had dark sawtooth edges around every stroke; they were removed. Smears should read as soft paint.

## Reference mockup

[`2026-11-07-watercolor-smudge-mockup.html`](2026-11-07-watercolor-smudge-mockup.html) is a runnable WebGL2 sketch (v2) of the approved interaction. A stick figure stands in for the depth camera's Body; drag to walk it and hold **W** to wave. It shows:

- the procedural sunset, which is the look for the stand-in painting;
- the extremity weighting ("Show the Body": red smears, grey doesn't);
- normal-flow motion from frame-to-frame Body change;
- streaky, pigment-mixing smear, the wet darkening, and heal after the room empties;
- live sliders for smear strength, "what counts as thin" and heal time.

The user approved this interaction as-is: *"this interaction paradigm is great as it is. Keep the tunability."* Treat its behaviour and default slider values as the target. It's a sketch for behaviour and look, not a code structure to copy. Cost is covered in "Target machine and cost".

## Behaviour (decided)

### Motion signal

- **Per-pixel motion from the Body changing between frames** (normal flow), as in the sketch: `v = −(∂B/∂t) · ∇B / (|∇B|² + ε)`, using the current and previous Body. It is non-zero only in the soft band at a moving silhouette edge, and points the way that edge moves. Leading and trailing edges both point forward.
- The previous Body has to be kept by the Setup, for example copied into a buffer each frame.
- **Flicker rejection is required** (anti-goal). Ways to get there are left to the builder: easing the Body over a few frames as `watering_can` does (`PRESENCE_EASE_S`, hysteresis), a minimum-speed dead zone, or gating by the person's blob velocity when they're standing still. The acceptance test is that a person standing still in front of the real camera leaves the painting untouched.

### Extremity weighting

- `ext = 1 − smoothstep` of the Body coverage on two rings around the point (radii about 0.045 and 0.08 screen heights in the sketch). Thin parts score near 1, the torso near 0. The threshold is the "what counts as thin" tunable.
- The radii are in screen units. In the player the camera's square view is stretched to the screen, so people look wider than in the sketch, and the defaults may need retuning against the real camera.
- With real people, legs often sit close together and score as broad, so the feet and a waving arm do most of the smearing. That matched the sketch and was accepted.

### Smear

- Semi-Lagrangian advection of a persistent **canvas buffer** by `v × ext × streak × strength`. `streak` is noise across the stroke direction, so the smear breaks into finger streaks.
- Where paint is moving, it mixes with its neighbours by a geometric mean, i.e. averaged in log space. This is the pigment-like mixing.
- A wetness channel rises where paint moves and decays over about 3 s. The final image darkens slightly where it's wet.

### Heal

- "Empty" means no Body presence. `iMouse.z > 0` is "anyone present" in the player (ADR-0021), or presence can be derived from the Body. Once the room has been empty for the heal delay (default 2 s), the canvas eases exponentially toward the original, reaching about 95 % in the heal time (default 10 s). While anyone is present, there's a tiny heal rate, which the sketch uses so that nothing drifts forever.
- The "empty for" timer needs per-frame state. Keep it in a buffer texel, as the other Setups keep state.

### The original painting

- **With an image bound:** the image, scaled to cover the screen. Aspect is kept and the overflow cropped, centred. *(Cover vs. stretch is my call.)*
- **Without an image** (the channel's `iChannelResolution` is zero): the procedural watercolor sunset from the sketch's `PAINT` shader. That's graded sky washes with pooled stroke edges, glazed clouds, a pale lifted sun with a pooled rim, low hills, a reflection, granulation, and a ragged unpainted paper border.
- The procedural sunset is costly, so compute it once into a buffer rather than every frame. For example, repaint it only when `iFrame == 0` or the resolution changes.
- **Paper border:** the procedural painting's border never smears and paint can't be dragged out of it, as in the sketch (`P.a`). Images get no border by default. If an image has an alpha channel, its transparent areas could act as that mask; this is optional and left to the builder.

### Display

- **Keep images as sharp as the player allows.** Every pass, including `image`, renders at `render_scale` (default 0.5) and is upscaled to the window by `shader_app.py`. This work doesn't change that: no full-resolution final pass. Within that, avoid a second resample. The `image` pass samples the bound image directly wherever the canvas is undisturbed, and shows the canvas only where it differs from the original. Watercolors are soft, so half-resolution output should hold up. If it doesn't, raising `render_scale` is a separate, measured decision. *(My call; the blend details are the builder's.)*
- Add procedural paper grain only over disturbed areas, plus the wet darkening. That way a smear doesn't drag the image's own scanned paper texture around with it, and untouched areas show the image exactly as painted. The procedural sunset gets grain everywhere, as in the sketch.

## Images

- **Pre-watercolored images**, not procedural watercolor-ification of arbitrary photos. Real watercolor gets wet edges, blooms and granulation for free, while a filter tends to read as a photo-app effect and adds per-frame cost. The shader adds only what comes from people moving through the painting: smear, mixing, wetness and fresh grain.
- They're committed **publicly** in `shaders/watercolor_smudge/images/`. None exist yet; the procedural sunset ships as the stand-in. Adding images later needs no code change.
- Advice to the artist, for the README: fairly saturated images with clear colour regions smear more legibly than soft, low-contrast ones.

## Player change: image channels (decided)

The player currently allows no textures (ADR-0021 "Consequences"). This adds one image source. Record it as a **new ADR (0023) amending ADR-0021**, as ADR-0022 did for blobs.

- **`setup.json`:** a new channel source, `"image"`. It binds this load's image from `<setup>/images/`.
- **Choosing the image:** on each load of the Setup, the player picks the next image from a shuffle bag of the folder's files, reusing `arc.ShuffleBag`, so you see a new image each time and none repeats until all have shown. *(One bag per Setup for the run is my call.)* Accepted formats: PNG and JPEG.
- **Only a real load advances the bag.** When this is the only Setup playing (`--setup NAME`, or a one-entry `setups.json`), `Rotation.next()` keeps the Setup loaded and only resets its timer, so the image stays the same. That's accepted; there's no mid-run image swap. The **R** hot-reload is a real load, so it advances the bag. *(My call: in the show, the rotation will have many Setups and videos.)*
- **Loading:** decode on load into an RGBA8 texture, flipped so row 0 is the bottom (GL convention, matching the Body). Use linear filtering and clamp, like every channel. Release it on unload.
  - Downscale an image larger than the **window**, or than the GPU's max texture size, before upload, so detail survives if `render_scale` is ever raised. *(My call: no mipmaps.)*
  - `iChannelResolution` reports the image size.
- **No images:** with an empty or missing folder, the channel is unbound, so it reads 0 and `iChannelResolution` is 0. The Setup uses that to fall back to procedural. This is *not* an error, so CI and fresh clones play the Setup fine.
- **A broken image file** (fails to decode): log it, drop it from the bag and try the next. If none decode, play with the channel unbound.
- **Shadertoy prototyping:** bind one of Shadertoy's built-in textures where the Setup uses `"image"`. The user confirmed a stand-in texture there is fine. Update the README's channel table and rules ("No textures…") to describe the new source.
- **Tests:** loading a Setup with an `"image"` source; the shuffle; the empty-folder fallback; a corrupt file. `make test` compiles every listed Setup, so the new Setup must compile with the folder empty.

## Target machine and cost

**The show machine for this Setup is an Intel Core Ultra 9 Linux PC, not the Pi 5.** The user decided to set the Pi aside, so render limits matter much less. The player itself is unchanged: it still uses RGBA16F buffers, `HW_PERFORMANCE` 0 and `render_scale`. On this machine, `render_scale` can be raised in that machine's settings if half resolution looks soft; this work doesn't change the default. Still, stay reasonable:

- Cache the procedural painting; don't regenerate it per frame.
- The Body arrives at about 10 Hz but renders at about 30 fps, so raw frame-to-frame change is spiky: zero on most frames, then a jump. Easing the Body is needed for smooth flow as well as for flicker.
- The sketch's 24-tap extremity test per pixel is fine on this machine. Don't spend effort reducing it unless fps (logged every 10 s by `shader_app.py`) says so.

16-bit float buffers: canvas colours are 0–1, so there's no precision problem with magnitude. Repeated advection does blur over time, and the heal and the "only show the canvas where disturbed" display both bound how much that shows. Watch for drift in a long busy session.

## Testing and sign-off

- **Automated** (`make test`), which must pass:
  - the Setup compiles with an empty `images/` folder;
  - the `"image"` source loads;
  - the shuffle bag advances per load;
  - the empty-folder fallback works;
  - a corrupt file is skipped.
- **At the rig, by the user, before merge:**
  - the standing-still test with the real depth camera (anti-goal 1);
  - walking and waving through it;
  - tuning the ring radii and thin threshold against real silhouettes;
  - an fps reading on the Ultra 9.

  The plan ends with a hand-off listing what to try and which constants to adjust. Tuning changes from that session land on the same branch.

## Tunables and defaults

All are named constants at the top of `common.glsl` with comments. Defaults are the sketch's.

| Constant | Default | Meaning |
|---|---|---|
| smear strength | 0.63 (sketch slider 45 × 1.4) | fraction of edge motion that moves paint |
| thin threshold | 0.5 (maps to coverage ≈ 0.315 ± 0.08) | what counts as an extremity |
| extremity ring radii | 0.045, 0.08 screen heights | scale of "thin" |
| streak noise | 0.7 + 0.6·noise, 45 /unit | finger-streak contrast and spacing |
| wet decay | ~0.35 /s | how long smears look wet |
| heal delay | 2 s | empty time before healing starts |
| heal time | 10 s | time to ~95 % healed |
| present heal rate | 0.004 /s | trickle heal while people are present |

## Setup facts

- **Folder:** `shaders/watercolor_smudge/`, added to `setups.json`.
- **`duration_s`:** 120. *(My call, to match the other Setups.)*
- **`setup.json` `_comment`:** names the spec, as the other Setups do.
- The buffer layout is the builder's, within the four buffers (A is the Body) and four channels per pass. One plausible layout:
  - B: canvas (rgb paint, a wetness)
  - C: previous Body, extremity and flow
  - D: cached original and state texels
  - image pass: B, D, `"image"`, A

## Left to the builder

- The buffer layout, how state is packed, and how the "empty for" timer is stored.
- The flicker-rejection method (it must pass the standing-still test).
- How the full-resolution and canvas blend are done.
- Whether image alpha acts as a no-smear mask.
- Exact tuning against the real camera, starting from the defaults above.
