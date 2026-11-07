# Watercolor Smudge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two pieces of work:

- The shader player gains an `"image"` channel source that shuffles through a Setup's `images/` folder, one image per load.
- A new Setup, `watercolor_smudge`, shows a watercolor painting. Only the thin, moving parts of a visitor's silhouette smear the paint, and it heals about 10 s after the room empties.

**Architecture:**

- **Player.** `shadertoy.py` gains:
  - an `"image"` source;
  - `Setup.images`, the files in `<setup>/images/`;
  - `decode_image()`, using Pillow, with row 0 at the bottom, fitted to a maximum size;
  - an image texture that `Renderer.load(setup, image=...)` binds. When no image is bound, the source reads 0 and its `iChannelResolution` is 0.

  `shader_app.Rotation` keeps one `ShuffleBag` of image paths per Setup. It decodes the next image on every real load (including **R**) and skips files that won't decode.
- **Setup.** Four tabs, rendered in the player's order B → C → D → Image:
  - **B, "original"**: the painting to heal toward. If an image is bound, B samples it to cover the screen every frame. Otherwise B paints the procedural sunset once and then copies itself. `.a` = the smearable mask.
  - **C, "motion"**: `.r` = eased Body, `.g` = last frame's eased Body, `.b` = extremity weight (ring coverage of the raw Body). Texel (0,0) `.a` = seconds the room has been empty.
  - **D, "canvas"**: rgb = paint, `.a` = wetness. Each frame: normal-flow motion from C's `.r`/`.g`, weighted by `.b`, advects the paint. Pigment mixing and wetness are applied, then the canvas heals toward B.
  - **Image**: shows the bound image sampled directly where the canvas matches the original. Where it differs, it shows the canvas, with paper grain and wet darkening there.

**Tech Stack:** Python 3, moderngl, numpy, Pillow (already in `requirements.txt`), pytest; GLSL in the Shadertoy dialect, wrapped by `shadertoy.py`.

**Spec:** `docs/superpowers/specs/2026-11-07-watercolor-smudge-design.md`, plus the approved sketch `docs/superpowers/specs/2026-11-07-watercolor-smudge-mockup.html`. Read both before starting. The sketch's `PAINT`, `SIM` and `SHOW` shaders and its `extremity()` are the behaviour and look to port. Its slider defaults are the tunable defaults. Also read:

- `ShowControl/FundingCAPTCHA/shaders/README.md`
- `docs/adr/0021-fundingcaptcha-shader-player.md` and `docs/adr/0022-shader-player-blob-records.md` (0022 is the model for the new ADR)
- `shaders/watering_can/common.glsl`, the model for tunable constants and Body easing

## Global Constraints

- **Target machine:** an Intel Core Ultra 9 Linux PC, not the Pi. The player is unchanged otherwise: RGBA16F buffers, `HW_PERFORMANCE` 0, `render_scale` (default 0.5). Don't add a full-resolution output pass.
- **Shader player rules** (`shaders/README.md`):
  - Read the Body (Buffer A) with `texture()` and UVs.
  - Buffer state is 0–1 colour, or a bounded "seconds since" counter clamped at `T_CLAMP = 99.0`.
  - Use `iTimeDelta` for all timing; behaviour must not depend on render rate.
- **Tunables:** every strength, threshold, radius, rate and time is a named, commented constant at the top of `shaders/watercolor_smudge/common.glsl`. Defaults are copied from the spec's table:

  | Constant | Default |
  |---|---|
  | `SMEAR_STRENGTH` | 0.63 |
  | `THIN` | 0.5 (coverage threshold `mix(.18,.45,THIN)` ± 0.08) |
  | `RING_R1`, `RING_R2` | 0.045, 0.08 |
  | `STREAK_BASE`, `STREAK_AMP`, `STREAK_FREQ` | 0.7, 0.6, 45.0 |
  | `WET_DECAY` | 0.35 |
  | `HEAL_DELAY_S` | 2.0 |
  | `HEAL_TIME_S` | 10.0 (heal rate `3.0 / HEAL_TIME_S`) |
  | `PRESENT_HEAL` | 0.004 |

  Builder-chosen constants also go there: `BODY_EASE_S`, `MIN_FLOW`, `FLOW_EPS`, `FLOW_MAX`, `MIX_MOVE`, `MIX_WET`.
- **Units:** sizes are in screen heights. `q = uv * vec2(iResolution.x / iResolution.y, 1.0)`, as in the sketch.
- **Presence:** "anyone present" is `iMouse.z > 0.0`. The player sets it while anyone is in the Body (ADR-0021), and the body painter sets it while the mouse is held.
- **Never draw the person.** No silhouette, outline or ghost.
- **Shadertoy:** every tab must paste unchanged. Buffer A runs `body_painter.glsl`. Where `setup.json` says `"image"`, Shadertoy binds a built-in texture; the user accepts this.
- **Repo rules:**
  - Never write a show, artist or album name into any file.
  - Never commit anything under `ShowControl/FundingCAPTCHA/images/private/`.
  - Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Branch:** `claude/watercolor-smudge` (the spec is committed there).
- **Tests:**
  - Run from `ShowControl/FundingCAPTCHA/`.
  - `make test` from the repo root must stay green, except `test_compile_error_reports_tab_line` on NVIDIA drivers, which already fails and is unrelated.

## Review Focus

1. **A still person whose silhouette edge flickers.** Depth-edge noise toggles a rim of pixels while the person doesn't move, and the Body arrives at 10 Hz against a 30 fps render. Expected: the painting stays untouched. Pinned by `test_still_flickering_person_leaves_paint_alone` (Task 3).
2. **The room empties briefly, then someone returns before the heal finishes.** Expected: healing pauses back to the trickle rate, and the smears left stay put while they play. Pinned by `test_heal_waits_for_delay_and_pauses_on_return` (Task 3).
3. **An image whose aspect differs from the screen** (portrait art on a 16:9 screen). Expected: cover-fit, centred, not stretched, with no clamped edge smear. Pinned by `test_image_covers_screen_keeping_aspect` (Task 2).
4. **Every file in `images/` is corrupt, or the folder holds non-image files** such as `.DS_Store` or `README.md`. Expected: non-images are ignored. If nothing decodes, the Setup plays the procedural sunset and nothing crashes. Pinned by `test_rotation_with_only_corrupt_images_binds_nothing` and `test_load_setup_lists_images_sorted_ignoring_others` (Task 1).
5. **Hours of running.** The empty timer clamps and every buffer value stays finite. Pinned by `test_state_stays_bounded_when_idle` (Task 3).

---

### Task 1: Player — the `"image"` channel source

**Files:**
- Modify: `ShowControl/FundingCAPTCHA/shadertoy.py`:
  - `SOURCES`
  - `Setup`
  - `load_setup`
  - new `IMAGE_EXTS` and `decode_image`
  - `Renderer.load`, `_release_setup`, `_source_tex`, `release`
  - the module docstring
- Modify: `ShowControl/FundingCAPTCHA/shader_app.py`: `Rotation.__init__`, `Rotation._load`, and `main()` (pass `image_max`)
- Create: `docs/adr/0023-shader-player-image-channel.md`
- Modify: `docs/adr/0021-fundingcaptcha-shader-player.md`: add 0023 to its "Amended by" line
- Modify: `ShowControl/FundingCAPTCHA/shaders/README.md`
- Test: `ShowControl/FundingCAPTCHA/test_shadertoy.py`

**Interfaces:**
- Produces:
  - `IMAGE_EXTS = (".png", ".jpg", ".jpeg")`, matched case-insensitively.
  - `Setup.images: list[Path]`: a sorted list of the files in `<setup>/images/` with an `IMAGE_EXTS` suffix. It's `[]` if the folder is missing.
  - `Setup.uses_image -> bool`: true when any pass binds `"image"`.
  - `decode_image(path: Path, max_size: tuple[int, int]) -> np.ndarray`: uint8 `(h, w, 4)` RGBA, with row 0 at the image's bottom.
    - Downscales (Pillow `LANCZOS`, keeping aspect) only if it's wider than `max_size[0]` or taller than `max_size[1]`.
    - Raises `ShaderError` for anything that won't decode.
  - `Renderer.load(setup: Setup, image: np.ndarray | None = None) -> None`: binds `image` as an RGBA8 texture, `LINEAR` filtered and clamped. `_release_setup` releases it.
  - `_source_tex("image")` returns that texture, or `None` when there is none, so the channel reads 0 and its `iChannelResolution` is `(0,0,0)`.
  - `Rotation(..., image_max: tuple[int, int] = (4096, 4096))`.
    - `Rotation._load(name)` decodes the next image for Setups with `uses_image` and passes it to `renderer.load`. It keeps one `ShuffleBag` per Setup name, built from `setup.images` on first use.
    - A path that raises `ShaderError` is logged and permanently dropped from that Setup's bag. The next one is tried, at most `len(images)` attempts per load.
    - If nothing decodes, it loads with `image=None`.
  - `main()` passes `image_max=(min(win[0], max_tex), min(win[1], max_tex))`, where `max_tex = ctx.info["GL_MAX_TEXTURE_SIZE"]`.

- [ ] **Step 1: Write the failing pure tests** in `test_shadertoy.py`, in the "Setup loading" section. They use Pillow to write images, e.g. `Image.new("RGBA", (w, h), colour).save(path)`.

```python
def test_load_setup_lists_images_sorted_ignoring_others(tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": ["image"]}})
    (d / "images").mkdir()
    for n in ("b.JPG", "a.png", "c.jpeg", "notes.md", ".DS_Store"):
        (d / "images" / n).write_bytes(b"x")
    s = load_setup(d)
    assert [p.name for p in s.images] == ["a.png", "b.JPG", "c.jpeg"]
    assert s.uses_image

def test_load_setup_without_images_folder_has_no_images(tmp_path):
    s = load_setup(_write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": ["image"]}}))
    assert s.images == [] and s.uses_image

def test_decode_image_puts_bottom_row_first(tmp_path):
    # 1×2 PNG: top pixel red, bottom pixel blue
    ...
    a = decode_image(p, (64, 64))
    assert a.shape == (2, 1, 4) and a.dtype == np.uint8
    assert tuple(a[0, 0]) == (0, 0, 255, 255) and tuple(a[1, 0]) == (255, 0, 0, 255)

def test_decode_image_fits_inside_max_keeping_aspect(tmp_path):
    # 400×200 image, max (100, 100) → 100×50
    assert decode_image(p, (100, 100)).shape == (50, 100, 4)

def test_decode_image_corrupt_raises(tmp_path):
    (tmp_path / "bad.png").write_bytes(b"not a png")
    with pytest.raises(ShaderError):
        decode_image(tmp_path / "bad.png", (64, 64))
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m pytest test_shadertoy.py -k "images or decode_image" -v`
Expected: FAIL. The import error for `decode_image` comes first, then "unknown source(s) ['image']".

- [ ] **Step 3: Implement `IMAGE_EXTS`, `Setup.images`, `Setup.uses_image`, the `"image"` entry in `SOURCES`, the `load_setup` listing, and `decode_image`** in `shadertoy.py`, as in the Interfaces block. Import Pillow inside `decode_image`; it's already a dependency. Convert to `"RGBA"`, then flip with `np.flipud`.

- [ ] **Step 4: Run them to verify they pass**

Run: `python3 -m pytest test_shadertoy.py -k "images or decode_image" -v`
Expected: PASS.

- [ ] **Step 5: Write the failing GL and rotation tests** in `test_shadertoy.py`. Add them to the GL section; the rotation tests go next to `test_single_setup_is_not_recompiled_on_expiry`.

```python
SHOW_CH0 = ("void mainImage(out vec4 o, in vec2 f) {"
            " o = vec4(texture(iChannel0, f / iResolution.xy).rgb,"
            "          iChannelResolution[0].x > 0.0 ? 1.0 : 0.0); }")

def test_image_channel_reaches_shader(ctx, tmp_path):
    # Load with a 1×2 array (row 0 = bottom = blue, row 1 = red) bound to "image".
    # The top half of the output is red, the bottom half blue, alpha 255.

def test_unbound_image_reads_zero_resolution(ctx, tmp_path):
    # Load the same Setup with image=None: the pixel is (0, 0, 0, 0).

def test_rotation_shuffles_images_per_load(ctx, tmp_path):
    # One Setup whose images/ holds 3 solid PNGs (red, green, blue), image.glsl = SHOW_CH0.
    # rot.next(), then rot.reload() twice: the three rendered colours are all different.
    # A 4th load (reload) gives one of the three again.

def test_rotation_skips_corrupt_image(ctx, tmp_path):
    # images/ = bad.png (garbage bytes) + good.png (green). Over 4 loads every frame is green;
    # no exception escapes.

def test_rotation_with_only_corrupt_images_binds_nothing(ctx, tmp_path):
    # images/ = bad.png only. The Setup still loads; the pixel's alpha is 0 (no resolution).
```

The rotation tests build their Setup folder with `_write_setup` and pass `shader_dir=tmp_path`, `names=["s"]`.

- [ ] **Step 6: Run them to verify they fail**

Run: `python3 -m pytest test_shadertoy.py -k "image_channel or unbound_image or rotation_" -v`
Expected: the new tests FAIL (unexpected keyword `image`, or a blank channel). The existing `rotation_` tests still pass.

- [ ] **Step 7: Implement the texture binding in `Renderer`, the per-Setup bags in `Rotation`, and `image_max` in `main()`**, as in the Interfaces block. Upload with `ctx.texture((w, h), 4, data=arr.tobytes())` and set `repeat_x`/`repeat_y` to `False`. Release it in `_release_setup` and `release`.

- [ ] **Step 8: Run the whole file to verify it passes**

Run: `python3 -m pytest test_shadertoy.py -v`
Expected: all PASS (apart from the known NVIDIA-only failure).

- [ ] **Step 9: Write the docs**
  - **ADR-0023**, following ADR-0022's shape (Status Accepted, Amends ADR-0021, Context/Decision/Consequences). It records:
    - the `"image"` source, the `images/` folder and its extensions;
    - one shuffle bag per Setup per run, with only real loads (including **R**) advancing it, and a single pinned Setup keeping its image;
    - decoding: row 0 at the bottom, downscaled to fit the window or the GL max texture size, no mipmaps, linear and clamp;
    - corrupt files dropped from the bag; no images meaning an unbound channel with `iChannelResolution` 0 (not an error);
    - Shadertoy prototyping with a built-in texture.
  - Add 0023 to ADR-0021's "Amended by" line.
  - **`shaders/README.md`:**
    - Replace "No textures…" with a rule saying the one exception is the `"image"` source.
    - Add `"image"` to the "Sources:" list.
    - Add a short "Images" section: the folder, the shuffle, the no-image fallback test `iChannelResolution[n].x == 0.0`, Shadertoy stand-in textures, and the advice "fairly saturated images with clear colour regions smear more legibly than soft, low-contrast ones".
  - Update the `shadertoy.py` module docstring's "Channel sources:" line.

- [ ] **Step 10: Commit**

```bash
git add ShowControl/FundingCAPTCHA/shadertoy.py ShowControl/FundingCAPTCHA/shader_app.py \
        ShowControl/FundingCAPTCHA/test_shadertoy.py ShowControl/FundingCAPTCHA/shaders/README.md \
        docs/adr/0023-shader-player-image-channel.md docs/adr/0021-fundingcaptcha-shader-player.md
git commit -m "Shader player: \"image\" channel source, shuffled per load (ADR-0023, #164)"
```

---

### Task 2: Setup skeleton — original painting, canvas and display

**Files:**
- Create in `ShowControl/FundingCAPTCHA/shaders/watercolor_smudge/`: `setup.json`, `common.glsl`, `buffer_b.glsl`, `buffer_c.glsl` (pass-through stub for now), `buffer_d.glsl`, `image.glsl`
- Modify: `ShowControl/FundingCAPTCHA/shaders/setups.json` (append `"watercolor_smudge"`)
- Test: `ShowControl/FundingCAPTCHA/test_watercolor_smudge.py`

**Interfaces:**
- Consumes: Task 1's `Renderer.load(setup, image=...)`, `decode_image`, and the `"image"` source.
- Produces:
  - **`setup.json`:**

    ```json
    {"_comment": "Watercolor smudge: a watercolor painting that visitors' moving hands, feet and head smear; heals once the room empties. Spec: docs/superpowers/specs/2026-11-07-watercolor-smudge-design.md",
     "duration_s": 120,
     "channels": {"buffer_b": ["B", "image"], "buffer_c": ["A", "C"],
                  "buffer_d": ["D", "B", "C"], "image": ["D", "B", "image"]}}
    ```
  - **`common.glsl`:**
    - all the Global Constraints tunables;
    - `vec3 PAPER = vec3(.965,.94,.885)`;
    - the sketch's `hash`, `vn`, `fbm`, `lum`, `glaze`;
    - `vec3 paintSunset(vec2 uv, vec2 res)` and `float paintMask(vec2 uv, vec2 res)`, ported from the sketch's `PAINT`;
    - `vec2 coverUV(vec2 uv, vec2 screen, vec2 img)`: centred cover-fit, so uv in 0–1 maps inside the image with the overflow cropped.
  - **Buffer B, "original":**
    - With `iChannelResolution[1].x > 0`: `rgb = texture(iChannel1, coverUV(...))` and `a = 1.0`, every frame.
    - Otherwise: paint `paintSunset`/`paintMask` when `iFrame == 0`, or when its own centre texel is `vec3(0)` (a Shadertoy resize). Copy itself otherwise.
  - **Buffer D, "canvas":** for now, copies B when `iFrame == 0` or its centre texel is `vec3(0)`, and otherwise holds itself. Task 3 adds motion and heal.
  - **Image:**
    - `disturbed = smoothstep(0.01, 0.04, max-channel |canvas − original|)`, combined with wetness.
    - With an image bound: `mix(texture(image, coverUV), canvas, disturbed)`. Grain and wet darkening (sketch `SHOW`) are applied only through `disturbed`.
    - Procedural: the canvas with grain everywhere and wet darkening, as in the sketch.

- [ ] **Step 1: Write the failing tests** in a new `test_watercolor_smudge.py`. Copy the `ctx` fixture and `_pixel` helper pattern from `test_shadertoy.py` (import them is fine too). Add helpers:
  - `_rig(ctx, size=(96, 54), image=None) -> Renderer`: `body_mode="camera"`, loads `shaders/watercolor_smudge`, uploads an empty Body.
  - `_buf(r, name) -> np.ndarray`: float32 `(h, w, 4)`, read from `r._buffers[name].read_tex` as float16.
  - `_out(r) -> np.ndarray`: uint8 `(h, w, 4)`.

```python
def test_without_image_paints_procedural_sunset(ctx):
    r = _rig(ctx); [r.render(1/30, (0,0,-1,-1)) for _ in range(3)]
    o = _out(r).astype(int)
    top, low = o[48, 48, :3], o[10, 48, :3]           # GL rows: 48 near top, 10 in the water
    assert top[2] > top[0]                             # sky top is blue-violet
    assert o.std() > 10                                # not flat
    assert (o[1, 1, :3] > 200).all()                   # ragged paper border at the corner

def test_canvas_starts_equal_to_original(ctx):
    # After 2 frames, |buffer_d.rgb − buffer_b.rgb| max < 1/255.

def test_image_shows_unchanged_when_undisturbed(ctx):
    # A 96×54 image: left half red, right half blue. Output pixels at (20,27) and (76,27) match within 2/255.

def test_image_covers_screen_keeping_aspect(ctx):
    # A 54×96 portrait image (top third green, middle third red, bottom third blue) on a 96×54 render.
    # Cover-fit crops top and bottom: the output's centre row is red, and no output pixel is green or blue.
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m pytest test_watercolor_smudge.py -v`
Expected: FAIL (the Setup folder is missing).

- [ ] **Step 3: Implement the Setup files, as in the Interfaces block, and append it to `setups.json`.** Port `PAINT` from the mockup HTML verbatim apart from the dialect: `mainImage`, `iResolution`, and returning the mask separately. Buffer C is a stub that writes `vec4(0)` until Task 3.

- [ ] **Step 4: Run them to verify they pass, along with the listed-Setup compile test**

Run: `python3 -m pytest test_watercolor_smudge.py "test_shadertoy.py::test_listed_setups_compile" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ShowControl/FundingCAPTCHA/shaders/watercolor_smudge ShowControl/FundingCAPTCHA/shaders/setups.json \
        ShowControl/FundingCAPTCHA/test_watercolor_smudge.py
git commit -m "Watercolor smudge: Setup skeleton, procedural sunset and image cover (#164)"
```

---

### Task 3: Motion, extremity smear and heal

**Files:**
- Modify: `shaders/watercolor_smudge/common.glsl`, `buffer_c.glsl`, `buffer_d.glsl`
- Test: `ShowControl/FundingCAPTCHA/test_watercolor_smudge.py`

**Interfaces:**
- Consumes: Task 2's buffer roles and `setup.json` bindings.
- Produces:
  - **Buffer C:**
    - `.r` = the Body eased toward `texture(iChannel0).r` with rate `1 − exp(−dt / BODY_EASE_S)`;
    - `.g` = last frame's `.r`;
    - `.b` = `extremity(iChannel0, uv, aspect, THIN)` (sketch `extremity`, radii `RING_R1`/`RING_R2`, on the raw Body);
    - texel `(0,0)` `.a` = `min(T_CLAMP, prev + dt)` while `iMouse.z <= 0`, and 0 while present.
  - **Buffer D:** the sketch's `SIM`, minus the bleed and wet-edge darkening (already removed in the sketch's v2), reading flow from C's `.r`/`.g` instead of B/Bp:
    - The flow is zeroed below `MIN_FLOW`, clamped to `FLOW_MAX`, and weighted by C's `.b` and B's `.a` at the pixel and upstream.
    - Advection uses streaks, log-space mixing (`MIX_MOVE`, `MIX_WET`), and wetness decaying by `WET_DECAY`.
    - Heal toward B: rate `3.0 / HEAL_TIME_S` once the timer exceeds `HEAL_DELAY_S`, and `PRESENT_HEAL` otherwise.
  - **Test helper:** `_bar(w_frac, x_frac) -> np.ndarray`, a uint8 RGBA Body `(54, 96, 4)` with a full-height vertical bar of width `w_frac` (screen widths) centred at `x_frac`. The Body texture is uploaded at the render size in tests.

- [ ] **Step 1: Write the failing tests**

```python
def test_extremity_scores_thin_high_and_broad_low(ctx):
    # Body = thin bar (0.02 wide, x 0.3) plus broad bar (0.25 wide, x 0.7). After 3 frames, C.b
    # at the thin bar's centre is > 0.8, and at the broad bar's centre is < 0.2.

def test_moving_limb_smears(ctx):
    # A thin bar moves from x 0.2 to 0.6 over 1 s (Body uploaded every 3rd frame, 10 Hz), present.
    # The max |canvas − original| over the swept region is > 0.1.

def test_moving_torso_does_not_smear(ctx):
    # A broad bar (0.3 wide) makes the same move. The max |canvas − original| at the bar's swept interior
    # (excluding 0.05 at each side of the start and end positions) is < 0.03.

def test_still_flickering_person_leaves_paint_alone(ctx):
    # A thin bar at x 0.5, still. Every 3rd frame, a random 1-px rim is added or removed on either side
    # (seeded rng). After 3 s present, the max |canvas − original| is < 0.02.

def test_smear_persists_while_present(ctx):
    # After test_moving_limb_smears' sweep, 5 s more with the bar still and present.
    # The summed |canvas − original| is still > 90 % of what it was.

def test_heal_waits_for_delay_and_pauses_on_return(ctx):
    # Sweep, then empty Body and iMouse.z = −1. At 1.5 s, the diff is > 90 % of the start.
    # At 2 s + 10 s, it's < 5 %.
    # Variant: empty for 4 s, then present again (Body still), 3 s more → the diff drops by < 5 % in those 3 s.

def test_paper_border_never_smears(ctx):
    # Procedural; a thin bar sweeps from x 0.0 to 0.2. Texels whose B.a < 0.01 keep canvas == original
    # (< 1/255).

def test_state_stays_bounded_when_idle(ctx):
    # 4000 frames empty (dt 1/30). C(0,0).a == 99.0 (T_CLAMP); every buffer is finite; and
    # |canvas − original| < 1/255.
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m pytest test_watercolor_smudge.py -v`
Expected: the Task 3 tests FAIL (C is a stub, D only holds). Task 2's tests still pass.

- [ ] **Step 3: Implement Buffers C and D, and add the new tunables to `common.glsl`**, as in the Interfaces block. Choose `BODY_EASE_S` and `MIN_FLOW` so the flicker test passes while the moving-limb test still smears. Start with `BODY_EASE_S = 0.12` (as `watering_can`) and `MIN_FLOW = 0.05` screen heights/s. If easing alone isn't enough, add a hysteresis like `watering_can`'s `BODY_ON`/`BODY_OFF`.

- [ ] **Step 4: Run them to verify they pass**

Run: `python3 -m pytest test_watercolor_smudge.py -v`
Expected: PASS.

- [ ] **Step 5: Write the failing display tests**

```python
def test_image_stays_sharp_outside_smear(ctx):
    # With an image bound (a 4-px checkerboard), sweep a thin bar through x 0.2–0.4. The output at x 0.8
    # matches the image exactly (within 2/255), and some output in the swept region differs by > 0.1.

def test_wet_smear_reads_darker_than_dry(ctx):
    # Procedural. Right after the sweep, the mean luminance of the swept region's output is lower than
    # 4 s later (still present, so no heal).
```

- [ ] **Step 6: Run them; they should pass already if Task 2's Image pass is right**

Run: `python3 -m pytest test_watercolor_smudge.py -k "sharp or wet" -v`
Expected: PASS. If one fails, fix the Image pass's `disturbed` blend.

- [ ] **Step 7: Run the full suite**

Run (repo root): `make test`
Expected: green, apart from the known NVIDIA-only failure.

- [ ] **Step 8: Commit**

```bash
git add ShowControl/FundingCAPTCHA/shaders/watercolor_smudge ShowControl/FundingCAPTCHA/test_watercolor_smudge.py
git commit -m "Watercolor smudge: extremity smear from Body motion, heal after the room empties (#164)"
```

---

### Task 4: Look check in the player, then hand-off for the rig test

**Files:**
- Possibly modify: `shaders/watercolor_smudge/*.glsl` (look fixes only)

- [ ] **Step 1: Run it with the painter Body**

Run (from `ShowControl/FundingCAPTCHA/`): `python3 shader_app.py --test-input --setup watercolor_smudge --windowed`

Expected:
- The procedural sunset matches the sketch.
- Dragging with the held mouse (the painter's person) smears where its edges move.
- Releasing for 2 s, then waiting about 10 s, heals it.
- **R** reloads it.

Compare against the mockup open in a browser. Fix look differences in the GLSL, re-run `python3 -m pytest test_watercolor_smudge.py`, and commit if anything changed.

- [ ] **Step 2: Try an image**

Copy any PNG into `shaders/watercolor_smudge/images/`, re-run, and confirm it shows cover-fit and smears. **Delete it afterwards. Don't commit test art.**

- [ ] **Step 3: Hand off to the user** for the rig test on the Ultra 9 with the Orbbec (`python3 shader_app.py --camera --setup watercolor_smudge`). Report back:
  - a checklist: stand still for 30 s with no smear; walk through; wave; leave and watch the heal; note the `fps` log line;
  - which `common.glsl` constants to turn for each symptom:
    - too broad: lower `THIN` or the ring radii;
    - too little smear: raise `SMEAR_STRENGTH`;
    - a still person smearing: raise `BODY_EASE_S` or `MIN_FLOW`;
    - heal too slow or too fast: `HEAL_TIME_S`.

  **R** reloads edits live. Tuning changes from that session land on this branch. The merge waits for the user's sign-off.
