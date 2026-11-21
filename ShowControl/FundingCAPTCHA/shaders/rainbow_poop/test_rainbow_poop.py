"""What a visitor sees in the rainbow_poop Setup (shaders/rainbow_poop/).

The Setup's promises. Every test below checks one of them, and says which.

1. An empty room is paper and clouds. Nothing drops.
2. Anyone in the room gets a poop on the head: the first soon after they appear, then one every
   BOMB_EVERY_S or so. It drops from the top of the sky and takes over a second to fall. Everyone
   gets their own. Fidgeting or walking steadily does not save you.
3. A splat sticks where it landed on your body as you move, is drawn only on your silhouette, and
   fades after its life. Leave and your splats clear; whoever comes next starts clean.
4. Step away after it drops and it misses, leaving a puddle on the ground.
5. A long stall leaves the scene sane.
6. It plays the same on every GPU. One renderer cannot show that, so the test for it reads the
   shader source (#214).

Tests assert the picture, or what dropped, landed and stuck, read through RainbowRig. None asserts
how Buffer B stores it.

Records come from the real BodyBlobs tracker run on synthetic masks with a fake clock (camera 10 Hz,
render 30 Hz), so record noise is realistic. GL tests need a headless context and skip without one.
"""
from __future__ import annotations

from functools import partial
from pathlib import Path

import numpy as np
import pytest

import shader_test_rig as rigs
from shader_test_rig import BODY, EMPTY, Rig, rect

SETUP = Path(__file__).parent
SIZE  = (128, 72)                         # render; ≥ 64 wide for the SPLAT row

K = rigs.glsl_consts(SETUP)           # so tests follow retuning
SPLAT_LIFE_S  = float(K["SPLAT_LIFE_S"])
GROUND_LIFE_S = float(K["GROUND_LIFE_S"])
FIRST_BOMB_S, FIRST_JITTER = float(K["FIRST_BOMB_S"]), float(K["FIRST_JITTER"])
BOMB_EVERY_S, BOMB_JITTER_S = float(K["BOMB_EVERY_S"]), float(K["BOMB_JITTER_S"])
LONGEST_FALL_S = float(K["SPAWN_Y"]) / float(K["FALL_SPEED"])   # top of the sky to the floor: how long to wait for a miss

standing = partial(rigs.standing, x=27)   # the test people stand at x = 27 unless told otherwise
flickering = partial(rigs.flickering, x=27)


class RainbowRig(Rig):
    """The one place in this file that knows Buffer B's layout (see common.glsl).
    Watches every rendered frame for poops dropping and landing, as each shows for one frame only."""

    def __init__(self, ctx, size=SIZE):
        super().__init__(ctx, SETUP, size)
        self.hits: list[tuple[float, int]] = []          # (time, slot) of every new splat
        self.misses: list[float] = []                     # time of every new ground splat
        self.drops: list[tuple[float, int]] = []         # (time, slot) of every poop dropped
        self._watching = True

    def run(self, masks, frames_per_camera=3, watch=True):
        self._watching = watch
        super().run(masks, frames_per_camera)

    def after_render(self):
        if not self._watching:
            return
        b = self.b()
        for k in range(8):
            if b[4, k * 8, 2] == 0:                       # age 0: landed this frame
                self.hits.append((self.t, k))
            if b[3, k, 0] > 0.5 and b[3, k, 3] == 0:      # falling, age 0: dropped this frame
                self.drops.append((self.t, k))
        if b[5, 0, 2] == 0:
            self.misses.append(self.t)

    def person_id(self, k) -> int:
        """The tracker id of slot k's person, or 0 if the slot is empty."""
        return int(self.b()[0, k, 0])

    def presence(self, k) -> float:
        """How solidly slot k's person and their splats are drawn: 1 there … 0 gone."""
        return float(self.b()[0, k, 2])

    def falling(self):
        """The slots with a poop in the air."""
        return [k for k in range(8) if self.b()[3, k, 0] > 0.5]

    def fall_age(self, k) -> float:
        """Seconds slot k's poop has been falling."""
        return float(self.b()[3, k, 3])

    def poop_xy(self, k):
        """Where slot k's poop is: x, y (Body UV)."""
        return self.b()[2, k, :2]

    def live_splats(self, k):
        """Slot k's splats still showing, one row each: x, y (relative to the person), age s, seed."""
        s = self.b()[4, k * 8:(k + 1) * 8]
        return s[s[:, 2] < SPLAT_LIFE_S]

    def splat_uv(self, k, s):
        """Where one of slot k's splats is on screen: x, y (Body UV)."""
        an = self.b()[1, k]                               # the person's anchor: x, y, height
        return an[0] + s[0] * an[2] / (self.size[0] / self.size[1]), an[1] + s[1] * an[2]

    def puddle_xy(self):
        """Where the newest ground puddle is: x, y (Body UV)."""
        return self.b()[5, 0, :2]


# ── Claim 1: the empty room ───────────────────────────────────────────────────

def test_empty_room_drops_nothing(ctx):
    rig = RainbowRig(ctx)
    for _ in range(40):                                   # 12 s
        rig.run([EMPTY] * 3)
        assert not rig.falling()
    assert not rig.hits and not rig.misses


# ── Claim 2: anyone in the room gets a poop on the head ───────────────────────

def test_standing_person_is_hit_soon_after_appearing(ctx):
    rig = RainbowRig(ctx)
    rig.run(flickering(60))                               # 6 s
    assert rig.drops and rig.hits, "never hit"
    # confirmed after ~0.4 s, then the first countdown
    assert rig.drops[0][0] < 0.4 + FIRST_BOMB_S + FIRST_JITTER + 0.5
    assert rig.hits[0][1] == 0 and not rig.misses


def test_splat_lands_on_the_head(ctx):
    rig = RainbowRig(ctx)
    rig.run(flickering(60))                               # rect(27, 8, 37, 36): UV x 0.42–0.58, y 0.1–0.8
    s = rig.live_splats(0)
    assert len(s) >= 1
    u, v = rig.splat_uv(0, s[0])
    assert 0.40 < u < 0.60                                # over the body
    assert 0.55 < v < 0.80                                # on its upper part, below the top


def test_cadence_is_about_every_five_seconds(ctx):
    rig = RainbowRig(ctx)
    rig.run(flickering(260))                              # 26 s
    t = [h[0] for h in rig.hits if h[1] == 0]
    assert len(t) >= 4, t
    gaps = np.diff(t)
    assert (gaps > BOMB_EVERY_S - BOMB_JITTER_S - 0.5).all(), gaps
    assert (gaps < BOMB_EVERY_S + BOMB_JITTER_S + 0.5).all(), gaps
    assert not rig.misses


def test_poop_falls_slowly_from_the_top(ctx):
    rig = RainbowRig(ctx)
    ys = []
    for k in range(60):
        rig.run(flickering(1, seed=k))                    # a fresh flicker each camera frame
        if rig.falling():
            ys.append(rig.poop_xy(0)[1])
        if rig.hits:
            break
    assert rig.hits and ys
    assert ys[0] > 0.98                                   # it starts at the top of the sky
    assert all(b <= a for a, b in zip(ys, ys[1:])), ys    # and only ever comes down
    fall = rig.hits[0][0] - rig.drops[0][0]               # timed to the render frame
    assert 1.0 < fall < 2.0, fall                         # slow enough to see coming, not a wait


def test_two_people_both_get_hit(ctx):
    rig = RainbowRig(ctx)
    two = [a | b for a, b in zip(flickering(80, x=8), flickering(80, x=46, seed=1))]
    rig.run(two)
    hit = {k for _, k in rig.hits}
    assert hit == {0, 1}


# ── Claim 3: splats stick, fade, and leave with you ───────────────────────────

def test_splats_fade_after_their_life(ctx):
    rig = RainbowRig(ctx)
    rig.run(standing(45))
    first = rig.live_splats(0)
    assert len(first) == 1
    seed, age = first[0, 3], first[0, 2]
    rig.run(standing(int((SPLAT_LIFE_S - age) * 10) + 5))
    live = rig.live_splats(0)
    assert seed not in live[:, 3]                         # the first splat has gone …
    assert 2 <= len(live) <= 4                            # … the later ones are still there


def test_splats_stay_put_on_the_body(ctx):                 # raised arms, arms out, walking
    rig = RainbowRig(ctx)
    rig.run(standing(45, x=10))
    seed = rig.live_splats(0)[0, 3]
    def where():                                          # the splat, relative to the torso's centre
        s = next(s for s in rig.live_splats(0) if s[3] == seed)
        u, v = rig.splat_uv(0, s)
        return u - (x + 5) / 64, v
    x = 10
    u0, v0 = where()
    worst = 0.0
    for k in range(40):
        x = 10 + k // 2                                   # walking right at 0.5 px per camera frame
        m = rect(x, 8, x + 10, 36)
        if k % 4 == 1: m |= rect(x + 7, 1, x + 10, 8)     # an arm straight up
        if k % 4 == 3: m |= rect(x + 10, 12, x + 18, 15)  # an arm out to the side
        rig.run([m], watch=False)
        u, v = where()
        worst = max(worst, abs(u - u0), abs(v - v0))
    assert worst < 0.035, worst                           # ~2 Body px; the box moves ~7 px


def person(cx, arm, rng):
    """A person, not a box: a head 3 px wide, a 7 px torso, two legs with a gap, an arm
    sometimes out, and flickering edges. Most of the box is empty, so a loose aim misses."""
    m = np.zeros(BODY[::-1], bool)
    c = int(round(cx))
    m[6:10, c - 1:c + 2] = True                           # head
    m[10:22, c - 3:c + 4] = True                          # torso
    m[22:36, c - 3:c - 1] = True                          # legs
    m[22:36, c + 2:c + 4] = True
    if arm:
        m[11:13, c + 4:c + 4 + arm] = True
    return m ^ ((rng.random(m.shape) < 0.08) & np.roll(m, 1, 1))


def test_fidgeting_person_is_always_hit(ctx):               # claim 2
    rig = RainbowRig(ctx)
    rng = np.random.default_rng(0)
    x, v = 30.0, 0.0
    for k in range(400):                                  # 40 s: a slow random walk, an arm in and out
        v = 0.9 * v + rng.normal(0, 0.15)
        x = float(np.clip(x + v, 10, 54))
        rig.run([person(x, 5 if (k // 7) % 3 == 0 else 0, rng)])
    assert len(rig.hits) >= 7 and not rig.misses


def test_leaving_fades_then_clears(ctx):
    rig = RainbowRig(ctx)
    rig.run(standing(45))
    assert rig.live_splats(0).size
    rig.run([EMPTY] * 9)                                  # coasting, then lost: presence falls
    assert rig.presence(0) < 1.0
    rig.run([EMPTY] * 20)                                 # gone
    assert rig.person_id(0) == 0 and rig.live_splats(0).size == 0


def test_new_person_in_a_reused_slot_starts_clean(ctx):
    rig = RainbowRig(ctx)
    rig.run(standing(45))
    assert rig.live_splats(0).size
    rig.run([EMPTY] * 30)
    rig.run(standing(5))                                  # someone new
    assert rig.person_id(0) == 2 and rig.live_splats(0).size == 0


# ── Claims 2 and 4: walking, and dodging ──────────────────────────────────────

def dodge(rig):
    """Walk right at 1 px per camera frame until a poop drops, then back left at 2 px until it lands.

    The way back goes on out of the frame: the Body is narrower than the walk, and a walker who stopped
    at its edge would stand still under a homing poop for seconds and be hit.
    """
    x = 4
    for _ in range(45):
        x += 1
        rig.run([rect(x, 8, x + 10, 36)])
        if rig.falling():
            break
    else:
        pytest.fail("nothing dropped")
    for _ in range(int(LONGEST_FALL_S * 10) + 15):        # a miss falls all the way to the floor
        x -= 2
        rig.run([rect(x, 8, x + 10, 36)])
        if not rig.falling():
            break


def test_steady_walker_is_hit(ctx):
    rig = RainbowRig(ctx)
    x, v = 4, 1
    for _ in range(120):
        x += v
        if x > 50 or x < 4:
            v = -v
        rig.run([rect(x, 8, x + 10, 36)])
    assert rig.hits


# ── Claims 1 to 4: the picture ────────────────────────────────────────────────

BIG = (320, 180)
PAPER = np.array((246, 241, 228))


def colourful(img) -> np.ndarray:
    """Saturated pixels: splat colours, not paper, ink or warm white."""
    px = img[..., :3].astype(int)
    return (px.max(axis=-1) - px.min(axis=-1)) > 90


def test_splats_drawn_only_on_the_silhouette(ctx):
    rig = RainbowRig(ctx, BIG)
    rig.run(standing(60))
    assert rig.live_splats(0).size
    img = rig.image()
    sat = colourful(img)
    # The body rect(27, 8, 37, 36) in BIG pixels (row 0 = bottom).
    c0, c1 = int(27 / 64 * BIG[0]), int(37 / 64 * BIG[0])
    r0, r1 = int((1 - 36 / 40) * BIG[1]), int((1 - 8 / 40) * BIG[1])
    on = sat[r0:r1, c0:c1].sum()
    assert on > 20
    beside = sat[r0:r1 - 30, c1 + 3:c1 + 40].sum() + sat[r0:r1 - 30, c0 - 40:c0 - 3].sum()
    assert beside == 0                                    # no splat colour off the body


def test_empty_room_is_paper_and_clouds(ctx):
    rig = RainbowRig(ctx, BIG)
    rig.run([EMPTY] * 10)
    img = rig.image()
    low = img[:int(BIG[1] * 0.6)]                         # below the clouds: plain paper
    assert (np.abs(low[..., :3].astype(int) - PAPER).max(axis=-1) < 6).all()
    assert colourful(img).sum() == 0                      # nothing in the sky


def test_falling_poop_is_drawn(ctx):
    rig = RainbowRig(ctx, BIG)
    for k in range(60):
        rig.run(flickering(1, seed=k))                    # a fresh flicker each camera frame
        if rig.falling() and rig.fall_age(0) > 0.4:
            break
    assert rig.falling()
    u, v = rig.poop_xy(0)
    r, c = int(v * BIG[1]), int(u * BIG[0])
    assert colourful(rig.image()[r - 10:r + 10, max(c - 12, 0):c + 12]).sum() > 10


def test_ground_puddle_is_drawn_at_the_feet(ctx):
    rig = RainbowRig(ctx, BIG)
    dodge(rig)
    assert rig.misses and not rig.hits                    # reversing after the release dodges ...
    rig.run([EMPTY] * 5)                                  # past the splat-in
    x, y = rig.puddle_xy()
    r, c = int(y * BIG[1]), int(x * BIG[0])
    assert colourful(rig.image()[max(r - 8, 0):r + 8, max(c - 20, 0):c + 20]).sum() > 10


# ── Claims 5 and 6: stalls, and other GPUs ────────────────────────────────────

def test_a_long_stall_leaves_the_scene_sane(ctx):
    rig = RainbowRig(ctx)
    rig.run(standing(45))
    rig.r.render(200.0, (0, 0, 0, 0))                     # one huge dt
    rig.run(standing(3))
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run([EMPTY] * 30)                                 # long enough for the tracker (on its own clock) to drop them
    assert np.isfinite(rig.b()).all()
    assert rig.person_id(0) == 0 and not rig.falling() and rig.live_splats(0).size == 0


def test_buffer_b_draws_no_random_number_from_the_sin_hash():
    # hash11() returns unrelated values on different GPUs (#214), and CI runs only one renderer.
    assert "hash11" not in (SETUP / "buffer_b.glsl").read_text()
