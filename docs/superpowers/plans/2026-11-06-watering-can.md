# Watering Can Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new shader player Setup, `watering_can`. When a person stays in one spot, dense vines climb their silhouette from its lowest points and bloom over about 20 s. Waggling is free and the plants ride on the body. Walking rewinds the growth. A crayon sun brightens with the garden.

**Architecture:** A Shadertoy-style Setup folder with three tabs. Buffer D stays free for the blob painter.

- **Buffer B, "Body memory"** (per pixel). It holds:
  - stabilised presence
  - the run extents: the bottom and top of the vertical run of body this pixel sits in
  - which tracked person owns the pixel
  - a "hold" that lets a lost person's plants rewind away rather than pop
- **Buffer C, "Garden"** (a small texel grid). It holds:
  - per slot: id, growth level, planted spot, smoothed base (feet), walk timer
  - per slot: a ghost record of the last person lost from that slot, so a returning or split track inherits growth
  - the sun level
- **Image** draws paper, the crayon sun, and the vines, leaves and flowers. All of them derive from B's run extents and C's growth levels every frame.

Tests drive the Setup headlessly with moderngl. Blob records come from the real `BodyBlobs` tracker running on synthetic masks with a fake clock, like `test_hunter_bird.py`.

**Tech Stack:** GLSL (Shadertoy dialect, wrapped by `shadertoy.py`), Python 3, pytest, moderngl, numpy.

**Spec:** `docs/superpowers/specs/2026-11-06-watering-can-design.md`, plus the mockup `docs/superpowers/specs/2026-11-06-watering-can-mockup.html`. Use the "Dense" panel, and scrub its slider. Also read the blob contract in `docs/adr/0022-shader-player-blob-records.md` and `shaders/README.md`. Read all of these before starting. `shaders/hunter_bird/` is the reference for per-slot state, fresh-id handling and the test rig. `shaders/endless_sunset/buffer_b.glsl` is the reference for soft presence and hole filling.

## Global Constraints

- **Shader player rules** (`ShowControl/FundingCAPTCHA/shaders/README.md`):
  - Read the Body (Buffer A) only with `texture()` and UVs.
  - Read blob records only with `texelFetch(ch, ivec2(slot, row), 0)`.
  - Buffers are RGBA16F. Store positions as UV, levels as 0–1, and time only as bounded "seconds since" counters clamped at `T_CLAMP`. Never store absolute `iTime`.
  - `HW_PERFORMANCE` is 0, and there are no textures.
- **The `blobs` contract is read-only.** If you need more from the tracker, stop and raise it.
- **Shadertoy:** every tab must paste unchanged, with `body_painter.glsl` in Buffer A and `blob_painter.glsl` in Buffer D. In Shadertoy, B and C read D's previous frame. Behaviour must not depend on that one-frame difference.
- **Tunables:** every threshold, rate, size and timing is a named constant at the top of `common.glsl`, so it can be retuned on site with **R**.
- **Units:** sizes are in screen heights. Mockup value N px → `N / 360.0`. Records and B are in UV. `toScreen(uv) = uv * iResolution.xy / iResolution.y`.
- **Timing:** everything is in seconds via `iTimeDelta`. Growth must not depend on render rate.
- **Palette (exact):**
  - paper `#f6f1e4`
  - ink `#111111`
  - yellow `#fff200`
  - orange `#e8862f`
  - pink `#e8957f`
  - violet `#6b5b95`
  - rust `#bc4c26`
  - Stem and leaf greens are free choices, ripening from near-grey to saturated.
- **Never draw the silhouette.** No outline, fill or wash. Where nothing has grown, the pixel is paper.
- **Repo rules:** never write a show, artist or album name into any file. Never commit anything under `ShowControl/FundingCAPTCHA/images/private/`.
- **Branch:** `claude/watering-can` (the spec is committed there).
- **Tests:**
  - Run from `ShowControl/FundingCAPTCHA/`, e.g. `python3 -m pytest test_watering_can.py -v`.
  - In a fresh container, `apt-get install -y libegl1 libgl1-mesa-dri` provides a headless GL context.
  - Baseline: `make test` is green, except `test_compile_error_reports_tab_line` on NVIDIA drivers. That failure already exists and is unrelated.

## Review Focus

1. **The tracker splits a still person.** For example, a raised arm breaks off as its own blob, or depth dropout cuts the torso. The new track would start bare, leaving part of the body unplanted. Expected: a new track overlapping, or next to, a planted person inherits their growth. Pinned by `test_split_off_part_inherits` (Task 2).
2. **Feet cut off by the bottom of the frame**, when someone stands close to the camera. The box bottom pins to the edge. Expected: standing still there doesn't rewind, and walking sideways still rewinds. Pinned by `test_feet_off_frame` (Task 2).
3. **Flicker shimmering the vines.** Run extents recomputed every frame from a flickering mask make vine tips and leaves jump. Expected: a planted, bloomed person's image is stable frame to frame. Pinned by `test_bloom_is_stable_under_flicker` (Task 3).
4. **Hours in 16-bit buffers.** Every counter stays bounded and finite. Pinned by `test_state_stays_bounded_when_idle` (Task 2).
5. **Frame rate on the Pi.** Per-pixel cost is bounded by early-outs:
   - B marches only inside the body.
   - Image looks at `VINE_NEIGHBOURS` vines and skips pixels with no body nearby.
   - If fps falls short, cut in this order: leaf count, flower petal count, `VINE_NEIGHBOURS`, `RUN_STEPS`.
   - Checked in Task 5.

---

## File Structure

All under `ShowControl/FundingCAPTCHA/`:

| File | Responsibility |
|---|---|
| `shaders/watering_can/setup.json` | Channel bindings, `duration_s: 120` |
| `shaders/watering_can/common.glsl` | Constants, palette, record and state accessors, `toScreen`, hash and noise |
| `shaders/watering_can/buffer_b.glsl` | Body memory (per pixel) |
| `shaders/watering_can/buffer_c.glsl` | Garden state (texel grid) |
| `shaders/watering_can/image.glsl` | Paper, sun, plants |
| `shaders/setups.json` | Add `"watering_can"` |
| `test_watering_can.py` | GL behaviour tests |
| `docs/FundingCAPTCHA.md` | List `watering_can` in "Setups in rotation", with a link to the spec |

**`setup.json`:**
```json
{
  "_comment": "Watering can: stay put and vines grow up your silhouette and bloom; walking rewinds. Spec: docs/superpowers/specs/2026-11-06-watering-can-design.md",
  "duration_s": 120,
  "channels": {
    "buffer_b": ["A", "B", "blobs"],
    "buffer_c": ["B", "C", "blobs"],
    "image":    ["B", "C", "blobs"]
  }
}
```

**Buffer B, per pixel:**

| `.r` | `.g` | `.b` | `.a` |
|---|---|---|---|
| presence 0–1 (soft, hole-filled, eased) | run bottom y (UV) | run top y (UV) | `owner + 0.9 * hold` |

- `owner` = slot + 1, or 0 for none.
- `hold` = 0–1, and is 1 while the body is present.
- Outside any run, `.g` and `.b` are 0.

**Buffer C, texel `(x, y)`, with `k` = slot 0–7.** Every texel that isn't listed writes 0.

| Texel | `.x` | `.y` | `.z` | `.w` |
|---|---|---|---|---|
| `(k, 0)` PERSON | id (0 = none) | growth 0–1 | planted spot x | planted spot y (UV) |
| `(k, 1)` BASE | base x | base y (UV, smoothed) | seconds since last walking step (≤ `T_CLAMP`) | — |
| `(k, 2)` GHOST | spot x | spot y | growth at loss | seconds since loss (`T_CLAMP` = no ghost) |
| `(0, 3)` SUN | sun level 0–1 (eased) | raw total growth | — | — |

---

### Task 1: Skeleton, Common, Body memory (Buffer B)

**Files:**
- Create: `shaders/watering_can/setup.json` (above), `common.glsl`, `buffer_b.glsl`
- Create: `buffer_c.glsl` (stub: writes 0)
- Create: `image.glsl` (stub: paper)
- Modify: `shaders/setups.json` → `["ripples", "endless_sunset", "hunter_bird", "watering_can"]`
- Create: `test_watering_can.py`

**Interfaces produced in `common.glsl`.** Use these exact names. Values are starting points, and Task 5 tunes them.
```glsl
const int   SLOTS = 8;
const float T_CLAMP = 99.0;
// Body memory
const float BODY_BLUR_TEXELS = 1.5, HOLE_FILL_TEXELS = 2.5;   // as endless_sunset
const float PRESENCE_EASE_S  = 0.12;     // eases presence so 1-px edge flicker averages out
const float BODY_ON          = 0.5;      // presence above this is body
const int   RUN_STEPS        = 64;       // max march taps each way
const float RUN_STEP_H       = 1.0/96.0; // march step, screen heights
const float RUN_EASE_S       = 0.15;     // eases run extents; snaps when they jump more than RUN_SNAP
const float RUN_SNAP         = 0.08;     // screen heights
const float LEAVE_S          = 2.0;      // a lost person's plants rewind away over this
// Garden
const float GROW_S = 20.0, REWIND_S = 20.0;           // empty → full bloom, full bloom → empty
const float BASE_BAND = 0.04;           // screen heights above the box bottom that count as feet
const int   BASE_TAPS = 16;
const float BASE_EASE_S = 0.3;
const float WALK_DIST   = 0.04;         // screen heights the base must move from the spot to count as a step
const float WALK_HOLD_S = 0.4;          // walking lasts this long after the last step
const float INHERIT_S = 3.0, INHERIT_DIST = 0.15;     // ghost lifetime; how near a new track must appear (screen heights)
const float SUN_FULL = 1.0, SUN_EASE_S = 1.5;         // total growth that fully lights the sun
// Plants (Task 3)
const float VINE_SPACING = 4.5/360.0;   // ~30 vines across an adult, as the mockup's Dense panel
const int   VINE_NEIGHBOURS = 2;        // vines evaluated each side of a pixel
const float VINE_WOBBLE = 5.0/360.0, SWAY_AMP = 2.0/360.0, SWAY_HZ = 0.25;
const float STEM_W = 2.2/360.0, INK_W = 1.2/360.0;
const float LEAF_STEP = 18.0/360.0, LEAF_LEN = 9.0/360.0, LEAF_WID = 3.8/360.0;
const float FLOWER_FROM = 0.6, FLOWER_FULL = 0.9;     // growth at which buds start, and are fully open
const float FLOWER_R = 8.0/360.0, BUD_R = 2.5/360.0;
const float SAT_MIN = 0.1, SAT_MAX = 0.95;
// Sun (Task 4)
const vec2  SUN_POS = vec2(-0.16, 0.84);   // x from the right edge (screen heights), y as a fraction of height
const float SUN_R = 0.09, RAY_LEN = 0.07;
```
Also in `common.glsl`:
- palette constants
- `S_EMPTY … S_LOST` and `isState`
- `recBox`, `recMot`, `recIdn` (as in `hunter_bird`)
- `cPerson(s,k)`, `cBase(s,k)`, `cGhost(s,k)`, `cSun(s)`
- `int bOwner(vec4 b)` and `float bHold(vec4 b)`, which decode B's `.a`
- `toScreen` (a `#define`, as in `hunter_bird`)
- `hash12` and `noise`

**B rules (per pixel):**
- Presence: compute endless_sunset's soft and hole-filled presence from A, then ease it towards that target with `PRESENCE_EASE_S`.
- Owner: the slot whose record is not empty and whose box contains the pixel. If several boxes contain it, pick the nearest box centre.
- Run extents: only if presence ≥ `BODY_ON`. March B's own previous-frame `.r` down and up from this pixel in `RUN_STEP_H` steps, at most `RUN_STEPS` each way, and stop at the first tap below `BODY_ON`.
  - The march uses previous-frame presence, so the extents lag by one frame. That's fine.
  - The extents are eased with `RUN_EASE_S`, except that they snap when the new value differs by more than `RUN_SNAP`.
- Hold, when the body is absent:
  - If the previous owner's record is empty or lost: keep the previous extents and owner, and decrease hold by `dt / LEAVE_S`.
  - Otherwise (the owner is still live and simply moved off this pixel): set hold to 0 and the owner to 0.
  - This is what stops walkers leaving trails.

- [ ] **Step 1: Check `git status` is clean on `claude/watering-can`.**
- [ ] **Step 2: Write the rig and the failing tests.**
  - Copy `ctx`, `Rig.run`, `rect`, `EMPTY` and `both` from `test_hunter_bird.py`.
  - Use `SETUP = …/"watering_can"`, `SIZE = (128, 72)`, `BODY = (64, 48)`, `BLOBS = BlobConfig(min_blob_pixels=20)`.
  - `Rig(ctx, size=SIZE, dt=DT)` takes the render `dt` as a parameter.
  - Add `Rig.buf(name)`, which returns float32 `(h, w, 4)` with row 0 at the GL bottom.
  - Add `Rig.person(k) = buf("buffer_c")[0, k]`, `Rig.base(k) = [1, k]`, `Rig.ghost(k) = [2, k]`, `Rig.sun() = [3, 0]`, and `Rig.image()`.
  - Add these mask builders. Masks are bool `(48, 64)` with row 0 at the top:

```python
def person(x=26, feet=44, arm="down", lift=None):
    """A figure 12 px wide, head to feet. x is its left edge; feet is the row below its feet.
    arm: "down" (hanging at the sides), "out" (right arm horizontal), "up" (right arm overhead).
    lift: "L" or "R" raises that foot 2 px (a weight shift)."""

def flickering(n, seed=0, **kw):
    """person(**kw) with its 1-px border toggled randomly, plus 3 random 1-px dropout holes inside, each camera frame."""

def walking(n, step=1, x=26, bounce=(4, 48), **kw):   # person starting at x, moving sideways step px per camera frame, bouncing within bounce
def owner(texel):   # python mirror of bOwner: int(floor(texel[3]))
def slot_of_live(rig):   # the one slot whose PERSON id != 0; asserts there is exactly one
def stepping_toward(n, **kw):   # feet row increases 1 px per camera frame from 36 to 47 (moving down the image)
```

Tests for this task:
```python
def b_at(rig, col, row):          # B texel under Body pixel (col, row), row 0 = top
def test_presence_ignores_edge_flicker(ctx):
    rig = Rig(ctx); rig.run(flickering(30))
    # one Body px inside the border, over 10 more camera frames:
    # presence at the torso centre stays > 0.95, and a pixel 3 px outside the figure stays < 0.05
def test_run_extents_span_leg_to_shoulder(ctx):
    rig = Rig(ctx); rig.run([person()] * 10)
    g, b = b_at(rig, 28, 40)[1:3]       # in a leg
    # g ≈ UV of the feet (1 - 44/48) within 1/48; b ≈ UV of the shoulder top within 2/48
def test_raised_arm_runs_start_at_its_lowest_point(ctx):
    rig = Rig(ctx); rig.run([person(arm="up")] * 10)
    # a pixel in the raised arm, above the head row: its run bottom is the arm's lowest row, not the feet
def test_owner_is_record_slot(ctx):
    rig = Rig(ctx); rig.run([person()] * 10)
    assert owner(b_at(rig, 30, 20)) == 1 and owner(b_at(rig, 2, 2)) == 0
def test_walker_leaves_no_hold_trail(ctx):
    rig = Rig(ctx); rig.run(walking(20))
    # every B texel with presence < 0.05 has hold == 0
def test_lost_person_holds_then_fades(ctx):
    rig = Rig(ctx); rig.run([person()] * 20); rig.run([EMPTY] * 15)   # 1.5 s: lost after 8 misses
    h1 = hold at the torso centre
    rig.run([EMPTY] * 25)
    # 0 < h1 < 1, and the hold is 0 after LEAVE_S more; the run extents were kept while hold > 0
```

- [ ] **Step 3: Run the tests.** `python3 -m pytest test_watering_can.py -v` should FAIL (stub B), and `test_shadertoy.py::test_listed_setups_compile[watering_can]` should PASS.
- [ ] **Step 4: Implement `common.glsl` and `buffer_b.glsl`** following the rules above.
- [ ] **Step 5: Run the tests.** Expected: PASS.
- [ ] **Step 6: Commit** "Watering can: Setup skeleton and Body memory".

### Task 2: Garden state (Buffer C)

**Files:** `buffer_c.glsl` and `test_watering_can.py`.

**Interfaces:**
- **Consumes:** B as in Task 1, through `bOwner`, `bHold` and `.r`; the record accessors.
- **Produces:** the C layout above, for Tasks 3 and 4.

**C rules (per frame; each texel reads the previous frame of every other texel):**
- **Fresh slot.** The record's id differs from PERSON.id, or the record is empty.
  - PERSON = `(record id or 0, inherit, base, base)`, where `base` = record box bottom-centre (x centre, y0).
  - `inherit` = the max of:
    - the growth of every GHOST with `since < INHERIT_S` whose spot is within `INHERIT_DIST` (screen units) of `base`;
    - the growth of every other live PERSON whose record box overlaps this box, or whose box is within `INHERIT_DIST`.
  - The second case covers splits and merges.
  - Reset BASE: walk timer = `T_CLAMP`.
- **GHOST for slot `k`:** when PERSON.id ≠ 0 and the slot turns fresh or lost this frame, write `(PERSON spot, PERSON growth, 0)`. Otherwise `since += dt` (clamped).
- **BASE:**
  - Sample B `.r` at `BASE_TAPS` x positions across the box, at `y0 + BASE_BAND/2`.
  - Take the presence-weighted mean x. If the weight is 0, use the box centre.
  - Base target = that x and `y0`. Ease toward it with `BASE_EASE_S`.
- **Walking.** If `length(toScreen(base - spot)) > WALK_DIST`: set spot = base and reset the walk timer to 0. Otherwise the timer advances by `dt`. `walking` = timer < `WALK_HOLD_S`.
- **Growth.** Only for confirmed records:
  - walking: `-= dt / REWIND_S`
  - otherwise: `+= dt / GROW_S`
  - clamp to 0–1
  - Tentative and coasting records hold their level.
- **SUN.**
  - raw = Σ live growth + Σ ghost growth × `max(0, 1 - since / LEAVE_S)`
  - level eases toward `clamp(raw / SUN_FULL, 0, 1)` with `SUN_EASE_S`
- `iFrame == 0` resets everything (ghost `since` = `T_CLAMP`).

- [ ] **Step 1: Write the failing tests.**
```python
def test_planted_flickering_person_blooms_in_20s(ctx):          # spec: ~20 s, never loses growth
    rig = Rig(ctx); levels = []
    for _ in range(22): rig.run(flickering(10)); levels.append(rig.person(0)[1])
    assert abs(levels[9] - 0.5) < 0.06 and levels[-1] > 0.98
    assert all(b >= a - 1e-3 for a, b in zip(levels, levels[1:]))
def test_arm_waving_does_not_rewind(ctx):
    rig = Rig(ctx); rig.run([person(arm=("down", "out", "up")[k // 5 % 3]) for k in range(100)])
    assert abs(rig.person(0)[1] - 0.5) < 0.06
def test_weight_shift_does_not_rewind(ctx):
    rig = Rig(ctx); rig.run([person(lift=(None, "L", None, "R")[k // 3 % 4]) for k in range(100)])
    assert abs(rig.person(0)[1] - 0.5) < 0.06
def test_walking_sideways_rewinds(ctx):
    rig = Rig(ctx); rig.run([person()] * 100); g0 = rig.person(0)[1]
    rig.run(walking(30, x=26))
    assert abs((g0 - rig.person(0)[1]) - 3.0 / 20.0) < 0.05
def test_stepping_toward_camera_rewinds(ctx):
    rig = Rig(ctx); rig.run([person(feet=36)] * 100); g0 = rig.person(0)[1]
    rig.run(stepping_toward(11)); assert rig.person(0)[1] < g0 - 0.03
def test_growth_resumes_after_walking(ctx):
    # grow 10 s, walk 3 s, then stand 3 s: the level rises from the post-walk value by ~3/20, never resetting to 0
def test_neighbour_walking_does_not_rewind_still_person(ctx):
    rig = Rig(ctx); rig.run(both([person(x=46)] * 100, walking(100, x=4, bounce=(4, 20))))
    # the still person's slot has growth ≈ 0.5 ± 0.06
def test_brief_loss_keeps_growth(ctx):
    rig = Rig(ctx); rig.run([person()] * 100); rig.run([EMPTY] * 20); rig.run([person()] * 5)
    assert rig.person(slot_of_live(rig))[1] > 0.45            # whichever slot and id it came back in
def test_merge_then_split_both_inherit(ctx):
    # two planted people 10 s apart, slide together until their masks overlap (one blob), then apart:
    # each resulting track's growth ≥ the merged level - 0.05
def test_split_off_part_inherits(ctx):                          # Review Focus 1
    # a planted person (10 s); then their right arm is detached by a 1-px gap for 2 s (a second blob):
    # the new track's growth ≥ the person's growth - 0.05
def test_feet_off_frame(ctx):                                   # Review Focus 2
    # person(feet=48, ...) cut by the bottom edge, flickering for 10 s: growth ≈ 0.5; then walking 3 s: it drops by ~0.15
def test_new_person_far_from_ghosts_starts_bare(ctx):
    # A planted 10 s at x=4 leaves; B appears at x=46 within INHERIT_S: B's growth < 0.05 after its first second
def test_sun_tracks_growth(ctx):
    # empty 3 s: sun < 0.02; one person 22 s: sun > 0.95; leaves: sun < 0.05 within LEAVE_S + 3·SUN_EASE_S
def test_growth_independent_of_render_rate(ctx):
    a = Rig(ctx, dt=1/30); a.run([person()] * 100, frames_per_camera=3)
    b = Rig(ctx, dt=1/60); b.run([person()] * 100, frames_per_camera=6)
    assert abs(a.person(0)[1] - b.person(0)[1]) < 0.02
def test_state_stays_bounded_when_idle(ctx):                     # Review Focus 4
    # as hunter_bird: two renders with dt = 200 s between empty runs; every C and B value is finite, and |C| ≤ 99
```
- [ ] **Step 2: Run** `python3 -m pytest test_watering_can.py -v`. Expected: the Task 2 tests FAIL.
- [ ] **Step 3: Implement `buffer_c.glsl`** following the rules above.
- [ ] **Step 4: Run the tests.** Expected: all PASS. If a test only passes after changing a constant, change it in `common.glsl` and note why in a comment.
- [ ] **Step 5: Commit** "Watering can: growth, walking, inheritance and sun level".

### Task 3: Image — plants

**Files:** `image.glsl` and `test_watering_can.py`.

**Interfaces:**
- **Consumes:** B (run extents, owner, hold), C PERSON growth and SUN.
- **Produces:** the final image, minus the sun.

**Drawing rules:**
- **Vines.** Vine `i` sits at screen x `i * VINE_SPACING`, plus a wobble `VINE_WOBBLE * sin(height * f + hash(i))` and a sway that grows with height up the run (`SWAY_AMP`, `SWAY_HZ`).
  - For each pixel, evaluate the vines within `VINE_NEIGHBOURS` either side.
  - For each vine, sample B at (vine x, pixel y), and also at pixel y ± `FLOWER_R`, so that overhanging leaves and flowers find their run.
- **Reach.** For a run with bottom `g`, top `b`, owner growth `G` and hold `h`: the tip is at `g + G * h * (b - g)`.
  - The stem is drawn from `g` to the tip, only where B presence ≥ `BODY_ON` or hold > 0. Stems stay inside.
  - Leaves are drawn at heights `g + j * LEAF_STEP` below the tip, on alternating sides. They may extend outside the body.
  - At the tip there's a bud below `FLOWER_FROM`. Between `FLOWER_FROM` and `FLOWER_FULL` it opens into a 5-petal flower of radius up to `FLOWER_R`. The flower may extend outside the body.
  - Flower colour is chosen per vine by hash from pink, orange, violet and rust, with a yellow centre.
- **Colour.** Saturation = `mix(SAT_MIN, SAT_MAX, G)`, uniform for the whole person. It applies to the greens and to the flowers.
  - The look is flat fills with `INK_W` ink outlines on leaves, petals and buds, as in the mockup.
- **Early-out.** If B presence and hold are both 0 at all sampled points, output paper.

- [ ] **Step 1: Write the failing tests.**
```python
PAPER = np.array([246, 241, 228])
def drawn(img, region=None):                # bool mask of pixels differing from paper by > 12 in any channel
def test_nothing_drawn_before_growth(ctx):  # anti-goal: never draw the silhouette
    rig = Rig(ctx); rig.run([person()] * 5)
    assert drawn(rig.image()).mean() < 0.002     # the sun corner is excluded via region
def test_bloom_fills_the_silhouette(ctx):
    rig = Rig(ctx); rig.run([person()] * 220)
    # ≥ 70% of the screen pixels inside the figure are drawn, and drawn pixels outside the figure lie within FLOWER_R + LEAF_LEN of it
def test_growth_climbs_from_the_feet(ctx):
    rig = Rig(ctx); rig.run([person()] * 60)                  # growth ≈ 0.3
    # drawn fraction in the figure's bottom third > 0.5; in the top third < 0.1
def test_colour_ripens(ctx):
    # mean HSV saturation of drawn pixels at growth 0.3 < at growth 1.0 - 0.25
def test_flowers_only_late(ctx):
    # pixels near the flower hues (pink/orange/violet/rust ± 30) are absent at growth 0.4 and present at growth 1.0
def test_vines_follow_the_arm(ctx):
    rig = Rig(ctx); rig.run([person(arm="up")] * 220)
    # drawn fraction inside the raised-arm rect > 0.5; then arm="down" for 3 camera frames: the arm rect drawn fraction < 0.1
def test_bloom_is_stable_under_flicker(ctx):                     # Review Focus 3
    rig = Rig(ctx); rig.run(flickering(220))
    # over 10 more camera frames, the mean |Δ| between consecutive images inside the figure is < 6 (of 255)
def test_lost_person_plants_rewind_without_popping(ctx):
    rig = Rig(ctx); rig.run([person()] * 220); counts = []
    for _ in range(40): rig.run([EMPTY]); counts.append(drawn(rig.image()).sum())
    # the count reaches 0 by 1.5 s (lost) + LEAVE_S + 0.5 s; no single camera frame loses more than 30% of the previous count
```
- [ ] **Step 2: Run the tests.** Expected: FAIL.
- [ ] **Step 3: Implement `image.glsl`.**
- [ ] **Step 4: Run the tests.** Expected: all PASS.
- [ ] **Step 5: Commit** "Watering can: vines, leaves and flowers".

### Task 4: Image — the crayon sun

**Files:** `image.glsl` and `test_watering_can.py`.

**Rules:**
- **Position.** The sun's centre is at `(iResolution.x/iResolution.y + SUN_POS.x, SUN_POS.y)` in screen units, which is the top right.
- **Disc.** Radius `SUN_R`, with a crayon look: the edge is broken by noise, and the fill is a grain or hatch of noise that leaves paper showing through.
- **Muted vs. lit.**
  - At sun level 0, the colour is a desaturated, paper-mixed yellow and there are no rays.
  - At level 1, the colour is `#fff200` with ~12 crayon rays of length `RAY_LEN`.
  - Ray length and colour follow the level.
- **Order.** Plants draw over the sun.

- [ ] **Step 1: Write the failing tests.**
```python
def sun_patch(img):    # the pixels within SUN_R + RAY_LEN of the sun centre
def test_sun_is_muted_when_empty(ctx):
    # empty 3 s: the sun disc is drawn (not paper), its mean saturation < 0.35, and nothing is drawn in the ray ring
def test_sun_brightens_and_grows_rays_with_bloom(ctx):
    # one person 22 s: disc saturation > 0.7, ray-ring drawn fraction > 0.15
```
- [ ] **Step 2: Run the tests.** Expected: FAIL. **Step 3:** Implement. **Step 4:** Run. Expected: PASS.
- [ ] **Step 5: Commit** "Watering can: crayon sun".

### Task 5: Look and feel, Shadertoy check, frame rate, camera tuning, docs

**Files:** `common.glsl` (constants only) and `docs/FundingCAPTCHA.md`.

- [ ] **Step 1: Check by eye with the mouse.** Run `python3 shader_app.py --test-input --windowed --setup watering_can`.
  - Hold still and watch it grow to full bloom in ~20 s.
  - Wiggle while holding the button: nothing should rewind.
  - Drag across the screen: it should rewind.
  - Release: the plants should rewind away.
  - Compare against the mockup's Dense panel, and tune constants only, with **R**.
- [ ] **Step 2: Mock camera.** Run `python3 shader_app.py --mock-camera --windowed --setup watering_can` for 2 minutes and note the fps lines. If fps is short of the other Setups, cut in the Review Focus 5 order.
- [ ] **Step 3: Shadertoy.**
  - Paste `body_painter.glsl` into A and `blob_painter.glsl` into D (channels: D, Keyboard).
  - Paste `common.glsl`, `buffer_b.glsl` (channels: A, B, D), `buffer_c.glsl` (channels: B, C, D) and `image.glsl` (channels: B, C, D).
  - Confirm it compiles and behaves the same. If no browser is available, say so in the hand-off.
- [ ] **Step 4: Docs.** In `docs/FundingCAPTCHA.md` → "Setups in rotation", add `watering_can` with a link to the design and a note that its tunables (including `WALK_DIST`, `GROW_S` and `REWIND_S`) are at the top of its `common.glsl`.
- [ ] **Step 5: Full suite.** Run `make test` from the repo root. It must be green, apart from the known NVIDIA-only failure.
- [ ] **Step 6: Commit** "Watering can: tuning pass and docs". The hand-off must state:
  - the constants that changed;
  - the fps seen with `--mock-camera`, and on the Pi 5 if it was run there;
  - that the walking threshold, flicker immunity and re-ID inheritance have **not** been verified with the real camera, unless they were.
  - That verification needs `--camera` on site:
    - a visitor stands 25 s and reaches full bloom without any rewind;
    - waving the arms doesn't rewind;
    - one sideways step visibly rewinds.
