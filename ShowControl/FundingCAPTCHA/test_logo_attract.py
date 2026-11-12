"""Behaviour tests for the logo_attract Setup (shaders/logo_attract/), the playlist's interstitial.

Blob records are written by hand: one confirmed visitor per slot, centroid in Body UV.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shadertoy import (BLOB_CONFIRMED, BLOB_ROWS, BLOB_SLOTS, BLOB_TENTATIVE, Renderer,
                       decode_image, load_setup)

SETUP  = Path(__file__).parent / "shaders" / "logo_attract"
SIZE   = (160, 90)
DT     = 1 / 30


class Rig:
    def __init__(self, ctx, image=True, size=SIZE):
        self.size = size
        self.r = Renderer(ctx, size, body_mode="camera")
        setup = load_setup(SETUP)
        self.r.load(setup, image=decode_image(setup.images[0], size) if image else None)
        self.r.defer_image = True

    def run(self, seconds, people=()):
        """people: (slot, id, x, y[, state]) — centroid in Body UV."""
        rec = np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32)
        for slot, ident, x, y, *state in people:
            rec[0, slot] = (x - 0.05, y - 0.2, x + 0.05, y + 0.2)
            rec[1, slot] = (x, y, 0, 0)
            rec[2, slot] = (ident, state[0] if state else BLOB_CONFIRMED, 0, 0.5)
        for _ in range(round(seconds / DT)):
            self.r.upload_blobs(rec)
            self.r.render(DT, (0, 0, 0, 0))

    def logo(self):
        """Logo centre in screen UV."""
        tex = self.r._buffers["buffer_b"].read_tex
        data = np.frombuffer(tex.read(), dtype=np.float16).reshape(self.size[1], self.size[0], 4)
        x, y = data[1, 0, :2].astype(float)
        return x / (self.size[0] / self.size[1]), y

    def life(self, slot):
        tex = self.r._buffers["buffer_b"].read_tex
        data = np.frombuffer(tex.read(), dtype=np.float16).reshape(self.size[1], self.size[0], 4)
        return float(data[0, slot, 1])

    def image(self):
        self.r.draw_deferred_image()
        data = np.frombuffer(self.r.output.read(components=4), dtype=np.uint8)
        return data.reshape(self.size[1], self.size[0], 4)

    def release(self):
        self.r.release()


@pytest.fixture
def rig(ctx):
    r = Rig(ctx)
    yield r
    r.release()


def test_ships_the_logo_image():
    assert [p.name for p in load_setup(SETUP).images] == ["logo.png"]


def test_rests_at_centre_when_nobody_is_there(rig):
    rig.run(3.0)
    assert rig.logo() == pytest.approx((0.5, 0.5), abs=0.01)
    img = rig.image()
    assert img[5, 5, :3].tolist() == [0, 0, 0]               # black background
    assert (img[..., :3].sum(-1) > 700).any()                # and the logo's white ring on it


def _white_extent(img) -> tuple[int, int]:
    ys, xs = np.nonzero(img[..., :3].astype(int).sum(-1) > 700)
    return xs.max() - xs.min() + 1, ys.max() - ys.min() + 1


@pytest.mark.parametrize("size", [(320, 180), (320, 200), (240, 180), (240, 320)])
def test_logo_is_round_at_any_aspect(ctx, size):
    rig = Rig(ctx, size=size)
    try:
        rig.run(1.0)
        w, h = _white_extent(rig.image())
        assert w == pytest.approx(h, abs=2)
        assert h == pytest.approx(2 * 0.3 * size[1], abs=3)    # diameter: 2 · RADIUS screen heights
    finally:
        rig.release()


def test_drifts_to_a_visitor_and_back(rig):
    rig.run(8.0, [(0, 1, 0.8, 0.5)])
    x, y = rig.logo()
    assert x > 0.7 and y == pytest.approx(0.5, abs=0.02)
    rig.run(6.0)
    assert rig.logo() == pytest.approx((0.5, 0.5), abs=0.02)


def test_newcomer_pulls_gently_at_first(rig):
    rig.run(0.5, [(0, 1, 0.8, 0.5)])
    assert rig.logo()[0] < 0.6


def test_stays_on_screen(rig):
    rig.run(8.0, [(0, 1, 1.0, 0.0)])
    x, y = rig.logo()
    assert 0.5 < x < 1.0 and 0.0 < y < 0.5
    assert y > 0.3 * 0.8 - 0.01                    # a radius-ish inside the bottom edge


def test_longer_visitor_wins_the_average(rig):
    rig.run(10.0, [(0, 1, 0.2, 0.5)])               # left, here 10 s
    rig.run(2.0, [(0, 1, 0.2, 0.5), (1, 2, 0.8, 0.5)])   # right, here 2 s
    assert rig.life(0) > 5 * rig.life(1)
    assert rig.logo()[0] < 0.4                      # still well left of centre
    rig.run(25.0, [(0, 1, 0.2, 0.5), (1, 2, 0.8, 0.5)])  # both capped: equal weight
    assert rig.logo()[0] == pytest.approx(0.5, abs=0.03)


def test_new_person_in_a_slot_starts_from_zero(rig):
    rig.run(5.0, [(0, 1, 0.8, 0.5)])
    rig.run(DT, [(0, 7, 0.8, 0.5)])
    assert rig.life(0) < 0.1


def test_tentative_blobs_dont_pull(rig):
    rig.run(5.0, [(0, 1, 0.9, 0.5, BLOB_TENTATIVE)])
    assert rig.logo() == pytest.approx((0.5, 0.5), abs=0.01)


def test_draws_a_stand_in_without_the_image(ctx):
    r = Rig(ctx, image=False)
    try:
        r.run(1.0)
        img = r.image()
        assert img[45, 80, :3].tolist() != img[5, 5, :3].tolist()
    finally:
        r.release()


def test_deferred_image_is_exact(ctx):
    rs = [Rig(ctx), Rig(ctx)]
    try:
        rs[0].r.defer_image = False
        for r in rs:
            r.run(1.0, [(0, 1, 0.7, 0.4)])
        rs[1].r.draw_deferred_image()
        assert rs[0].r.output.read() == rs[1].r.output.read()
    finally:
        for r in rs:
            r.release()
