"""Behaviour tests for the barn_dancers Setup (shaders/barn_dancers/).

Records come from the real BodyBlobs tracker run on synthetic depth frames with
a fake clock (camera 10 Hz, render 30 Hz). Buffer B layout: see common.glsl.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shader_test_rig import BLOBS, BODY, DT, Rig
from shadertoy import ShaderError, decode_image, load_setup

SETUP = Path(__file__).parent
SIZE  = (192, 108)
CYCLE_S = 1.75                            # common.glsl


class BarnRig(Rig):
    """Buffer B layout: see common.glsl."""

    def __init__(self, ctx, image: np.ndarray | None = None):
        super().__init__(ctx, SETUP, SIZE, blobs=BLOBS, image=image)

    def dancer(self, k): return self.b()[0, k]            # x, nearness, energy, id
    def stage(self, k):  return self.b()[1, k]            # risen, leaving, sideways speed
    def order(self):     return [int(v + 0.5) for v in self.b()[3, :8, 0]]
    def beat(self):      return self.b()[4, 0]            # phase, troupe energy

    def image(self) -> np.ndarray:
        """The Image as int (h, w, 3), row 0 = bottom."""
        return super().image()[..., :3].astype(int)


def barn_red(img: np.ndarray) -> np.ndarray:
    """Pixels the colour of a dancer's walls: nothing else in the scene is as red
    (the big barn behind the yard is washed out, the wire is rust-brown)."""
    return (img[..., 0] > 110) & (img[..., 0] > 1.9 * img[..., 1])


def person(x0=36, w=10, mm=2500):
    fg = np.zeros(BODY[::-1], dtype=np.uint16)
    fg[8:36, x0:x0 + w] = mm
    return fg


EMPTY = np.zeros(BODY[::-1], dtype=np.uint16)


def standing(n, x0=36, mm=2500):
    return [person(x0, mm=mm)] * n


def flailing(n, x0=30):
    """Arms out and in: the box width swings by 12 px at ~2 Hz."""
    return [person(x0 - 6 * (k % 5 in (1, 2, 3)), 10 + 12 * (k % 5 in (1, 2, 3))) for k in range(n)]


def flickering(n, seed=0):
    """A still person whose 1-px border toggles randomly each camera frame."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        fg = person()
        edge = np.zeros(BODY[::-1], dtype=bool)
        edge[7:37, 35:47] = True
        edge[9:35, 37:45] = False
        fg[edge] = np.where(rng.random(edge.sum()) < 0.5, 2500, 0)
        out.append(fg)
    return out


# ── Who gets a barn ───────────────────────────────────────────────────────────

def test_empty_room_shows_only_the_field(ctx):
    rig = BarnRig(ctx)
    rig.run([EMPTY] * 10)
    assert not rig.b()[0, :8, 3].any()                    # no slot holds a barn
    img = rig.image()
    assert not barn_red(img).any()
    assert img[90:].mean() > img[:20].mean() + 30         # pale sky up top …
    assert img[:20, :, 0].mean() > img[:20, :, 2].mean() + 30         # … brown mud below
    rig.release()


def test_tentative_visitor_gets_no_barn(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(2))                                  # still tentative (min_confirm_frames 4)
    assert rig.dancer(0)[3] == 0
    rig.release()


def test_confirmed_visitor_gets_a_barn_that_rises_at_their_position(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(8))
    assert rig.dancer(0)[3] > 0
    partway = rig.stage(0)[0]
    assert 0 < partway < 1
    rig.run(standing(30))
    assert rig.stage(0)[0] == 1 and rig.stage(0)[1] == 0
    assert rig.dancer(0)[0] == pytest.approx(41 / 64, abs=0.02)        # the person's centre, Body UV
    ys, xs = np.nonzero(barn_red(rig.image()))
    assert xs.size > 150
    assert xs.mean() == pytest.approx(41 / 64 * SIZE[0], abs=5)
    assert ys.min() > 0.07 * SIZE[1]                      # standing on the ground line, not below it
    rig.release()


def test_barn_follows_its_visitor(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(20, x0=8))
    left = rig.dancer(0)[0]
    rig.run([person(8 + 2 * k) for k in range(20)] + standing(15, x0=46))
    assert rig.dancer(0)[0] == pytest.approx(51 / 64, abs=0.02) and left < 0.25
    xs = np.nonzero(barn_red(rig.image()))[1]
    assert xs.mean() == pytest.approx(51 / 64 * SIZE[0], abs=5)
    rig.release()


def test_barn_bows_out_when_its_visitor_leaves(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(20))
    rig.run([EMPTY] * 6)                                  # coasting: the tracker may yet find them
    assert rig.stage(0)[1] == 0
    rig.run([EMPTY] * 10)                                 # lost: the barn is on its way out
    assert rig.dancer(0)[3] > 0 and 0 < rig.stage(0)[1] < 1
    rig.run([EMPTY] * 15)
    assert rig.dancer(0)[3] == 0 and not rig.stage(0).any()
    assert not barn_red(rig.image()).any()
    rig.release()


# ── The dance ─────────────────────────────────────────────────────────────────

def test_beat_keeps_time_in_an_empty_room(ctx):
    rig = BarnRig(ctx)
    rig.run([EMPTY] * 10)                                 # 30 renders: frame 0 only initialises
    assert rig.beat()[0] == pytest.approx((29 * DT / CYCLE_S) % 1, abs=0.01)
    rig.release()


def test_moving_visitor_dances_bigger_and_speeds_the_beat(ctx):
    still, mover = BarnRig(ctx), BarnRig(ctx)
    still.run(standing(40))
    mover.run(flailing(40))
    assert still.dancer(0)[2] < 0.05 and still.beat()[1] < 0.05
    assert mover.dancer(0)[2] > 0.5 and mover.beat()[1] > 0.3
    still.release(); mover.release()


def test_flickering_still_visitor_stays_calm(ctx):
    rig = BarnRig(ctx)
    rig.run(flickering(40))
    assert rig.dancer(0)[2] < 0.05
    rig.release()


def test_barn_moves_between_beats(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(30))
    a = barn_red(rig.image())
    rig.run(standing(4))                                  # 0.4 s on: another part of the cycle
    b = barn_red(rig.image())
    assert (a ^ b).sum() > 20
    rig.release()


def test_nearer_barns_are_drawn_over_farther_ones(ctx):
    rig = BarnRig(ctx)
    rig.run([person(6, mm=1500) + person(46, mm=3500)] * 20)
    near, far = (0, 1) if rig.dancer(0)[1] > rig.dancer(1)[1] else (1, 0)
    assert rig.dancer(near)[1] > rig.dancer(far)[1] + 0.3
    order = rig.order()
    assert sorted(order) == list(range(8))
    assert order.index(far) < order.index(near)
    rig.release()


# ── The sprite sheet ──────────────────────────────────────────────────────────

def test_sheet_barn_stands_where_the_drawn_one_does(ctx):
    """The shipped sheet and common.glsl's ATLAS block agree: both barns stand in the same place, the same size."""
    sheets = load_setup(SETUP).images
    assert [p.name for p in sheets] == ["barn.png"]
    try:
        sheet = decode_image(sheets[0], (4096, 4096))
    except ShaderError:
        pytest.skip("barn.png is a Git LFS pointer here (git lfs pull)")
    drawn, sprite = BarnRig(ctx), BarnRig(ctx, image=sheet)
    for rig in (drawn, sprite):
        rig.run(standing(30))
    (ya, xa), (yb, xb) = (np.nonzero(barn_red(rig.image())) for rig in (drawn, sprite))
    assert xb.size > 150
    assert xb.mean() == pytest.approx(xa.mean(), abs=2) and yb.mean() == pytest.approx(ya.mean(), abs=2)
    assert np.ptp(xb) == pytest.approx(np.ptp(xa), abs=4) and np.ptp(yb) == pytest.approx(np.ptp(ya), abs=4)
    drawn.release(); sprite.release()
