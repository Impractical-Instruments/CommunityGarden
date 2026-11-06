# Hunter Bird — shader player Setup

A new FundingCAPTCHA shader player Setup (ADR-0021): a debug view of the blob tracker, drawn as a bird in a tree hunting the visitors. It reads the tracker's boxes, IDs and lifecycle through the `blobs` source (ADR-0022).

## Intent

Role reversal: the bird is birdwatching *you*. The screen is what the bird sees, through its two eyes. The tracker's real boxes, IDs and states are the bird's field notes on the specimens in the clearing. Its attention, a reticle, follows whoever moves most. Hold still and it loses interest. Let it lock on and it strikes, stamping you with a tick: verified. It's a CAPTCHA joke drawn in the storybook ink style of The Community Garden concept art.

## Goals

- An honest tracker debug view. Every box, number and state change on screen is the real tracker's record, not a dramatisation.
- A bird you only ever see as its eyes: two merged lenses, eyelids for mood and blinks, a yellow iris band that closes in as it locks on.
- A play loop visitors discover on their own:
  - **Move** and the bird notices you.
  - **Freeze** and it loses interest.
  - **Flail** and it locks on and strikes.
  - **Everyone stamped** and it's smug, then drowsy.
- It runs on the show Pi 5 in the existing shader player, and can be prototyped in Shadertoy with `body_painter.glsl` and `blob_painter.glsl`.

## Non-goals

- No depth image or contour map. The background is the empty clearing on paper.
- No words, letters or numbers other than the IDs. Language-free: numbers and glyphs only (`?`, tick).
- The bird's body is never seen. Eyes, eyelids and iris only.
- No sound.

## Anti-goals

- Fake tracking. A box with no tracker record behind it, or a state the tracker didn't report.
- Mask flicker reading as movement. A visitor standing still must be able to escape the bird.
- A frame so busy the people get lost. Colour stays a sparse accent; the specimens and the reticle carry the scene.

## Reference mockup

[`2026-11-04-hunter-bird-mockup.html`](2026-11-04-hunter-bird-mockup.html) is the approved look and behaviour, as a runnable 2D-canvas sketch with a scrubber. Its stand-in figures and simulated tracker are not part of the spec. The Setup uses the Body and the `blobs` records. Its constants are the starting values. Where this spec and the mockup differ, this spec wins. The differences are listed under each section.

## The look (decided)

All sizes are in screen heights (mockup px / 360). Colour comes from the sunset palette: paper `#f6f1e4`, ink `#111111`, slate `#719aad`, deep blue `#2076a3`, rust `#bc4c26`, yellow `#fff200`, orange `#e8862f`, violet `#6b5b95`, warm white `#fffaf0`.

Back to front:

1. **World** (zooms on a strike):
   1. **Paper**: the clearing.
   2. **Ground**: a few thin wavy slate lines across the lower part of the screen.
   3. **People**: the Body as a warm-white fill with an ink outline (~2.6 px). Slate diagonal hatching fills the lower ~40% of each person's box, reading as legs, and gets denser with nearness. A Body pixel inside no box gets fill and outline but no hatching.
   4. **Canopy**: branches across the top corners and a perch in the bottom-left foreground, drawn as ink-outlined paper with short hatch strokes. Leaves are ink-outlined: mostly paper, some slate, a few deep blue, rarely violet, some hatched, all swaying gently, and they shiver briefly when someone new appears. *Differs from the mockup:* the side leaves are thinned to two or three per side near the top corners, so the canopy reads as a top band.
2. **Field notes** (the tracker; zooms with the world, drawn on top of the canopy):
   - **Boxes** are wobbly hand-drawn corner brackets. Arm length is 22% of the box's shorter side, clamped to 10–24 px.
     - **Tentative:** a dashed slate rectangle with a small slate `?`.
     - **Confirmed:** ink brackets, heavier on the bird's target.
     - **Coasting:** dashed ink brackets fading with `age_s`, plus a `?`.
     - **Lost:** ink brackets scribbled through with a zigzag drawn over ~0.25 s, then fading.
   - **Tag**: a bird-ringing tag hanging by a string from the box's top-right corner, swinging with velocity. The ID is drawn in wobbly seven-segment digits (1–3 digits). The fill is yellow for the bird's target and paper otherwise. *Differs from the mockup:* a stamped visitor's tag carries a small rust tick for as long as their track lives.
   - **Velocity**: a deep-blue ink arrow from the centroid, about 0.35 s of travel long, shown above a minimum speed.
   - **Footprints**: small slate ovals left behind a walking track at the bottom of its box, alternating sides, fading over 4 s.
3. **Attention**:
   - **Reticle**: a wobbly rust circle with four diagonal ticks. Its radius shrinks from ~58 px to ~20 px as lock builds, and it trembles slightly near full lock. A thick rust arc around it fills with lock. When the bird has no target, the reticle wanders, half-transparent, with a rust `?` inside.
   - **Stamp**: a rust double ring with radiating dashes and a bold tick, rotated about −13°. It slams down from 2.4× scale to 1× in 0.12 s on the target's box centre, follows the box, and fades out by 3.2 s.
4. **Eye** (screen space, never zooms):
   - **Two eyes** (changed 2026-11-05, from one centred eye; mockup: `2026-11-05-hunter-bird-two-eyes-mockup.html`): two ellipses 1.25× as wide as tall, centres ~150 px either side of the screen's centre line. They overlap, and their openings merge into one view, like wraparound sunglasses. Each eye owns its side of the centre line, and the two meet in a notch at top and bottom. Outside the eyes is a hatched socket.
   - **Iris band**: a yellow band ~34 px wide around each opening, with short ink striations and ink edges. The opening is ~150 px tall-radius with no lock. At full lock the radius and the eyes' separation both shrink to 0.8×, so the view narrows toward the centre. On a strike they snap to ~1.1× before easing back.
   - **Eyelids**: each eye has its own top and bottom lid, inside the eye, with almond-curved rims. They're paper with slate hatching, an ink rim, a yellow eye-ring just inside the rim, and feather scallops along the crease. The eye's outer rim is drawn over them, so the shape always reads. Their openness is the bird's mood (Behaviour). At openness 1 a lid's rim sits on the eye's outer edge.
   - **Blink**: both eyes' lids snap shut and open again over ~0.32 s. (This replaced a nictitating membrane that swept across the screen.)

## Behaviour (decided)

The bird's attention is separate from the tracker. The tracker says who is there; the bird decides who is interesting.

- **Motion**, per confirmed slot (0–1): speed plus how fast the box's size is changing (waving arms grow and shrink the box), minus a noise floor, smoothed. Only confirmed records have motion. *Differs from the mockup:* the mockup measured clean positions; this measures the eased records, so the noise floor is real and must be tuned (below).
- **Interest**, per slot (0–1): rises while motion is above an "on" threshold, in proportion to motion, and drains while it's below. Tentative, coasting and lost records drain. **A stamped visitor's interest is held at 0.**
- **Target**: the confirmed, unstamped slot with the highest interest above 0.25. The bird only switches if a rival beats the current target by 0.2, and a switch keeps 30% of the lock.
- **Lock** (0–1): builds while the target moves (∝ motion²), so flailing locks in ~2 s and walking about never does. It drains while the target is still or there is none.
- **Strike**, **once per person**: at full lock the slot is marked stamped. That triggers the punch-in zoom, iris dilation, the stamp and a smug blink, and lock resets. The bird then ignores that visitor for the rest of their track. A new ID in the same slot (a different person, or the same person re-acquired after the tracker lost them) can be stamped again. The latter is accepted.
- **Reticle**: springs to the target's upper chest (30% down its box), faster the more interested the bird is. With no target and someone present, it drifts slowly around where it last was. With nobody present, or only stamped visitors, it fades out.
- **Eyelid mood** (openness 0 closed … 1 wide):

  | Situation | Openness |
  |---|---|
  | empty room | drowsy, 0.42 with a slow ±0.05 droop |
  | someone present, no target | suspicious squint, 0.7 |
  | target held | wide, 0.96 |
  | the 0.9 s after a strike | 1.0 |
  | then for 3.2 s after a strike | smug, 0.58 |
  | everyone present is stamped | smug, then drowsy after a few seconds |

  The lids open quickly and close slowly.
- **Blinks** (lids): 0.15 s after a new ID appears, 2.3 s after a strike, and at irregular idle intervals of ~6–10 s.
- **Strike sequence**: punch-in zoom about the stamp point, up to 1.38× in 0.12 s, held to 0.9 s, eased out by 1.7 s.

**Real camera** *(builder-check call)*: on the Pi, records ease toward each new camera frame, so a standing person's box breathes by a pixel or two. That must read as motion 0, so the noise floor and the on-threshold are named constants at the top of `common.glsl`. "Freeze and it loses you" is unverified until it has been run with the real camera (`--camera`; `--mock-camera` and `--test-input` are first approximations). The plan must include that pass and say so if it couldn't happen.

**Stretch** *(accepted)*: Body UV is stretched to the screen on the Pi, so boxes and silhouettes stretch together and stay aligned. Glyphs, digits, tags, reticle and stamp are sized in screen heights, so they don't stretch.

## Constraints

- The shader player rules in `ShowControl/FundingCAPTCHA/shaders/README.md`:
  - Read the Body with `texture()`, and the blob records with `texelFetch`.
  - Buffers are RGBA16F: keep stored values small and positions in UV.
  - `HW_PERFORMANCE` is 0; no textures.
  - The Pi renders at half resolution.
- The `blobs` contract (ADR-0022) is read-only from here. If the Setup needs more from the tracker, that's a contract change, not a workaround.
- It must paste into Shadertoy with `body_painter.glsl` (Buffer A) and `blob_painter.glsl` (a spare buffer).
- It must hold a smooth frame rate on the Pi 5. If something has to give, cut in this order: canopy leaf count, footprints. Never the tracker notes.
- No show, artist or album names in any file (repo rule).

## Where it goes (decided)

- A new Setup folder, `ShowControl/FundingCAPTCHA/shaders/hunter_bird/`.
- Added to `shaders/setups.json` alongside `ripples` and `endless_sunset`, with `duration_s` 120.
- `make test` compiles every listed Setup and must pass.

## Left to the builder

- How bird state is laid out across buffers (the plan proposes one).
- Antialiasing and exact line weights, within "hand-drawn pen, ~2–3 px at 1080p".
- Exact glyph shapes for `?` and the tick, and the seven-segment proportions.
- Leaf count and positions, within the top-band rule.
