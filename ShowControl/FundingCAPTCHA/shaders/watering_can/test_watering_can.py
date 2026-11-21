"""What a visitor sees in the watering_can Setup (shaders/watering_can/).

The Setup's promises. Every test below checks one of them, and says which.

1. Empty room: paper, backdrop, static grit, and a sun peeking from the corner with no rays.
   A bare silhouette is never drawn.
2. Stand still and a plant grows up you from the feet, filling your silhouette in about GROW_S.
   Flowers start pale and low, and ripen bold and high.
3. Fidgeting is not walking: camera flicker, arm waving and weight shifts lose no growth.
   Vines follow a moving arm, and the bloom does not shimmer.
4. Walking rewinds growth gradually, sideways or toward the camera, and stopping resumes it.
   A walker leaves footprint plants that grow, then rewind away.
5. Each person has their own garden: a neighbour walking, touching or passing costs a still person
   nothing. A newcomer starts bare. People who merge and then split both keep the growth.
6. Leaving: plants rewind without popping. Dropped camera frames or backing away do not pop the tree.
   Coming back to your spot soon gets your garden back.
7. The sun grows inked rays as the room blooms, and loses them when it empties.
8. Frame rate does not change the result, and a long stall leaves the picture sane.

Tests assert the picture, or a person's growth level read through WateringRig. None asserts how a
buffer stores its state. Levels are compared with each other or with an undisturbed person, never
with a Python copy of the shader's growth curve.

Records come from the real BodyBlobs tracker run on synthetic masks with a fake clock (camera 10 Hz,
render at DT), so record noise is realistic. GL tests need a headless context and skip without one.
"""
from __future__ import annotations

from functools import partial
from pathlib import Path

import numpy as np
import pytest

from shader_test_rig import BLOBS, DT, Rig, glsl_consts
from shader_test_rig import rect as body_rect

SETUP = Path(__file__).parent
K = glsl_consts(SETUP)
SIZE  = (128, 72)                         # render
BODY  = (64, 48)                          # camera ROI (w, h)
LEAVE_S, GROW_S, SUN_EASE_S = K["LEAVE_S"], K["GROW_S"], K["SUN_EASE_S"]
COAST_S = 0.8                             # BlobConfig max_miss_frames at 10 Hz: missing → lost
# Walks start at x=16 so 30 steps never reach walking()'s bounce at 48: a walker who turns
# back crosses their own last spot, and that stretch (~0.7 s) rightly isn't a step.
WALK_X = 16

rect = partial(body_rect, body=BODY)
EMPTY = rect(0, 0, 0, 0)


class WateringRig(Rig):
    """The one place in this file that knows Buffer C's layout (see common.glsl)."""

    def __init__(self, ctx, size=SIZE, dt=DT):
        super().__init__(ctx, SETUP, size, dt=dt)

    def growth(self, k) -> float:
        """Slot k's growth: 0 bare … 1 full bloom."""
        return float(self.buf("buffer_c")[0, k, 1])

    def live_slots(self):
        c = self.buf("buffer_c")
        return [k for k in range(8) if c[0, k, 0] != 0]

    def slot_near(self, x_px, confirmed=False):
        """The live slot whose base is nearest Body column x_px. confirmed: only confirmed tracks count
        (a coasting or lost record of the same person, left over from a merge or split, doesn't)."""
        c = self.buf("buffer_c")
        ks = [k for k in self.live_slots() if not confirmed or c[1, k, 3] == 2]
        assert ks, "nobody there"
        return min(ks, key=lambda k: abs(c[1, k, 0] - x_px / BODY[0]))

    def growth_near(self, x_px) -> float:
        """Growth of the confirmed person nearest Body column x_px."""
        return self.growth(self.slot_near(x_px, confirmed=True))

    def sun_level(self) -> float:
        """How far the sun's rays are out: 0 none … 1 full."""
        return float(self.buf("buffer_c")[3, 0, 0])

    def footprints(self) -> int:
        """How many footprint plants are alive."""
        c = self.buf("buffer_c")
        return sum(c[3, 1 + f, 2] < K["FOOT_LIFE"] for f in range(K["FOOTPRINTS"]))


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


def both(a, b):
    """Two people at once: the camera frames of two mask lists, overlaid."""
    return [x | y for x, y in zip(a, b)]


def rising(levels):
    """True if the levels never fall."""
    return all(b >= a - 1e-3 for a, b in zip(levels, levels[1:]))


@pytest.fixture(scope="module")
def still_10s(ctx):
    """An undisturbed person's growth after standing still for 10 s: what the fidgeters are compared with."""
    rig = WateringRig(ctx)
    rig.run([person()] * 100)
    g = rig.growth(0)
    rig.release()
    return g


@pytest.fixture(scope="module")
def third_grown(ctx):
    """Camera frames a still person takes to be about a third grown."""
    rig = WateringRig(ctx)
    n = 0
    while rig.growth(0) < 0.3:
        rig.run([person()])
        n += 1
        assert n < 10 * GROW_S, "never got a third grown"
    rig.release()
    return n


# ── Claim 2: stand still and a plant grows up you (growth level) ──────────────

def test_planted_flickering_person_blooms_in_about_grow_s(ctx):          # claims 2, 3
    rig = WateringRig(ctx)
    levels = []
    for _ in range(round(GROW_S) + 2):
        rig.run(flickering(10))
        levels.append(rig.growth(0))
    assert levels[round(GROW_S / 2) - 1] < 0.9, levels   # not long before GROW_S ...
    assert levels[-1] > 0.98, levels                     # ... and in full bloom just after it
    assert rising(levels), levels                        # never losing any on the way
    assert rig.footprints() == 0                         # flicker is not walking
    rig.release()


# ── Claim 3: fidgeting is not walking (growth level) ──────────────────────────

def test_arm_waving_does_not_rewind(ctx, still_10s):
    rig = WateringRig(ctx)
    rig.run([person(arm=("down", "out", "up")[k // 5 % 3]) for k in range(100)])
    assert abs(rig.growth(0) - still_10s) < 0.06, (rig.growth(0), still_10s)
    assert rig.footprints() == 0
    rig.release()


def test_weight_shift_does_not_rewind(ctx, still_10s):
    rig = WateringRig(ctx)
    rig.run([person(lift=(None, "L", None, "R")[k // 3 % 4]) for k in range(100)])
    assert abs(rig.growth(0) - still_10s) < 0.06, (rig.growth(0), still_10s)
    rig.release()


# ── Claim 4: walking rewinds growth (growth level) ────────────────────────────

def test_stepping_toward_camera_rewinds(ctx):
    # Toward the camera for 1.1 s, then back away for 1.1 s. Detecting a step takes ~2 px of
    # movement plus easing (~0.4 s, still growing meanwhile), so 1.1 s alone nets very little.
    rig = WateringRig(ctx)
    rig.run([person(feet=36)] * 100)
    g0 = rig.growth(0)
    assert g0 > 0.4
    rig.run(stepping_toward(11) + [person(feet=46 - k) for k in range(11)])
    assert rig.growth(0) < g0 - 0.03, (g0, rig.growth(0))
    rig.release()


def test_walking_sideways_rewinds_then_growth_resumes(ctx):
    rig = WateringRig(ctx)
    rig.run([person(x=WALK_X)] * 100)
    g0 = rig.growth(0)
    walk = walking(30, x=WALK_X)
    rig.run(walk)                                    # 3 s of walking
    g1 = rig.growth(0)
    assert g1 < g0 - 0.05, (g0, g1)                  # rewinds ...
    assert g1 > 0.5 * g0, (g0, g1)                   # ... gradually: not a reset
    levels = []
    for _ in range(3):
        rig.run([walk[-1]] * 10)
        levels.append(rig.growth(0))
    # Walking lasts a moment past the last step, so the first second may still rewind a little;
    # then it grows from where the rewind got to, not from 0.
    assert all(g >= g1 - 0.05 for g in levels), (g1, levels)
    assert levels[-1] > levels[0], (g1, levels)
    rig.release()


def test_feet_off_frame(ctx, still_10s):
    # Standing so close that the frame cuts the feet off: growing and rewinding still work.
    rig = WateringRig(ctx)
    for _ in range(10):
        rig.run(flickering(10, x=WALK_X, feet=48))
    g0 = rig.growth(0)
    assert abs(g0 - still_10s) < 0.06, (g0, still_10s)
    rig.run(walking(30, x=WALK_X, feet=48))
    assert rig.growth(0) < g0 - 0.05, (g0, rig.growth(0))
    rig.release()


# ── Claim 5: each person has their own garden (growth level) ──────────────────

def test_neighbour_walking_does_not_rewind_still_person(ctx, still_10s):
    rig = WateringRig(ctx)
    rig.run(both([person(x=46)] * 100, walking(100, x=4, bounce=(4, 20))))
    assert len(rig.live_slots()) == 2
    still, walker = rig.slot_near(52), rig.slot_near(4)
    assert still != walker
    assert abs(rig.growth(still) - still_10s) < 0.06, (rig.growth(still), still_10s)
    assert rig.growth(walker) < 0.1, rig.growth(walker)
    rig.release()


def test_merge_then_split_both_inherit(ctx):
    # A has grown far more than B, so B starting from the merged level is told apart from B keeping its own.
    rig = WateringRig(ctx)
    rig.run([person(x=4)] * 150)                                       # A alone, 15 s
    rig.run(both([person(x=4)] * 30, [person(x=40)] * 30))             # B arrives, 3 s
    assert len(rig.live_slots()) == 2
    ga, gb = rig.growth(rig.slot_near(10)), rig.growth(rig.slot_near(46))
    assert ga > 0.8 and gb < 0.45, (ga, gb)
    # B slides left into A until their masks overlap (one blob), and they stand merged for 3 s
    rig.run(both([person(x=4)] * 26, [person(x=max(40 - k, 14)) for k in range(26)]))
    rig.run(both([person(x=4)] * 30, [person(x=14)] * 30))
    merged = max(rig.growth(k) for k in rig.live_slots())
    assert merged > ga
    # then B jumps back out: two blobs again
    rig.run(both([person(x=4)] * 8, [person(x=22)] * 8))
    live = rig.live_slots()
    assert len(live) == 2, live
    for k in live:
        assert rig.growth(k) >= merged - 0.05, (merged, gb, [rig.growth(j) for j in live])
    rig.release()


@pytest.mark.parametrize("contact", ["every 0.3 s", "every 1 s", "50% of frames"])
def test_touching_still_people_keep_growing(ctx, contact):
    # Two people planted side by side with a 1-px gap. The tracker merges them into one blob whenever the
    # gap is bridged; neither moves, so neither may lose growth to the box swelling and shrinking.
    # Compared with the same two people over the same time, never bridged.
    rng = np.random.default_rng(1)
    a, b = person(x=10), person(x=23)
    rig = WateringRig(ctx)
    rig.run([a | b] * 60)
    before = rig.growth_near(16), rig.growth_near(29)
    start = rig.snapshot()
    rig.run([a | b] * 108)
    apart = rig.growth_near(16), rig.growth_near(29)
    rig.restore(start)
    frames = []
    for k in range(100):
        m = a | b
        if {"every 0.3 s": k // 3 % 2 == 0, "every 1 s": k // 10 % 2 == 0, "50% of frames": rng.random() < 0.5}[contact]:
            m[:, 22] = True                                   # bridged: one blob
        frames.append(m)
    rig.run(frames + [a | b] * 8)
    touching = rig.growth_near(16), rig.growth_near(29)
    for g0, want, got in zip(before, apart, touching):
        assert got - g0 > 0.85 * (want - g0), (contact, before, apart, touching)
    rig.release()


def test_passer_by_costs_nothing_once_past(ctx):
    # Someone walks across in front of planted A (merging with them on the way). Merged, they share a level;
    # once the passer-by is clear, A loses nothing more and is growing again straight away.
    feet = 44
    rig = WateringRig(ctx)
    a = person(x=26)                                          # spans Body columns 26..38
    rig.run([a] * 100)
    xs = list(range(-12, 64, 2))                              # 2 px per camera frame: a brisk walk
    clear = xs.index(40)                                      # the passer-by's left edge 2 px past A's right edge
    rig.run([a | person(x=x, feet=feet) for x in xs[:clear]])
    levels = []
    for m in [a | person(x=x, feet=feet) for x in xs[clear:]] + [a] * 20:
        rig.run([m])
        levels.append(rig.growth_near(32))
    assert rising(levels), str(np.round(levels, 3))
    assert levels[10] > levels[0], str(np.round(levels, 3))   # already growing within a second
    rig.release()


def test_merged_neighbour_stepping_nearer_does_not_rewind_a_still_person(ctx):
    # B stands touching planted A, nearer the camera, then steps nearer still. The tracker sees one blob whose
    # bottom is B's feet; B's step must not be read as A's. Compared with B standing where they were.
    rig = WateringRig(ctx)
    a = person(x=26)
    rig.run([a] * 100)
    rig.run([a | person(x=38, feet=45)] * 20)                 # touching, so one blob
    g0, start = rig.growth_near(32), rig.snapshot()
    rig.run([a | person(x=38, feet=45)] * 18)
    want = rig.growth_near(32) - g0
    rig.restore(start)
    levels = [g0]
    for f in [46, 47, 48] + [48] * 15:
        rig.run([a | person(x=38, feet=f)])
        levels.append(rig.growth_near(32))
    assert rising(levels), str(np.round(levels, 3))
    assert levels[-1] - g0 > 0.85 * want, (want, levels)
    rig.release()


def detached_arm(x=26, feet=44):
    """person(arm="out") with a 1-px gap between the outstretched arm and the torso: two blobs."""
    m = person(x=x, feet=feet, arm="out")
    m[:, x + 10] = False
    return m


def test_split_off_part_inherits(ctx):
    # A camera dropout cuts an arm off its body. The arm becomes a second "person"; it must not show up bare.
    from body_blobs import find_blobs
    arm = detached_arm()
    sizes = sorted(d.pixels for d in find_blobs(arm, np.zeros(arm.shape), BLOBS.min_blob_pixels))
    assert len(sizes) == 2 and sizes[0] >= BLOBS.min_blob_pixels, sizes   # really a second blob
    rig = WateringRig(ctx)
    rig.run([person(arm="out")] * 100)
    assert rig.growth(0) > 0.4
    rig.run([arm] * 20)
    live = rig.live_slots()
    assert len(live) == 2, live
    new = [k for k in live if k != 0][0]
    assert rig.growth(new) >= rig.growth(0) - 0.05, (rig.growth(0), rig.growth(new))
    rig.release()


def test_newcomer_beside_bloomed_person_starts_bare(ctx):
    rig = WateringRig(ctx)
    rig.run([person(x=4)] * 200)                   # A in full bloom
    assert rig.growth(0) > 0.9
    rig.run(both([person(x=4)] * 10, [person(x=20)] * 10))   # B appears with a 4 px gap, for 1 s
    assert len(rig.live_slots()) == 2
    a, b = rig.slot_near(10), rig.slot_near(26)
    assert a != b
    assert rig.growth(a) > 0.9
    assert rig.growth(b) < 0.5 * rig.growth(a), (rig.growth(a), rig.growth(b))   # its own second of growth, nothing inherited
    rig.release()


# ── Claim 6: leaving and coming back (growth level) ───────────────────────────

def test_returning_to_your_spot_soon_gets_the_garden_back(ctx):
    rig = WateringRig(ctx)
    rig.run([person(x=4)] * 100)
    g = rig.growth(0)
    assert g > 0.4
    rig.run([EMPTY] * 19)                          # gone for 1.9 s: the tracker has dropped them
    assert rig.live_slots() == []
    rig.run([person(x=4)] * 3)
    assert abs(rig.growth(rig.slot_near(10)) - g) < 0.05, (g, rig.growth(rig.slot_near(10)))
    rig.release()


def test_someone_new_elsewhere_does_not_get_the_leavers_garden(ctx):
    rig = WateringRig(ctx)
    rig.run([person(x=4)] * 100)
    g = rig.growth(0)
    assert g > 0.4
    rig.run([EMPTY] * 10)                          # A has just left
    rig.run([person(x=46)] * 10)                   # B arrives across the room, for 1 s
    b = rig.growth(rig.slot_near(52))
    assert b < 0.5 * g, (g, b)                     # its own second of growth, nothing inherited
    rig.release()


# ── Claim 7: the sun follows the room's bloom (level; drawn in the Image tests below) ──

def test_sun_tracks_growth(ctx):
    per_cam = 3
    rig = WateringRig(ctx, dt=1 / 30)
    rig.run([EMPTY] * 30, frames_per_camera=per_cam)
    assert rig.sun_level() < 0.02
    rig.run([person()] * 300, frames_per_camera=per_cam)   # full bloom from ~21 s, then 6 SUN_EASE_S to catch up
    assert rig.growth(0) == 1.0 and rig.sun_level() > 0.99, rig.sun_level()
    rig.run([EMPTY] * int(round((COAST_S + LEAVE_S + 3 * SUN_EASE_S) * 10)), frames_per_camera=per_cam)
    assert rig.sun_level() < 0.05, rig.sun_level()
    rig.release()


# ── Claim 8: frame rate and stalls ────────────────────────────────────────────

def test_growth_independent_of_render_rate(ctx):
    a = WateringRig(ctx, dt=1 / 30)
    a.run([person()] * 150, frames_per_camera=3)              # 15 s
    b = WateringRig(ctx, dt=1 / 240)
    b.run([person()] * 150, frames_per_camera=24)
    assert 0.5 < a.growth(0) < 1.0, a.growth(0)               # mid-growth, so a difference would show
    assert abs(a.growth(0) - b.growth(0)) < 0.02, (a.growth(0), b.growth(0))
    a.release(); b.release()


def test_a_long_stall_leaves_an_empty_room_empty(ctx):
    rig = WateringRig(ctx)
    rig.run([person()] * 10)
    rig.r.render(200.0, (0, 0, 0, 0))              # one huge dt
    rig.run([EMPTY] * 3)
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run([EMPTY] * 30)                          # long enough for the tracker (on its own clock) to drop them
    for name in ("buffer_b", "buffer_c"):
        assert np.isfinite(rig.buf(name)).all(), name
    assert rig.live_slots() == [] and rig.footprints() == 0
    assert drawn(rig.image()).sum() == 0
    rig.release()


# ── The picture: helpers for the Image tests ──────────────────────────────────

PAPER = np.round(np.array(K["PAPER"]) * 255).astype(int)
FLOWER_R, REACH = K["FLOWER_R"], K["REACH"]
TWIG_REACH = (1 + K["FORK_LEN"]) * K["TWIG_LEN"] + K["SPRIG_LEN"]   # a forked twig and its sprig, from its node
SUN_R, RAY_LEN = K["SUN_R"], K["RAY_LEN"]
FLOWER_RGB = np.array([[251, 233, 160], [113, 154, 173], [232, 134, 47]])   # pale yellow, light blue, orange
IMG = (256, 144)                                   # image tests: big enough that petals have pure-colour pixels


def screen_xy(size):
    """Pixel centres in screen heights, (h, w) each, row 0 = bottom."""
    w, h = size
    ys, xs = np.mgrid[0:h, 0:w]
    return (xs + 0.5) / h, (ys + 0.5) / h


def sun_offset(size):
    """(dx, dy) of every pixel from the sun's centre, which is SUN_PEEK × SUN_R inside the top-right corner."""
    x, y = screen_xy(size)
    peek = K["SUN_PEEK"] * SUN_R
    return x - (size[0] / size[1] - peek), y - (1 - peek)


def sun_region(size):
    """Pixels the sun may draw on: its outline and as far as its rays reach."""
    return np.hypot(*sun_offset(size)) <= K["SUN_REACH"]


def off_paper(img):
    """Pixels differing from flat paper by > 12 in any channel."""
    return (np.abs(img[..., :3].astype(int) - PAPER) > 12).any(axis=-1)


_EMPTY_SCENES = {}                                 # render size → the Image of an empty room


@pytest.fixture(autouse=True, scope="module")
def _empty_scene_ctx(ctx):
    _EMPTY_SCENES["ctx"] = ctx
    yield
    _EMPTY_SCENES.clear()


def empty_scene(size):
    """The Image with nobody there: paper and the backdrop (which is static), as int RGB. Rendered once per size."""
    if size not in _EMPTY_SCENES:
        rig = WateringRig(_EMPTY_SCENES["ctx"], size=size)
        rig.run([EMPTY])
        _EMPTY_SCENES[size] = rig.image()[..., :3].astype(int)
        rig.release()
    return _EMPTY_SCENES[size]


def drawn(img):
    """Pixels the plants changed: differing from the empty scene by > 12 in any channel, outside the sun's corner."""
    size = (img.shape[1], img.shape[0])
    return (np.abs(img[..., :3].astype(int) - empty_scene(size)) > 12).any(axis=-1) & ~sun_region(size)


def on_screen(mask, size):
    """A Body mask (row 0 = top) as screen pixels (row 0 = bottom): the camera view is stretched to the screen."""
    w, h = size
    ys, xs = np.mgrid[0:h, 0:w]
    col = ((xs + 0.5) / w * mask.shape[1]).astype(int)
    row = ((1 - (ys + 0.5) / h) * mask.shape[0]).astype(int)
    return mask[row, col]


def rows(r0, r1):
    """Body rows r0..r1 (row 0 = top) as a Body mask."""
    return rect(0, r0, BODY[0], r1)


def saturation(px):
    """HSV saturation of uint8 RGB pixels (n, 3)."""
    px = px.astype(float)
    mx, mn = px.max(axis=-1), px.min(axis=-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0.0)


def off_ink_line(img):
    """Each pixel's RGB distance from the line through ink and paper: 0 for ink drawn on the paper, at any coverage.
    The paper is tinted, so "not grey" won't tell a flower from a line's antialiased edge; this does."""
    ink = 255 * np.array(K["INK"])
    axis = (PAPER - ink) / np.linalg.norm(PAPER - ink)
    v = img[..., :3] - ink
    return np.linalg.norm(v - (v @ axis)[..., None] * axis, axis=-1)


def flower_pixels(img):
    """Pixels within 30 per channel of a flower colour (and not ink on paper, which passes near the light blue)."""
    rgb = img[..., :3].astype(int)
    return (np.abs(rgb[..., None, :] - FLOWER_RGB).max(axis=-1) <= 30).any(axis=-1) & (off_ink_line(img) > 6)


def grown_rig(ctx, frames, size=IMG, **kw):
    rig = WateringRig(ctx, size=size)
    rig.run([person(**kw)] * frames)
    return rig


@pytest.fixture(scope="module")
def _shared_rigs(ctx):
    rigs = {}                                      # (frames, size, kw) -> (rig, snapshot right after growing)
    yield rigs
    for rig, _ in rigs.values():
        rig.release()


@pytest.fixture
def shared_rig(ctx, _shared_rigs):
    """grown_rig(), but each distinct growth is simulated once per module and restored for every test that asks.

    Growing to full bloom is ~660 frames; on software GL that dominates this file. The rig is restored before it is
    handed out, so a test may run() it further: the next test still gets it as freshly grown. Don't release() it.
    """
    def get(frames, size=IMG, **kw):
        key = (frames, size, tuple(sorted(kw.items())))
        if key not in _shared_rigs:
            rig = grown_rig(ctx, frames, size, **kw)
            _shared_rigs[key] = rig, rig.snapshot()
        rig, snap = _shared_rigs[key]
        rig.restore(snap)
        return rig
    return get


# ── Claims 1 and 2: nothing until you stand still, then a plant from the feet up (Image) ──

def test_nothing_drawn_before_growth(ctx):         # a bare silhouette is never drawn
    rig = grown_rig(ctx, 4)
    assert 0 < rig.growth(0) < 0.03, rig.growth(0)             # growing, barely
    assert drawn(rig.image()).mean() < 0.002
    rig.release()


def test_bloom_fills_the_silhouette(shared_rig):
    rig = shared_rig(220)
    assert rig.growth(0) > 0.99
    d, fig = drawn(rig.image()), on_screen(person(), IMG)
    assert d[fig].mean() >= 0.7, d[fig].mean()
    # Overhang is twigs, sprigs and flowers only: within a twig's or a daisy's reach (plus sway and a pixel
    # of antialiasing) of the figure.
    x, y = screen_xy(IMG)
    fx, fy = x[fig], y[fig]
    out = d & ~fig
    far = [np.hypot(fx - x[r, c], fy - y[r, c]).min() for r, c in np.argwhere(out)]
    assert out.sum() > 0 and max(far) <= max(TWIG_REACH, REACH) + K["SWAY_AMP"] + 1.5 / IMG[1], max(far)


def test_growth_climbs_from_the_feet(shared_rig, third_grown):
    rig = shared_rig(third_grown)
    assert abs(rig.growth(0) - 0.3) < 0.05, rig.growth(0)
    d, fig = drawn(rig.image()), person()
    top, bottom = on_screen(fig & rows(6, 19), IMG), on_screen(fig & rows(31, 44), IMG)   # thirds of rows 6..44
    assert d[bottom].mean() > 0.25, d[bottom].mean()       # a sparse tree, but clearly there ...
    assert d[top].mean() < 0.05, d[top].mean()             # ... and the top still bare


def coloured(img):
    """Flower pixels: drawn and not ink on paper. The wood and leaves are ink on paper; only flowers carry colour."""
    return drawn(img) & (off_ink_line(img) > 6)


def test_colour_ripens_flowers_pale_low_then_bold_high(shared_rig, third_grown):
    fig = on_screen(person(), IMG)
    _, y = screen_xy(IMG)
    top, bottom = y[fig].max(), y[fig].min()
    low = y < bottom + (top - bottom) / 3                  # the figure's lower and upper thirds
    high = y > top - (top - bottom) / 3
    early = shared_rig(third_grown)
    assert abs(early.growth(0) - 0.3) < 0.05, early.growth(0)
    img = early.image()
    colour_early = off_ink_line(img)[drawn(img)].mean()   # not HSV saturation: the paper's own tint would count
    c = coloured(img)
    assert c[low].sum() > 20, c[low].sum()                  # flowers already open, low on the body ...
    assert (flower_pixels(img) & drawn(img)).sum() < 5      # ... and pale: hardly a pixel in full colour yet
    full = shared_rig(220)
    assert full.growth(0) > 0.99, full.growth(0)
    img = full.image()
    colour_full = off_ink_line(img)[drawn(img)].mean()
    assert colour_full > 1.5 * colour_early, (colour_early, colour_full)   # rises clearly: the palette is pastel, the wood ink
    bold = flower_pixels(img) & drawn(img)
    assert bold.sum() > 30                                  # bold flowers at full bloom (only the outer ones: few at this size)
    assert bold[high].sum() > 2 * bold[low].sum(), (bold[high].sum(), bold[low].sum())   # and mostly high up


# ── Claims 2 and 3: arms bloom too, and the bloom holds still (Image) ─────────

def test_vines_follow_the_arm(ctx):
    rig = grown_rig(ctx, 220, arm="up")
    # The raised arm above the head (arm-only columns, clear of the shoulders' flowers).
    arm = on_screen(rect(36, 0, 38, 8), IMG)
    assert drawn(rig.image())[arm].mean() > 0.5, drawn(rig.image())[arm].mean()
    # 0.6 s: the rewinding tip clears in a few camera frames; twigs point up, so they outlast it by a frame or two
    rig.run([person(arm="down")] * 6)
    assert drawn(rig.image())[arm].mean() < 0.1, drawn(rig.image())[arm].mean()
    rig.release()


def test_horizontal_arm_blooms(ctx):                 # a thin run grows to full bloom too: no bare stencil hole
    thick = 4                                        # Body rows of a 96-row Body: 0.042 screen heights (thicker arms
                                                     # only bloom more)
    # A finer Body than BODY, so the arm can be thinner than a flower and still be body after B's blur.
    m = np.kron(person(arm="out"), np.ones((2, 2), dtype=bool))   # 128 x 96; the arm is rows 26-31
    m[26 + thick:32, 72:] = False                                  # thin it from below
    rig = WateringRig(ctx, size=IMG)
    rig.run([m] * 220)
    assert rig.growth(0) > 0.99
    arm = rect(0, 0, 0, 0).repeat(2, 0).repeat(2, 1)
    arm[26:26 + thick, 76:100] = True                              # the outstretched arm, clear of the torso
    d = drawn(rig.image())[on_screen(arm, IMG)].mean()
    assert d >= 0.5, d
    rig.release()


def test_bloom_is_stable_under_flicker(ctx):
    rig = WateringRig(ctx, size=IMG)
    rig.run(flickering(220))
    fig = on_screen(person(), IMG)
    prev, deltas = rig.image()[..., :3].astype(int), []
    for k in range(10):
        rig.run(flickering(1, seed=100 + k))
        img = rig.image()[..., :3].astype(int)
        deltas.append(np.abs(img - prev)[fig].mean())
        prev = img
    assert max(deltas) < 6, deltas
    rig.release()


# ── Claim 6: leaving, dropouts and backing away (Image) ───────────────────────

def test_lost_person_plants_rewind_without_popping(shared_rig):
    rig = shared_rig(220)
    n0, counts = drawn(rig.image()).sum(), []
    for _ in range(40):
        rig.run([EMPTY])
        counts.append(drawn(rig.image()).sum())
    end = int(round((1.5 + LEAVE_S + 0.5) * 10))
    assert counts[end - 1] == 0, counts
    # No popping: no camera frame loses more than 30% of the previous count. A steady fade over
    # LEAVE_S loses ~5% of the bloom a frame, so near its end that is more than 30% of what's
    # left: drops of up to 10% of the full bloom (twice the steady rate) are allowed too.
    prev = [n0] + counts[:-1]
    assert all(p - c <= max(0.3 * p, 0.1 * n0) for p, c in zip(prev, counts)), (n0, counts)
    assert counts[4] > 0.5 * n0, (n0, counts)       # it rewinds: still mostly there half a second in


@pytest.mark.parametrize("missing", [2, 5])         # camera frames: shorter than the tracker's coast
def test_dropped_camera_frames_dont_pop_the_tree(shared_rig, missing):
    # The body comes back under its held shape: the tree stays, rather than being wiped as presence eases
    # back up and rebuilt cell by cell from the feet (a whole tree in ~1.5 s: it popped out and back in).
    rig = shared_rig(220)
    n0, counts = drawn(rig.image()).sum(), []
    for m in [EMPTY] * missing + [person()] * 15:
        rig.run([m])
        counts.append(drawn(rig.image()).sum())
    assert min(counts) > 0.8 * n0, (n0, counts)


def test_backing_away_keeps_the_tree(shared_rig):
    # Backing away lifts the feet up the image. The root used to ease up after them over a second, lag more than
    # TREE_ROOT_BAND below every cell, and leave the whole tree with no way back to it: it un-grew to nothing,
    # then grew back in once the root caught up.
    rig = shared_rig(220)
    n0, counts = drawn(rig.image()).sum(), []
    for m in [person(feet=44 - k) for k in range(1, 9)] + [person(feet=36)] * 30:
        rig.run([m])
        counts.append(drawn(rig.image()).sum())
    assert min(counts) > 0.6 * n0, (n0, counts)


# ── Claim 4: a walker leaves footprint plants (Image) ─────────────────────────

FOOT_LIFE = K["FOOT_LIFE"]


def test_walker_leaves_footprints_that_grow_then_rewind_away(ctx):
    rig = WateringRig(ctx, size=IMG)
    rig.run([person(x=WALK_X)] * 30)
    rig.run(walking(30, x=WALK_X))                  # 30 px right in 3 s
    feet = 1 - 44 / BODY[1]                         # the feet's row, UV y
    assert rig.footprints() >= 4, rig.footprints()
    rig.run([EMPTY] * 15)                           # the walker leaves; their own plants rewind away
    assert rig.footprints()
    # Off the body, where the walker passed: footprint plants, standing up off the floor at the feet's row.
    x, y = screen_xy(IMG)
    floor = (y > feet - 0.03) & (y < feet + 0.12)
    n0 = (drawn(rig.image()) & floor).sum()
    assert n0 > 200, n0
    counts = []
    for _ in range(int(FOOT_LIFE * 10)):            # then they rewind away, without popping
        rig.run([EMPTY])
        counts.append(drawn(rig.image()).sum())
    assert rig.footprints() == 0 and counts[-1] == 0, counts
    prev = [n0] + counts[:-1]
    assert all(p - c <= max(0.3 * p, 0.1 * n0) for p, c in zip(prev, counts)), (n0, counts)
    rig.release()


# ── Claims 1 and 7: the sun (Image) ───────────────────────────────────────────

SUN_RGB = np.round(np.array(K["SUN_COL"]) * 255).astype(int)


def luma(img):
    return img[..., :3].astype(float) @ np.array([0.299, 0.587, 0.114])


def sunny(img):
    """Pixels within 30 per channel of the sun's yellow."""
    return (np.abs(img[..., :3].astype(int) - SUN_RGB) <= 30).all(axis=-1)


def inky(img):
    """Pixels with ink on them, on the paper or on the sun: darker than both by a margin."""
    return luma(img) < min(PAPER @ [0.299, 0.587, 0.114], SUN_RGB @ [0.299, 0.587, 0.114]) - 25


def sun_patch(img):
    """(inside, rim, shade, ring) masks: pixels well inside the disc, clear of its hatching; the band its outline
    wanders in; the band just inside the rim on the side away from the light, where it's hatched; and the ring
    its rays reach."""
    dx, dy = sun_offset((img.shape[1], img.shape[0]))
    r = np.hypot(dx, dy)
    band = K["SUN_EDGE_WOBBLE"] * SUN_R + K["SUN_INK_W"] + 1.0 / img.shape[0]
    away = -(dx + dy) / np.sqrt(2) / np.maximum(r, 1e-9)
    shade = (r > SUN_R - 0.5 * K["SUN_SHADE_W"] * SUN_R) & (r < SUN_R - band) & (away > 0.8)
    return (r <= (1 - 1.2 * K["SUN_SHADE_W"]) * SUN_R, np.abs(r - SUN_R) <= band, shade,
            (r >= K["SUN_RAY_FROM"] * SUN_R) & (r <= SUN_R + RAY_LEN))


def assert_sun_is_drawn_as_a_flower(img, hatched=True):
    """hatched: check the hatching too. Its lines are as fine as a daisy's, so they need a big render to show."""
    inside, rim, shade, _ = sun_patch(img)
    assert sunny(img)[inside].mean() > 0.98, sunny(img)[inside].mean()          # a flat yellow fill
    assert inky(img)[rim].mean() > 0.15, inky(img)[rim].mean()                   # in an ink outline
    if hatched:
        assert inky(img)[shade].mean() > 0.15, inky(img)[shade].mean()           # hatched away from the light
        assert sunny(img)[shade].mean() > 0.3, sunny(img)[shade].mean()          # lightly: still mostly yellow


def test_sun_is_drawn_as_a_flower_without_rays_when_empty(ctx):
    rig = WateringRig(ctx, size=(1024, 576))
    rig.run([EMPTY] * 30)
    img = rig.image()
    assert_sun_is_drawn_as_a_flower(img)
    assert (sunny(img) & sun_patch(img)[3]).sum() == 0                 # no rays
    rig.release()


def test_sun_grows_inked_rays_with_bloom(shared_rig):
    rig = shared_rig(220)
    img = rig.image()
    assert_sun_is_drawn_as_a_flower(img, hatched=False)
    ring = sun_patch(img)[3]
    assert (sunny(img) & ring).sum() > 0.05 * ring.sum(), ((sunny(img) & ring).sum(), ring.sum())
    assert (inky(img) & ring).sum() > 0.03 * ring.sum(), ((inky(img) & ring).sum(), ring.sum())


def seam_extents(img):
    """Farthest drawn radius from the sun's centre in the two pixel rows of the left-pointing ray that are just above
    and just below atan's branch cut (the ray's axis when it hasn't drifted). 0 where the ray isn't drawn in a row."""
    size = (img.shape[1], img.shape[0])
    dx, dy = sun_offset(size)
    r = np.hypot(dx, dy)
    ray = (dx < 0) & (r > 1.3 * SUN_R) & (r < SUN_R + RAY_LEN + 0.02)
    d = (np.abs(img[..., :3].astype(int) - empty_scene(size)) > 12).any(axis=-1)   # the empty scene has no rays
    row = 1.0 / size[1]
    far = lambda m: r[m].max(initial=0.0)
    return far(ray & d & (dy > 0) & (dy < row)), far(ray & d & (dy <= 0) & (dy > -row))


def test_sun_ray_has_no_seam_at_the_atan_cut(ctx):
    # The ray pointing left lies on atan's branch cut, and the slow drift (one ray width in ~170 s) carries it across.
    # It must stay one ray, not two halves with their own length. Drift is a function of iTime: sample it directly.
    rig = grown_rig(ctx, 220, size=(1024, 576))
    straddled = 0
    for k in range(16):                                      # iTime 0–3.75 s: the ray is within a pixel or two of the cut
        rig.r.time = 0.25 * k
        rig.r.render(1e-4, (0, 0, 0, 0))
        up, down = seam_extents(rig.image())
        if up and down:
            straddled += 1
            assert abs(up - down) < 0.0025, (up, down, rig.r.time)      # 0.0025 = 1.4 px of this render
    assert straddled >= 4, straddled                                      # the ray did sit on the cut
    rig.release()


# ── Claim 1: the paper's grit (Image) ─────────────────────────────────────────

def test_paper_has_sparse_static_ink_grit(ctx):
    # The sky between the far hills and the sun: nothing but paper and its grit. Sparse flecks of ink, not a wash,
    # fainter than the backdrop's lines, and they hold still. Big enough that they're drawn at full strength.
    size = (1024, 576)
    rig = WateringRig(ctx, size=size)
    rig.run([EMPTY] * 3)
    first = rig.image()
    rig.run([EMPTY] * 30)
    img = rig.image()
    _, y = screen_xy(size)
    sky = (y > K["HORIZON_Y"] + K["HORIZON_WOBBLE"] + max(K["HILL_A"][2], K["HILL_B"][2]) + 0.02) & ~sun_region(size)
    flecks = off_paper(img) & sky
    assert 0.005 < flecks[sky].mean() < 0.1, flecks[sky].mean()
    assert (off_ink_line(img)[sky] < 6).all()                          # ink on paper: no colour of its own
    darkest = luma(img)[sky].min()
    assert darkest > PAPER @ [0.299, 0.587, 0.114] * (1 - K["BACKDROP_INK"]), darkest   # fainter than the backdrop
    assert np.array_equal(first[sky], img[sky])                        # static
    rig.release()
