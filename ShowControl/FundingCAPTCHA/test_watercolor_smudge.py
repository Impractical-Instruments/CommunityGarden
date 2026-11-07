"""Behaviour tests for the watercolor_smudge Setup (shaders/watercolor_smudge/).

Spec: docs/superpowers/specs/2026-11-07-watercolor-smudge-design.md.
Buffers: B original painting, C motion (eased Body, extremity, empty timer),
D canvas (paint + wetness). The Body is uploaded directly at render size.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from shadertoy import Renderer, load_setup

SETUP = Path(__file__).parent / "shaders" / "watercolor_smudge"
SIZE  = (96, 54)
DT    = 1 / 30
ABSENT, PRESENT = (0.0, 0.0, -1.0, -1.0), (48.0, 27.0, 48.0, 27.0)


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


def _rig(ctx, image: np.ndarray | None = None) -> Renderer:
    r = Renderer(ctx, SIZE, body_mode="camera")
    r.load(load_setup(SETUP), image=image)
    r.upload_body(np.zeros((SIZE[1], SIZE[0], 4), dtype=np.uint8))
    return r


def _buf(r: Renderer, name: str) -> np.ndarray:
    tex = r._buffers[name].read_tex
    data = np.frombuffer(tex.read(), dtype=np.float16)
    return data.reshape(tex.size[1], tex.size[0], 4).astype(np.float32)


def _out(r: Renderer) -> np.ndarray:
    data = np.frombuffer(r.output.read(components=4), dtype=np.uint8)
    return data.reshape(SIZE[1], SIZE[0], 4)


def _frames(r: Renderer, n: int, mouse=ABSENT) -> None:
    for _ in range(n):
        r.render(DT, mouse)


def _halves(left: tuple, right: tuple) -> np.ndarray:
    img = np.zeros((SIZE[1], SIZE[0], 4), dtype=np.uint8)
    img[:, : SIZE[0] // 2] = left
    img[:, SIZE[0] // 2:] = right
    return img


# ── Task 2: original painting, canvas, display ────────────────────────────────

def test_without_image_paints_procedural_sunset(ctx):
    r = _rig(ctx)
    _frames(r, 3)
    o = _out(r).astype(int)
    top = o[48, 48, :3]                                   # GL row 48 is near the top
    assert top[2] > top[0]                                # sky top is blue-violet
    assert o.std() > 10                                   # not flat
    assert (o[1, 1, :3] > 200).all()                      # ragged paper border at the corner
    r.release()


def test_canvas_starts_equal_to_original(ctx):
    r = _rig(ctx)
    _frames(r, 2)
    diff = np.abs(_buf(r, "buffer_d")[..., :3] - _buf(r, "buffer_b")[..., :3])
    assert diff.max() < 1 / 255
    r.release()


def test_image_shows_unchanged_when_undisturbed(ctx):
    r = _rig(ctx, image=_halves((255, 0, 0, 255), (0, 0, 255, 255)))
    _frames(r, 3)
    o = _out(r).astype(int)
    assert np.abs(o[27, 20, :3] - (255, 0, 0)).max() <= 2
    assert np.abs(o[27, 76, :3] - (0, 0, 255)).max() <= 2
    r.release()


def test_image_covers_screen_keeping_aspect(ctx):
    # Portrait 54×96, bands top→bottom green / red / blue (row 0 = bottom).
    img = np.zeros((96, 54, 4), dtype=np.uint8)
    img[64:] = (0, 255, 0, 255)
    img[32:64] = (255, 0, 0, 255)
    img[:32] = (0, 0, 255, 255)
    r = _rig(ctx, image=img)
    _frames(r, 3)
    o = _out(r).astype(int)
    assert (o[..., 0] > 200).all()                        # cover crops top and bottom: all red
    assert (o[..., 1] < 30).all() and (o[..., 2] < 30).all()
    r.release()
