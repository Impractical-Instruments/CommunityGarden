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


def make(ctx) -> Renderer:
    r = Renderer(ctx, SIZE, body_mode="camera")
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
    return np.frombuffer(r.output.read(components=4), dtype=np.uint8).reshape(SIZE[1], SIZE[0], 4)


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
    run(r, [rect(30, 20, 33, 28)] * 40)          # ~1% of frame, 4 s
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
