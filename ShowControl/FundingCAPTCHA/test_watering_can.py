"""Behaviour tests for the watering_can Setup (shaders/watering_can/).

Records come from the real BodyBlobs tracker run on synthetic masks with a
fake clock (camera 10 Hz, render at DT), so record noise is realistic.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from body_blobs import BlobConfig, BodyBlobs
from shadertoy import Renderer, load_setup, pack_body

SETUP = Path(__file__).parent / "shaders" / "watering_can"
SIZE  = (128, 72)                         # render
BODY  = (64, 48)                          # camera ROI (w, h)
SLABS = [{"near_mm": 1000, "far_mm": 4000}]
DT    = 1 / 30
LEAVE_S = 2.0                              # shaders/watering_can/common.glsl
BLOBS = BlobConfig(min_blob_pixels=20)    # the shipped defaults, but for the small test Body


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
    """Renderer + the real BodyBlobs on a fake clock: camera at 10 Hz, render at `dt`."""

    def __init__(self, ctx, size=SIZE, dt=DT, slot=0):
        self.size, self.dt, self.slot = size, dt, slot   # slot: move the tracker's records there (owner = slot + 1)
        self.r = Renderer(ctx, size, body_mode="camera")
        self.r.load(load_setup(SETUP))
        self.blobs = BodyBlobs(BLOBS)
        self.t = 0.0

    def run(self, masks, frames_per_camera=3):
        for m in masks:                                   # one mask per camera frame, row 0 = top
            fg = np.where(m, 2000, 0).astype(np.uint16)
            body = pack_body(fg, {"x": 0, "y": 0, "w": BODY[0], "h": BODY[1]}, SLABS)
            self.r.upload_body(body)
            self.blobs.update(body[..., 0] > 0, body[..., 1] / 255.0, now=self.t)
            for _ in range(frames_per_camera):
                self.r.upload_blobs(np.roll(self.blobs.records(now=self.t), self.slot, axis=1))
                self.r.render(self.dt, (0, 0, 0, 0))
                self.t += self.dt

    def buf(self, name) -> np.ndarray:
        """A buffer as float32 (h, w, 4), row 0 = the GL bottom."""
        t = self.r._buffers[name].read_tex
        return np.frombuffer(t.read(), dtype=np.float16).astype(np.float32).reshape(t.size[1], t.size[0], 4)

    def person(self, k): return self.buf("buffer_c")[0, k]   # id, growth, spot x, y
    def base(self, k):   return self.buf("buffer_c")[1, k]   # base x, y, since step
    def ghost(self, k):  return self.buf("buffer_c")[2, k]   # spot x, y, growth, since loss
    def sun(self):       return self.buf("buffer_c")[3, 0]   # level, raw total

    def image(self) -> np.ndarray:
        """The Image as uint8 (h, w, 4), row 0 = bottom."""
        return np.frombuffer(self.r.output.read(components=4), np.uint8).reshape(self.size[1], self.size[0], 4)

    def release(self):
        self.r.release()


def rect(x0, y0, x1, y1):
    m = np.zeros(BODY[::-1], dtype=bool)
    m[max(y0, 0):y1, max(x0, 0):x1] = True
    return m


EMPTY = np.zeros(BODY[::-1], dtype=bool)


def person(x=26, feet=44, arm="down", lift=None):
    """A figure 12 px wide, head to feet. x is its left edge; feet is the row below its feet.
    arm: "down" (hanging at the sides), "out" (right arm horizontal), "up" (right arm overhead).
    lift: "L" or "R" raises that foot 2 px (a weight shift)."""
    top = feet - 38
    m = rect(x + 4, top, x + 8, top + 6)                       # head
    m |= rect(x + 2, top + 6, x + 10, top + 20)                # torso (shoulder top = top + 6)
    m |= rect(x + 2, top + 20, x + 6, feet - (2 if lift == "L" else 0))     # left leg
    m |= rect(x + 6, top + 20, x + 10, feet - (2 if lift == "R" else 0))    # right leg
    m |= rect(x, top + 7, x + 3, top + 22)                     # left arm, hanging
    if arm == "down":
        m |= rect(x + 9, top + 7, x + 12, top + 22)
    elif arm == "out":
        m |= rect(x + 9, top + 7, x + 24, top + 10)
    elif arm == "up":
        m |= rect(x + 9, top - 6, x + 12, top + 7)
    return m


def flickering(n, seed=0, **kw):
    """person(**kw) with its 1-px border toggled randomly, plus 3 random 1-px dropout holes inside, each camera frame."""
    rng = np.random.default_rng(seed)
    base = person(**kw)

    def grow(m):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        return g

    def shrink(m):
        return ~grow(~m)

    edge = grow(base) & ~shrink(base)
    inner = np.argwhere(shrink(base))
    out = []
    for _ in range(n):
        m = base.copy()
        m[edge] = rng.random(edge.sum()) < 0.5
        for y, x in inner[rng.integers(0, len(inner), 3)]:
            m[y, x] = False
        out.append(m)
    return out


def walking(n, step=1, x=26, bounce=(4, 48), **kw):
    """A person starting at x, moving sideways `step` px per camera frame, bouncing within `bounce`."""
    out, d = [], 1
    for _ in range(n):
        out.append(person(x=x, **kw))
        if not bounce[0] <= x + d * step <= bounce[1]:
            d = -d
        x += d * step
    return out


def stepping_toward(n, **kw):
    """Feet row increases 1 px per camera frame from 36 to 47 (moving down the image)."""
    return [person(feet=min(36 + k, 47), **kw) for k in range(n)]


def owner(texel):
    return int(np.floor(texel[3]))


def slot_of_live(rig):
    """The one slot whose PERSON id != 0."""
    live = [k for k in range(8) if rig.person(k)[0] != 0]
    assert len(live) == 1, live
    return live[0]


# ── Task 1: Body memory (Buffer B) ────────────────────────────────────────────

def b_at(rig, col, row):
    """B texel under Body pixel (col, row), row 0 = top."""
    w, h = rig.size
    return rig.buf("buffer_b")[int((1 - (row + 0.5) / BODY[1]) * h), int((col + 0.5) / BODY[0] * w)]


def test_presence_ignores_edge_flicker(ctx):
    rig = Rig(ctx)
    rig.run(flickering(30))
    for _ in range(10):
        rig.run(flickering(1, seed=_ + 5))
        assert b_at(rig, 32, 20)[0] > 0.95            # torso centre
        assert b_at(rig, 22, 20)[0] < 0.05            # 3 px outside the flickering border
    rig.release()


def test_run_extents_span_leg_to_shoulder(ctx):
    rig = Rig(ctx)
    rig.run([person()] * 10)
    g, b = b_at(rig, 29, 40)[1:3]                     # in a leg
    assert abs(g - (1 - 44 / 48)) < 1 / 48
    assert abs(b - (1 - 12 / 48)) < 2 / 48            # shoulder top: row 6 + 6
    rig.release()


def test_raised_arm_runs_start_at_its_lowest_point(ctx):
    rig = Rig(ctx)
    rig.run([person(arm="up")] * 10)
    g = b_at(rig, 36, 3)[1]                           # in the raised arm, above the head
    assert abs(g - (1 - 12 / 48)) < 2 / 48            # its lowest row (the shoulder), not the feet
    assert g > 0.5
    rig.release()


def test_owner_is_record_slot(ctx):
    rig = Rig(ctx)
    rig.run([person()] * 10)
    assert owner(b_at(rig, 30, 20)) == 1 and owner(b_at(rig, 2, 2)) == 0
    rig.release()


def test_walker_leaves_no_hold_trail(ctx):
    rig = Rig(ctx)
    rig.run(walking(20))
    b = rig.buf("buffer_b")
    gone = b[..., 0] < 0.05
    assert gone.any() and (b[..., 3][gone] == 0).all()
    rig.release()


def test_lost_person_holds_then_fades(ctx):
    rig = Rig(ctx)
    rig.run([person()] * 20)
    rig.run([EMPTY] * 15)                             # 1.5 s: lost after 8 misses
    h1 = b_at(rig, 32, 20)
    hold1 = (h1[3] % 1.0) / 0.9
    g1, b1 = h1[1], h1[2]
    assert 0 < hold1 < 1 and owner(h1) == 1
    rig.run([EMPTY] * 25)                             # LEAVE_S more
    h2 = b_at(rig, 32, 20)
    assert h2[3] == 0
    assert g1 > 0 and b1 > g1                         # the extents were kept while hold > 0
    rig.release()


@pytest.mark.parametrize("slot", [0, 7])               # owner 8 has the coarsest half-float spacing
@pytest.mark.parametrize("dt, per_cam", [(1 / 30, 3), (1 / 240, 24)])
def test_hold_fade_independent_of_render_rate(ctx, dt, per_cam, slot):
    """A lost person's hold falls by 1/LEAVE_S per second, +/- 15%, at any render rate.
    Measured as the slope of the mean hold over the torso between 0.5 s and 1.5 s into the fade."""
    rig = Rig(ctx, dt=dt, slot=slot)
    rig.run([person()] * 20, frames_per_camera=per_cam)

    def hold():                                        # mean over a torso patch, so per-pixel noise averages out
        a = np.array([b_at(rig, c, r)[3] for c in range(30, 35) for r in range(14, 22)])
        return float(np.mean((a % 1.0) / 0.9))

    h = []
    for _ in range(16):
        rig.run([EMPTY], frames_per_camera=per_cam)
        h.append(hold())
    assert h[1] < 1.0                                  # fading has started
    # camera frames are 0.1 s apart: frames 4 -> 14 span 1.0 s
    fall = h[4] - h[14]
    assert abs(fall - 1.0 / LEAVE_S) < 0.15 * (1.0 / LEAVE_S), fall
    rig.release()
