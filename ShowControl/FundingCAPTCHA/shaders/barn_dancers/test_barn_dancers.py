"""What a visitor sees in the barn_dancers Setup (shaders/barn_dancers/).

The Setup's promises. Every test below checks one of them, and says which.

1. An empty room shows only the field: pale sky, brown mud, no barn.
2. Each visitor the tracker is sure of gets a barn. It rises where they stand, follows them, and
   bows out when they leave.
3. The barns dance to a beat that never stops. A moving visitor's barn dances bigger and speeds the
   beat. A still visitor's barn stays calm, camera flicker included.
4. Nearer barns are drawn over farther ones.
5. The sprite-sheet barn stands where the drawn one does, the same size.

Tests assert the picture, or a barn's state read through BarnRig. None asserts how Buffer B stores it.

Records come from the real BodyBlobs tracker run on synthetic depth frames with a fake clock
(camera 10 Hz, render 30 Hz). GL tests need a headless context and skip without one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shader_test_rig import BLOBS, BODY, Rig
from shadertoy import ShaderError, decode_image, load_setup

SETUP = Path(__file__).parent
SIZE  = (192, 108)


class BarnRig(Rig):
    """The one place in this file that knows Buffer B's layout (see common.glsl)."""

    def __init__(self, ctx, image: np.ndarray | None = None):
        super().__init__(ctx, SETUP, SIZE, blobs=BLOBS, image=image)

    def has_barn(self, k) -> bool:  return bool(self.b()[0, k, 3] > 0)
    def barns(self) -> int:         return int((self.b()[0, :8, 3] > 0).sum())
    def x(self, k) -> float:        return float(self.b()[0, k, 0])      # where the barn stands, Body UV
    def nearness(self, k) -> float: return float(self.b()[0, k, 1])
    def energy(self, k) -> float:   return float(self.b()[0, k, 2])      # how big it dances: 0 calm … 1
    def risen(self, k) -> float:    return float(self.b()[1, k, 0])      # 0 below ground … 1 fully up
    def leaving(self, k) -> float:  return float(self.b()[1, k, 1])      # 0 staying … 1 gone
    def draw_order(self):           return [int(v + 0.5) for v in self.b()[3, :8, 0]]   # slots, back to front
    def beat(self) -> float:        return float(self.b()[4, 0, 0])      # phase within the cycle, 0 … 1
    def troupe_energy(self) -> float: return float(self.b()[4, 0, 1])    # what speeds the beat

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


# ── Claims 1 and 2: who gets a barn ───────────────────────────────────────────

def test_empty_room_shows_only_the_field(ctx):
    rig = BarnRig(ctx)
    rig.run([EMPTY] * 10)
    assert rig.barns() == 0
    img = rig.image()
    assert not barn_red(img).any()
    assert img[90:].mean() > img[:20].mean() + 30         # pale sky up top …
    assert img[:20, :, 0].mean() > img[:20, :, 2].mean() + 30         # … brown mud below
    rig.release()


def test_tentative_visitor_gets_no_barn(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(2))                                  # still tentative (min_confirm_frames 4)
    assert rig.barns() == 0
    rig.release()


def test_confirmed_visitor_gets_a_barn_that_rises_at_their_position(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(8))
    assert rig.has_barn(0) and 0 < rig.risen(0) < 1       # on its way up
    rig.run(standing(30))
    assert rig.risen(0) == 1 and rig.leaving(0) == 0
    assert rig.x(0) == pytest.approx(41 / 64, abs=0.02)   # the person's centre
    ys, xs = np.nonzero(barn_red(rig.image()))
    assert xs.size > 150
    assert xs.mean() == pytest.approx(41 / 64 * SIZE[0], abs=5)
    assert ys.min() > 0.07 * SIZE[1]                      # standing on the ground line, not below it
    rig.release()


def test_barn_follows_its_visitor(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(20, x0=8))
    left = rig.x(0)
    rig.run([person(8 + 2 * k) for k in range(20)] + standing(15, x0=46))
    assert rig.x(0) == pytest.approx(51 / 64, abs=0.02) and left < 0.25
    xs = np.nonzero(barn_red(rig.image()))[1]
    assert xs.mean() == pytest.approx(51 / 64 * SIZE[0], abs=5)
    rig.release()


def test_barn_bows_out_when_its_visitor_leaves(ctx):
    rig = BarnRig(ctx)
    rig.run(standing(20))
    rig.run([EMPTY] * 6)                                  # coasting: the tracker may yet find them
    assert rig.leaving(0) == 0
    rig.run([EMPTY] * 10)                                 # lost: the barn is on its way out
    assert rig.has_barn(0) and 0 < rig.leaving(0) < 1
    rig.run([EMPTY] * 15)
    assert rig.barns() == 0
    assert not barn_red(rig.image()).any()
    rig.release()


# ── Claims 3 and 4: the dance ─────────────────────────────────────────────────

def test_beat_keeps_time_in_an_empty_room(ctx):
    rig = BarnRig(ctx)
    phases = []
    for _ in range(4):                                    # four looks, 0.1 s apart
        rig.run([EMPTY])
        phases.append(rig.beat())
    steps = [(b - a) % 1 for a, b in zip(phases, phases[1:])]
    assert all(0.01 < d < 0.5 for d in steps), phases     # moving on, forwards ...
    assert max(steps) - min(steps) < 0.01, phases         # ... at a steady pace
    rig.release()


def test_moving_visitor_dances_bigger_and_speeds_the_beat(ctx):
    still, mover = BarnRig(ctx), BarnRig(ctx)
    still.run(standing(40))
    mover.run(flailing(40))
    assert still.energy(0) < 0.05 and still.troupe_energy() < 0.05
    assert mover.energy(0) > 0.5 and mover.troupe_energy() > 0.3
    still.release(); mover.release()


def test_flickering_still_visitor_stays_calm(ctx):
    rig = BarnRig(ctx)
    rig.run(flickering(40))
    assert rig.energy(0) < 0.05
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
    near, far = (0, 1) if rig.nearness(0) > rig.nearness(1) else (1, 0)
    assert rig.nearness(near) > rig.nearness(far) + 0.3
    order = rig.draw_order()
    assert sorted(order) == list(range(8))
    assert order.index(far) < order.index(near)
    rig.release()


# ── Claim 5: the sprite sheet ─────────────────────────────────────────────────

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
