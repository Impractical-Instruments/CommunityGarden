# Hunter Bird Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new shader player Setup, `hunter_bird`: the blob tracker's real boxes, IDs and lifecycle, drawn as a bird in a tree hunting visitors. You see it only as its eye. Move and it notices you; freeze and it loses interest; flail and it locks on and stamps you, once.

**Architecture:** A Shadertoy-style Setup folder with three tabs:
- **Buffer B** is "Bird state". It's a small grid of texels holding:
  - per slot: tracked ID, motion, interest, stamped, previous box, footprint head
  - global: target, lock, strike, reticle, lids, blinks
  - a footprint ring
- **Image** draws the world from the Body, the field notes from the `blobs` records, the attention from B, and the eye from B.
- **Common** holds every tunable constant, the palette, the record and state accessors, the glyph SDFs and the canopy layout.

The tests drive the Setup headlessly with moderngl. Records come from the real `BodyBlobs` tracker run on synthetic masks with a fake clock, so record noise is realistic.

**Tech Stack:** GLSL (Shadertoy dialect, wrapped to GLSL 330 by `shadertoy.py`), Python 3, pytest, moderngl, numpy.

**Spec:** `docs/superpowers/specs/2026-11-04-hunter-bird-design.md`. The mockup is `docs/superpowers/specs/2026-11-04-hunter-bird-mockup.html`. The `blobs` contract is `docs/adr/0022-shader-player-blob-records.md` and `shaders/README.md` → "Blobs". Read all three before starting. Open the mockup in a browser and scrub it.

## Global Constraints

- **Shader player rules** (`ShowControl/FundingCAPTCHA/shaders/README.md`):
  - Read the Body (Buffer A) only with `texture()` and UVs.
  - Read blob records only with `texelFetch(ch, ivec2(slot, row), 0)`.
  - Buffers are RGBA16F. Keep stored values small, positions in UV, IDs ≤ 999, and time as bounded "seconds since" counters clamped at `T_CLAMP`, never absolute `iTime`.
  - `HW_PERFORMANCE` is 0. No textures. Filtering is linear and clamped.
- **The `blobs` contract is read-only.** If you need more from the tracker, stop and raise it; don't work around it.
- **Shadertoy:** every tab must paste unchanged, with `body_painter.glsl` in Buffer A and `blob_painter.glsl` in Buffer D. In Shadertoy, B reads D from the previous frame (render order A, B, C, D); on the Pi, blobs are current. Behaviour must not depend on that one-frame difference.
- **Tunables:** every threshold, gain and timing is a named constant at the top of `common.glsl`, so it can be retuned on site with **R** (reload).
- **Units:** size everything in screen heights (`iResolution.y`). Mockup value N px → `N / 360.0`. Records are in Body UV. Convert with `uv * iResolution.xy`, then divide by `iResolution.y`. Glyphs, tags, reticle and stamp are sized in screen heights so they don't stretch.
- **Palette (exact):**
  - paper `#f6f1e4`
  - ink `#111111`
  - slate `#719aad`
  - deep blue `#2076a3`
  - rust `#bc4c26`
  - yellow `#fff200`
  - orange `#e8862f`
  - violet `#6b5b95`
  - warm white `#fffaf0`
- **Repo rules:** never write a show, artist or album name into any file. Never commit anything under `ShowControl/FundingCAPTCHA/images/private/`.
- **Branch:** if PR "Hunter bird: design, blob-records contract, and build plan" (`claude/hunter-bird-mockup`) has merged, branch `claude/hunter-bird` off `main`. Otherwise branch off `claude/hunter-bird-mockup` and stack.
- **Tests:** run from `ShowControl/FundingCAPTCHA/`, e.g. `python3 -m pytest test_hunter_bird.py -v`. GL tests need a headless context. In a fresh container, `apt-get install -y libegl1 libgl1-mesa-dri` gives llvmpipe. Baseline: `make test` is all green, so it must stay that way.

## Review Focus

1. **A still person must be able to escape.** On the Pi, records ease toward each 10 Hz camera frame, so a still person's box breathes by a pixel or two, and edge flicker changes its size. That must read as motion 0, and interest must drain. Pinned by `test_flickering_still_person_has_no_motion` (Task 1) and `test_freezing_loses_the_bird` (Task 2).
2. **Once per person.** The same ID is never stamped twice, however long it flails. A new ID in a reused slot is stampable. Pinned by `test_strike_once_per_person` and `test_reused_slot_resets_stamp` (Task 2).
3. **Hours of running in 16-bit buffers.** Every counter stays bounded, and no absolute time is stored. Pinned by `test_state_stays_bounded_when_idle` (Task 2).
4. **Only confirmed, unstamped records can be the target.** Pinned by `test_only_confirmed_unstamped_can_be_target` (Task 2).
5. **Frame rate on the Pi.** Per-pixel work is bounded by early-outs: canopy only in its band, notes only near their box, footprints by distance. If fps suffers, cut in the spec's order: canopy leaves, membrane streaks, footprints.

---

## File Structure

All under `ShowControl/FundingCAPTCHA/`:

| File | Responsibility |
|---|---|
| `shaders/hunter_bird/setup.json` | Channel bindings, `duration_s: 120` |
| `shaders/hunter_bird/common.glsl` | Constants, palette, record and state accessors, noise, glyph SDFs (seven-segment digits, `?`, tick), canopy layout |
| `shaders/hunter_bird/buffer_b.glsl` | Bird state (layout below) |
| `shaders/hunter_bird/image.glsl` | World, field notes, attention, eye |
| `shaders/setups.json` | Add `"hunter_bird"` |
| `test_hunter_bird.py` | GL behaviour tests |
| `docs/FundingCAPTCHA.md` | List `hunter_bird` among the Setups in rotation, linking the spec |

**Channel bindings (`setup.json`):**
```json
{
  "_comment": "Hunter bird: the blob tracker's notes drawn as a bird hunting visitors. Spec: docs/superpowers/specs/2026-11-04-hunter-bird-design.md",
  "duration_s": 120,
  "channels": {
    "buffer_b": ["B", "blobs"],
    "image":    ["A", "B", "blobs"]
  }
}
```
In Shadertoy, "blobs" is Buffer D running `blob_painter.glsl` (its channels: D, Keyboard).

**Buffer B layout** (texel coordinates `(x, y)`; `k` = slot 0–7; every texel not listed writes `vec4(0)`):

| Texel | `.x` | `.y` | `.z` | `.w` |
|---|---|---|---|---|
| `(k, 0)` SLOT | id (0 = none) | motion 0–1 | interest 0–1 | stamped 0/1 |
| `(k, 1)` PREV | x0 | y0 | x1 | y1 — this slot's box last frame (UV), for the size-change rate |
| `(k, 2)` HEAD | last print x | last print y | side 0/1 | seconds since last print |
| `(0, 3)` ATTN | target slot + 1 (0 = none) | lock 0–1 | seconds since strike | id struck last |
| `(1, 3)` RETICLE | x | y (screen UV) | radius (screen heights) | alpha |
| `(2, 3)` MOOD | lid openness | shiver 0–1 | wander anchor x | wander anchor y |
| `(3, 3)` BLINK | seconds since blink start (negative = scheduled) | idle countdown s | seconds everyone present has been stamped | — |
| `(4, 3)` STAMP | x | y (screen UV) | — | — |
| `(k·PRINTS + j, 4)` PRINT | x | y (Body UV) | age s | angle |

In the PRINT rows, `j = 0` is the newest print.

`PRINTS = 12`, so row 4 needs a buffer at least 96 texels wide. The Pi renders at 640×360; tests use 128×72.

Cross-texel reads see the previous frame (B reads itself). So:
- A strike decided in ATTN on frame N is applied to its SLOT on frame N+1.
- SLOT matches on **id**, not slot: `stamped = 1` when `ATTN.w == SLOT.id && ATTN.z < STRIKE_ACK_S`.
- Lock is 0 right after a strike, so no second strike can happen in between.

---

### Task 1: Skeleton, Common, per-slot state (motion, interest, id reset)

**Files:**
- Create: `shaders/hunter_bird/setup.json` (content above)
- Create: `shaders/hunter_bird/common.glsl`
- Create: `shaders/hunter_bird/buffer_b.glsl` (SLOT, PREV and HEAD rows; the other texels pass through 0 for now)
- Create: `shaders/hunter_bird/image.glsl` (stub: paper)
- Modify: `shaders/setups.json` → `["ripples", "endless_sunset", "hunter_bird"]`
- Create: `test_hunter_bird.py`

**Interfaces produced in `common.glsl`** (exact names; values are starting points from the mockup, and Task 7 tunes them):
```glsl
const int   SLOTS = 8, PRINTS = 12;
const float T_CLAMP = 99.0;              // every "seconds since" counter clamps here
// motion (per confirmed slot)
const float SPEED_FULL    = 0.39;        // screen heights/s of speed that alone reads as motion 1
const float SIZE_FULL     = 0.61;        // screen heights/s of (w + h) change that alone reads as motion 1
const float MOTION_FLOOR  = 0.15;        // subtracted: eased-box breathing and flicker live below this
const float MOTION_RISE_S = 0.15, MOTION_FALL_S = 0.3;
// interest, target, lock
const float MOTION_ON      = 0.2;        // above: interest rises; below: drains
const float INTEREST_GAIN  = 0.9;        // per second, × motion
const float INTEREST_DRAIN = 0.45;       // per second
const float TARGET_MIN     = 0.25, TARGET_SWITCH = 0.2, SWITCH_KEEP = 0.3;
const float LOCK_RATE      = 0.32;       // per second, × motion²
const float LOCK_DRAIN     = 0.3;
const float STRIKE_ACK_S   = 0.2;        // window in which a SLOT accepts the strike for its id
// reticle
const float RET_R_LOOSE = 58.0/360.0, RET_R_LOCKED = 20.0/360.0, RET_R_WANDER = 66.0/360.0;
const float RET_K_MIN = 3.0, RET_K_GAIN = 6.0, RET_K_WANDER = 1.2;   // spring rates, 1/s
const float WANDER_X = 90.0/360.0, WANDER_Y = 40.0/360.0, WANDER_RATE = 0.6;
// mood (lid openness 0–1) and blinks
const float LID_DROWSY = 0.42, LID_DROOP = 0.05, LID_SQUINT = 0.7, LID_WIDE = 0.96, LID_STRIKE = 1.0, LID_SMUG = 0.58;
const float LID_OPEN_RATE = 9.0, LID_CLOSE_RATE = 3.0;
const float STRIKE_WIDE_S = 0.9, STRIKE_SMUG_S = 3.2, ALL_STAMPED_DROWSY_S = 6.0;
const float BLINK_S = 0.32, BLINK_NEW_DELAY = 0.15, BLINK_STRIKE_DELAY = 2.3, IDLE_BLINK_MIN = 6.0, IDLE_BLINK_SPAN = 4.0;
// strike sequence
const float PUNCH_ZOOM = 0.38, PUNCH_RISE_S = 0.12, PUNCH_HOLD_S = 0.9, PUNCH_END_S = 1.7;
const float STAMP_SLAM_S = 0.12, STAMP_FADE_START_S = 2.6, STAMP_END_S = 3.2;
// footprints
const float PRINT_EVERY_S = 0.33, PRINT_MIN_SPEED = 25.0/360.0, PRINT_LIFE_S = 4.0;
// eye
const float IRIS_R_OPEN = 345.0/360.0, IRIS_R_LOCKED = 250.0/360.0, IRIS_R_STRIKE = 380.0/360.0, IRIS_BAND = 34.0/360.0;
// line weights
const float INK_W = 2.2/360.0, INK_W_HEAVY = 2.6/360.0, INK_W_LIGHT = 1.6/360.0;
```
Also in `common.glsl`:
- Palette: `const vec3 PAPER, INK, SLATE, DEEP, RUST, YELLOW, ORANGE, VIOLET, WARM_WHITE`.
- State: `const float S_EMPTY = 0., S_TENTATIVE = 1., S_CONFIRMED = 2., S_COASTING = 3., S_LOST = 4.`
- Record accessors: `vec4 recBox(sampler2D b, int k)`, `vec4 recMot(...)`, `vec4 recIdn(...)` (rows 0–2).
- State accessors: `vec4 bSlot(sampler2D s, int k)`, `bPrev`, `bHead`, `bAttn`, `bReticle`, `bMood`, `bBlink`, `bStamp`, `bPrint(s, k, j)`.
- `vec2 toScreen(vec2 uv)`: UV → screen-height units (`uv * iResolution.xy / iResolution.y`).

**SLOT rules (per frame):**
- If the record's id ≠ stored id, or the record state is empty: reset SLOT (id = record id, everything else 0), PREV = this box, and HEAD (`since = T_CLAMP`).
- Motion target:
  - only for confirmed records;
  - `raw = speed_h / SPEED_FULL + abs(d(w_h + h_h)/dt) / SIZE_FULL`, where `speed_h` is the record velocity in screen heights/s and `w_h`, `h_h` are box size in screen heights against PREV;
  - `target = clamp(raw - MOTION_FLOOR, 0, 1)`;
  - smoothed with the rise and fall time constants.
- Interest: `+= dt * INTEREST_GAIN * motion` when `motion > MOTION_ON`, else `-= dt * INTEREST_DRAIN`; clamp to 0–1. Held at 0 if stamped or not confirmed.
- Stamped: set when `ATTN.w == id && ATTN.z < STRIKE_ACK_S`, and kept until reset.
- Reset everything when `iFrame == 0`.

- [ ] **Step 1: Branch** (see Global Constraints), then check `git status` is clean.

- [ ] **Step 2: Write the test rig and the failing tests.** `test_hunter_bird.py`:

```python
"""Behaviour tests for the hunter_bird Setup (shaders/hunter_bird/)."""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
import pytest
from body_blobs import BlobConfig, BodyBlobs
from shadertoy import Renderer, load_setup, pack_body

SETUP = Path(__file__).parent / "shaders" / "hunter_bird"
SIZE  = (128, 72)                         # render; ≥ 96 wide for the PRINT row
BODY  = (64, 40)                          # camera ROI (w, h)
SLABS = [{"near_mm": 1000, "far_mm": 4000}]
DT    = 1 / 30
# The shipped defaults, except a smaller min_blob_pixels for the small test Body.
BLOBS = BlobConfig(min_blob_pixels=20)

# ctx fixture: copy test_shadertoy.py's module-scoped `ctx` fixture verbatim.

class Rig:
    """Renderer + the real BodyBlobs on a fake clock: camera at 10 Hz, render at 30 Hz."""
    def __init__(self, ctx):
        self.r = Renderer(ctx, SIZE, body_mode="camera"); self.r.load(load_setup(SETUP))
        self.blobs = BodyBlobs(BLOBS); self.t = 0.0

    def run(self, masks, frames_per_camera=3):
        for m in masks:                                   # one mask per camera frame, row 0 = top
            fg = np.where(m, 2000, 0).astype(np.uint16)
            body = pack_body(fg, {"x": 0, "y": 0, "w": BODY[0], "h": BODY[1]}, SLABS)
            self.r.upload_body(body)
            self.blobs.update(body[..., 0] > 0, body[..., 1] / 255.0, now=self.t)
            for _ in range(frames_per_camera):
                self.r.upload_blobs(self.blobs.records(now=self.t))
                self.r.render(DT, (0, 0, 0, 0)); self.t += DT

    def b(self) -> np.ndarray:
        """Buffer B as float32 (h, w, 4), row 0 = texel y 0."""
        t = self.r._buffers["buffer_b"].read_tex
        return np.frombuffer(t.read(), dtype=np.float16).astype(np.float32).reshape(t.size[1], t.size[0], 4)

    def slot(self, k): return self.b()[0, k]              # id, motion, interest, stamped
    def attn(self):    return self.b()[3, 0]              # target+1, lock, since strike, id struck
    def image(self):   return np.frombuffer(self.r.output.read(components=4), np.uint8).reshape(SIZE[1], SIZE[0], 4)

def rect(x0, y0, x1, y1):
    m = np.zeros(BODY[::-1], dtype=bool); m[y0:y1, x0:x1] = True; return m

def standing(n, x=36):  return [rect(x, 8, x + 10, 36)] * n
def walking(n, step=1):   # ~0.28 screen heights/s here: motion ≈ 0.57, so lock stays < 1 for 6 s at the defaults
    return [rect(6 + (k * step) % 40, 8, 16 + (k * step) % 40, 36) for k in range(n)]
def flailing(n):        # arms out and in: the box width swings by 12 px at ~2 Hz
    return [rect(30 - 6 * (k % 5 in (1, 2, 3)), 8, 40 + 6 * (k % 5 in (1, 2, 3)), 36) for k in range(n)]
def flickering(n, seed=0):
    """A still person whose 1-px border toggles randomly each camera frame."""
    rng = np.random.default_rng(seed); base = rect(36, 8, 46, 36); out = []
    for _ in range(n):
        m = base.copy(); edge = rect(35, 7, 47, 37) & ~rect(37, 9, 45, 35)
        m[edge] = rng.random(edge.sum()) < 0.5; out.append(m)
    return out
```

Task 1 tests:
```python
def test_slot_tracks_record_id(ctx):
    rig = Rig(ctx); rig.run(standing(8)); assert rig.slot(0)[0] == 1

def test_walking_has_motion(ctx):
    rig = Rig(ctx); rig.run(walking(20)); assert rig.slot(0)[1] > 0.3

def test_flickering_still_person_has_no_motion(ctx):     # Review Focus 1
    rig = Rig(ctx); rig.run(flickering(40)); assert rig.slot(0)[1] < 0.05

def test_interest_rises_with_motion_and_drains_still(ctx):
    rig = Rig(ctx); rig.run(walking(30)); hi = rig.slot(0)[2]
    rig.run([walking(31)[-1]] * 40); assert hi > 0.5 and rig.slot(0)[2] < hi - 0.5

def test_tentative_has_no_motion_or_interest(ctx):
    rig = Rig(ctx); rig.run(walking(2))                    # still tentative (min_confirm_frames 4)
    assert rig.slot(0)[1] == 0 and rig.slot(0)[2] == 0
```

- [ ] **Step 3: Run them to verify they fail**, then implement.
- [ ] **Step 4: Implement Task 1**, then run `python3 -m pytest test_hunter_bird.py test_shadertoy.py -v`. Expected: the new tests pass, including `test_listed_setups_compile[hunter_bird]`.
  - If the flicker test fails, raise `MOTION_FLOOR`; if the walking test fails, lower it.
  - Record the final value in the commit message.
- [ ] **Step 5: Commit** "Hunter bird Setup: skeleton and per-slot bird state".

---

### Task 2: Attention — target, lock, strike once per person, reticle, mood, blinks

**Files:** Modify `buffer_b.glsl` (the ATTN, RETICLE, MOOD, BLINK and STAMP texels) and `test_hunter_bird.py`.

**Rules** (all from the spec's Behaviour section):
- **Target** (ATTN.x):
  - Candidates are confirmed, unstamped slots with interest > `TARGET_MIN`.
  - Keep the current target unless it drops out or a rival beats it by `TARGET_SWITCH`.
  - On a switch, `lock *= SWITCH_KEEP`.
- **Lock:** `+= dt * LOCK_RATE * motion²` while the target's motion > `MOTION_ON`; otherwise `-= dt * LOCK_DRAIN`.
- **Strike** at lock ≥ 1:
  - `ATTN.z = 0`, `ATTN.w = target id`, lock = 0;
  - STAMP = the target's box centre (screen UV);
  - schedule a blink at `-BLINK_STRIKE_DELAY`.
  - STAMP then follows that id's box while its record lives.
- **Reticle:**
  - **With a target:** springs to `(box centre x, y1 − 0.3·height)` at `RET_K_MIN + RET_K_GAIN · interest`. Radius goes from `RET_R_LOOSE` to `RET_R_LOCKED` with lock. Alpha → 1.
  - **No target, someone unstamped present:** drifts around the wander anchor (set where the target was lost) by noise of `iTime · WANDER_RATE`, at `RET_K_WANDER`, alpha → 0.55.
  - **Otherwise:** alpha → 0.
- **Mood** (lids): follow the spec's table. Open at `LID_OPEN_RATE`, close at `LID_CLOSE_RATE`. "Everyone present is stamped" uses BLINK.z.
- **Shiver** (MOOD.y): → 1 when a new id appears; decays at about 1.5/s.
- **Blinks** (BLINK.x is seconds since the blink started, negative while scheduled):
  - `-BLINK_NEW_DELAY` when any record carries an id no SLOT holds yet;
  - `-BLINK_STRIKE_DELAY` on a strike;
  - idle when the countdown reaches 0, then reset the countdown to `IDLE_BLINK_MIN + IDLE_BLINK_SPAN · hash`.
- Clamp every counter at `T_CLAMP`.

Tests (two people are `rect(4, 8, 14, 36)` and `rect(48, 8, 58, 36)`, animated independently):
```python
def test_flailing_becomes_target_and_strikes(ctx):
    rig = Rig(ctx); rig.run(flailing(45))                  # 4.5 s
    a = rig.attn(); assert a[3] == 1                      # id 1 struck
    assert rig.slot(0)[3] == 1                            # stamped

def test_walking_alone_never_strikes(ctx):
    rig = Rig(ctx); rig.run(walking(60)); assert rig.attn()[3] == 0 and rig.attn()[1] < 1

def test_freezing_loses_the_bird(ctx):                     # Review Focus 1
    rig = Rig(ctx); rig.run(walking(30)); assert rig.attn()[0] == 1
    rig.run(flickering(40)); assert rig.attn()[0] == 0     # a flickering still person: target dropped

def test_strike_once_per_person(ctx):                      # Review Focus 2
    rig = Rig(ctx); rig.run(flailing(45)); rig.run(flailing(90))
    assert rig.attn()[0] == 0 and rig.slot(0)[2] == 0     # ignored after the stamp, despite flailing

def test_reused_slot_resets_stamp(ctx):                     # Review Focus 2
    rig = Rig(ctx); rig.run(flailing(45)); rig.run([np.zeros(BODY[::-1], bool)] * 30)   # leaves; lost; slot frees
    rig.run(flailing(45)); assert rig.slot(0)[0] == 2 and rig.slot(0)[3] == 1          # new id, stamped anew

def test_only_confirmed_unstamped_can_be_target(ctx):      # Review Focus 4
    # Flail for 2 frames only (tentative): no target. Then two people, one stamped: the other gets targeted.

def test_flailer_steals_target_from_walker(ctx):
    # The walker at the left becomes the target; then the right one flails: the target switches to its slot.

def test_mood(ctx):
    # Empty: lids ≈ LID_DROWSY. Walker targeted: > 0.9. Flickering still, no target: ≈ LID_SQUINT.

def test_state_stays_bounded_when_idle(ctx):               # Review Focus 3
    rig = Rig(ctx); rig.r.render(200.0, (0, 0, 0, 0))     # one huge dt
    rig.run([np.zeros(BODY[::-1], bool)] * 3)
    assert np.isfinite(rig.b()).all() and np.abs(rig.b()).max() <= 99.0
```
Write the three stubbed tests out in full. Each needs a two-person mask helper. The flailing timings depend on the defaults; if `test_flailing_becomes_target_and_strikes` needs more than ~4 s, raise `LOCK_RATE` rather than lengthening the test.

- [ ] Steps: write the tests → see them fail → implement → pass → commit "Hunter bird: attention, strike once per person, mood and blinks".

---

### Task 3: Footprints

**Files:** Modify `buffer_b.glsl` (the HEAD row and the PRINT row) and `common.glsl`.

- `bool emitsPrint(vec4 head, vec4 idn, vec4 mot, float dt)`: the record is confirmed, the speed in screen heights/s ≥ `PRINT_MIN_SPEED`, and `head.w + dt ≥ PRINT_EVERY_S`. HEAD and every PRINT texel of that slot evaluate the same function on the same inputs, so they agree.
- On emit:
  - HEAD = (box centre x, box y0, 1 − side, 0);
  - PRINT j = 0 is the new print (offset by side, angle `atan(vy, vx)`);
  - PRINT j > 0 takes j − 1's previous value.
- Otherwise, prints age by dt (clamp `T_CLAMP`).
- Prints persist across an id change and fade on their own.

Tests:
- `test_walking_leaves_prints`: after 3 s of walking, at least 6 prints with age < `PRINT_LIFE_S`.
- `test_standing_leaves_no_prints`.
- `test_prints_age_out`: after walking and then 5 s empty, every print age is ≥ `PRINT_LIFE_S`.

- [ ] Steps as before → commit "Hunter bird: footprints".

---

### Task 4: Image — world (paper, ground, people, canopy)

**Files:** Modify `image.glsl` and `common.glsl` (canopy layout, noise).

- Punch-in zoom:
  - `zoom = 1 + PUNCH_ZOOM · punch(ATTN.z)`, where `punch` rises over `PUNCH_RISE_S`, holds to `PUNCH_HOLD_S` and eases out by `PUNCH_END_S`;
  - world UV = `stamp + (uv − stamp) / zoom`, computed in screen-height units so it zooms evenly;
  - it applies to the world and the notes, never to the eye.
- **People:**
  - The Body's `.r` gives fill (warm white) and outline (ink). The outline is where `.r` at any of 8 taps at radius `INK_W_HEAVY` differs from the centre.
  - Hatching: slate diagonal lines inside the Body, in the lower 40% of the box of any non-empty slot containing the pixel. Spacing shrinks with Body `.g`.
- **Ground:** three or four wavy slate lines below ~0.17 screen heights from the bottom.
- **Canopy:**
  - Branches across the top corners and a perch at the bottom left.
  - About 20 leaves in the top band plus two or three per side near the top corners, as `const` arrays in `common.glsl`.
  - Leaf: a two-quadratic lens SDF with a midrib.
  - Sway: `0.07 · sin(iTime · 0.9 + i)` plus shiver.
  - Early-out: skip the leaf loop unless the pixel is in the top band, the corner columns or the perch box.

Tests (colour classes: `near(px, INK)` means within 40 per channel):
- `test_person_has_white_fill_and_ink_outline`: standing; the centre of the person ≈ warm white, the edge column ≈ ink.
- `test_hatching_only_in_lower_box`: standing; the lower-box interior contains slate pixels, the upper-box interior has none.
- `test_canopy_stays_in_its_band`: empty; the screen centre ≈ paper; the top row has ink somewhere.

The eye (Task 6) will later cover the screen edges. Pick world sample points that stay inside the lids at every openness ≥ 0.42, for example within 0.2 H of the screen centre. Check the canopy on the top row now, and accept that Task 6 may move that check inward.

- [ ] Steps as before → commit "Hunter bird: world".

---

### Task 5: Image — field notes and attention

**Files:** Modify `image.glsl` and `common.glsl` (glyph SDFs).

Per slot, early-out unless the pixel is within (box expanded by tag size + `RET_R_LOOSE`):

| State | Drawing |
|---|---|
| Tentative | dashed slate rectangle (dash ~4/5 px, crawling) and a small slate `?` above the top-right corner |
| Confirmed | ink corner brackets. Arm `clamp(0.22 · min(w, h), 10/360, 24/360)`, wobble ~1.2 px from noise. `INK_W_HEAVY` for the target, `INK_W_LIGHT` at 0.75 alpha for others |
| Coasting | dashed brackets, alpha `1 − age_s / COAST_FADE` (a constant, starting at 0.8 s, which matches the tracker's `max_miss_frames` at 10 fps), and an ink `?` |
| Lost | brackets fading from 0.4 s; zigzag scribble progressive over 0.25 s |

Then, per slot:
- **Tag:**
  - String from the top-right corner, swinging by `clamp(−vx · k, ±0.5) + small sine`.
  - Body 12 + 9n px wide by 17 px; yellow fill for the target, paper otherwise; ink outline and a hole.
  - Seven-segment digits of the id with ±0.5 px wobble.
  - A small rust tick on stamped slots.
- **Arrow:** deep blue, from the centroid along `vel · 0.35 s`, drawn when speed > 22/360 screen heights/s, with a chevron head.
- **Prints:** slate ovals (4.5 × 2.6 px) rotated by angle, alpha `0.85 · (1 − age / PRINT_LIFE_S)`. Loop over all `SLOTS · PRINTS`, early-out on distance.
- **Reticle:**
  - From RETICLE: a wobbly rust circle, four diagonal ticks, tremble `1.4 px · lock`.
  - Lock arc: `5 px` thick at `r + 7 px`, from 12 o'clock.
  - A rust `?` when there's no target.
- **Stamp** (while `ATTN.z < STAMP_END_S`):
  - Double ring (36 and 28 px), 12 dashes from 42 to 50 px, tick; rotated −0.22 rad; rust.
  - Scale from 2.4 to 1 over `STAMP_SLAM_S`; fade from `STAMP_FADE_START_S`.

Tests:
- `test_confirmed_box_has_ink_brackets`: an ink pixel near the box's top-left corner.
- `test_tentative_box_is_slate_and_dashed`: slate pixels and paper gaps along one edge.
- `test_target_tag_is_yellow`: a yellow pixel near the top-right corner.
- `test_stamp_appears_after_strike_then_clears`: rust at the stamp point shortly after the strike; none after `STAMP_END_S`.
- `test_reticle_hidden_when_empty`: no rust anywhere in an empty room.

- [ ] Steps as before → commit "Hunter bird: field notes, reticle and stamp".

---

### Task 6: Image — the eye (iris band, eyelids, membrane)

**Files:** Modify `image.glsl` and `common.glsl`.

**Screen-space**, after the world and notes, centred on the screen, in screen-height units:
- **Iris:**
  - Inner radius `Ri = mix(IRIS_R_OPEN, IRIS_R_LOCKED, smoothstep(0, 1, lock))`, blending to `IRIS_R_STRIKE` for `STRIKE_WIDE_S` after a strike.
  - Yellow annulus `[Ri, Ri + IRIS_BAND]` with ~110 short ink striations of hashed length, and ink edges (3 px inner, 2 px outer).
  - Beyond `Ri + IRIS_BAND`: paper with slate hatching at 0.55.
- **Lids:**
  - Profile `prof(x) = max(0, 1 − ((x − cx) / (0.76·W))²)` in pixels. Top rim `cy + 0.64·H·open·prof`, bottom rim `cy − 0.6·H·open·prof` (GL y up).
  - Paper with slate hatching; a yellow band 5 px wide, 4 px inside the rim; a 3 px ink rim; feather scallops (radius 9 px, every 22 px) 22 px beyond the rim.
- **Membrane:**
  - While `0 ≤ BLINK.x ≤ BLINK_S`: `u = BLINK.x / BLINK_S`, edge `x = −30 + sin(π·u)·(W + 90)` px plus slant and wave.
  - Fill warm paper at 0.82; seven slate streaks parallel to the edge; ink edge.

Tests:
- `test_lids_drowsy_when_empty`: in an empty room, a pixel 0.35 H above centre is lid (not paper-only: hatching present).
- `test_lids_open_on_target`: walking; the same pixel is in the world.
- `test_iris_band_narrows_view_on_lock`: a pixel at radius 0.8 H from centre is world at lock 0 and yellow or socket near full lock. Drive lock by flailing for ~1.5 s.

- [ ] Steps as before → commit "Hunter bird: the eye".

---

### Task 7: Look and feel, Shadertoy check, frame rate, docs

**Files:** `common.glsl` (constants only) and `docs/FundingCAPTCHA.md`.

- [ ] **Step 1: By eye with the mouse.** Run `python3 shader_app.py --test-input --windowed --setup hunter_bird`.
  - Walk the arc: empty (drowsy) → hold and drag (noticed, tagged) → hold still (lock drains, `?`) → shake the mouse hard (strike) → keep shaking (ignored: once per person) → release (coasting, lost).
  - Use **Space** to park a second person and **C** to clear.
  - Compare it with the mockup and tune constants only, using **R**.
- [ ] **Step 2: Mock camera.** Run `python3 shader_app.py --mock-camera --windowed --setup hunter_bird` for 2 minutes. Note the fps lines.
  - If the frame rate falls below the target on the Pi, cut in the spec's order: leaf count, membrane streaks, footprints.
- [ ] **Step 3: Shadertoy.**
  - Paste `body_painter.glsl` into A and `blob_painter.glsl` into D (channels: D, Keyboard).
  - Paste `common.glsl`, `buffer_b.glsl` (channels: B, D) and `image.glsl` (channels: A, B, D).
  - Confirm it compiles and behaves the same. If no browser is available, say so in the hand-off rather than claiming it was checked.
- [ ] **Step 4: Docs.** In `docs/FundingCAPTCHA.md` → "Shader player", add `hunter_bird` to "Setups in rotation" with a link to the spec.
- [ ] **Step 5: Full suite.** Run `make test` from the repo root. It must be all green.
- [ ] **Step 6: Commit** "Hunter bird: tuning pass and docs". The hand-off must state:
  - the constant values that changed;
  - the fps seen with `--mock-camera`, and on the Pi if it was run there;
  - that "freeze and it loses you" (the noise floor and `MOTION_ON`) has **not** been verified with the real Orbbec camera, unless it was. That check needs `--camera` on site: a visitor stands still for 5 s and must lose the reticle; one who flails must be stamped within ~3 s.
