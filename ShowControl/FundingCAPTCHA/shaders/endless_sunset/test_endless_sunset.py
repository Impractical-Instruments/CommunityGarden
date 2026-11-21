"""What a visitor sees in the endless_sunset Setup (shaders/endless_sunset/).

The Setup's promises. Every test below checks one of them, and says which.

1. The scene: a big yellow sun low over the horizon, with water lines below it that stay on screen
   and clear of the horizon. An empty room dims and slows; anyone, however small or far, wakes it.
2. A person is filled with concentric lines that crawl, the sun showing between them, inside a dark
   cool outline. A small blob is tinted and see-through. Depth dropouts ink no holes and pop no
   lines, and someone who has just arrived fills fast.
3. Moving squiggles the outline. Standing still does not, camera flicker included, and the squiggle
   does not pulse with the camera's frames.
4. People stir the liquid background around them, less with distance. It stays calm under them.
5. The scene loops with no seam. It looks the same at any resolution, and the shortcuts taken away
   from people change nothing.

Tests assert the picture, or the scene's state read through the accessors below (wake, flail, clock,
ripple_field). None asserts how a buffer stores its state.

GL tests need a headless context and skip without one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shader_test_rig import BODY, DT, load_renderer, pack_frame, read_image, rect
from shadertoy import Renderer

SETUP = Path(__file__).parent
SIZE  = (96, 54)                         # render size


def make(ctx, size=SIZE) -> Renderer:
    return load_renderer(ctx, SETUP, size)


def run(r, masks, frames_per_camera=3):
    """Upload each mask, then render frames_per_camera frames (camera 10 fps, render 30)."""
    for m in masks:
        r.upload_body(pack_frame(m))
        for _ in range(frames_per_camera):
            r.render(DT, (0, 0, 0, 0))


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


# ── Reading the scene's state: the one place that knows the buffer layout (see common.glsl) ──

EMPTY = rect(0, 0, 0, 0)


def wake(r) -> float:
    """How awake the scene is: 0 asleep (empty room) … 1 awake."""
    return float(r.read_buffer("buffer_c")[0, 0, 0])


def flail(r) -> float:
    """How much the room is moving: 0 still … 1 flailing."""
    return float(r.read_buffer("buffer_c")[0, 0, 1])


def clock(r) -> float:
    """The scene clock, seconds."""
    s = r.read_buffer("buffer_c")[0, 0]
    return float(s[2] + s[3])


def ripple_field(r) -> np.ndarray:
    """Nearness to a person, (h, w): 1 on a body, falling to 0 away from it. Row 0 = bottom."""
    return r.read_buffer("buffer_b")[..., 2]


# ── Claim 1: an empty room sleeps, anyone wakes it (state) ────────────────────

def test_empty_room_sleeps(ctx):
    r = make(ctx)
    run(r, [EMPTY] * 30)
    assert wake(r) < 0.05 and flail(r) < 0.05


def test_small_far_person_fully_wakes(ctx):
    r = make(ctx)
    run(r, [rect(30, 20, 33, 28)] * 60)          # ~1% of frame, 6 s (rise ceiling 1 - e^-4 = 0.98)
    assert wake(r) > 0.9


def test_clock_runs_slower_when_empty(ctx):
    def advance(masks):
        r = make(ctx)
        run(r, masks[:30])                          # 3 s to settle
        c0 = clock(r)
        run(r, masks[30:])                          # then measure 3 s
        return clock(r) - c0
    empty, awake = advance([EMPTY] * 60), advance(standing(60))
    assert 0 < empty < 0.6 * awake, (empty, awake)


# ── Claim 3: moving flails, standing does not (state) ─────────────────────────

def test_standing_never_reaches_flail(ctx):
    r = make(ctx)
    run(r, flickering(60))
    assert flail(r) < 0.2


def test_walking_flails(ctx):
    r = make(ctx)
    run(r, walking(30, step=3))
    assert flail(r) > 0.6


def test_flail_is_steady_between_camera_frames(ctx):
    r = make(ctx)
    run(r, walking(20, step=3))
    vals = []
    for m in walking(6, step=3):
        r.upload_body(pack_frame(m))
        for _ in range(3):
            r.render(DT, (0, 0, 0, 0))
            vals.append(flail(r))
    assert max(vals) - min(vals) < 0.15


# ── Claim 1: the sunset (Image) ───────────────────────────────────────────────

CORNER = rect(0, 0, 6, 6)                           # keeps the scene awake, clear of the sun


def px(img, x_frac, y_frac_from_bottom):
    return img[int(y_frac_from_bottom * (SIZE[1] - 1)), int(x_frac * (SIZE[0] - 1)), :3].astype(int)


def test_empty_room_is_dimmer(ctx):
    def mean(masks):
        r = make(ctx)
        run(r, masks)
        return read_image(r)[..., :3].mean()
    assert mean([EMPTY] * 40) < 0.8 * mean([CORNER] * 40)


# ── Claims 2 and 3: the person's outline (Image) ──────────────────────────────

def to_render(mask, size):
    """Body mask (row 0 = top) → render-space mask (row 0 = GL bottom), nearest neighbour."""
    ys = ((np.arange(size[1]) + 0.5) * BODY[1] / size[1]).astype(int)
    xs = ((np.arange(size[0]) + 0.5) * BODY[0] / size[0]).astype(int)
    return mask[::-1][ys][:, xs]


def grow(m, n):
    for _ in range(n):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m


def test_outline_contrasts_with_the_scene_by_default(ctx, tmp_path):
    # The scene is pale and warm, so the outline is dark and cool (#173). The outline's pixels
    # are the ones that change when it's drawn in yellow instead; by default they must be navy.
    size = (384, 216)
    def render(r):
        run(r, [CORNER | standing(1)[0]] * 30)
        return read_image(r)[..., :3].astype(int)
    default = render(make(ctx, size))
    yellow  = render(make_with(ctx, tmp_path, size, OUTLINE_COL="YELLOW"))
    outline = np.abs(default - yellow).max(axis=2) > 100
    assert outline.sum() > 50
    px = default[outline]
    assert px.sum(axis=1).mean() < 300                      # dark: PAPER is 715, the old grey was 631
    assert (px[:, 2] - px[:, 0]).mean() > 25                # cool: bluer than it is red


def test_flailing_squiggles_the_outline(ctx, tmp_path):
    size = (384, 216)                               # big enough that the full squiggle is ~4 px
    def ink_in_band(masks):
        r = make_with(ctx, tmp_path, size, OUTLINE_COL="INK")   # ink, so the outline is easy to find
        run(r, masks)
        img = read_image(r)[..., :3].astype(int).sum(axis=2)
        m = to_render(masks[-1], size)
        band = grow(m, 5) & ~grow(m, 2)             # 3–5 px outside the true edge
        return int(((img < 200) & band).sum())
    jiggle = [0, 3, 6, 3, 0, -3, -6, -3]            # flailing in place, ends where standing() stands
    still = ink_in_band(standing(30))
    flail = ink_in_band([rect(36 + jiggle[k % 8], 8, 48 + jiggle[k % 8], 36) for k in range(32)])
    assert flail > still + 10


# ── Claims 1, 2, 4 and 5: specks, the liquid, the water, the loop (Image) ─────

def test_small_blob_is_tinted_and_see_through(ctx):
    # At Pi scale (960×540 render, 640×400 camera): a 3-texel speck vs the blob-size reach.
    size, cam = (960, 540), (400, 640)
    def render(with_speck):
        m = np.zeros(cam, dtype=bool)
        m[300:400, 0:60] = True                     # a person at the edge keeps the scene awake
        if with_speck:
            m[40:43, 560:563] = True                # camera-noise speck over the sky, far away
        r = make(ctx, size)
        r.upload_body(pack_frame(m))
        for _ in range(60):
            r.render(DT, (0, 0, 0, 0))
        return read_image(r)[..., :3].astype(int)
    a, b = render(True), render(False)
    c = (size[1] - 1 - int(41.5 * size[1] / cam[0]), int(561.5 * size[0] / cam[1]))
    assert np.abs(a[c] - b[c]).max() > 15                           # it shows up
    assert (a[c][0] - a[c][1]) > (b[c][0] - b[c][1]) + 8            # tinted pink
    assert np.abs(a[c] - [255, 250, 240]).max() > 20                # not a solid white person


def make_with(ctx, tmp_path, size=SIZE, **consts) -> Renderer:
    """This Setup with some common.glsl constants overridden, e.g. LIQUID_AMP="0.0", OUTLINE_COL="INK"."""
    import re
    import shutil
    d = tmp_path / "endless_sunset"
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(SETUP, d, ignore=shutil.ignore_patterns("test_*.py", "__pycache__"))
    c = d / "common.glsl"
    src = c.read_text()
    for k, v in consts.items():
        src, n = re.subn(rf"(const (?:float|vec3) {k}\s*=\s*)[^;]+;", rf"\g<1>{v};", src)
        assert n == 1, f"{k} not found in common.glsl"
    c.write_text(src)
    return load_renderer(ctx, d, size)


def test_people_stir_the_background(ctx, tmp_path):
    size = (384, 216)
    m = CORNER | rect(40, 4, 46, 24)                # standing in the sky, right of the sun
    def render(r):
        run(r, [m] * 30)
        return read_image(r)[..., :3].astype(float)
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
        return read_image(r)[..., :3].astype(float)
    stirred = render(make(ctx, size))
    still   = render(make_with(ctx, tmp_path, size, LIQUID_AMP="0.0"))
    inside  = ~grow(~to_render(rect(30, 6, 50, 38), size), 30)   # well inside the silhouette
    assert np.abs(stirred - still)[inside].max() < 6


def test_horizon_low_and_sun_big(ctx):
    r = make(ctx)
    run(r, [CORNER] * 60)
    img = read_image(r)
    yellow = lambda c: np.abs(c - [255, 242, 0]).max() < 40
    assert yellow(px(img, 0.5, 0.26))               # just above a horizon at 20%
    assert yellow(px(img, 0.5, 0.32))               # a sun of radius 60/360 reaches up to ~0.37
    assert not yellow(px(img, 0.5, 0.40))
    assert not yellow(px(img, 0.5, 0.15))           # below the horizon is water
    assert img[..., :3].mean() > 120                # awake: sun and paper, not the dim empty room


def test_outline_skips_tiny_holes(ctx, tmp_path):
    # At Pi scale (960×540 render, 640×400 camera), depth dropouts inside a person must not
    # get ink: the holey body's inside looks like a solid body's.
    size, cam = (960, 540), (400, 640)
    solid = np.zeros(cam, dtype=bool)
    solid[60:400, 250:400] = True
    rng = np.random.default_rng(2)
    def ink_inside(holes):
        r = make_with(ctx, tmp_path, size, OUTLINE_COL="INK")   # ink, so stray outline is easy to find
        for _ in range(30):
            m = solid & ~(rng.random(cam) < 0.08) if holes else solid
            r.upload_body(pack_frame(m))
            for _ in range(3):
                r.render(DT, (0, 0, 0, 0))
        dark = read_image(r)[..., :3].astype(int).sum(axis=2) < 200
        ys = ((np.arange(size[1]) + 0.5) * cam[0] / size[1]).astype(int)
        xs = ((np.arange(size[0]) + 0.5) * cam[1] / size[0]).astype(int)
        inside = ~grow(~solid[::-1][ys][:, xs], 12)
        return int(dark[inside].sum())
    assert ink_inside(holes=True) <= ink_inside(holes=False) + 5


def test_clock_wrap_is_seamless_everywhere(ctx, tmp_path):
    # Every clock-driven motion must complete whole cycles per LOOP_S: drawing the same frame
    # one full loop later (CLOCK_SHIFT = LOOP_S) must look identical.
    def frame(r):
        run(r, [CORNER] * 20)
        return read_image(r)[..., :3].astype(int)
    now   = frame(make(ctx))
    later = frame(make_with(ctx, tmp_path, CLOCK_SHIFT="360.0"))
    assert np.abs(now - later).max() <= 2


def test_water_lines_are_all_on_screen_and_clear_the_horizon(ctx, tmp_path):
    # Line spacing fits the water under a 20% horizon: the deepest (8th) line sits at ~90% of
    # the water depth (~2% up the screen) and the 7th at ~6%. Before, both fell off-screen.
    size = (960, 540)
    r = make_with(ctx, tmp_path, size, LIQUID_AMP="0.0", RIPPLE_AMP="0.0")
    run(r, [CORNER] * 40)
    img = read_image(r)[..., :3].astype(int)                               # row 0 = bottom
    dark = (img.sum(axis=2) < 450) | (np.abs(img - [32, 118, 163]).max(axis=2) < 40)
    line = dark[:, int(0.15 * size[0])]
    assert line[5:15].any()                         # 8th line
    assert line[26:36].any()                        # 7th line
    # Line 1's wiggle is scaled with the line spacing, so it never touches the horizon.
    horizon = int(round(0.20 * size[1]))
    for x in range(20, size[0], 7):
        if abs(x - size[0] // 2) < 120:             # skip the sun's reflection
            continue
        down = dark[horizon - 12: horizon + 2, x][::-1]  # from inside the horizon line, walking down
        run_ = int(np.argmin(down))                   # contiguous dark rows from the horizon down
        assert run_ <= 5, f"line 1 merges into the horizon at x={x} ({run_} dark rows)"


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
            r.upload_body(pack_frame(m))
            for _ in range(3):
                r.render(DT, (0, 0, 0, 0))
        return read_image(r)[..., :3].astype(int)
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
        r.upload_body(pack_frame(m))
        for _ in range(6):                          # 0.2 s: the front is still moving
            r.render(DT, (0, 0, 0, 0))
        row = ripple_field(r)[size[1] // 2]
        edge = int(340 * size[0] / cam[1]) + 2          # just right of the body
        return np.argmax(row[edge:] < 0.05) / size[1]   # how far the front got, in screen heights
    assert front((480, 270)) == pytest.approx(front((960, 540)), abs=0.02)


# ── Claim 2: concentric lines fill the person (Image) ─────────────────────────
# At Pi scale (960×540 render, 640×400 camera). A tall person covering the sun: inside the
# sun's disc the only things drawn are the sun (static, blue = 0) and the warm-white lines.

PI_SIZE, PI_CAM = (960, 540), (400, 640)
SUN_PERSON = (slice(40, 400), slice(190, 450))      # camera rows/cols: from above the sun to the floor


def pi_frames(n, holes=0.0, seed=3):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        m = np.zeros(PI_CAM, dtype=bool)
        m[SUN_PERSON] = True
        if holes:
            m &= ~(rng.random(PI_CAM) < holes)
        out.append(m)
    return out


def pi_run(r, masks, after=None):
    """Upload each camera mask, render 3 frames each; after(r) is called after every frame."""
    for m in masks:
        r.upload_body(pack_frame(m))
        for _ in range(3):
            r.render(DT, (0, 0, 0, 0))
            if after:
                after(r)


def sun_row(img, y_frac=0.28, channel=2):
    """One channel along a row through the sun, x within the sun's disc (blue: lines high, sun 0)."""
    y = int(y_frac * PI_SIZE[1])
    half = int(np.sqrt((60 / 360) ** 2 - (y_frac - 0.2) ** 2) * PI_SIZE[1]) - 8
    cx = PI_SIZE[0] // 2
    return img[y, cx - half:cx + half, channel].astype(int)


def runs(row, hi=180):
    """Start indices of bright runs along a row."""
    on = row > hi
    return np.flatnonzero(on[1:] & ~on[:-1]) + 1


def calm(ctx, tmp_path):
    return make_with(ctx, tmp_path, PI_SIZE, LIQUID_AMP="0.0", RIPPLE_AMP="0.0")


def test_person_is_filled_with_concentric_lines_that_crawl(ctx, tmp_path):
    # Replaces the old flat 80% warm-white fill: the sun now shows between the lines.
    r = calm(ctx, tmp_path)
    pi_run(r, pi_frames(40))
    img = read_image(r)
    row, red = sun_row(img), sun_row(img, channel=0)
    starts = runs(row)
    assert len(starts) >= 4, row                    # several lines …
    assert (row < 60).mean() > 0.3                  # … with the sun showing between them …
    assert (red[row < 60] > 200).all()              # … (yellow, not ink)
    gap = np.median(np.diff(starts)) / PI_SIZE[1]
    assert 7 / 360 < gap < 14 / 360                 # about 10/360 screen heights apart
    pi_run(r, pi_frames(5))                         # half a second later, body unchanged:
    assert np.abs(row - sun_row(read_image(r))).mean() > 20   # the lines have crawled


def test_concentric_lines_ignore_depth_dropouts(ctx, tmp_path):
    # 8% flickering holes must not ring the holes with lines or make the lines pop:
    # the holey person's lines match the solid person's.
    solid = calm(ctx, tmp_path)
    pi_run(solid, pi_frames(40))
    r = calm(ctx, tmp_path)
    pi_run(r, pi_frames(40, holes=0.08))
    a, b = sun_row(read_image(solid)), sun_row(read_image(r))
    assert (np.abs(a - b) > 90).mean() < 0.08
    assert abs(len(runs(a)) - len(runs(b))) <= 1
    # Nor do they tear between camera frames: rendering at 30 fps from a 10 fps camera, from one
    # render frame to the next the lines only crawl a little, even with flickering holes.
    rows = []
    pi_run(r, pi_frames(4, holes=0.08, seed=9), after=lambda r: rows.append(sun_row(read_image(r))))
    steps = [(np.abs(a - b) > 120).mean() for a, b in zip(rows, rows[1:])]
    assert max(steps) < 0.25, steps


def test_concentric_lines_fill_a_body_that_just_arrived(ctx, tmp_path):
    # Flailing arms land somewhere new every camera frame, and someone stepping in should
    # fill with lines fast: here 0.6 s fills a body ~200 render px deep (a fixed-step
    # distance field growing 4 px per frame would take ~1.6 s).
    corner = np.zeros(PI_CAM, dtype=bool)
    corner[340:400, 0:60] = True                    # someone else keeps the scene awake
    r = calm(ctx, tmp_path)
    pi_run(r, [corner] * 60 + [corner | m for m in pi_frames(6)])
    assert len(runs(sun_row(read_image(r)))) >= 4
