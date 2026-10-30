"""Behaviour tests for the endless_sunset Setup (shaders/endless_sunset/).

GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
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


@pytest.fixture(scope="module")
def ctx():
    moderngl = pytest.importorskip("moderngl")
    for kw in ({"backend": "egl"}, {}):
        try:
            c = moderngl.create_standalone_context(**kw)
            break
        except Exception:
            continue
    else:
        if os.environ.get("CI"):
            pytest.fail("no headless OpenGL context in CI — GL tests would silently skip")
        pytest.skip("no headless OpenGL context")
    yield c
    c.release()


def make(ctx, size=SIZE) -> Renderer:
    r = Renderer(ctx, size, body_mode="camera")
    r.load(load_setup(SETUP))
    return r


def body(mask: np.ndarray) -> np.ndarray:
    """mask: bool (h, w), row 0 = top → packed Body."""
    fg = np.where(mask, 2000, 0).astype(np.uint16)
    return pack_body(fg, {"x": 0, "y": 0, "w": mask.shape[1], "h": mask.shape[0]}, SLABS)


def rect(x0, y0, x1, y1) -> np.ndarray:
    m = np.zeros(BODY[::-1], dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


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
    return np.frombuffer(r.output.read(components=4), dtype=np.uint8).reshape(r.size[1], r.size[0], 4)


def standing(n):
    return [rect(36, 8, 48, 36)] * n


def walking(n, step=2):
    """Rect moves step px per camera frame, wrapping."""
    return [rect(10 + (k * step) % 30, 8, 22 + (k * step) % 30, 36) for k in range(n)]


def flickering(n, seed=0):
    """Still person whose 1-px border toggles randomly each camera frame."""
    rng  = np.random.default_rng(seed)
    base = rect(36, 8, 48, 36)
    edge = rect(35, 7, 49, 37) & ~rect(37, 9, 47, 35)
    out  = []
    for _ in range(n):
        m = base.copy()
        m[edge] = rng.random(edge.sum()) < 0.5
        out.append(m)
    return out


# ── Body memory (Buffer B) ────────────────────────────────────────────────────
# Body x ∈ [36,48) of 64 ↔ render x ∈ [54,72) of 96.

def test_soft_presence_follows_body(ctx):
    r = make(ctx)
    run(r, standing(5))
    b = buf(r, "buffer_b")
    assert b[27, 63, 0] > 0.9
    assert b[27, 10, 0] < 0.05


def test_ripple_field_decays_with_distance(ctx):
    r = make(ctx)
    run(r, standing(20))
    f = buf(r, "buffer_b")[27, :, 2]
    assert f[63] > 0.9 and f[50] > f[40] > f[25] >= 0.0


def test_walking_leaves_movement_trail(ctx):
    r = make(ctx)
    run(r, walking(15))
    assert buf(r, "buffer_b")[..., 1].max() > 0.5


def test_edge_flicker_is_not_flailing(ctx):
    r = make(ctx)
    run(r, flickering(30))
    assert buf(r, "buffer_b")[..., 1].max() < 0.15


# ── State (Buffer C) ──────────────────────────────────────────────────────────

EMPTY = rect(0, 0, 0, 0)


def state(r) -> np.ndarray:
    return buf(r, "buffer_c")[0, 0]


def test_empty_room_sleeps(ctx):
    r = make(ctx)
    run(r, [EMPTY] * 30)
    s = state(r)
    assert s[0] < 0.05 and s[1] < 0.05


def test_small_far_person_fully_wakes(ctx):
    r = make(ctx)
    run(r, [rect(30, 20, 33, 28)] * 60)          # ~1% of frame, 6 s (rise ceiling 1 - e^-4 = 0.98)
    assert state(r)[0] > 0.9


def test_standing_never_reaches_flail(ctx):
    r = make(ctx)
    run(r, flickering(60))
    assert state(r)[1] < 0.2


def test_walking_flails(ctx):
    r = make(ctx)
    run(r, walking(30, step=3))
    assert state(r)[1] > 0.6


def test_flail_is_steady_between_camera_frames(ctx):
    r = make(ctx)
    run(r, walking(20, step=3))
    vals = []
    for m in walking(6, step=3):
        r.upload_body(body(m))
        for _ in range(3):
            r.render(DT, (0, 0, 0, 0))
            vals.append(state(r)[1])
    assert max(vals) - min(vals) < 0.15


def test_clock_runs_slower_when_empty(ctx):
    def advance(masks):
        r = make(ctx)
        run(r, masks[:30])                          # 3 s to settle
        c0 = state(r)[2] + state(r)[3]
        run(r, masks[30:])                          # then measure 3 s
        return state(r)[2] + state(r)[3] - c0
    assert advance([EMPTY] * 60) == pytest.approx(3.0 * 0.35, rel=0.15)
    assert advance(standing(60)) == pytest.approx(3.0 * 1.0, rel=0.15)


def test_clock_stays_bounded_and_split(ctx):
    r = make(ctx)
    r.upload_body(body(standing(1)[0]))
    for _ in range(3700):                           # 370 s at rate ~1 → wrapped once
        r.render(0.1, (0, 0, 0, 0))
    s = state(r)
    assert 0.0 <= s[2] < 360.0 and s[2] == round(s[2]) and 0.0 <= s[3] < 1.0
    assert s[2] < 20.0


# ── Image: the sunset ─────────────────────────────────────────────────────────

CORNER = rect(0, 0, 6, 6)                           # keeps the scene awake, clear of the sun


def px(img, x_frac, y_frac_from_bottom):
    return img[int(y_frac_from_bottom * (SIZE[1] - 1)), int(x_frac * (SIZE[0] - 1)), :3].astype(int)


def test_sun_and_paper_when_awake(ctx):
    r = make(ctx)
    run(r, [CORNER] * 40)
    img = image(r)
    assert np.abs(px(img, 0.5, 0.30) - [255, 242, 0]).max() < 40
    assert img[..., :3].mean() > 120


def test_empty_room_is_dimmer(ctx):
    def mean(masks):
        r = make(ctx)
        run(r, masks)
        return image(r)[..., :3].mean()
    assert mean([EMPTY] * 40) < 0.8 * mean([CORNER] * 40)


def test_no_pop_across_clock_wrap(ctx):
    r = make(ctx)
    r.upload_body(body(CORNER))
    prev, at_wrap, elsewhere = None, [], []
    for k in range(3700):                           # 370 s at rate ~1, crosses LOOP_S
        r.render(0.1, (0, 0, 0, 0))
        if k > 3300:
            img = image(r)[..., :3].astype(float)
            clock = state(r)[2] + state(r)[3]
            if prev is not None:
                d = np.abs(img - prev).mean()
                (at_wrap if clock < 1.0 or clock > 359.0 else elsewhere).append(d)
            prev = img
    assert at_wrap, "never crossed the wrap"
    assert max(at_wrap) < 1.5 * np.median(elsewhere)   # a wrap frame looks like any other frame


# ── Image: the person ─────────────────────────────────────────────────────────

def to_render(mask, size):
    """Body mask (row 0 = top) → render-space mask (row 0 = GL bottom), nearest neighbour."""
    ys = ((np.arange(size[1]) + 0.5) * BODY[1] / size[1]).astype(int)
    xs = ((np.arange(size[0]) + 0.5) * BODY[0] / size[0]).astype(int)
    return mask[::-1][ys][:, xs]


def grow(m, n):
    for _ in range(n):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m


def test_person_draws_over_sun(ctx, tmp_path):
    r = make_with(ctx, tmp_path, LIQUID_AMP="0.0", RIPPLE_AMP="0.0")   # keep the sun put behind them
    run(r, [rect(26, 14, 38, 40)] * 80)             # covers the sun; 8 s so it's fully awake (no dim wash)
    c = px(image(r), 0.5, 0.30)                     # over the sun's disc
    assert np.abs(c[:2] - [255, 248]).max() < 15    # mostly warm white …
    assert 170 < c[2] < 215                         # … at 80%: the yellow sun shows through (white = 240, sun = 0)


def test_person_has_ink_outline(ctx):
    r = make(ctx)
    run(r, standing(30))
    row = image(r)[27, 40:90, :3].astype(int).sum(axis=1)
    assert row.min() < 150


def test_flailing_squiggles_the_outline(ctx):
    size = (384, 216)                               # big enough that the full squiggle is ~4 px
    def ink_in_band(masks):
        r = make(ctx, size)
        run(r, masks)
        img = image(r)[..., :3].astype(int).sum(axis=2)
        m = to_render(masks[-1], size)
        band = grow(m, 5) & ~grow(m, 2)             # 3–5 px outside the true edge
        return int(((img < 200) & band).sum())
    jiggle = [0, 3, 6, 3, 0, -3, -6, -3]            # flailing in place, ends where standing() stands
    still = ink_in_band(standing(30))
    flail = ink_in_band([rect(36 + jiggle[k % 8], 8, 48 + jiggle[k % 8], 36) for k in range(32)])
    assert flail > still + 10


# ── Image: blob size sets fill colour and transparency ────────────────────────

def test_small_blob_is_tinted_and_see_through(ctx):
    # At Pi scale (960×540 render, 640×400 camera): a 3-texel speck vs the blob-size reach.
    size, cam = (960, 540), (400, 640)
    def render(with_speck):
        m = np.zeros(cam, dtype=bool)
        m[300:400, 0:60] = True                     # a person at the edge keeps the scene awake
        if with_speck:
            m[40:43, 560:563] = True                # camera-noise speck over the sky, far away
        r = make(ctx, size)
        r.upload_body(pack_body(np.where(m, 2000, 0).astype(np.uint16),
                                {"x": 0, "y": 0, "w": cam[1], "h": cam[0]}, SLABS))
        for _ in range(60):
            r.render(DT, (0, 0, 0, 0))
        return image(r)[..., :3].astype(int)
    a, b = render(True), render(False)
    c = (size[1] - 1 - int(41.5 * size[1] / cam[0]), int(561.5 * size[0] / cam[1]))
    assert np.abs(a[c] - b[c]).max() > 15                           # it shows up
    assert (a[c][0] - a[c][1]) > (b[c][0] - b[c][1]) + 8            # tinted pink
    assert np.abs(a[c] - [255, 250, 240]).max() > 20                # not a solid white person


def make_with(ctx, tmp_path, size=SIZE, **consts) -> Renderer:
    """This Setup with some common.glsl constants overridden, e.g. LIQUID_AMP="0.0"."""
    import re
    import shutil
    d = tmp_path / "endless_sunset"
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(SETUP, d)
    c = d / "common.glsl"
    src = c.read_text()
    for k, v in consts.items():
        src, n = re.subn(rf"(const float {k}\s*=\s*)[^;]+;", rf"\g<1>{v};", src)
        assert n == 1, f"{k} not found in common.glsl"
    c.write_text(src)
    r = Renderer(ctx, size, body_mode="camera")
    r.load(load_setup(d))
    return r


def test_people_stir_the_background(ctx, tmp_path):
    size = (384, 216)
    m = CORNER | rect(40, 4, 46, 24)                # standing in the sky, right of the sun
    def render(r):
        run(r, [m] * 30)
        return image(r)[..., :3].astype(float)
    stirred = render(make(ctx, size))
    still   = render(make_with(ctx, tmp_path, size, LIQUID_AMP="0.0"))
    rm   = to_render(m, size)
    diff = np.abs(stirred - still)
    near = diff[grow(rm, 40) & ~grow(rm, 4)].mean()             # within ~1 falloff (42 px here)
    far  = diff[grow(rm, 126) & ~grow(rm, 80)].mean()           # 2–3 falloffs out
    assert near > 1.0                                           # the liquid around them moves
    assert near > 2.0 * far                                     # and fades with distance


def test_liquid_is_calm_under_people(ctx, tmp_path):
    # Seen through the 80% fill, a warped background tears; under a person it stays put.
    size = (384, 216)
    body_ = rect(30, 6, 50, 38)                     # a big person across the horizon and water
    rng = np.random.default_rng(1)
    frames = []
    for _ in range(30):                             # depth dropouts: small holes that flicker
        f = CORNER | body_
        f[body_ & (rng.random(body_.shape) < 0.08)] = False
        frames.append(f)
    def render(r):
        run(r, frames)
        return image(r)[..., :3].astype(float)
    stirred = render(make(ctx, size))
    still   = render(make_with(ctx, tmp_path, size, LIQUID_AMP="0.0"))
    inside  = ~grow(~to_render(rect(30, 6, 50, 38), size), 30)   # well inside the silhouette
    assert np.abs(stirred - still)[inside].max() < 6


def test_horizon_low_and_sun_big(ctx):
    r = make(ctx)
    run(r, [CORNER] * 60)
    img = image(r)
    yellow = lambda c: np.abs(c - [255, 242, 0]).max() < 40
    assert yellow(px(img, 0.5, 0.26))               # just above a horizon at 20%
    assert yellow(px(img, 0.5, 0.32))               # a sun of radius 60/360 reaches up to ~0.37
    assert not yellow(px(img, 0.5, 0.40))
    assert not yellow(px(img, 0.5, 0.15))           # below the horizon is water


def test_outline_skips_tiny_holes(ctx):
    # At Pi scale (960×540 render, 640×400 camera), depth dropouts inside a person must not
    # get ink: the holey body's inside looks like a solid body's.
    size, cam = (960, 540), (400, 640)
    solid = np.zeros(cam, dtype=bool)
    solid[60:400, 250:400] = True
    rng = np.random.default_rng(2)
    def ink_inside(holes):
        r = make(ctx, size)
        for _ in range(30):
            m = solid & ~(rng.random(cam) < 0.08) if holes else solid
            r.upload_body(pack_body(np.where(m, 2000, 0).astype(np.uint16),
                                    {"x": 0, "y": 0, "w": cam[1], "h": cam[0]}, SLABS))
            for _ in range(3):
                r.render(DT, (0, 0, 0, 0))
        dark = image(r)[..., :3].astype(int).sum(axis=2) < 200
        ys = ((np.arange(size[1]) + 0.5) * cam[0] / size[1]).astype(int)
        xs = ((np.arange(size[0]) + 0.5) * cam[1] / size[0]).astype(int)
        inside = ~grow(~solid[::-1][ys][:, xs], 12)
        return int(dark[inside].sum())
    assert ink_inside(holes=True) <= ink_inside(holes=False) + 5


def test_ripple_field_reaches_its_documented_falloff(ctx):
    # .b ≈ exp(-dist / RIPPLE_FALLOFF): one falloff out from the edge it should be ~e^-1.
    size, cam = (960, 540), (400, 640)
    m = np.zeros(cam, dtype=bool)
    m[100:400, 300:340] = True                      # a person; their right edge at camera x = 340
    r = make(ctx, size)
    r.upload_body(pack_body(np.where(m, 2000, 0).astype(np.uint16),
                            {"x": 0, "y": 0, "w": cam[1], "h": cam[0]}, SLABS))
    for _ in range(90):                             # 3 s: plenty to settle at 4 px per frame
        r.render(DT, (0, 0, 0, 0))
    row = buf(r, "buffer_b")[300, :, 2]             # GL row 300 crosses the body
    edge_px = int(340 * size[0] / cam[1])
    falloff_px = int(70 / 360 * size[1])            # RIPPLE_FALLOFF in render px
    assert 0.2 < row[edge_px + falloff_px] < 0.55
    assert 0.03 < row[edge_px + 2 * falloff_px] < 0.25


def test_clock_wrap_is_seamless_everywhere(ctx, tmp_path):
    # Every clock-driven motion must complete whole cycles per LOOP_S: drawing the same frame
    # one full loop later (CLOCK_SHIFT = LOOP_S) must look identical.
    def frame(r):
        run(r, [CORNER] * 20)
        return image(r)[..., :3].astype(int)
    now   = frame(make(ctx))
    later = frame(make_with(ctx, tmp_path, CLOCK_SHIFT="360.0"))
    assert np.abs(now - later).max() <= 2


def test_all_water_lines_are_on_screen(ctx, tmp_path):
    # Line spacing fits the water under a 20% horizon: the deepest (8th) line sits at ~90% of
    # the water depth (~2% up the screen) and the 7th at ~6%. Before, both fell off-screen.
    size = (960, 540)
    r = make_with(ctx, tmp_path, size, LIQUID_AMP="0.0", RIPPLE_AMP="0.0")
    run(r, [CORNER] * 40)
    col = image(r)[:, int(0.15 * size[0]), :3].astype(int)            # row 0 = bottom
    line = (col.sum(axis=1) < 450) | (np.abs(col - [32, 118, 163]).max(axis=1) < 40)
    assert line[5:15].any()                         # 8th line
    assert line[26:36].any()                        # 7th line


def test_skipping_work_away_from_people_changes_nothing(ctx, tmp_path):
    # The early-outs (person drawing, field disc) are for speed only: with them disabled the
    # picture must be the same — specks, outlines, flailing, ripples and stir included.
    size, cam = (480, 270), (400, 640)
    rng = np.random.default_rng(3)
    frames = []
    for k in range(30):
        m = np.zeros(cam, dtype=bool)
        x = 250 + 10 * (k % 5)
        m[80:400, x:x + 60] = True                  # a person shuffling side to side
        m[20:23, 560:563] = True                    # a lone speck
        m &= ~(rng.random(cam) < 0.05)
        frames.append(m)
    def render(r):
        for m in frames:
            r.upload_body(pack_body(np.where(m, 2000, 0).astype(np.uint16),
                                    {"x": 0, "y": 0, "w": cam[1], "h": cam[0]}, SLABS))
            for _ in range(3):
                r.render(DT, (0, 0, 0, 0))
        return image(r)[..., :3].astype(int)
    gated   = render(make(ctx, size))
    ungated = render(make_with(ctx, tmp_path, size, PERSON_GATE="-1.0", FIELD_GATE="-1.0"))
    # Excluding a 2 px border: there the disc's taps clamp to the screen edge, so a ~0 centre no
    # longer bounds them (a sub-pixel stir difference, invisible).
    assert np.abs(gated - ungated)[2:-2, 2:-2].max() <= 3


def test_field_spreads_at_the_same_speed_at_any_resolution(ctx):
    # The ripple field's spread is set in screen heights per second, not px per frame,
    # so a 1080p Shadertoy tab and the 540p Pi look the same.
    def front(size):
        cam = (400, 640)
        m = np.zeros(cam, dtype=bool)
        m[:, 300:340] = True
        r = make(ctx, size)
        r.upload_body(pack_body(np.where(m, 2000, 0).astype(np.uint16),
                                {"x": 0, "y": 0, "w": cam[1], "h": cam[0]}, SLABS))
        for _ in range(6):                          # 0.2 s: the front is still moving
            r.render(DT, (0, 0, 0, 0))
        row = buf(r, "buffer_b")[size[1] // 2, :, 2]
        edge = int(340 * size[0] / cam[1]) + 2          # just right of the body
        return np.argmax(row[edge:] < 0.05) / size[1]   # how far the front got, in screen heights
    assert front((480, 270)) == pytest.approx(front((960, 540)), abs=0.02)


def test_top_water_lines_clear_the_horizon(ctx, tmp_path):
    # Line 1's wiggle is scaled with the line spacing, so it never touches the horizon.
    size = (960, 540)
    r = make_with(ctx, tmp_path, size, LIQUID_AMP="0.0", RIPPLE_AMP="0.0")
    run(r, [CORNER] * 40)
    img = image(r)[..., :3].astype(int)
    dark = (img.sum(axis=2) < 450) | (np.abs(img - [32, 118, 163]).max(axis=2) < 40)
    horizon = int(round(0.20 * size[1]))
    for x in range(20, size[0], 7):
        if abs(x - size[0] // 2) < 120:             # skip the sun's reflection
            continue
        down = dark[horizon - 12: horizon + 2, x][::-1]  # from inside the horizon line, walking down
        run_ = int(np.argmin(down))                   # contiguous dark rows from the horizon down
        assert run_ <= 5, f"line 1 merges into the horizon at x={x} ({run_} dark rows)"
