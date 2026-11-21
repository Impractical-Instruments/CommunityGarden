"""What a visitor sees in the watercolor_smudge Setup (shaders/watercolor_smudge/).

The Setup's promises. Every test below checks one of them, and says which.

1. Left alone, the painting shows as it is. An image covers the screen, keeping its aspect. With no
   image there is a painted sunset inside a ragged paper border.
2. A moving limb smears the paint along its path, whatever colour the paint is. A moving torso does
   not, and nor does someone standing still while the camera flickers. The paper border never smears,
   and the painting stays sharp away from the smear.
3. A smear stays while anyone is there, and a fresh one reads darker than a dry one. Once the room is
   empty it waits, then heals. Healing pauses when someone comes back.
4. Left idle for minutes, the painting is unchanged.

Not met, and marked xfail below: an arm reaching out along its own axis should smear, and does not.

Tests assert the picture, or how far the paint has moved, read through smear() and paper_border().
None asserts how a buffer stores its state.

The Body is uploaded directly at render size. GL tests need a headless context and skip without one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shader_test_rig import DT, glsl_consts, load_renderer, read_image
from shadertoy import Renderer

SETUP = Path(__file__).parent
SIZE  = (96, 54)
K = glsl_consts(SETUP)
ABSENT, PRESENT = (0.0, 0.0, -1.0, -1.0), (48.0, 27.0, 48.0, 27.0)


def _rig(ctx, image: np.ndarray | None = None) -> Renderer:
    r = load_renderer(ctx, SETUP, SIZE, image=image)
    r.upload_body(np.zeros((SIZE[1], SIZE[0], 4), dtype=np.uint8))
    return r


def _frames(r: Renderer, n: int, mouse=ABSENT) -> None:
    for _ in range(n):
        r.render(DT, mouse)


def _halves(left: tuple, right: tuple) -> np.ndarray:
    img = np.zeros((SIZE[1], SIZE[0], 4), dtype=np.uint8)
    img[:, : SIZE[0] // 2] = left
    img[:, SIZE[0] // 2:] = right
    return img


# ── Claim 1: left alone, the painting shows as it is (Image) ──────────────────

def test_without_image_paints_procedural_sunset(ctx):
    r = _rig(ctx)
    _frames(r, 3)
    o = read_image(r).astype(int)
    top = o[48, 48, :3]                                   # GL row 48 is near the top
    assert top[2] > top[0]                                # sky top is blue-violet
    assert o.std() > 10                                   # not flat
    assert (o[1, 1, :3] > 200).all()                      # ragged paper border at the corner
    r.release()


def test_image_shows_unchanged_when_undisturbed(ctx):
    r = _rig(ctx, image=_halves((255, 0, 0, 255), (0, 0, 255, 255)))
    _frames(r, 3)
    o = read_image(r).astype(int)
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
    o = read_image(r).astype(int)
    assert (o[..., 0] > 200).all()                        # cover crops top and bottom: all red
    assert (o[..., 1] < 30).all() and (o[..., 2] < 30).all()
    r.release()


# ── Claims 2, 3 and 4: what smears, and how it heals ──────────────────────────

CAMERA = (384, 216)                       # a camera-like Body resolution, for flicker


def _bar(w_frac: float, x_frac: float, extra: np.ndarray | None = None,
         size: tuple[int, int] = SIZE) -> np.ndarray:
    """Body: a full-height vertical bar w_frac screen widths wide, centred at x_frac."""
    body = np.zeros((size[1], size[0], 4), dtype=np.uint8)
    x = (np.arange(size[0]) + 0.5) / size[0]
    body[:, np.abs(x - x_frac) < w_frac / 2, 0] = 255
    if extra is not None:
        body[..., 0] = np.maximum(body[..., 0], extra)
    return body


# The two places in this file that know the buffer layout (see common.glsl).

def smear(r: Renderer) -> np.ndarray:
    """How far each texel's paint is from the original painting's: 0 untouched … 1. (h, w), row 0 = bottom."""
    return np.abs(r.read_buffer("buffer_d")[..., :3] - r.read_buffer("buffer_b")[..., :3]).max(axis=2)


def paper_border(r: Renderer) -> np.ndarray:
    """Where the bare paper round the painting is. (h, w) bool, row 0 = bottom."""
    return r.read_buffer("buffer_b")[..., 3] < 0.01


def _sweep(r: Renderer, w_frac: float, x0: float, x1: float, seconds: float = 1.0) -> None:
    """Move a bar from x0 to x1, Body at 10 Hz, render at 30 Hz, someone present."""
    n = int(round(seconds / DT))
    for i in range(n + 1):
        if i % 3 == 0:
            r.upload_body(_bar(w_frac, x0 + (x1 - x0) * i / n))
        r.render(DT, PRESENT)


def _cols(x0: float, x1: float) -> slice:
    return slice(int(x0 * SIZE[0]), int(x1 * SIZE[0]))


def _checker(cell: int = 6) -> np.ndarray:
    yy, xx = np.mgrid[0:SIZE[1], 0:SIZE[0]]
    ch = ((xx // cell + yy // cell) % 2).astype(np.uint8) * 255
    return np.stack([ch, 255 - ch, np.full_like(ch, 128), np.full_like(ch, 255)], -1)


def test_moving_limb_smears_most_of_its_path(ctx):
    """A camera-hard Body edge still carries paint along, as the sketch's soft figure did."""
    r = _rig(ctx, image=_checker())
    _frames(r, 2)
    _sweep(r, 0.02, 0.2, 0.6)
    assert (smear(r)[:, _cols(0.25, 0.55)] > 0.1).mean() > 0.3
    r.release()


def test_black_paint_at_centre_still_smears(ctx):
    img = _checker()
    img[20:34, 40:56, :3] = 0                              # pure black patch over the centre
    r = _rig(ctx, image=img)
    _frames(r, 2)
    _sweep(r, 0.02, 0.2, 0.6)
    assert (smear(r)[:, _cols(0.25, 0.55)] > 0.1).mean() > 0.3
    r.release()


def _arm(x0: float, x1: float, y: float = 0.5, h: float = 0.07) -> np.ndarray:
    """Body: a horizontal arm from x0 to x1 (screen widths), h screen heights thick."""
    body = np.zeros((SIZE[1], SIZE[0], 4), dtype=np.uint8)
    xs = (np.arange(SIZE[0]) + 0.5) / SIZE[0]
    ys = (np.arange(SIZE[1]) + 0.5) / SIZE[1]
    body[np.ix_(np.abs(ys - y) < h / 2, (xs >= x0) & (xs <= x1))] = (255, 0, 0, 0)
    return body


@pytest.mark.xfail(strict=True, reason="known limitation (final-review ruling): an arm extending along its own "
                   "axis only gains Body at the tip, so the balance gate reads it as appearing and suppresses "
                   "the smear. strict: a gate change that fixes it fails here, so remove this mark then")
def test_reaching_arm_along_its_axis_smears(ctx):
    """An arm reaching out along its own axis smears its path, as a sideways sweep does."""
    r = _rig(ctx, image=_checker())
    r.upload_body(_arm(0.25, 0.3))
    _frames(r, 15, PRESENT)
    n = 30
    for i in range(n + 1):
        if i % 3 == 0:
            r.upload_body(_arm(0.25, 0.3 + 0.5 * i / n))
        r.render(DT, PRESENT)
    rows = slice(int(0.465 * SIZE[1]), int(0.535 * SIZE[1]))   # the arm's own rows
    assert (smear(r)[rows, _cols(0.35, 0.75)] > 0.1).mean() > 0.3   # as test_moving_limb_smears_most_of_its_path
    r.release()


def test_moving_torso_does_not_smear(ctx):
    r = _rig(ctx)
    _frames(r, 2)
    _sweep(r, 0.3, 0.2, 0.6)
    assert smear(r).max() < 0.03
    r.release()


def test_still_flickering_person_leaves_paint_alone(ctx):
    """A still limb whose 1-camera-px edge flickers at 10 Hz (rim pixels on/off, edge dropout)."""
    rng = np.random.default_rng(7)
    r = _rig(ctx)
    _frames(r, 2)
    base = _bar(0.02, 0.5, size=CAMERA)
    cols = np.flatnonzero(base[0, :, 0])
    for i in range(90):                                    # 3 s
        if i % 3 == 0:
            body = base.copy()
            for side in (cols[0] - 1, cols[-1] + 1):       # rim pixels switch on
                body[rng.random(CAMERA[1]) < 0.5, side, 0] = 255
            for edge in (cols[0], cols[-1]):               # edge pixels drop out
                body[rng.random(CAMERA[1]) < 0.3, edge, 0] = 0
            r.upload_body(body)
        r.render(DT, PRESENT)
    assert smear(r).max() < 0.02
    r.release()


def test_smear_persists_while_present(ctx):
    r = _rig(ctx)
    _frames(r, 2)
    _sweep(r, 0.02, 0.2, 0.6)
    before = smear(r).sum()
    _frames(r, 150, PRESENT)                               # 5 s, bar still at 0.6
    assert smear(r).sum() > 0.9 * before
    r.release()


def _smeared_then_empty(ctx) -> tuple[Renderer, float]:
    r = _rig(ctx)
    _frames(r, 2)
    _sweep(r, 0.02, 0.2, 0.6)
    _sweep(r, 0.02, 0.6, 0.6, seconds=0.5)                 # stand still so the paint settles
    r.upload_body(np.zeros((SIZE[1], SIZE[0], 4), dtype=np.uint8))
    return r, smear(r).sum()


def test_heal_waits_for_delay_then_heals_in_heal_time(ctx):
    r, start = _smeared_then_empty(ctx)
    delay, heal = round(K["HEAL_DELAY_S"] / DT), round(K["HEAL_TIME_S"] / DT)
    _frames(r, delay * 3 // 4)                             # most of the delay: nothing yet
    assert smear(r).sum() > 0.9 * start
    _frames(r, delay // 4 + heal)                          # the rest of it, and the heal
    assert smear(r).sum() < 0.05 * start
    r.release()


def test_heal_pauses_when_someone_returns(ctx):
    r, start = _smeared_then_empty(ctx)
    _frames(r, 120)                                        # 4 s empty: 2 s of healing
    r.upload_body(_bar(0.02, 0.6))
    _frames(r, 15, PRESENT)                                # let the arrival settle
    mid = smear(r).sum()
    _frames(r, 90, PRESENT)                                # 3 s present
    assert smear(r).sum() > 0.95 * mid
    r.release()


def test_paper_border_never_smears(ctx):
    r = _rig(ctx)
    _frames(r, 2)
    _sweep(r, 0.02, 0.0, 0.2)
    border = paper_border(r)
    assert border.any()
    assert smear(r)[border].max() < 1 / 255
    r.release()


def test_idle_for_minutes_leaves_the_painting_unchanged(ctx):
    r = _rig(ctx)
    _frames(r, 4000)
    for name in ("buffer_b", "buffer_c", "buffer_d"):
        assert np.isfinite(r.read_buffer(name)).all()
    assert smear(r).max() < 1 / 255
    r.release()


# ── Claims 2 and 3: how the smear looks (Image) ───────────────────────────────

def test_image_stays_sharp_outside_smear(ctx):
    yy, xx = np.mgrid[0:SIZE[1], 0:SIZE[0]]
    checker = ((xx // 4 + yy // 4) % 2).astype(np.uint8) * 255
    img = np.stack([checker, 255 - checker, np.full_like(checker, 128), np.full_like(checker, 255)], -1)
    r = _rig(ctx, image=img)
    _frames(r, 2)
    _sweep(r, 0.02, 0.2, 0.4)
    o = read_image(r).astype(int)
    far = _cols(0.75, 0.95)
    assert np.abs(o[:, far, :3] - img[:, far, :3].astype(int)).max() <= 2
    assert np.abs(o[:, _cols(0.2, 0.4), :3] - img[:, _cols(0.2, 0.4), :3].astype(int)).max() > 25
    r.release()


def test_wet_smear_reads_darker_than_dry(ctx):
    r = _rig(ctx)
    _frames(r, 2)
    _sweep(r, 0.02, 0.2, 0.6)
    swept = (slice(None), _cols(0.25, 0.55))
    wet = read_image(r)[swept][..., :3].astype(float).mean()
    _frames(r, 120, PRESENT)                               # 4 s, present: it dries but does not heal
    assert wet < read_image(r)[swept][..., :3].astype(float).mean()
    r.release()
