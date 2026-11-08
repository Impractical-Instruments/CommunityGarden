"""Behaviour tests for the rainbow_poop Setup (shaders/rainbow_poop/).

Records come from the real BodyBlobs tracker run on synthetic masks with a
fake clock (camera 10 Hz, render 30 Hz), so record noise is realistic.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pytest

from body_blobs import BlobConfig, BodyBlobs
from shadertoy import Renderer, load_setup, pack_body

SETUP = Path(__file__).parent / "shaders" / "rainbow_poop"
SIZE  = (128, 72)                         # render; ≥ 64 wide for the SPLAT row
BODY  = (64, 40)                          # camera ROI (w, h)
SLABS = [{"near_mm": 1000, "far_mm": 4000}]
DT    = 1 / 30
BLOBS = BlobConfig(min_blob_pixels=20)    # the shipped defaults, but for the small test Body


def const(name: str) -> float:
    """A float constant from common.glsl, so tests follow retuning."""
    src = (SETUP / "common.glsl").read_text()
    m = re.search(rf"\b{name}\s*=\s*([0-9.]+)", src)
    assert m, name
    return float(m.group(1))


SPLAT_LIFE_S  = const("SPLAT_LIFE_S")
GROUND_LIFE_S = const("GROUND_LIFE_S")
FIRST_BOMB_S, FIRST_JITTER = const("FIRST_BOMB_S"), const("FIRST_JITTER")
BOMB_EVERY_S, BOMB_JITTER_S = const("BOMB_EVERY_S"), const("BOMB_JITTER_S")
DIVE_S = const("DIVE_S")


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


class Rig:
    """Renderer + the real BodyBlobs on a fake clock: camera at 10 Hz, render at 30 Hz."""

    def __init__(self, ctx, size=SIZE):
        self.size = size
        self.r = Renderer(ctx, size, body_mode="camera")
        self.r.load(load_setup(SETUP))
        self.blobs = BodyBlobs(BLOBS)
        self.t = 0.0
        self.hits: list[tuple[float, int]] = []          # (time, slot) of every new splat
        self.misses: list[float] = []                     # time of every new ground splat

    def run(self, masks, frames_per_camera=3, watch=True):
        for m in masks:                                   # one mask per camera frame, row 0 = top
            fg = np.where(m, 2000, 0).astype(np.uint16)
            body = pack_body(fg, {"x": 0, "y": 0, "w": BODY[0], "h": BODY[1]}, SLABS)
            self.r.upload_body(body)
            self.blobs.update(body[..., 0] > 0, body[..., 1] / 255.0, now=self.t)
            for _ in range(frames_per_camera):
                self.r.upload_blobs(self.blobs.records(now=self.t))
                self.r.render(DT, (0, 0, 0, 0))
                self.t += DT
                if watch:
                    self._watch()

    def _watch(self):
        b = self.b()
        for k in range(8):
            if b[7, k * 8, 2] == 0:                       # age 0: landed this frame
                self.hits.append((self.t, k))
        if b[8, 0, 2] == 0:
            self.misses.append(self.t)

    def b(self) -> np.ndarray:
        """Buffer B as float32 (h, w, 4), row 0 = texel y 0."""
        t = self.r._buffers["buffer_b"].read_tex
        return np.frombuffer(t.read(), dtype=np.float16).astype(np.float32).reshape(t.size[1], t.size[0], 4)

    def slot(self, k):    return self.b()[0, k]          # id, due s, presence
    def anchor(self, k):  return self.b()[1, k]           # top-centre x, y, height
    def bird(self, i):    return self.b()[2, i]           # x, y, vx, vy
    def plan(self, i):    return self.b()[3, i]           # mode, t, ±(slot+1), id
    def drop(self, i):    return self.b()[6, i]           # slot+1, floor, -, age
    def splats(self, k):  return self.b()[7, k * 8:(k + 1) * 8]   # x, y, age, seed
    def grounds(self):    return self.b()[8, :8]

    def live_splats(self, k):
        s = self.splats(k)
        return s[s[:, 2] < SPLAT_LIFE_S]

    def image(self) -> np.ndarray:
        """The Image as uint8 (h, w, 4), row 0 = bottom."""
        return np.frombuffer(self.r.output.read(components=4), np.uint8).reshape(self.size[1], self.size[0], 4)


def rect(x0, y0, x1, y1):
    m = np.zeros(BODY[::-1], dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


EMPTY = np.zeros(BODY[::-1], dtype=bool)


def standing(n, x=27):
    return [rect(x, 8, x + 10, 36)] * n


def flickering(n, x=27, seed=0):
    """A still person whose 1-px border toggles randomly each camera frame."""
    rng = np.random.default_rng(seed)
    base = rect(x, 8, x + 10, 36)
    edge = rect(x - 1, 7, x + 11, 37) & ~rect(x + 1, 9, x + 9, 35)
    out = []
    for _ in range(n):
        m = base.copy()
        m[edge] = rng.random(edge.sum()) < 0.5
        out.append(m)
    return out


# ── The flock ─────────────────────────────────────────────────────────────────

def test_empty_room_birds_circle_in_the_sky(ctx):
    rig = Rig(ctx)
    ys = []
    for _ in range(40):                                   # 12 s
        rig.run([EMPTY] * 3)
        ys += [rig.bird(i)[1] for i in range(4)]
    assert min(ys) > 0.6                                  # never come down
    assert all(rig.plan(i)[0] == 0 for i in range(4))
    assert not rig.hits and not rig.misses
    xs = [rig.bird(i)[0] for i in range(4)]
    assert max(xs) - min(xs) > 0.1                        # spread out, not one clump
    a = [rig.bird(i)[:2].copy() for i in range(4)]
    rig.run([EMPTY] * 5)
    assert all(np.linalg.norm(rig.bird(i)[:2] - a[i]) > 0.01 for i in range(4))   # moving


# ── Bombing a standing person ─────────────────────────────────────────────────

def test_standing_person_is_hit_soon_after_appearing(ctx):
    rig = Rig(ctx)
    rig.run(flickering(60))                               # 6 s
    assert rig.hits, "never hit"
    first = rig.hits[0]
    # confirmed after ~0.4 s, then the first countdown, the dive and the fall
    assert first[0] < 0.4 + FIRST_BOMB_S + FIRST_JITTER + DIVE_S + 0.8
    assert first[1] == 0 and not rig.misses


def test_splat_lands_on_the_head_in_the_persons_frame(ctx):
    rig = Rig(ctx)
    rig.run(flickering(60))
    s = rig.live_splats(0)
    assert len(s) >= 1
    x, y = s[0, 0], s[0, 1]
    half_w = 10 / 64 * (128 / 72) / 2 / (28 / 40)        # half the body width, in box heights
    assert abs(x) < half_w * 1.2                          # over the body
    assert -0.2 < y < 0.0                                 # just below the box top


def test_cadence_is_about_every_five_seconds(ctx):
    rig = Rig(ctx)
    rig.run(flickering(260))                              # 26 s
    t = [h[0] for h in rig.hits if h[1] == 0]
    assert len(t) >= 4, t
    gaps = np.diff(t)
    assert (gaps > BOMB_EVERY_S - BOMB_JITTER_S - 0.5).all(), gaps
    assert (gaps < BOMB_EVERY_S + BOMB_JITTER_S + 0.5).all(), gaps
    assert not rig.misses


def test_one_bird_per_person_at_a_time(ctx):
    rig = Rig(ctx)
    for _ in range(80):
        rig.run(flickering(1))
        diving = [rig.plan(i) for i in range(4) if rig.plan(i)[0] == 1]
        assert len(diving) <= 1


def test_two_people_both_get_hit(ctx):
    rig = Rig(ctx)
    two = [a | b for a, b in zip(flickering(80, x=8), flickering(80, x=46, seed=1))]
    rig.run(two)
    hit = {k for _, k in rig.hits}
    assert hit == {0, 1}


# ── Sticking, fading, leaving ─────────────────────────────────────────────────

def walk_from(x0, n, step=1):
    return [rect(x0 + k * step, 8, x0 + k * step + 10, 36) for k in range(n)]


def test_splats_follow_a_walker(ctx):
    rig = Rig(ctx)
    rig.run(standing(45, x=10))
    before = rig.live_splats(0).copy()
    assert len(before)
    a0 = rig.anchor(0).copy()
    rig.run(walk_from(10, 30) + standing(10, x=39), watch=False)
    assert rig.anchor(0)[0] - a0[0] > 0.4                 # the anchor moved with them …
    after = {round(float(s[3]), 4): s for s in rig.live_splats(0)}
    for s in before:                                      # … and splats stayed put in it
        np.testing.assert_allclose(after[round(float(s[3]), 4)][:2], s[:2], atol=1e-3)


def test_splats_fade_after_their_life(ctx):
    rig = Rig(ctx)
    rig.run(standing(45))
    first = rig.live_splats(0)
    assert len(first) == 1
    seed, age = first[0, 3], first[0, 2]
    rig.run(standing(int((SPLAT_LIFE_S - age) * 10) + 5))
    live = rig.live_splats(0)
    assert seed not in live[:, 3]                         # the first splat has gone …
    assert 2 <= len(live) <= 4                            # … the later ones are still there


def test_ages_keep_time_in_half_floats(ctx):               # f16 adds of 1/30 above 8 s drift ~6%
    rig = Rig(ctx)
    rig.run(standing(45))
    t0, age0 = rig.t, rig.live_splats(0)[-1, 2]
    rig.run(standing(150))                                # 15 s more
    oldest = rig.live_splats(0)[-1, 2]
    assert abs((oldest - age0) - (rig.t - t0)) < 0.1


def test_leaving_fades_then_clears(ctx):
    rig = Rig(ctx)
    rig.run(standing(45))
    assert rig.live_splats(0).size
    rig.run([EMPTY] * 9)                                  # coasting, then lost: presence falls
    assert rig.slot(0)[2] < 1.0
    rig.run([EMPTY] * 20)                                 # the slot empties
    assert rig.slot(0)[0] == 0 and rig.live_splats(0).size == 0


def test_new_person_in_a_reused_slot_starts_clean(ctx):
    rig = Rig(ctx)
    rig.run(standing(45))
    assert rig.live_splats(0).size
    rig.run([EMPTY] * 30)
    rig.run(standing(5))                                  # someone new
    assert rig.slot(0)[0] == 2 and rig.live_splats(0).size == 0


# ── Dodging ───────────────────────────────────────────────────────────────────

def dodge(rig):
    """Pace at 2 px per camera frame until a poop is falling, then turn round for 1.5 s."""
    x, v = 4, 2
    for _ in range(200):
        x += v
        if x > 46: v = -2
        if x < 4:  v = 2
        rig.run([rect(x, 8, x + 10, 36)])
        if any(rig.drop(i)[0] for i in range(4)):
            break
    else:
        pytest.fail("never released")
    v = -v
    for _ in range(15):
        x = int(np.clip(x + v, 0, 54))
        rig.run([rect(x, 8, x + 10, 36)])


def test_reversing_after_the_release_dodges(ctx):
    rig = Rig(ctx)
    dodge(rig)
    assert rig.misses and not rig.hits


def test_steady_walker_is_hit(ctx):
    rig = Rig(ctx)
    x, v = 4, 1
    for _ in range(120):
        x += v
        if x > 50 or x < 4:
            v = -v
        rig.run([rect(x, 8, x + 10, 36)])
    assert rig.hits


# ── The picture ───────────────────────────────────────────────────────────────

BIG = (320, 180)
PAPER = np.array((246, 241, 228))


def colourful(img) -> np.ndarray:
    """Saturated pixels: splat colours, not paper, ink or warm white."""
    px = img[..., :3].astype(int)
    return (px.max(axis=-1) - px.min(axis=-1)) > 90


def test_splats_drawn_only_on_the_silhouette(ctx):
    rig = Rig(ctx, BIG)
    rig.run(standing(60))
    assert rig.live_splats(0).size
    img = rig.image()
    sat = colourful(img)
    # The body rect(27, 8, 37, 36) in BIG pixels (row 0 = bottom); birds can be anywhere above it.
    c0, c1 = int(27 / 64 * BIG[0]), int(37 / 64 * BIG[0])
    r0, r1 = int((1 - 36 / 40) * BIG[1]), int((1 - 8 / 40) * BIG[1])
    on = sat[r0:r1, c0:c1].sum()
    assert on > 20
    beside = sat[r0:r1 - 30, c1 + 3:c1 + 40].sum() + sat[r0:r1 - 30, c0 - 40:c0 - 3].sum()
    assert beside == 0                                    # no splat colour off the body below the birds


def test_empty_room_is_paper_birds_and_clouds(ctx):
    rig = Rig(ctx, BIG)
    rig.run([EMPTY] * 10)
    img = rig.image()
    low = img[:int(BIG[1] * 0.5)]                         # the lower half is empty paper
    assert (np.abs(low[..., :3].astype(int) - PAPER).max(axis=-1) < 6).all()
    assert colourful(img[int(BIG[1] * 0.6):]).sum() > 20  # birds up there


def test_ground_puddle_is_drawn_at_the_feet(ctx):
    rig = Rig(ctx, BIG)
    dodge(rig)
    assert rig.misses
    g = rig.grounds()[0]
    r, c = int(g[1] * BIG[1]), int(g[0] * BIG[0])
    assert colourful(rig.image()[max(r - 8, 0):r + 8, max(c - 20, 0):c + 20]).sum() > 10


# ── Robustness ────────────────────────────────────────────────────────────────

def test_state_stays_bounded_with_huge_steps(ctx):
    rig = Rig(ctx)
    rig.run(standing(45))
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run(standing(3))
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run([EMPTY] * 3)
    b = rig.b()
    assert np.isfinite(b).all() and np.abs(b).max() <= 99.0
