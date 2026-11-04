"""Behaviour tests for the hunter_bird Setup (shaders/hunter_bird/).

Records come from the real BodyBlobs tracker run on synthetic masks with a
fake clock (camera 10 Hz, render 30 Hz), so record noise is realistic.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
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

    def __init__(self, ctx):
        self.r = Renderer(ctx, SIZE, body_mode="camera")
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
                self.r.upload_blobs(self.blobs.records(now=self.t))
                self.r.render(DT, (0, 0, 0, 0))
                self.t += DT

    def b(self) -> np.ndarray:
        """Buffer B as float32 (h, w, 4), row 0 = texel y 0."""
        t = self.r._buffers["buffer_b"].read_tex
        return np.frombuffer(t.read(), dtype=np.float16).astype(np.float32).reshape(t.size[1], t.size[0], 4)

    def slot(self, k):  return self.b()[0, k]             # id, motion, interest, stamped
    def head(self, k):  return self.b()[2, k]             # last print x, y, side, since
    def attn(self):     return self.b()[3, 0]             # target+1, lock, since strike, id struck
    def reticle(self):  return self.b()[3, 1]             # x, y, radius, alpha
    def mood(self):     return self.b()[3, 2]             # lids, shiver, anchor x, y
    def blink(self):    return self.b()[3, 3]             # since blink, idle countdown, all-stamped s
    def stamp(self):    return self.b()[3, 4]             # x, y
    def prints(self):   return self.b()[4, :8 * 12]       # x, y, age, angle

    def image(self) -> np.ndarray:
        """The Image as uint8 (h, w, 4), row 0 = bottom."""
        return np.frombuffer(self.r.output.read(components=4), np.uint8).reshape(SIZE[1], SIZE[0], 4)

    def release(self):
        self.r.release()


def rect(x0, y0, x1, y1):
    m = np.zeros(BODY[::-1], dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


EMPTY = np.zeros(BODY[::-1], dtype=bool)


def standing(n, x=36):
    return [rect(x, 8, x + 10, 36)] * n


def walking(n, step=1):
    """~0.28 screen heights/s here: motion ≈ 0.57, so lock stays < 1 for 6 s at the defaults."""
    return [rect(6 + (k * step) % 40, 8, 16 + (k * step) % 40, 36) for k in range(n)]


def flailing(n, x=30):
    """Arms out and in: the box width swings by 12 px at ~2 Hz."""
    return [rect(x - 6 * (k % 5 in (1, 2, 3)), 8, x + 10 + 6 * (k % 5 in (1, 2, 3)), 36) for k in range(n)]


def flickering(n, seed=0):
    """A still person whose 1-px border toggles randomly each camera frame."""
    rng = np.random.default_rng(seed)
    base = rect(36, 8, 46, 36)
    edge = rect(35, 7, 47, 37) & ~rect(37, 9, 45, 35)
    out = []
    for _ in range(n):
        m = base.copy()
        m[edge] = rng.random(edge.sum()) < 0.5
        out.append(m)
    return out


# ── Task 1: per-slot state ────────────────────────────────────────────────────

def test_slot_tracks_record_id(ctx):
    rig = Rig(ctx)
    rig.run(standing(8))
    assert rig.slot(0)[0] == 1


def test_walking_has_motion(ctx):
    rig = Rig(ctx)
    rig.run(walking(20))
    assert rig.slot(0)[1] > 0.3


def test_flickering_still_person_has_no_motion(ctx):     # Review Focus 1
    rig = Rig(ctx)
    rig.run(flickering(40))
    assert rig.slot(0)[1] < 0.05


def test_interest_rises_with_motion_and_drains_still(ctx):
    rig = Rig(ctx)
    rig.run(walking(30))
    hi = rig.slot(0)[2]
    rig.run([walking(31)[-1]] * 40)
    assert hi > 0.5 and rig.slot(0)[2] < hi - 0.5


def test_tentative_has_no_motion_or_interest(ctx):
    rig = Rig(ctx)
    rig.run(walking(2))                                   # still tentative (min_confirm_frames 4)
    assert rig.slot(0)[1] == 0 and rig.slot(0)[2] == 0
