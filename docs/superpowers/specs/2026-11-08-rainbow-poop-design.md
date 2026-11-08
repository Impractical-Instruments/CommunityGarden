# Rainbow Poop — shader player Setup

A new FundingCAPTCHA shader player Setup (ADR-0021), from issue #161. A flock of cartoon birds circles overhead. Every few seconds one of them picks a visitor, swoops down, and drops a rainbow poop that splats on their silhouette. The splats stick to the person, follow them as they move, drip, and fade. A visitor who dodges at the right moment makes the bird miss, and the poop splats on the ground instead.

## Intent

Slapstick. Standing in front of the screen gets you pooped on, which is funny the first time and funnier when it happens to your friend. The joke works because it's clearly aimed at *you*: the bird picks you, dives at you, and the splat stays on you as you walk around. Dodging is the game inside the joke.

## Goals

- **Empty room:** the flock circles lazily in the upper sky. The scene is never still.
- **Someone appears:** within about 2 s of the tracker confirming them, a bird peels off, swoops down above their head, releases a poop, and climbs back to the flock.
- **Cadence:** each person is bombed about every 5 s (4–6 s with jitter). *(Decided.)*
- **Splats stick:** a splat lands where the poop hits the silhouette, is drawn only on the silhouette, and travels with the person. Drips run down from it over the first few seconds. It fades out about 20 s after landing. *(Decided.)*
- **Dodging:** the bird leads its target, aiming where they'll be when the poop lands. Changing pace or direction after the release makes it miss. A miss splats on the ground at the target's feet and fades sooner.
- Runs on the show Pi 5 in the existing shader player, and can be prototyped in Shadertoy with the body painter and blob painter like every other Setup.

## Non-goals

- No uploaded art, textures, video or sound.
- Nearness (`.g`) isn't used.
- Splats don't survive a tracker re-ID (see Behaviour).

## Anti-goals

- **Noise.** The screen mustn't fill with poop. With one bomb per person per ~5 s and a 20 s life, a person carries about four splats at a time.
- **Splats floating off people.** A splat is never drawn outside the silhouette.
- **Popping.** Splats appear with a quick splat-in and leave with a fade, never a cut.
- **Realism.** Flat, ink-outlined storybook drawing, like the other Setups.

## The look (decided)

- **Style:** the shared line-drawn storybook style: black ink lines about 2–3 px at 1080p, flat fills, paper `#f6f1e4` background.
- **Sky:** paper with a few slow, ink-outlined clouds near the top.
- **People:** a flat warm-white fill with an ink outline (as `hunter_bird`), so you can see who's being bombed.
- **Birds:** a shared flock of four cartoon birds: a round slate body, a flapping wing, an orange beak and an eye, all ink-outlined. Wings beat faster while climbing and tuck back in the dive.
- **Poop in flight:** a small rainbow teardrop with an ink outline.
- **Splat:** a cartoon blob with lumpy edges, concentric rainbow bands (red outside to violet inside), a few satellite droplets, an ink outline, and two or three drips in rainbow colours running down from it. Everything is clipped to the silhouette.
- **Ground splat:** a flattened rainbow puddle at the target's feet.

## Behaviour (decided)

- **Flock:** `BIRDS` = 4, shared. Each circles its own slowly drifting orbit in the upper sky when idle.
- **Picking a target:** each confirmed person has a countdown, first `FIRST_BOMB_S` (about 2 s), then `BOMB_EVERY_S` ± `BOMB_JITTER_S`. When it runs out, the nearest idle bird is assigned to them, at most one bird per person at a time. If no bird is free, the person waits.
- **The dive:** a fixed-time swoop (`DIVE_S`) from the bird's position to a release point `DROP_ABOVE` above the target's head, arriving flying horizontally. The release point is updated every frame from the target's box and velocity, leading them by the poop's fall time. After the release the bird climbs away and rejoins its orbit.
- **The poop:** falls under gravity from the release point with the bird's horizontal velocity. It splats on the first silhouette pixel it reaches, on whichever tracked person's box holds that pixel (the target or a bystander). If it passes the target's feet without touching anyone, it splats on the ground there.
- **Sticking:** a splat is stored in its person's local frame (the low-passed box top-centre, scaled by box height). It follows them and scales as they step nearer or further away. Arms that move far from where the splat landed may carry it off the silhouette, where it's clipped.
- **Leaving, overlaps and slot swaps:** splats belong to a track. When the track is lost (the person left, merged into someone else, or got a new ID), its splats fade out over `LEAVE_FADE_S` (about 1 s). A new track starts clean. *(Decided: the simple rule. Inheriting splats across a re-ID is a possible later improvement.)*
- **Run length:** `duration_s` 120, like the other Setups.

## Constraints

- Shader player rules (`ShowControl/FundingCAPTCHA/shaders/README.md`): procedural only, Body read with `texture()` and UVs, blob records with `texelFetch`, 16-bit float buffers (positions as UV, bounded "seconds since" counters), `HW_PERFORMANCE` 0, half-resolution render.
- Leave Buffer D free for the blob painter, so the Setup can be prototyped in Shadertoy.
- Body and tracker run at about 10 fps, render at about 30. All timing is in seconds via `iTimeDelta`.
- Every tunable is a named constant at the top of `common.glsl`.

## Testing

Headless GL tests in the style of `test_hunter_bird.py`, with the real `BodyBlobs` tracker on synthetic masks and a fake clock:
- the empty room keeps the birds in the sky and drops nothing
- a standing person is bombed within about 3 s and then about every 5 s, and the splat is in their local frame on the body
- a splat follows a person who walks, and is clipped to the silhouette in the Image
- a person who reverses direction just after a release is missed, and the poop lands on the ground
- splats fade after their life, and fade when the track is lost
- a new track in a reused slot starts with no splats
- state stays bounded and finite through huge time steps

Unverified until run with the real camera: how the cadence and dodge timing feel, and frame rate on the Pi 5.
