# Watering Can — shader player Setup

A new FundingCAPTCHA shader player Setup (ADR-0021), from issue #163. People are watering cans: when someone stays in one spot, vines sprout from the lowest points of their silhouette and climb, then flowers bloom at the tips. Walking away from the spot rewinds the growth. Waving and waggling don't rewind: the vines ride along on the body, so a visitor can waggle their own garden around.

## Intent

The reward for staying put. A visitor who stops in one place watches themselves slowly turn into a garden. The silhouette itself is never drawn; the person is revealed only by what grows on them, so by full bloom their shape reads clearly as "that's me, made of flowers". Once they're growing, moving their arms and body is play, not punishment: the vines and flowers wave around with them. Only walking costs growth. Even then it's gentle: the growth plays backwards like a reversed film, and nothing vanishes or pops.

## Goals

- **Growth while planted.** Sprouts start at the lowest point of each part of the silhouette and climb upward. They become leafy vines, and flowers open at the growing tips near the end. Growth stays inside the silhouette.
- **Everything grows upward from its lowest point.** Legs grow from the feet, a hanging arm from the hand, a raised arm from its lowest point, as if sprouting from the ground. Nothing grows outward from the shoulder.
- **Full bloom holds** for as long as the person stays in their spot.
- **Waggling is free.** Arm waves, flailing, swaying, bending and dancing in place don't rewind anything, and growth keeps going. The plants are attached to the body and move with it.
- **Walking rewinds.** When the base of a person's silhouette (their feet) moves to a new spot, their whole growth runs backwards: flowers close, vines shrink back down, colour drains. This covers steps in any direction, including straight toward or away from the camera. When they plant themselves again, growth resumes from wherever the rewind got to, not from bare.
- **Timing.** Standing in one spot fills a person to full bloom in about **20 s**. Rewind runs at the same rate by default. The two rates are separate tunables.
- **Colour ripens with maturity.** The whole plant on a person ripens together: muted while young, saturating as it grows, sprout to vine to flower. Full bloom is the big, vivid payoff, and at full bloom the whole person is vivid.
- **The sun follows the garden.** The empty room is plain paper with a muted crayon-drawn sun in one corner. The sun gets brighter and grows rays in step with how much is growing and blooming across everyone in frame, and dims back as growth rewinds or people leave.
- Runs on the show Pi 5 in the existing shader player, and can be prototyped in Shadertoy with the mouse body painter and blob painter like every other Setup.

## Non-goals

- No uploaded art, textures or video (the player doesn't support them). Everything is procedural.
- No limb or skeleton detection.
- No sound.
- Nearness (`.g`) isn't used for drawing. *(My call.)*

## Anti-goals

- **A planted person losing growth because of the camera.** This would ruin the piece. That includes depth-edge flicker, dropout holes, grain, tracker jitter in the person's box, and the tracker briefly losing them or giving them a new ID.
- **Waggling rewinding.** If waving your arms costs you growth, the fun idea is lost.
- **Drawing the silhouette.** No outline, no fill and no ghost of the person. Before anything grows, nothing marks where they stand.
- **Popping.** Rewinding must look like growth playing backwards. Plants never vanish or cut out.
- **A hard cut-out edge.** Growth shouldn't look like a stencil of the body.
- **Realistic rendering** (gradients, glow, photographic plants). It must read as flat, line-drawn storybook.

## Reference mockup

[`2026-11-06-watering-can-mockup.html`](2026-11-06-watering-can-mockup.html) is a runnable 2D-canvas sketch with a growth slider and Play/Rewind buttons. **The "Dense" panel is the approved look**: density, whole-plant ripening, no silhouette drawn, stems inside, leaves and flowers overhanging the edge. It doesn't show the sun, movement or real camera input. It's a sketch for look and feel, not a spec for code structure, and the vines in the real thing should look better than its stand-ins.

## The look (decided)

- **Style:** the same line-drawn storybook style as the other Setups (see `endless_sunset`): black ink lines, about 2–3 px at 1080p, with flat colour fills from the shared palette in `endless_sunset/common.glsl`.
- **Background:** plain paper `#f6f1e4`. Nothing else: no ground line or horizon.
- **Sun:** muted and crayon-drawn, in one corner. "Crayon" means a waxy, slightly broken, hand-drawn stroke and fill rather than a clean ink outline. When the garden is empty it's dull and has no rays. As total growth rises it brightens toward the palette yellow `#fff200` and grows rays. *(Which corner is my call: top right. The ray style is left to the builder, in the same crayon hand.)*
- **Vines:** dense. The approved mockup has about 30 vines across one standing adult, so the person's shape fills in clearly by full bloom. Spacing should be set in screen units.
  - Stems are ink-edged or dark green lines that stay **inside** the silhouette.
  - Leaves are flat green with ink outlines. Like the flowers, they may **hang past the edge**, so the outline looks soft and overgrown.
  - Vines sway slightly, so a still, fully bloomed person doesn't look frozen. *(Sway is my call.)*
- **Flowers:** they open at vine tips in the last part of the growth and grow from buds to open blooms. They use a mix of palette colours with yellow centres (pink `#e8957f`, orange `#e8862f`, violet `#6b5b95`, rust `#bc4c26`), so a full bloom looks like a mixed bouquet. *(The colour mix is my call.)*

## Behaviour (decided)

- **One growth level per person.**
  - Each person has a single growth level, 0–1, which rises while they stay planted and falls while they walk.
  - The drawing derives from that level and the person's *current* silhouette every frame. In each vertical run of their body pixels (a column of the silhouette between a bottom edge and a top edge), the vine reaches from the run's bottom up a fraction of the run equal to the growth level, as in the mockup's `tip = g * span`.
  - So when an arm moves, its vines move with it. A raised arm grows from its new lowest point.
  - Colour saturation and flower opening follow the same level.
- **Planted vs. walking:** decided by whether the person's **base** moves, not their whole outline.
  - Use the per-person tracker: the `"blobs"` records from ADR-0022, with stable slots, boxes, velocity and lifecycle.
  - The base means the feet, for example the box bottom together with the horizontal position of the lowest body pixels in the box. It does not mean the centroid or the whole box, because an outstretched or flailing arm moves those without the person walking.
  - A person is walking when their base has moved more than a tunable distance from their planted spot, judged over a short window, so jitter and weight-shifting don't count. A step toward or away from the camera moves the base up or down the image, so it counts too.
  - All thresholds are tunable.
- **Rewind:** while walking, the growth level falls at the rewind rate. When the person is planted again, their new spot becomes the planted spot and the level rises from wherever it is.
- **Several people:** each tracked person has their own level, so one person walking doesn't rewind a still neighbour.
  - Where the tracker merges two overlapping people into one blob, they share one level for as long as they're merged.
  - When they separate, each one starts from the merged level. *(My call.)*
- **Tracker hiccups don't cost growth.** If a person's track is briefly lost and comes back, possibly in a different slot or with a new ID, they keep their growth. That covers occlusion, a split or merge, or flicker. A new track that appears where a recently lost one was standing inherits its level. *(The approach is my call. The requirement is the anti-goal above.)*
- **Leaving:** a person's plants leave with them. Walking out of frame rewinds on the way. If their track is lost while they still have growth, for example when they step out quickly, their plants rewind away over a short tunable time, about 2 s by default, rather than vanishing. *(The default is my call.)*
- **Sun level:** follows the total growth across everyone, smoothed. One person in full bloom brings the sun to full brightness, and more people don't push it past full. *(The saturation point is my call. It's tunable.)*
- **Run length:** `duration_s` 120, like the other Setups. *(My call.)*

## Constraints

- **Shader player rules** (see `ShowControl/FundingCAPTCHA/shaders/README.md`):
  - Procedural only.
  - Read the Body with `texture()` and normalised UVs. Blob records are the exception: read them with `texelFetch`.
  - Buffers are 16-bit float on the Pi. Store positions and levels as 0–1.
  - `HW_PERFORMANCE` is 0 on the Pi.
  - The Pi renders at half resolution.
  - The camera's square view is stretched to the screen.
- **Blob limits:** at most eight people are tracked at once (slots). The player only runs tracking while a Setup binds `"blobs"`. With all of Buffers B–D in use, the Setup can't be prototyped with blobs in Shadertoy, so leave one buffer free for the blob painter.
- **Real camera input:**
  - The Body and tracker run at about 10 fps, and the shader at about 30.
  - Growth timing must be in seconds, independent of frame rate.
  - The silhouette flickers. Per-run vine heights derived from it every frame must not visibly jitter, so smooth or stabilise them as needed.
- **Tunables:** every value lives as a named constant at the top of `common.glsl`, so it can be retuned on site with **R** reload. That includes:
  - growth time, rewind rate and leave time
  - walking distance and window
  - inheritance radius and time for lost tracks
  - vine spacing, sway, and leaf and flower sizes
  - when flowers open
  - saturation range
  - sun saturation point and position
- **Performance:**
  - Dense vines are drawn per pixel. Keep the per-pixel cost bounded, for example by evaluating only nearby vines.
  - Aim for the same smoothness as the existing Setups on the show Pi 5. *(My call.)*
  - The plan must include a frame-rate check on the Pi. If that couldn't happen, it must say so.

## Testing (decided)

Headless GL tests against fake camera Bodies and blob records, in the style of `test_endless_sunset.py` and `test_hunter_bird.py`, covering at least:
- **Reaching full bloom:**
  - a planted person with realistic edge flicker, dropout holes and box jitter reaches full bloom in about 20 s and never loses growth
  - waving an arm or flailing while planted doesn't rewind, and the vines follow the arm
- **Rewinding:**
  - walking sideways rewinds
  - stepping toward or away from the camera rewinds
  - after walking stops, growth resumes from where it was, not from zero
- **Several people:** a still neighbour isn't rewound by someone walking next to them
- **Tracker hiccups:**
  - a brief track loss or ID change for a planted person keeps their growth
  - a lost track with growth rewinds away without popping
- **The sun:** its level tracks total growth
- **Timing:** it holds at Pi scale, with a 10 fps Body and tracker under a 30 fps render

The walking threshold, and how often the real tracker drops or re-IDs a still person, are unverified until the Setup has been run with the camera (`--camera`, or `--mock-camera` as a first approximation). The plan must include that tuning pass. If it couldn't happen, the plan must say so.

## Left to the builder

- Buffer layout and how per-person state is stored, as long as the behaviour above holds.
- How the base (feet) position is measured from the Body and the box.
- How vines are generated procedurally: placement, wobble, leaf rhythm, flower shapes, bud-to-bloom animation, and how vines follow a moving silhouette without shimmering.
- The crayon texture technique for the sun, and the ray style.
- Exact line weights and default constants beyond those stated.

## Revisions after the first build

- **Look:** the vines are drawn after the concept art's branches. Trunks taper and are ink-outlined, and they rise in pairs and merge where they meet. Forking twigs end in sprigs of pointed petals. About half the branch tips open into hatched daisies. The palette and ripening are unchanged. Density is about three quarters of the mockup's Dense panel.
- **Growth curve:** growth starts fast, reaching `GROW_EARLY` in `GROW_EARLY_S`, then slows so full bloom still comes at about `GROW_S`.
- **Footprints:** a walker leaves plants on the floor where they step. Each footprint is a small clump of branches with a daisy that grows in fast, holds, then rewinds away (`FOOT_*` in `common.glsl`). This is the one exception to "a person's plants leave with them". A person's own plants still ride on their body and rewind while they walk. Live footprints are never overwritten. When all `FOOTPRINTS` are live, walkers leave none until the oldest has gone.
