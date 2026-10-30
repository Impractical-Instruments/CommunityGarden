# Endless Sunset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new shader player Setup, `endless_sunset`. It shows a line-drawn storybook sunset that zooms forever. The sunset smoulders when the room is empty, wakes up when someone stands in front of it, and squiggles and ripples when they flail.

**Architecture:** It's a Shadertoy-style Setup folder with four tabs:
- **Buffer B** is "Body memory": a per-pixel soft presence, a movement trail, and a ripple field.
- **Buffer C** is "State": one texel holds the smoothed awake level, the smoothed flail level, and an accumulated clock that changes speed with state.
- **Image** draws the sunset layers and the person from B and C.
- **Common** holds every tunable constant plus the shared helpers.

The tests drive the Setup headlessly with moderngl, using fake camera Bodies.

**Tech Stack:** GLSL (Shadertoy dialect, wrapped to GLSL 330 by `shadertoy.py`), Python 3 + pytest + moderngl + numpy for tests.

**Spec:** `docs/superpowers/specs/2026-10-30-endless-sunset-design.md`. The reference mockup is `docs/superpowers/specs/2026-10-30-endless-sunset-mockup.html`; it shows treatment **A, wiggly outline**. Read both before starting.

## Global Constraints

- Shader player rules (`ShowControl/FundingCAPTCHA/shaders/README.md`):
  - Read the Body (Buffer A) only with `texture()` and normalised UVs, never `texelFetch`.
  - Only `.r` (presence) and `.g` (nearness) of the Body mean anything.
  - Buffers are RGBA16F: keep stored values small (exact integers only up to ~2048) and store positions as UVs.
  - `HW_PERFORMANCE` is 0.
  - No textures, sound or video.
  - Filtering is always linear and clamped.
  - The Pi renders at half resolution.
- Every tab must paste unchanged into Shadertoy with `body_painter.glsl` in Buffer A.
- All thresholds and gains live as named constants at the top of `common.glsl`, so they can be tuned on site with **R** (reload).
- Size everything in units of `iResolution.y`. The mockup is 640×360, so a mockup value of N px becomes `N / 360.0` of the screen height.
- Palette (exact):
  - paper `#f6f1e4`
  - ink `#111111`
  - slate `#719aad`
  - deep blue `#2076a3`
  - rust `#bc4c26`
  - yellow `#fff200`
  - pale yellow `#fbe9a0`
  - warm white `#fffaf0`
  - orange `#e8862f`
  - pink `#e8957f`
  - violet `#6b5b95`
  - dim wash `#1d3550`
- Never write a show, artist or album name into any file. Never commit anything under `ShowControl/FundingCAPTCHA/images/private/`.
- Work on a new branch, `claude/endless-sunset`, off `claude/shader-player` (PR #156 is still open, so this stacks on it).
- Baseline: `test_compile_error_reports_tab_line` already fails locally with moderngl 5.13, because its error text has no driver log. It isn't this plan's concern, so don't fix it here. Every other test must stay green.
- Run tests from `ShowControl/FundingCAPTCHA/` with the repo venv: `../../.venv/bin/python -m pytest test_endless_sunset.py -v`.

## Review Focus

1. **A still person on a real depth camera.** Their mask edges flicker every camera frame (~10 fps, while the shader renders at ~30). They must stay "standing", not "flailing". This is pinned by `test_edge_flicker_is_not_flailing` (Task 1) and `test_standing_never_reaches_flail` (Task 2).
2. **One small, distant person.** A far-off visitor covers only ~1–2% of the frame and must still fully wake the scene. This is pinned by `test_small_far_person_fully_wakes` (Task 2).
3. **Hours of running.** The accumulated clock must not lose precision in a 16-bit buffer, and must never jump visibly when it wraps. This is pinned by `test_clock_stays_bounded_and_split` (Task 2) and `test_no_pop_across_clock_wrap` (Task 3).
4. **Camera frames arrive slower than render frames.** Between camera frames the Body is identical, so the measured movement is zero on two out of three frames. The flail level must not flicker at 10 Hz because of that. This is pinned by `test_flail_is_steady_between_camera_frames` (Task 2).
5. **A person standing right over the sun or the horizon.** The figure must draw on top of every sunset layer, as a white fill with an ink outline, wherever they stand. This is pinned by `test_person_draws_over_sun` (Task 4).

---

## File Structure

All under `ShowControl/FundingCAPTCHA/`:

| File | Responsibility |
|---|---|
| `shaders/endless_sunset/setup.json` | Channel bindings, `duration_s: 120` |
| `shaders/endless_sunset/common.glsl` | Every tunable constant, palette, clock helpers, layer phase/scale/alpha helpers, state-texel accessor |
| `shaders/endless_sunset/buffer_b.glsl` | Body memory, per pixel |
| `shaders/endless_sunset/buffer_c.glsl` | State, in texel (0,0) only |
| `shaders/endless_sunset/image.glsl` | Sunset layers, person, ripples, dimming |
| `shaders/setups.json` | Add `"endless_sunset"` |
| `test_endless_sunset.py` | GL behaviour tests for this Setup |

**Channel bindings (`setup.json`):**
```json
{
  "_comment": "Endless sunset: storybook sunset that zooms forever; visitors wake it, flailing squiggles them. Spec: docs/superpowers/specs/2026-10-30-endless-sunset-design.md",
  "duration_s": 120,
  "channels": {
    "buffer_b": ["A", "B"],
    "buffer_c": ["B", "C"],
    "image":    ["B", "C"]
  }
}
```
Passes render in the order B → C → Image. A pass that reads itself sees the previous frame; a pass that reads an earlier pass sees this frame.

**Buffer B texel layout (per pixel):**
- `.r`: soft presence, 0–1 (the Body's `.r` with a small blur, about 1.5 px at render resolution)
- `.g`: movement trail, 0–1, local, decaying
- `.b`: ripple field, 0–1, ≈ `exp(-distance_to_body / RIPPLE_FALLOFF)`; 1 inside a person
- `.a`: soft presence as of the last camera frame that changed it, used for the frame difference

**Buffer C texel (0,0) layout:**
- `.r`: awake, 0–1
- `.g`: flail, 0–1
- `.b`: clock whole seconds, an integer in [0, `LOOP_S`)
- `.a`: clock fractional seconds, in [0, 1)

Every other C texel writes `vec4(0)`.

---

### Task 1: Setup skeleton, Common, and Body memory (Buffer B)

**Files:**
- Create: `shaders/endless_sunset/setup.json` (content above)
- Create: `shaders/endless_sunset/common.glsl`
- Create: `shaders/endless_sunset/buffer_b.glsl`
- Create: `shaders/endless_sunset/buffer_c.glsl` (stub: `o = vec4(0.0);`, replaced in Task 2)
- Create: `shaders/endless_sunset/image.glsl` (stub: paper colour, replaced in Task 3)
- Modify: `shaders/setups.json` → `["ripples", "endless_sunset"]`
- Create: `test_endless_sunset.py`
- Also commit the spec and the mockup: `docs/superpowers/specs/2026-10-30-endless-sunset-design.md`, `docs/superpowers/specs/2026-10-30-endless-sunset-mockup.html`, and this plan.

**Interfaces:**
- Produces, in `common.glsl`:
  - The constants below, with these exact names. Values are the starting points; Task 5 tunes them.
    ```glsl
    const float LOOP_S          = 360.0;  // clock wraps here; every clock-driven motion must complete a whole number of cycles per LOOP_S
    const float N_LAYERS        = 6.0;
    const float T_RAYS          = 9.0;    // s per layer cycle at rate 1  (40 per loop)
    const float T_RINGS         = 11.25;  // s per layer cycle at rate 1  (32 per loop; mockup ran rings at 0.8x)
    const float LAYER_GROWTH    = 8.0;
    const float RATE_EMPTY      = 0.35;
    const float RATE_AWAKE      = 1.0;
    const float RATE_FLAIL_BONUS= 0.6;
    const float DIM_EMPTY       = 0.5;    // wash strength when empty
    const float AWAKE_COVERAGE  = 0.004;  // fraction of state samples present that counts as fully awake
    const float AWAKE_RISE_S    = 1.5;
    const float AWAKE_FALL_S    = 2.5;
    const float MOTION_FLOOR    = 0.35;   // per-pixel soft-presence change below this is camera noise
    const float MOTION_DECAY_S  = 0.6;    // trail half-life-ish (exp time constant)
    const float FLAIL_FULL      = 0.05;   // mean trail over samples that counts as full flail
    const float FLAIL_RISE_S    = 0.3;
    const float FLAIL_FALL_S    = 1.0;
    const float RIPPLE_FALLOFF  = 45.0 / 360.0;  // screen heights
    const float RIPPLE_AMP      = 22.0 / 360.0;
    const float RIPPLE_STANDING = 0.12;   // ripple strength when present but still
    const float WIGGLE_MIN      = 1.2 / 360.0;
    const float WIGGLE_MAX      = 7.0 / 360.0;
    const float INK_W           = 2.2 / 360.0;
    ```
  - Palette constants: `const vec3 PAPER, INK, SLATE, DEEP, RUST, YELLOW, PALE, WARM_WHITE, ORANGE, PINK, VIOLET, DIM_WASH`, with the hex values from Global Constraints converted to 0–1.
  - `float loopWave(float t, float cyclesPerLoop)`, which returns `6.2831853 * cyclesPerLoop * t / LOOP_S`. This is the only way clock-driven code may make a sine argument, so the wrap stays seamless.
  - `float layerPhase(float t, float periodS, float i)`, which returns `fract(t / periodS + i / N_LAYERS)`.
  - `float layerScale(float p)`, which returns `pow(LAYER_GROWTH, p)`.
  - `float layerAlpha(float p)`, which returns `pow(sin(3.14159265 * p), 2.0)`.
  - `vec4 readState(sampler2D stateBuf)`, which returns `texelFetch(stateBuf, ivec2(0), 0)`.
  - `float stateClock(vec4 s)`, which returns `s.b + s.a`.
- Produces: Buffer B's layout, as defined above.

- [ ] **Step 1: Create the branch.** Run `git switch -c claude/endless-sunset claude/shader-player`, then check that `git status` shows only the untracked FundingCAPTCHA images, the spec, the mockup and this plan.

- [ ] **Step 2: Write the failing tests.** Create `test_endless_sunset.py` with these shared helpers, plus the four tests after them.

```python
"""Behaviour tests for the endless_sunset Setup (shaders/endless_sunset/)."""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
import pytest
from shadertoy import Renderer, load_setup, pack_body

SETUP = Path(__file__).parent / "shaders" / "endless_sunset"
SIZE  = (96, 54)                         # render size
BODY  = (64, 40)                         # camera ROI size (w, h)
SLABS = [{"near_mm": 1000, "far_mm": 4000}]
DT    = 1 / 30

# ctx fixture: copy test_shadertoy.py's module-scoped `ctx` fixture verbatim.

def make(ctx) -> Renderer:
    r = Renderer(ctx, SIZE, body_mode="camera")
    r.load(load_setup(SETUP))
    return r

def body(mask: np.ndarray) -> np.ndarray:
    """mask: bool (h, w), row 0 = top. → packed Body."""
    fg = np.where(mask, 2000, 0).astype(np.uint16)
    return pack_body(fg, {"x": 0, "y": 0, "w": mask.shape[1], "h": mask.shape[0]}, SLABS)

def rect(x0, y0, x1, y1) -> np.ndarray:
    m = np.zeros(BODY[::-1], dtype=bool); m[y0:y1, x0:x1] = True; return m

def run(r, masks, frames_per_camera=3):
    """Upload each mask, then render frames_per_camera frames (camera 10 fps, render 30)."""
    for m in masks:
        r.upload_body(body(m))
        for _ in range(frames_per_camera):
            r.render(DT, (0, 0, 0, 0))

def buf(r, name) -> np.ndarray:
    """float32 (h, w, 4), row 0 = GL bottom."""
    t = r._buffers[name].read_tex
    return np.frombuffer(t.read(), dtype=np.float16).astype(np.float32).reshape(t.size[1], t.size[0], 4)

def image(r) -> np.ndarray:
    return np.frombuffer(r.output.read(components=4), dtype=np.uint8).reshape(SIZE[1], SIZE[0], 4)

def standing(n):          # same mask, n camera frames
    return [rect(36, 8, 48, 36)] * n

def walking(n, step=2):   # rect moves step px per camera frame, bouncing
    return [rect(10 + (k * step) % 30, 8, 22 + (k * step) % 30, 36) for k in range(n)]

def flickering(n, seed=0):  # still person whose 1-px border toggles randomly each camera frame
    rng = np.random.default_rng(seed); base = rect(36, 8, 48, 36); out = []
    for _ in range(n):
        m = base.copy(); edge = rect(35, 7, 49, 37) & ~rect(37, 9, 47, 35)
        m[edge] = rng.random(edge.sum()) < 0.5; out.append(m)
    return out
```

Tests (the Body maps onto the whole render, so Body x ∈ [36,48) out of 64 ↔ render x ∈ [54,72) out of 96):

```python
def test_soft_presence_follows_body(ctx):
    r = make(ctx); run(r, standing(5)); b = buf(r, "buffer_b")
    assert b[27, 63, 0] > 0.9            # inside the person
    assert b[27, 10, 0] < 0.05           # far outside

def test_ripple_field_decays_with_distance(ctx):
    r = make(ctx); run(r, standing(20)); f = buf(r, "buffer_b")[27, :, 2]
    assert f[63] > 0.9 and f[50] > f[40] > f[25] >= 0.0

def test_walking_leaves_movement_trail(ctx):
    r = make(ctx); run(r, walking(15)); assert buf(r, "buffer_b")[..., 1].max() > 0.5

def test_edge_flicker_is_not_flailing(ctx):
    r = make(ctx); run(r, flickering(30)); assert buf(r, "buffer_b")[..., 1].max() < 0.15
```

- [ ] **Step 3: Run the tests to verify they fail.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py -v`. Expected: they FAIL, either with `ShaderError` / `image.glsl missing` or on the assertions.

- [ ] **Step 4: Implement `setup.json`, `common.glsl`, the stub `buffer_c.glsl` / `image.glsl`, and `buffer_b.glsl`.**
  - Soft presence: average the Body's `.r` over a 3×3 tap at ±1 render px.
  - Movement: `motion = max(abs(soft - prev.a) - MOTION_FLOOR, 0.0) / (1.0 - MOTION_FLOOR)`.
    - `trail = max(prev.g * exp(-iTimeDelta / MOTION_DECAY_S), motion)`.
    - Store `.a = soft` only when `abs(soft - prev.a) > 0.01`, so `.a` holds the last frame that changed.
  - Ripple field: `field = max(soft, max over 8 directions of prev.b sampled at uv + dir * STEP) * exp(-STEP / RIPPLE_FALLOFF)`, with STEP = 4 render px expressed in screen-height units. This spreads it 4 px per frame.
  - Reset everything to 0 when `iFrame == 0`.
  - Add `"endless_sunset"` to `shaders/setups.json`.

- [ ] **Step 5: Run the tests to verify they pass.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py test_shadertoy.py -v`. Expected: the 4 new tests PASS, and so does `test_listed_setups_compile[endless_sunset]`. Only the known baseline test fails. If the flicker test fails, raise `MOTION_FLOOR`; if the walking test fails, lower it. Record the value you settle on.

- [ ] **Step 6: Commit.**
```bash
git add ShowControl/FundingCAPTCHA/shaders/endless_sunset ShowControl/FundingCAPTCHA/shaders/setups.json \
        ShowControl/FundingCAPTCHA/test_endless_sunset.py docs/superpowers/specs/2026-10-30-endless-sunset-* \
        docs/superpowers/plans/2026-10-30-endless-sunset.md
git commit -m "Endless sunset Setup: Body memory buffer (presence, movement trail, ripple field)"
```

---

### Task 2: State (Buffer C) — awake, flail, variable-speed clock

**Files:**
- Modify: `shaders/endless_sunset/buffer_c.glsl`
- Test: `test_endless_sunset.py`

**Interfaces:**
- Consumes: Buffer B's layout, plus `readState`, the constants, and `loopWave` from Task 1.
- Produces: the Buffer C texel (0,0) layout defined above. Image reads it through `readState(iChannel1)` and `stateClock(s)`.

- [ ] **Step 1: Write the failing tests.**

```python
def state(r) -> np.ndarray:
    return buf(r, "buffer_c")[0, 0]

def test_empty_room_sleeps(ctx):
    r = make(ctx); run(r, [rect(0, 0, 0, 0)] * 30); s = state(r)
    assert s[0] < 0.05 and s[1] < 0.05

def test_small_far_person_fully_wakes(ctx):
    r = make(ctx); run(r, [rect(30, 20, 33, 28)] * 40)   # ~1% of frame, 4 s
    assert state(r)[0] > 0.9

def test_standing_never_reaches_flail(ctx):
    r = make(ctx); run(r, flickering(60)); assert state(r)[1] < 0.2

def test_walking_flails(ctx):
    r = make(ctx); run(r, walking(30, step=3)); assert state(r)[1] > 0.6

def test_flail_is_steady_between_camera_frames(ctx):
    r = make(ctx); run(r, walking(20, step=3))
    vals = []
    for m in walking(6, step=3):
        r.upload_body(body(m))
        for _ in range(3):
            r.render(DT, (0, 0, 0, 0)); vals.append(state(r)[1])
    assert max(vals) - min(vals) < 0.15

def test_clock_runs_slower_when_empty(ctx):
    def advance(masks):
        r = make(ctx); run(r, masks[:30]); c0 = state(r)[2] + state(r)[3]   # 3 s to settle
        run(r, masks[30:]); return state(r)[2] + state(r)[3] - c0          # then measure 3 s
    empty, awake = advance([rect(0, 0, 0, 0)] * 60), advance(standing(60))
    assert empty == pytest.approx(3.0 * 0.35, rel=0.15)
    assert awake == pytest.approx(3.0 * 1.0, rel=0.15)

def test_clock_stays_bounded_and_split(ctx):
    r = make(ctx); r.upload_body(body(standing(1)[0]))
    for _ in range(3700): r.render(0.1, (0, 0, 0, 0))     # 370 s at rate 1 → wrapped once
    s = state(r)
    assert 0.0 <= s[2] < 360.0 and s[2] == round(s[2]) and 0.0 <= s[3] < 1.0
    assert s[2] < 20.0                                     # 370 mod 360 ≈ 10
```

- [ ] **Step 2: Run the tests to verify they fail.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py -v -k "sleeps or wakes or flail or clock"`. Expected: FAIL, because the stub writes zeros.

- [ ] **Step 3: Implement `buffer_c.glsl`.**
  - Only `ivec2(fragCoord) == ivec2(0)` does any work; every other texel outputs `vec4(0)`.
  - Sample Buffer B on a 32×18 grid of texel centres.
    - Coverage is the fraction of samples with `.r > 0.5`.
    - Movement is the mean of `.g`.
  - `awakeTarget = clamp(coverage / AWAKE_COVERAGE, 0, 1)`, and `flailTarget = clamp(movement / FLAIL_FULL, 0, 1) * awakeTarget`.
  - Ease each value toward its target with `1 - exp(-iTimeDelta / tau)`. Use the RISE time constant when rising and the FALL constant when falling.
  - Clock:
    - `rate = mix(RATE_EMPTY, RATE_AWAKE, awake) + RATE_FLAIL_BONUS * flail`.
    - `frac += iTimeDelta * rate`.
    - Carry whole seconds into `.b` with `floor`, and wrap `.b` with `mod(.b, LOOP_S)`.
  - When `iFrame == 0`, start from zero.
  - The movement trail already decays smoothly in B, so the flail level needs no extra handling between camera frames. If `test_flail_is_steady_between_camera_frames` fails, lengthen `MOTION_DECAY_S`.

- [ ] **Step 4: Run the tests to verify they pass.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py -v`. Expected: all of them PASS. Tune `FLAIL_FULL` and `AWAKE_COVERAGE` if a threshold test fails, and record the values you settle on.

- [ ] **Step 5: Commit.** `git commit -am "Endless sunset: state buffer (awake, flail, variable-speed wrapped clock)"`

---

### Task 3: Image — the endless sunset (no person yet)

**Files:**
- Modify: `shaders/endless_sunset/image.glsl`
- Test: `test_endless_sunset.py`

**Interfaces:**
- Consumes: `iChannel0` = Buffer B and `iChannel1` = Buffer C (via `readState`, `stateClock`), plus all the Common helpers.
- Produces: `vec3 sunset(vec2 p, float t, float ripple)` in `image.glsl`.
  - `p` is in screen-height units, with the origin at the sun centre on the horizon.
  - `t` is the clock.
  - `ripple` is a radial displacement in screen heights, which Task 4 supplies; pass 0 for now.

The layout is the mockup's, drawn per pixel. Work back to front:
1. Paper.
2. Rings. These are half-annuli above the horizon, so each layer is `r < R_i(θ)`:
   - Radius: `R_i = (56/360) * layerScale(p_i) * (1 + 0.05 * sin(9θ + loopWave(t, 74) + i))`, with `p_i = layerPhase(t, T_RINGS, i)`.
   - Colours in layer order: YELLOW, ORANGE, PINK, RUST, VIOLET, SLATE.
   - Fill alpha is `0.75 * layerAlpha`. The ink outline (`INK_W`) uses alpha `layerAlpha`.
   - Larger rings composite first.
3. Rays: 17 of them, at `θ_k = π(k + 0.5)/17`.
   - Layer `i` uses `p = layerPhase(t, T_RAYS, i + 0.5 * (k mod 2))`.
   - Each segment runs from `rA = (48/360) * layerScale(p)` to `1.35 rA`.
   - The perpendicular wiggle is `sin(r * 43.2 - loopWave(t, 172)) * (4/360 + 0.03 r)`.
   - Width is `(3 + 2p)/360`. Colour is WARM_WHITE when `(k+i) % 3 != 0`, otherwise PALE. There is no outline.
   - Alpha is `layerAlpha(p)`.
4. Sun: a YELLOW half-disc of radius 40/360 with an ink outline.
5. Horizon: an ink line at the screen height where `p.y = 0`, which is 0.34 of the screen height from the bottom.
6. Water below the horizon: 8 lines.
   - Line `j` sits at a depth of `(j² · 1.6 + 4)/360`.
   - Each line wiggles by `sin(x · 18 + loopWave(t, 115) + j) · 1.6/360`.
   - Colours alternate DEEP and INK.
   - An ORANGE reflection streak of half-width `(40/360)(1 - j/10)` sits at the sun's x, swaying by `sin(loopWave(t, 115) + j) · 4/360`.
7. Dimming: `col = mix(col, DIM_WASH, DIM_EMPTY * (1 - awake))`.

Antialias every edge with `smoothstep` over about one render pixel (`1.0 / iResolution.y`).

- [ ] **Step 1: Write the failing tests.**

```python
def px(img, x_frac, y_frac_from_bottom):
    return img[int(y_frac_from_bottom * (SIZE[1] - 1)), int(x_frac * (SIZE[0] - 1)), :3].astype(int)

def test_sun_and_paper_when_awake(ctx):
    r = make(ctx); run(r, [rect(0, 0, 3, 3)] * 40); img = image(r)
    assert np.abs(px(img, 0.5, 0.36) - [255, 242, 0]).max() < 40      # sun just above horizon
    assert img[..., :3].mean() > 120

def test_empty_room_is_dimmer(ctx):
    def mean(masks):
        r = make(ctx); run(r, masks); return image(r)[..., :3].mean()
    assert mean([rect(0, 0, 0, 0)] * 40) < 0.8 * mean([rect(0, 0, 3, 3)] * 40)

def test_no_pop_across_clock_wrap(ctx):
    r = make(ctx); r.upload_body(body(rect(0, 0, 3, 3)))
    prev, worst = None, 0.0
    for k in range(3700):                                    # 370 s at rate ~1, crosses LOOP_S
        r.render(0.1, (0, 0, 0, 0))
        if k > 3500:
            img = image(r)[..., :3].astype(float)
            if prev is not None: worst = max(worst, np.abs(img - prev).mean())
            prev = img
    assert worst < 12.0
```

(The tiny 3×3 body in the corner keeps the scene awake without overlapping the sun.)

- [ ] **Step 2: Run the tests to verify they fail.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py -v -k "sun or dimmer or pop"`. Expected: FAIL, because the stub paints flat paper.

- [ ] **Step 3: Implement `sunset()` and `mainImage` in `image.glsl`** as laid out above.

- [ ] **Step 4: Run the tests to verify they pass.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py -v`. Expected: PASS. Then compare against the mockup by eye: run `cd ShowControl/FundingCAPTCHA && ../../.venv/bin/python shader_app.py --test-input --windowed --setup endless_sunset` beside the mockup HTML in a browser. The rings, rays, sun, water and smoulder should match the mockup's look.

- [ ] **Step 5: Commit.** `git commit -am "Endless sunset: draw the endless rings, rays, sun and water"`

---

### Task 4: Image — person, squiggle outline, ripples

**Files:**
- Modify: `shaders/endless_sunset/image.glsl`
- Test: `test_endless_sunset.py`

**Interfaces:**
- Consumes: `sunset(p, t, ripple)` from Task 3, Buffer B's `.r .g .b`, and the state's flail and awake levels.
- Produces: the finished Image.

Approach:
1. **Ripples.**
   - `dist = -RIPPLE_FALLOFF * log(max(B.b, 1e-3))`.
   - `strength = awake * mix(RIPPLE_STANDING, 1.0, flail)`.
   - `ripple = strength * RIPPLE_AMP * B.b * sin(dist * 50.4 - iTime * 9.0)`. Here 50.4 is the mockup's 0.14/px expressed per screen height; `iTime` is fine because this term doesn't wrap.
   - Pass `ripple` into `sunset()`. It adds to the ring radius test, and to the ray's perpendicular wiggle at 1.3×.
2. **Person.** Find the signed distance to the soft-presence 0.5 contour: `d = (0.5 - soft) / max(length(grad soft), eps)`.
   - Measure the gradient with central differences on B at ±1 px, and convert `d` to screen heights.
   - Squiggle: `d += (WIGGLE_MIN + (WIGGLE_MAX - WIGGLE_MIN) * B.g) * sin(x * 32.4 + iTime * 9.0) * sin(y * 28.8 - iTime * 7.0)`, with x and y in screen heights (the mockup's 0.09 and 0.08 per px).
   - Where `d < -INK_W * 0.75`, fill with WARM_WHITE. Where `|d| < INK_W * 0.75`, draw INK. Antialias both.
   - Composite the person after `sunset()` and before dimming.

- [ ] **Step 1: Write the failing tests.**

```python
def test_person_draws_over_sun(ctx):
    r = make(ctx); run(r, [rect(26, 14, 38, 40)] * 30); img = image(r)   # covers the sun
    assert (np.abs(px(img, 0.5, 0.2) - [255, 250, 240]).max() < 20)      # warm-white body

def test_person_has_ink_outline(ctx):
    r = make(ctx); run(r, standing(30)); img = image(r)
    row = img[27, 40:90, :3].astype(int).sum(axis=1)
    assert row.min() < 150                                                # dark ink at the edge

def to_render(mask):
    """Body mask (row 0 = top) → render-space mask (row 0 = GL bottom), nearest neighbour."""
    ys = ((np.arange(SIZE[1]) + 0.5) * BODY[1] / SIZE[1]).astype(int)
    xs = ((np.arange(SIZE[0]) + 0.5) * BODY[0] / SIZE[0]).astype(int)
    return mask[::-1][ys][:, xs]

def grow(m, n):
    for _ in range(n):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m

def test_flailing_squiggles_the_outline(ctx):
    def ink_in_band(masks):
        r = make(ctx); run(r, masks); img = image(r)[..., :3].astype(int).sum(axis=2)
        m = to_render(masks[-1]); band = grow(m, 6) & ~grow(m, 2)   # 3–6 px outside the true edge
        return int(((img < 200) & band).sum())
    still = ink_in_band(standing(30))
    flail = ink_in_band(walking(30, step=3))
    assert flail > still + 10
```

The band also catches some sunset ink (ring outlines, the horizon), so the margin is deliberately small. If it's flaky, park both bodies over the same plain stretch of sky and compare there. The intent is that a squiggling outline wanders 3–6 px off the true edge, and a still one doesn't.

- [ ] **Step 2: Run the tests to verify they fail.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py -v -k "person or squiggle"`. Expected: FAIL.

- [ ] **Step 3: Implement the ripples and the person in `image.glsl`** as described in the approach above.

- [ ] **Step 4: Run the tests to verify they pass.** Run `../../.venv/bin/python -m pytest test_endless_sunset.py test_shadertoy.py -v`. Expected: everything passes except the known baseline test.

- [ ] **Step 5: Commit.** `git commit -am "Endless sunset: squiggly visitors and ripples around them"`

---

### Task 5: Look and feel pass, Shadertoy check, docs

**Files:**
- Modify (constants only): `shaders/endless_sunset/common.glsl`
- Modify: `docs/FundingCAPTCHA.md`, adding one line under "Shader player" that lists the Setups (`ripples`, `endless_sunset`) and links the spec.

- [ ] **Step 1: Check by eye in the player.**
  - Run `../../.venv/bin/python shader_app.py --test-input --windowed --setup endless_sunset`.
  - Go through the whole arc: empty smoulder → hold the mouse (standing) → drag fast (flailing) → release.
  - Compare it with the mockup. Tune only the `common.glsl` constants, using **R** to reload.
- [ ] **Step 2: Check it against the mock camera.**
  - Run `../../.venv/bin/python shader_app.py --mock-camera --windowed --setup endless_sunset` for 2 minutes.
  - Note the fps line that is logged every 10 s.
  - Drifting visitors should read as "standing", with light ripples and little squiggle.
- [ ] **Step 3: Check that it pastes into Shadertoy.**
  - Paste `body_painter.glsl` into Buffer A, then `common.glsl`, `buffer_b.glsl`, `buffer_c.glsl` and `image.glsl` into their tabs, with the channels from `setup.json` (B: A, B; C: B, C; Image: B, C).
  - Confirm it compiles and behaves the same. If no browser is available, say so in the hand-off rather than claiming it was checked.
- [ ] **Step 4: Run the full suite.** Run `make test` from the repo root. Expected: all pass except the known baseline test.
- [ ] **Step 5: Commit.** Run `git commit -am "Endless sunset: tuning pass and docs"`. The hand-off must state:
  - the final constant values that changed
  - the fps seen with `--mock-camera`
  - that the standing/flailing split has **not** been verified with the real Orbbec camera, unless it was.
