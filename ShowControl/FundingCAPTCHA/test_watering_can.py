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
            body = pack_body(fg, {"x": 0, "y": 0, "w": m.shape[1], "h": m.shape[0]}, SLABS)   # usually BODY
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


def both(a, b):
    """Two people at once: the camera frames of two mask lists, overlaid."""
    return [x | y for x, y in zip(a, b)]


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


# ── Task 2: Garden state (Buffer C) ───────────────────────────────────────────

GROW_S = 20.0                                      # shaders/watering_can/common.glsl
INHERIT_S, SUN_EASE_S = 3.0, 1.5
COAST_S = 0.8                                      # BlobConfig max_miss_frames at 10 Hz: missing → lost
# Walks start at x=16 so 30 steps never reach walking()'s bounce at 48: a walker who turns
# back crosses their own last spot, and that stretch (~0.7 s) rightly isn't a step.
WALK_X = 16


def live_slots(rig):
    return [k for k in range(8) if rig.person(k)[0] != 0]


def slot_near(rig, x_px):
    """The live slot whose base is nearest Body column x_px."""
    return min(live_slots(rig), key=lambda k: abs(rig.base(k)[0] - x_px / BODY[0]))


def test_planted_flickering_person_blooms_in_20s(ctx):          # spec: ~20 s, never loses growth
    rig = Rig(ctx)
    levels = []
    for _ in range(22):
        rig.run(flickering(10))
        levels.append(rig.person(0)[1])
    assert abs(levels[9] - 0.5) < 0.06 and levels[-1] > 0.98, levels
    assert all(b >= a - 1e-3 for a, b in zip(levels, levels[1:])), levels
    rig.release()


def test_arm_waving_does_not_rewind(ctx):
    rig = Rig(ctx)
    rig.run([person(arm=("down", "out", "up")[k // 5 % 3]) for k in range(100)])
    assert abs(rig.person(0)[1] - 0.5) < 0.06, rig.person(0)
    rig.release()


def test_weight_shift_does_not_rewind(ctx):
    rig = Rig(ctx)
    rig.run([person(lift=(None, "L", None, "R")[k // 3 % 4]) for k in range(100)])
    assert abs(rig.person(0)[1] - 0.5) < 0.06, rig.person(0)
    rig.release()


def test_walking_sideways_rewinds(ctx):
    rig = Rig(ctx)
    rig.run([person(x=WALK_X)] * 100)
    g0 = rig.person(0)[1]
    rig.run(walking(30, x=WALK_X))
    assert abs((g0 - rig.person(0)[1]) - 3.0 / 20.0) < 0.05, (g0, rig.person(0))
    rig.release()


def test_stepping_toward_camera_rewinds(ctx):
    # Toward the camera for 1.1 s, then back away for 1.1 s. Detecting a step takes ~2 px of
    # movement plus easing (~0.4 s, still growing meanwhile), so 1.1 s alone nets only ~0.01.
    rig = Rig(ctx)
    rig.run([person(feet=36)] * 100)
    g0 = rig.person(0)[1]
    assert g0 > 0.4
    rig.run(stepping_toward(11) + [person(feet=46 - k) for k in range(11)])
    assert rig.person(0)[1] < g0 - 0.03, (g0, rig.person(0))
    rig.release()


def test_growth_resumes_after_walking(ctx):
    rig = Rig(ctx)
    rig.run([person(x=WALK_X)] * 100)
    walk = walking(30, x=WALK_X)
    rig.run(walk)
    g1 = rig.person(0)[1]
    assert 0.25 < g1 < 0.45, g1                    # rewound, not reset
    levels = []
    for _ in range(3):
        rig.run([walk[-1]] * 10)
        levels.append(rig.person(0)[1])
    # Walking lasts WALK_HOLD_S (plus easing) past the last step, so the first ~0.6 s still
    # rewinds a little; then it grows at the full rate from where the rewind got to, not from 0.
    assert all(g >= g1 - 0.05 for g in levels), (g1, levels)
    assert abs((levels[-1] - levels[0]) - 2.0 / GROW_S) < 0.02, (g1, levels)
    rig.release()


def test_neighbour_walking_does_not_rewind_still_person(ctx):
    rig = Rig(ctx)
    rig.run(both([person(x=46)] * 100, walking(100, x=4, bounce=(4, 20))))
    assert len(live_slots(rig)) == 2
    still, walker = slot_near(rig, 52), slot_near(rig, 4)
    assert still != walker
    assert abs(rig.person(still)[1] - 0.5) < 0.06, rig.person(still)
    assert rig.person(walker)[1] < 0.1, rig.person(walker)
    rig.release()


def test_brief_loss_keeps_growth(ctx):
    rig = Rig(ctx)
    rig.run([person()] * 100)
    rig.run([EMPTY] * 20)                          # lost, then emptied: the track is gone
    assert rig.person(0)[0] == 0
    rig.run([person()] * 5)
    assert rig.person(slot_of_live(rig))[1] > 0.45            # whichever slot and id it came back in
    rig.release()


def test_merge_then_split_both_inherit(ctx):
    rig = Rig(ctx)
    rig.run(both([person(x=4)] * 100, [person(x=40)] * 100))
    assert len(live_slots(rig)) == 2
    # B slides left into A until their masks overlap (one blob), and they stand merged for 3 s
    rig.run(both([person(x=4)] * 26, [person(x=max(40 - k, 14)) for k in range(26)]))
    rig.run(both([person(x=4)] * 30, [person(x=14)] * 30))
    merged = max(rig.person(k)[1] for k in live_slots(rig))
    assert merged > 0.4
    # then B jumps back out: two blobs again
    rig.run(both([person(x=4)] * 8, [person(x=22)] * 8))
    live = live_slots(rig)
    assert len(live) == 2, live
    for k in live:
        assert rig.person(k)[1] >= merged - 0.05, (merged, [rig.person(j) for j in live])
    rig.release()


def detached_arm(x=26, feet=44):
    """person(arm="out") with a 1-px gap between the outstretched arm and the torso: two blobs."""
    m = person(x=x, feet=feet, arm="out")
    m[:, x + 10] = False
    return m


def test_split_off_part_inherits(ctx):                          # Review Focus 1
    from body_blobs import find_blobs
    arm = detached_arm()
    sizes = sorted(d.pixels for d in find_blobs(arm, np.zeros(arm.shape), BLOBS.min_blob_pixels))
    assert len(sizes) == 2 and sizes[0] >= BLOBS.min_blob_pixels, sizes   # really a second blob
    rig = Rig(ctx)
    rig.run([person(arm="out")] * 100)
    g = rig.person(0)[1]
    assert g > 0.4
    rig.run([arm] * 20)
    live = live_slots(rig)
    assert len(live) == 2, live                    # a second live track exists
    new = [k for k in live if k != 0][0]
    assert rig.person(new)[1] >= rig.person(0)[1] - 0.05, (rig.person(0), rig.person(new))
    rig.release()


def test_feet_off_frame(ctx):                                   # Review Focus 2
    rig = Rig(ctx)
    for _ in range(10):
        rig.run(flickering(10, x=WALK_X, feet=48))
    g0 = rig.person(0)[1]
    assert abs(g0 - 0.5) < 0.06, g0
    rig.run(walking(30, x=WALK_X, feet=48))
    assert abs((g0 - rig.person(0)[1]) - 3.0 / 20.0) < 0.05, (g0, rig.person(0))
    rig.release()


def test_new_person_far_from_ghosts_starts_bare(ctx):
    rig = Rig(ctx)
    rig.run([person(x=4)] * 100)
    assert rig.person(0)[1] > 0.4
    rig.run([EMPTY] * 10)                          # A is lost; its ghost is fresh
    gh = rig.ghost(0)
    assert gh[2] > 0.4 and gh[3] < INHERIT_S, gh
    rig.run([person(x=46)] * 10)
    b = slot_near(rig, 52)
    assert rig.person(b)[0] != 0 and rig.ghost(0)[3] < INHERIT_S
    assert rig.person(b)[1] < 0.05, rig.person(b)
    rig.release()


@pytest.mark.parametrize("frag_frames", [1, 6])
def test_fragment_in_freed_slot_keeps_ghost(ctx, frag_frames):
    # A is lost and their slot frees; a short fragment takes that slot and leaves; A comes
    # back at their old spot within INHERIT_S and must still inherit their own ghost.
    # 1 frame: a tentative fragment that expires bare. 6 frames: it confirms, grows a little,
    # and is lost after the ghost has faded from the sun (since > LEAVE_S) but is still inheritable.
    rig = Rig(ctx)
    rig.run([person(x=4)] * 100)
    g = rig.person(0)[1]
    assert g > 0.4
    rig.run([EMPTY] * 19)                          # coasted, lost, and the slot freed
    assert rig.person(0)[0] == 0 and rig.ghost(0)[2] > 0.4
    rig.run([person(x=46)] * frag_frames)          # a fragment takes the freed slot 0 ...
    assert rig.person(0)[0] != 0 and rig.person(0)[2] > 0.5
    frag_g = rig.person(0)[1]
    for _ in range(12):                            # ... and leaves: lost or expired
        rig.run([EMPTY])
        if rig.person(0)[0] == 0 or rig.base(0)[3] > 3.5:
            break
    assert rig.person(0)[0] == 0 or rig.base(0)[3] > 3.5
    since = rig.ghost(0)[3]
    assert since < INHERIT_S
    if frag_frames > 1:                            # the case R5 measured wrongly
        assert 0 < frag_g < g and since > LEAVE_S, (frag_g, since)
    rig.run([person(x=4)] * 3)
    k = slot_near(rig, 10)
    assert rig.person(k)[2] < 0.3                  # A, back at their spot
    assert abs(rig.person(k)[1] - g) < 0.05, (g, rig.person(k))
    rig.release()


def test_newcomer_beside_bloomed_person_starts_bare(ctx):
    rig = Rig(ctx)
    rig.run([person(x=4)] * 200)                   # A in full bloom
    assert rig.person(0)[1] > 0.9
    rig.run(both([person(x=4)] * 10, [person(x=20)] * 10))   # B appears with a 4 px gap
    live = live_slots(rig)
    assert len(live) == 2, live                    # a live, separate track
    a, b = slot_near(rig, 10), slot_near(rig, 26)
    assert a != b
    assert rig.person(a)[1] > 0.9
    assert rig.person(b)[1] < 0.05, rig.person(b)
    rig.release()


def test_sun_tracks_growth(ctx):
    rig = Rig(ctx)
    rig.run([EMPTY] * 30)
    assert rig.sun()[0] < 0.02
    rig.run([person()] * 220)
    assert rig.sun()[0] > 0.95, rig.sun()
    rig.run([EMPTY] * int(round((COAST_S + LEAVE_S + 3 * SUN_EASE_S) * 10)))
    assert rig.sun()[0] < 0.05, rig.sun()
    rig.release()


@pytest.mark.parametrize("dt, per_cam", [(1 / 60, 6), (1 / 240, 24)])   # a half float stalls small steps
def test_growth_independent_of_render_rate(ctx, dt, per_cam):
    a = Rig(ctx, dt=1 / 30)
    a.run([person()] * 150, frames_per_camera=3)              # 15 s: through the coarser steps above 0.5
    b = Rig(ctx, dt=dt)
    b.run([person()] * 150, frames_per_camera=per_cam)
    assert abs(a.person(0)[1] - 0.73) < 0.06, a.person(0)
    assert abs(a.person(0)[1] - b.person(0)[1]) < 0.02, (a.person(0), b.person(0))
    a.release(); b.release()


def test_state_stays_bounded_when_idle(ctx):                     # Review Focus 4
    rig = Rig(ctx)
    rig.run([person()] * 10)
    rig.r.render(200.0, (0, 0, 0, 0))              # one huge dt
    rig.run([EMPTY] * 3)
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run([EMPTY] * 3)
    for name in ("buffer_b", "buffer_c"):
        v = rig.buf(name)
        assert np.isfinite(v).all(), name
    assert np.abs(rig.buf("buffer_c")).max() <= 99.0
    assert rig.ghost(0)[3] > INHERIT_S             # the counters ran: the ghost is long gone
    rig.release()


# ── Task 3: plants (Image) ────────────────────────────────────────────────────

PAPER = np.array([246, 241, 228])
FLOWER_R, LEAF_LEN = 8.0 / 360.0, 9.0 / 360.0     # shaders/watering_can/common.glsl
SUN_POS, SUN_R, RAY_LEN = (-0.16, 0.84), 0.09, 0.07
FLOWER_RGB = np.array([[232, 149, 127], [232, 134, 47], [107, 91, 149], [188, 76, 38]])   # pink, orange, violet, rust
IMG = (256, 144)                                   # image tests: big enough that petals have pure-colour pixels


def screen_xy(size):
    """Pixel centres in screen heights, (h, w) each, row 0 = bottom."""
    w, h = size
    ys, xs = np.mgrid[0:h, 0:w]
    return (xs + 0.5) / h, (ys + 0.5) / h


def sun_region(size):
    """Pixels the sun (Task 4) may draw on: within SUN_R + RAY_LEN of its centre."""
    x, y = screen_xy(size)
    cx = size[0] / size[1] + SUN_POS[0]
    return np.hypot(x - cx, y - SUN_POS[1]) <= SUN_R + RAY_LEN


def drawn(img, region=None):
    """Pixels differing from paper by > 12 in any channel, within region (default: all but the sun's corner)."""
    d = (np.abs(img[..., :3].astype(int) - PAPER) > 12).any(axis=-1)
    if region is None:
        region = ~sun_region((img.shape[1], img.shape[0]))
    return d & region


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


def flower_pixels(img):
    """Pixels within 30 per channel of a flower colour."""
    rgb = img[..., :3].astype(int)
    return (np.abs(rgb[..., None, :] - FLOWER_RGB).max(axis=-1) <= 30).any(axis=-1)


def grown_rig(ctx, frames, size=IMG, **kw):
    rig = Rig(ctx, size=size)
    rig.run([person(**kw)] * frames)
    return rig


def test_run_ends_agree_along_a_column(ctx):          # else the plants tear into rows
    size = (640, 360)                               # the march's step is 5.6 px here
    rig = Rig(ctx, size=size)
    rig.run(flickering(20))
    b = rig.buf("buffer_b")
    for col in (29.5, 32.5, 34.5):                  # inside the legs and torso (an edge is ragged under flicker)
        c = b[:, int(col / BODY[0] * size[0])]
        run = c[(c[:, 0] > 0.9) & (c[:, 2] > 0)]
        assert len(run) > 100
        assert (np.ptp(run[:, 1:3], axis=0) < 1.0 / size[1]).all(), (col, np.ptp(run[:, 1:3], axis=0) * size[1])
    rig.release()


def test_sun_region_is_top_right():
    r, (w, h) = sun_region(IMG), IMG
    assert r[int(0.84 * h), int(w - 0.16 * h)]                 # its centre
    assert not r[: h // 2].any() and not r[:, : w // 2].any()   # only in the top right quarter


def test_nothing_drawn_before_growth(ctx):         # anti-goal: never draw the silhouette
    rig = grown_rig(ctx, 5)
    assert 0 < rig.person(0)[1] < 0.03, rig.person(0)          # growing, barely
    assert drawn(rig.image()).mean() < 0.002
    rig.release()


def test_bloom_fills_the_silhouette(ctx):
    rig = grown_rig(ctx, 220)
    assert rig.person(0)[1] > 0.99
    d, fig = drawn(rig.image()), on_screen(person(), IMG)
    assert d[fig].mean() >= 0.7, d[fig].mean()
    # Overhang is leaves and flowers only: within FLOWER_R + LEAF_LEN (and a pixel of antialiasing) of the figure.
    x, y = screen_xy(IMG)
    fx, fy = x[fig], y[fig]
    out = d & ~fig
    far = [np.hypot(fx - x[r, c], fy - y[r, c]).min() for r, c in np.argwhere(out)]
    assert out.sum() > 0 and max(far) <= FLOWER_R + LEAF_LEN + 1.5 / IMG[1], max(far)
    rig.release()


def test_growth_climbs_from_the_feet(ctx):
    rig = grown_rig(ctx, 60)
    assert abs(rig.person(0)[1] - 0.3) < 0.05, rig.person(0)
    d, fig = drawn(rig.image()), person()
    top, bottom = on_screen(fig & rows(6, 19), IMG), on_screen(fig & rows(31, 44), IMG)   # thirds of rows 6..44
    assert d[bottom].mean() > 0.5, d[bottom].mean()
    assert d[top].mean() < 0.1, d[top].mean()
    rig.release()


def test_colour_ripens(ctx):
    sats = []
    for frames, g in ((60, 0.3), (220, 1.0)):
        rig = grown_rig(ctx, frames)
        assert abs(rig.person(0)[1] - g) < 0.05, rig.person(0)
        img = rig.image()
        sats.append(saturation(img[..., :3][drawn(img)]).mean())
        rig.release()
    assert sats[0] < sats[1] - 0.25, sats


def test_flowers_only_late(ctx):
    found = []
    for frames, g in ((85, 0.4), (220, 1.0)):
        rig = grown_rig(ctx, frames)
        assert abs(rig.person(0)[1] - g) < 0.05, rig.person(0)
        img = rig.image()
        found.append((flower_pixels(img) & drawn(img)).sum())
        rig.release()
    assert found[0] == 0 and found[1] > 100, found


def test_vines_follow_the_arm(ctx):
    rig = grown_rig(ctx, 220, arm="up")
    # The raised arm above the head (arm-only columns, clear of the shoulders' flowers).
    arm = on_screen(rect(36, 0, 38, 8), IMG)
    assert drawn(rig.image())[arm].mean() > 0.5, drawn(rig.image())[arm].mean()
    rig.run([person(arm="down")] * 3)
    assert drawn(rig.image())[arm].mean() < 0.1, drawn(rig.image())[arm].mean()
    rig.release()


@pytest.mark.parametrize("thick", [6, 4])              # Body rows of a 96-row Body: 0.0625 and 0.042 screen heights
def test_horizontal_arm_blooms(ctx, thick):          # a thin run grows to full bloom too: no bare stencil hole
    # A finer Body than BODY, so the arm can be thinner than a flower and still be body after B's blur.
    m = np.kron(person(arm="out"), np.ones((2, 2), dtype=bool))   # 128 x 96; the arm is rows 26-31
    m[26 + thick:32, 72:] = False                                  # thin it from below
    rig = Rig(ctx, size=IMG)
    rig.run([m] * 220)
    assert rig.person(0)[1] > 0.99
    arm = rect(0, 0, 0, 0).repeat(2, 0).repeat(2, 1)
    arm[26:26 + thick, 76:100] = True                              # the outstretched arm, clear of the torso
    d = drawn(rig.image())[on_screen(arm, IMG)].mean()
    assert d >= 0.5, d
    rig.release()


def test_bloom_is_stable_under_flicker(ctx):        # Review Focus 3
    rig = Rig(ctx, size=IMG)
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


def test_lost_person_plants_rewind_without_popping(ctx):
    rig = grown_rig(ctx, 220)
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
    rig.release()
