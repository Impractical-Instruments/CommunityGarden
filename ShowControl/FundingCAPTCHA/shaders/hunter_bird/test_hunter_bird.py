"""Behaviour tests for the hunter_bird Setup (shaders/hunter_bird/).

Records come from the real BodyBlobs tracker run on synthetic masks with a
fake clock (camera 10 Hz, render 30 Hz), so record noise is realistic.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from body_blobs import BlobConfig
from shader_test_rig import DT, EMPTY, Rig, flailing, flickering, pack_frame, rect, standing, walking
from shadertoy import BLOB_ROWS, BLOB_SLOTS

SETUP = Path(__file__).parent
SIZE  = (128, 72)                         # render; ≥ 96 wide for the PRINT row


class HunterRig(Rig):
    """Buffer B layout: see common.glsl."""

    def __init__(self, ctx, size=SIZE, blobs=None):
        kw = {} if blobs is None else {"blobs": blobs}
        super().__init__(ctx, SETUP, size, **kw)

    def slot(self, k):  return self.b()[0, k]             # id, motion, interest, stamped
    def head(self, k):  return self.b()[2, k]             # last print x, y, side, since
    def attn(self):     return self.b()[3, 0]             # target+1, lock, since strike, id struck
    def reticle(self):  return self.b()[3, 1]             # x, y, radius, alpha
    def mood(self):     return self.b()[3, 2]             # lids, shiver, anchor x, y
    def blink(self):    return self.b()[3, 3]             # since blink, idle countdown, all-stamped s
    def stamp(self):    return self.b()[3, 4]             # x, y
    def prints(self):   return self.b()[4, :8 * 12]       # x, y, age, angle


# ── Task 1: per-slot state ────────────────────────────────────────────────────

def test_walking_has_motion(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(20))
    assert rig.slot(0)[1] > 0.3


def test_flickering_still_person_has_no_motion(ctx):     # Review Focus 1
    rig = HunterRig(ctx)
    rig.run(flickering(40))
    assert rig.slot(0)[1] < 0.05


def test_interest_rises_with_motion_and_drains_still(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(30))
    hi = rig.slot(0)[2]
    rig.run([walking(31)[-1]] * 40)
    assert hi > 0.5 and rig.slot(0)[2] < hi - 0.5


def test_tentative_has_no_motion_or_interest(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(2))                                   # still tentative (min_confirm_frames 4)
    assert rig.slot(0)[1] == 0 and rig.slot(0)[2] == 0


# ── Task 2: attention ─────────────────────────────────────────────────────────

LEFT, RIGHT = (4, 8, 14, 36), (48, 8, 58, 36)


def both(a, b):
    """Two people, animated independently: frame-wise union of two mask lists."""
    return [ma | mb for ma, mb in zip(a, b)]


def pacing(n, at, span=6):
    """A person walking back and forth by `span` px at 1 px per camera frame."""
    x0, y0, x1, y1 = at
    out = []
    for k in range(n):
        o = abs(k % (2 * span) - span)
        out.append(rect(x0 + o, y0, x1 + o, y1))
    return out


def still(n, at):
    return [rect(*at)] * n


def stamped_slot(rig):
    hits = [k for k in range(8) if rig.slot(k)[3] == 1]
    assert len(hits) == 1, hits
    return hits[0]


def slot_of_id(rig, ident):
    return next(k for k in range(8) if rig.slot(k)[0] == ident)


def test_flailing_becomes_target_and_strikes(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(45))                                 # 4.5 s
    a = rig.attn()
    assert a[3] == 1                                      # id 1 struck
    assert rig.slot(0)[3] == 1                            # stamped


def test_walking_alone_never_strikes(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(60))
    assert rig.attn()[3] == 0 and rig.attn()[1] < 1


def test_freezing_loses_the_bird(ctx):                     # Review Focus 1
    rig = HunterRig(ctx)
    rig.run(walking(30))
    assert rig.attn()[0] == 1
    rig.run(flickering(40))                               # a flickering still person: target dropped
    assert rig.attn()[0] == 0


def test_strike_once_per_person(ctx):                      # Review Focus 2
    rig = HunterRig(ctx)
    rig.run(flailing(45))
    struck_at = rig.attn()[2]
    rig.run(flailing(90))
    a = rig.attn()
    assert a[0] == 0 and rig.slot(0)[2] == 0              # ignored after the stamp, despite flailing
    assert a[2] > struck_at + 8.5                         # and never struck again


def test_reused_slot_resets_stamp(ctx):                     # Review Focus 2
    rig = HunterRig(ctx)
    rig.run(flailing(45))
    rig.run([EMPTY] * 30)                                 # leaves; lost; slot frees
    assert rig.slot(0)[0] == 0
    rig.run(flailing(45))
    assert rig.slot(0)[0] == 2 and rig.slot(0)[3] == 1    # new id, stamped anew


def test_only_confirmed_unstamped_can_be_target(ctx):      # Review Focus 4
    rig = HunterRig(ctx)
    rig.run(flailing(2))                                  # tentative: never a target
    assert rig.attn()[0] == 0 and rig.slot(0)[2] == 0
    rig = HunterRig(ctx)
    rig.run(both(flailing(45, x=10), still(45, RIGHT)))   # the left one is stamped
    done = stamped_slot(rig)
    rig.run(both(flailing(30, x=10), pacing(30, RIGHT)))  # left keeps flailing, right paces
    a = rig.attn()
    assert a[0] != 0 and a[0] - 1 != done
    assert rig.slot(int(a[0]) - 1)[3] == 0


def test_mood(ctx):
    rig = HunterRig(ctx)
    rig.run([EMPTY] * 30)
    assert abs(rig.mood()[0] - 0.42) < 0.06               # drowsy
    rig.run(walking(30))
    assert rig.attn()[0] != 0 and rig.mood()[0] > 0.9     # hunting: wide
    rig.run(flickering(50))
    assert rig.attn()[0] == 0
    assert abs(rig.mood()[0] - 0.7) < 0.03                # suspicious squint


def test_smug_after_strike_then_drowsy_when_all_stamped(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(45))
    since = rig.attn()[2]
    assert since < 3.2 and rig.mood()[0] >= 0.58 - 0.05
    rig.run(flailing(90))                                 # everyone present is stamped
    assert abs(rig.mood()[0] - 0.42) < 0.06


def test_blink_scheduled_for_new_id(ctx):
    rig = HunterRig(ctx)
    rig.run([EMPTY] * 3)
    rig.run(standing(1), frames_per_camera=1)             # the id appears this frame
    assert -0.16 < rig.blink()[0] < 0.0
    assert rig.mood()[1] > 0.9                            # leaves shiver


def test_reticle_follows_target_and_hides_when_empty(ctx):
    rig = HunterRig(ctx)
    rig.run([EMPTY] * 10)
    assert rig.reticle()[3] < 0.02
    rig.run(walking(30))
    r = rig.reticle()
    assert r[3] > 0.9
    box = rig.blobs.records(now=rig.t)[0, 0]
    assert abs(r[0] - (box[0] + box[2]) / 2) < 0.08
    assert abs(r[1] - (box[3] - 0.3 * (box[3] - box[1]))) < 0.08


def test_stamp_lands_on_target(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(45))
    box = rig.blobs.records(now=rig.t)[0, 0]
    s = rig.stamp()
    assert abs(s[0] - (box[0] + box[2]) / 2) < 0.02 and abs(s[1] - (box[1] + box[3]) / 2) < 0.02


def test_state_stays_bounded_when_idle(ctx):               # Review Focus 3
    rig = HunterRig(ctx)
    rig.r.render(200.0, (0, 0, 0, 0))                     # one huge dt
    rig.run([EMPTY] * 3)
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run([EMPTY] * 3)
    assert np.isfinite(rig.b()).all() and np.abs(rig.b()).max() <= 99.0


# ── Task 3: footprints ────────────────────────────────────────────────────────

PRINT_LIFE_S = 4.0


def test_walking_leaves_prints(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(30))
    p = rig.prints()
    fresh = p[p[:, 2] < PRINT_LIFE_S]
    assert len(fresh) >= 6
    box = rig.blobs.records(now=rig.t)[0, 0]
    assert (fresh[:, 1] < box[1] + 0.02).all()            # at the bottom of the box
    assert len(set(np.round(fresh[:, 1], 3))) >= 2        # alternating sides


def test_standing_leaves_no_prints(ctx):
    rig = HunterRig(ctx)
    rig.run(flickering(30))
    assert (rig.prints()[:, 2] >= PRINT_LIFE_S).all()


def test_prints_age_out(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(30))
    rig.run([EMPTY] * 50)
    assert (rig.prints()[:, 2] >= PRINT_LIFE_S).all()


# ── Task 4: the world ─────────────────────────────────────────────────────────
# Image tests render larger, so pen widths (sized in screen heights) are ≥ 1 px.

BIG = (320, 180)
PALETTE = {
    "paper": (246, 241, 228), "ink": (17, 17, 17), "slate": (113, 154, 173),
    "deep": (32, 118, 163), "rust": (188, 76, 38), "yellow": (255, 242, 0),
    "white": (255, 250, 240),
}


def near(px, name, tol=40):
    return all(abs(int(a) - b) <= tol for a, b in zip(px[:3], PALETTE[name]))


def to_px(u, v, size=BIG):
    """Body UV (y up) → image (row, col), row 0 = bottom."""
    return int(v * size[1]), int(u * size[0])


# The eyes at no lock (common.glsl: EYE_R, EYE_SEP, EYE_LENS, EYE_Y), in BIG pixels.
EYE_R, EYE_SEP, EYE_LENS = BIG[1] * 150 / 360, BIG[1] * 150 / 360, 1.25
EYE_ROW = BIG[1] // 2
EYE_COLS = (int(BIG[0] / 2 - EYE_SEP), int(BIG[0] / 2 + EYE_SEP))     # left, right eye centres


def in_opening(row, col, margin=0.0):
    """Is (row, col) inside an eye's opening at no lock, by at least `margin` px (roughly)?"""
    return any(((col - c) / EYE_LENS) ** 2 + (row - EYE_ROW) ** 2 < (EYE_R - margin) ** 2 for c in EYE_COLS)


def test_person_has_white_fill_and_ink_outline(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run(standing(10))                                 # rect(36, 8, 46, 36): UV x 0.5625–0.719, y 0.1–0.8
    img = rig.image()
    # Sample above the idle reticle: it rests near the centre, and its upper-right tick
    # crosses this edge around v 0.62, where it covers the outline on some GPUs, not others.
    v = 0.74
    rx, ry, rr, _ = rig.reticle()
    aspect = BIG[0] / BIG[1]
    assert np.hypot((0.5625 - rx) * aspect, v - ry) > rr + 16 / 360   # beyond the reticle's reach
    assert near(img[to_px(0.64, v)], "white")             # upper body: fill
    row = to_px(0.64, v)[0]
    left = to_px(0.5625, v)[1]
    assert any(near(img[row, c], "ink") for c in range(left - 3, left + 1))   # outline just outside


def test_hatching_only_in_lower_box(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run(standing(10))
    img = rig.image()
    r0, r1 = to_px(0, 0.14)[0], to_px(0, 0.36)[0]         # lower 40% of the box, inside its edges
    c0, c1 = to_px(0.58, 0)[1], to_px(0.70, 0)[1]
    lower = img[r0:r1, c0:c1].reshape(-1, 4)
    upper = img[to_px(0, 0.45)[0]:to_px(0, 0.75)[0], c0:c1].reshape(-1, 4)
    assert any(near(p, "slate", 30) for p in lower)
    assert not any(near(p, "slate", 30) for p in upper)


def test_canopy_stays_in_its_band(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run([EMPTY] * 5)
    img = rig.image()
    assert near(img[BIG[1] // 2, BIG[0] // 2], "paper", 12)   # the screen centre is the clearing
    rig = HunterRig(ctx, BIG)
    rig.run(walking(30))                                  # lids wide, no lock: the eyes' tops are in view
    img = rig.image()
    top = [img[r, c] for r in range(int(BIG[1] * 0.82), BIG[1]) for c in range(BIG[0])
           if in_opening(r, c, margin=4)]                 # above the walker's brackets, clear of the eye's rim
    assert top and any(not near(p, "paper", 12) for p in top)   # the canopy, through the tops of the eyes


# ── Task 5: field notes and attention ─────────────────────────────────────────

def fake_records(box, state, ident=7, vel=(0.0, 0.0), age=0.0):
    """One record in slot 0: box (x0, y0, x1, y1) Body UV. No Body behind it, so only notes draw."""
    rec = np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32)
    rec[0, 0] = box
    rec[1, 0] = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, *vel)
    rec[2, 0] = (ident, state, age, 0.5)
    return rec


def render_records(rig, rec, frames=5):
    rig.r.upload_body(pack_frame(EMPTY))
    for _ in range(frames):
        rig.r.upload_blobs(rec)
        rig.r.render(DT, (0, 0, 0, 0))
    return rig.image()


def count(img, name, tol=40):
    px = img[..., :3].reshape(-1, 3).astype(int)
    return int((np.abs(px - PALETTE[name]) <= tol).all(axis=1).sum())


def test_confirmed_box_has_ink_brackets(ctx):
    rig = HunterRig(ctx, BIG)
    box = (0.30, 0.30, 0.60, 0.80)
    img = render_records(rig, fake_records(box, 2))
    row, c0 = to_px(box[0], box[3])
    arm = range(c0 + 2, c0 + 8)                            # along the top-left bracket's arm
    assert min(int(img[r, c, :3].sum()) for r in range(row - 2, row + 2) for c in arm) < 3 * 140   # dark ink
    mid = to_px((box[0] + box[2]) / 2, box[3])            # the middle of the top edge is open
    assert near(img[mid], "paper", 12)


def test_tentative_box_is_slate_and_dashed(ctx):
    rig = HunterRig(ctx, BIG)
    box = (0.30, 0.30, 0.60, 0.80)
    img = render_records(rig, fake_records(box, 1))
    col = to_px(box[0], 0)[1]
    edge = [img[r, c] for r in range(to_px(0, 0.38)[0], to_px(0, 0.72)[0]) for c in (col - 1, col)]
    assert any(int(p[2]) - int(p[0]) > 12 and p[0] < 225 for p in edge)   # slate: bluish, not ink or paper
    assert any(near(p, "paper", 12) for p in edge[::2])    # gaps in the dashes


def test_target_tag_is_yellow(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run(walking(30))
    assert rig.attn()[0] == 1
    box = rig.blobs.records(now=rig.t)[0, 0]
    r1, c1 = to_px(box[2], box[3])
    patch = rig.image()[r1 - 25:r1 + 2, c1 - 4:c1 + 30]
    assert count(patch, "yellow", 30) > 10


def test_stamp_appears_after_strike_then_clears(ctx):
    rig = HunterRig(ctx, BIG)
    for m in flailing(60):
        rig.run([m])
        if rig.attn()[3] == 1:
            break
    assert rig.attn()[3] == 1
    rig.run(flailing(5))                                  # 0.5 s after the strike
    sr, sc = to_px(*rig.stamp()[:2])
    assert count(rig.image()[sr - 25:sr + 25, sc - 25:sc + 25], "rust") > 30
    rig.run(flailing(40))                                 # 4.5 s after: gone
    sr, sc = to_px(*rig.stamp()[:2])
    assert count(rig.image()[sr - 25:sr + 25, sc - 25:sc + 25], "rust") == 0


def test_reticle_hidden_when_empty(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run([EMPTY] * 10)
    assert count(rig.image(), "rust") == 0


def test_reticle_drawn_on_target(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run(walking(30))
    r = rig.reticle()
    rr, rc = to_px(r[0], r[1])
    assert count(rig.image()[rr - 30:rr + 30, rc - 30:rc + 30], "rust") > 20


# ── Task 6: the eye ───────────────────────────────────────────────────────────

def lid_patch(rig):
    """Pixels 0.3 H above the left eye's centre: under the lid when drowsy, in view when wide."""
    img = rig.image()
    r, c = int(BIG[1] * 0.8), EYE_COLS[0]
    return img[r - 3:r + 3, c - 8:c + 8]


def bluish(patch):
    px = patch[..., :3].reshape(-1, 3).astype(int)
    return int(((px[:, 2] - px[:, 0] > 5) & (px[:, 0] < 235)).sum())     # paper is b − r = −18


def test_lids_drowsy_when_empty(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run([EMPTY] * 10)
    assert bluish(lid_patch(rig)) > 5                     # lid: paper with slate hatching


def test_lids_open_on_target(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run(walking(30))
    assert rig.mood()[0] > 0.9
    patch = lid_patch(rig)
    assert bluish(patch) == 0 and all(near(p, "paper", 12) for p in patch.reshape(-1, 4))


def iris_patch(rig):
    """Pixels 0.78–0.86 H left of the screen centre, at eye height: the left eye's outer corner.
    In view at no lock (the opening reaches 0.94 H); in the iris band at full lock (0.75–0.87 H)."""
    img = rig.image()
    c = BIG[0] // 2
    return img[EYE_ROW - 2:EYE_ROW + 2, c - int(0.86 * BIG[1]):c - int(0.78 * BIG[1])]


def test_iris_band_narrows_view_on_lock(ctx):
    rig = HunterRig(ctx, BIG)
    rig.run(flailing(9))
    assert rig.attn()[1] < 0.2
    patch = iris_patch(rig)
    assert count(patch, "yellow", 30) == 0 and bluish(patch) == 0   # world at lock 0
    for m in flailing(60)[9:]:
        rig.run([m])
        if rig.attn()[1] > 0.9:
            break
    assert rig.attn()[1] > 0.9
    patch = iris_patch(rig)
    assert count(patch, "yellow", 30) + bluish(patch) > 10            # iris band or socket


def test_lids_shut_during_blink(ctx):
    rig = HunterRig(ctx, BIG)
    rec = fake_records((0.02, 0.35, 0.12, 0.6), 1)        # a new id at the far left, no Body
    def right_eye():                                      # 0.15 H above its centre: in view between blinks
        img = rig.image()
        r, c = int(BIG[1] * 0.65), EYE_COLS[1]
        return img[r - 3:r + 3, c - 8:c + 8]
    render_records(rig, rec, frames=2)
    assert -0.16 < rig.blink()[0] < 0.0                   # scheduled
    assert bluish(right_eye()) == 0
    for _ in range(15):
        render_records(rig, rec, frames=1)
        if 0.1 < rig.blink()[0] < 0.22:                   # mid-blink: the lids are nearly shut
            assert bluish(right_eye()) > 5
            return
    pytest.fail("no blink")


# ── Review fixes ──────────────────────────────────────────────────────────────

def test_brisk_walking_never_strikes(ctx):                 # "walking about never does" (spec)
    rig = HunterRig(ctx)
    rig.run(walking(100, step=2))                         # ~0.56 screen heights/s for 10 s
    assert rig.attn()[3] == 0 and rig.attn()[1] < 0.2


def test_flailer_steals_target_from_moving_walker(ctx):
    rig = HunterRig(ctx)
    rig.run(both(walking(30, step=1)[:30], still(30, RIGHT)))
    walker = int(rig.attn()[0]) - 1
    assert walker >= 0
    moving = [rect(4 + (k % 12), 8, 14 + (k % 12), 36) for k in range(40)]   # keeps walking on the left
    rig.run(both(moving, flailing(40, x=48)))
    a = rig.attn()
    assert a[0] - 1 not in (walker, -1) or a[3] == rig.slot(1 - walker)[0]   # stolen (or already stamped)


class BigRig(HunterRig):
    """The shipped scale: 480 × 480 masks (camera_roi) and the default BlobConfig."""

    def __init__(self, ctx):
        super().__init__(ctx, blobs=BlobConfig())


def jittery_still(n, k, seed=0):
    """A still person at 480 × 480 whose every box side jitters by ±k px each camera frame."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        j = rng.integers(-k, k + 1, 4)
        m = np.zeros((480, 480), bool)
        m[100 + j[1]:400 + j[3], 200 + j[0]:280 + j[2]] = True
        out.append(m)
    return out


def test_still_person_with_box_jitter_escapes(ctx):        # Review Focus 1, with the box breathing
    rig = BigRig(ctx)
    rig.run(jittery_still(60, 6))
    s = rig.slot(0)
    assert s[1] < 0.2 and s[2] < 0.25 and rig.attn()[0] == 0 and rig.attn()[3] == 0


# ── Adversarial review fixes ──────────────────────────────────────────────────

def big_walker(n, px_per_frame, stride, x0=40, legs_hz=2.0):
    """480 × 480: an 80 × 300 person walking right whose box widens by up to
    `stride` px as the legs swing apart, twice per gait cycle (camera 10 Hz)."""
    out = []
    for k in range(n):
        x = x0 + px_per_frame * k
        w = 80 + stride * abs(np.sin(np.pi * legs_hz * k / 10.0))
        m = np.zeros((480, 480), bool)
        m[100:400, max(int(x), 0):min(int(x + w), 480)] = True
        out.append(m)
    return out


def big_flailer(n, arm, one_sided=False, cx=240):
    """480 × 480: an 80 × 300 person standing still, arms swinging out by `arm` px
    (one arm only if one_sided, so the centroid wobbles too)."""
    out = []
    for k in range(n):
        out_now = k % 5 in (1, 2, 3)
        left = arm * out_now * (not one_sided)
        right = arm * out_now
        m = np.zeros((480, 480), bool)
        m[100:400, cx - 40:cx + 40] = True
        m[150:180, cx - 40 - left:cx + 40 + right] = True      # arms at shoulder height
        out.append(m)
    return out


# (4, 40): just above DRIFT_WALK, the drift gate's edge. (8, 80): the most box motion. Faster walkers close the gate
# fully whatever their stride; every other case tried left the lock at exactly 0.
@pytest.mark.parametrize("speed,stride", [(4, 40), (8, 80)])
def test_striding_walker_never_strikes(ctx, speed, stride):  # "walking about never does" (spec)
    rig = BigRig(ctx)
    n = min(60, int((480 - 40 - 80 - stride) / speed))     # stay inside the frame
    rig.run(big_walker(n, speed, stride))
    assert rig.attn()[3] == 0 and rig.attn()[1] < 0.3, (rig.t, rig.attn())


@pytest.mark.parametrize("one_sided", [False, True])
def test_big_flailer_strikes(ctx, one_sided):              # "flail and it locks on and strikes"
    rig = BigRig(ctx)
    rig.run(big_flailer(50, 60, one_sided))                # 5 s
    assert rig.attn()[3] != 0


def test_target_keeps_lock_through_a_dropped_frame(ctx):   # mask flicker with a rival present
    rig = HunterRig(ctx)
    flail = flailing(40, x=12)
    walk = [rect(40 + (k % 12), 8, 50 + (k % 12), 36) for k in range(40)]
    rig.run(both(flail[:18], walk[:18]))
    a = rig.attn()
    assert a[3] == 0 and a[1] > 0.2, a                     # flailer targeted, not yet struck
    tgt, before = int(a[0]) - 1, a[1]
    rig.run([walk[18]])                                    # the flailer's blob is missed once
    rig.run(both(flail[19:21], walk[19:21]))
    a = rig.attn()
    assert int(a[0]) - 1 == tgt and (a[1] > before - 0.1 or a[3] != 0), (before, a)
