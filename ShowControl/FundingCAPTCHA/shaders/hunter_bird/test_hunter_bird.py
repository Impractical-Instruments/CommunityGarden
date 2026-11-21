"""What a visitor sees in the hunter_bird Setup (shaders/hunter_bird/).

The Setup's promises. Every test below checks one of them, and says which.

1. An empty room is a paper clearing under a canopy, seen through a bird's two drowsy eyes. No reticle.
2. A person is a white figure in an ink outline, hatched low. The bird's field notes box them: ink
   brackets once the tracker is sure of them, slate dashes before. Walking leaves footprints that
   fade; standing leaves none.
3. The bird watches whoever moves. A mover becomes the target: a yellow tag, the reticle on them,
   the eyes wide. Freeze and it loses you, and squints. A newcomer makes it blink and the leaves shiver.
4. Flail and it locks on and strikes: the view narrows to the iris, a stamp lands on you and fades,
   and the bird looks smug, then drowsy. Walking about never gets you struck, however briskly, and
   nor does standing still while the camera's box around you jitters.
5. Each person is struck once, and a new person is fair game. Only people the tracker is sure of,
   and has not struck, are targets. A flailer takes the target from a walker, and one dropped camera
   frame does not lose the lock.
6. A long stall leaves the scene sane.

Tests assert the picture, or the bird's state read through HunterRig. None asserts how Buffer B
stores it. Lid levels are compared with each other, never with a copy of the shader's numbers.

Records come from the real BodyBlobs tracker run on synthetic masks with a fake clock (camera 10 Hz,
render 30 Hz), so record noise is realistic. GL tests need a headless context and skip without one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from body_blobs import BlobConfig
from shader_test_rig import DT, EMPTY, Rig, flailing, flickering, glsl_consts, pack_frame, rect, standing, walking
from blobs_contract import BLOB_ROWS, BLOB_SLOTS

SETUP = Path(__file__).parent
K = glsl_consts(SETUP)
SIZE  = (128, 72)                         # render; ≥ 96 wide for the footprints' row


class HunterRig(Rig):
    """The one place in this file that knows Buffer B's layout (see common.glsl)."""

    def __init__(self, ctx, size=SIZE, blobs=None):
        kw = {} if blobs is None else {"blobs": blobs}
        super().__init__(ctx, SETUP, size, **kw)

    def target(self):
        """The slot the bird is watching, or None."""
        t = int(self.b()[3, 0, 0])
        return t - 1 if t else None

    def lock(self) -> float:
        """How far the bird has locked on to its target: 0 … 1, and it strikes at 1."""
        return float(self.b()[3, 0, 1])

    def since_strike(self) -> float:
        """Seconds since the last strike."""
        return float(self.b()[3, 0, 2])

    def struck_id(self) -> int:
        """The tracker id of the last person struck, or 0 if nobody has been."""
        return int(self.b()[3, 0, 3])

    def struck_slots(self):
        """The slots whose person has been struck."""
        return [k for k in range(8) if self.b()[0, k, 3] == 1]

    def reticle(self):
        """The reticle as drawn: x, y (Body UV), radius, alpha."""
        return self.b()[3, 1]

    def lids(self) -> float:
        """How far the eyes are open: 0 shut … 1 wide."""
        return float(self.b()[3, 2, 0])

    def shiver(self) -> float:
        """How hard the leaves are shivering: 0 … 1."""
        return float(self.b()[3, 2, 1])

    def blink_time(self) -> float:
        """Seconds into the current blink; negative while one is on its way."""
        return float(self.b()[3, 3, 0])

    def stamp(self):
        """Where the stamp landed: x, y (Body UV)."""
        return self.b()[3, 4, :2]

    def footprints(self):
        """The footprints still showing, one row each: x, y (Body UV), age s, angle."""
        p = self.b()[4, :8 * K["PRINTS"]]
        return p[p[:, 2] < K["PRINT_LIFE_S"]]

    def box(self, k=0):
        """The tracker's box round slot k's person: x0, y0, x1, y1 (Body UV). What the shader is given."""
        return self.blobs.records(now=self.t)[0, k]


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


# ── Claims 3 and 4: who the bird watches, and who it strikes (state) ──────────

def test_flailing_becomes_target_and_strikes(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(45))                                 # 4.5 s
    assert rig.struck_id() == 1 and rig.struck_slots() == [0]


def test_walking_alone_never_strikes(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(60))
    assert rig.struck_id() == 0 and rig.lock() < 1


def test_brisk_walking_never_strikes(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(100, step=2))                         # ~0.56 screen heights/s for 10 s
    assert rig.struck_id() == 0 and rig.lock() < 0.2


def test_freezing_loses_the_bird(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(30))
    assert rig.target() == 0
    rig.run(flickering(40))                               # still, but for the camera's flicker
    assert rig.target() is None


def test_tentative_person_is_not_watched(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(2))                                  # the tracker is not yet sure of them
    assert rig.target() is None


# ── Claim 5: once each, and who can be a target (state) ───────────────────────

def test_strike_once_per_person(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(45))
    struck_at = rig.since_strike()
    rig.run(flailing(90))                                 # 9 s more of flailing
    assert rig.target() is None                           # ignored after the stamp
    assert rig.since_strike() > struck_at + 8.5           # and never struck again


def test_a_new_person_is_struck_anew(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(45))
    assert rig.struck_id() == 1
    rig.run([EMPTY] * 30)                                 # they leave; the tracker forgets them
    assert rig.struck_slots() == []
    rig.run(flailing(45))                                 # someone new, in the same place
    assert rig.struck_id() == 2


def test_a_struck_person_is_passed_over_for_someone_else(ctx):
    rig = HunterRig(ctx)
    rig.run(both(flailing(45, x=10), still(45, RIGHT)))   # the left one is struck
    (done,) = rig.struck_slots()
    rig.run(both(flailing(30, x=10), pacing(30, RIGHT)))  # left keeps flailing, right paces
    assert rig.target() not in (None, done)
    assert rig.target() not in rig.struck_slots()


def test_flailer_steals_target_from_moving_walker(ctx):
    rig = HunterRig(ctx)
    rig.run(both(walking(30, step=1)[:30], still(30, RIGHT)))
    walker = rig.target()
    assert walker is not None
    moving = [rect(4 + (k % 12), 8, 14 + (k % 12), 36) for k in range(40)]   # keeps walking on the left
    rig.run(both(moving, flailing(40, x=48)))
    flailer = 1 - walker
    assert rig.target() == flailer or flailer in rig.struck_slots()          # stolen (or already struck)


def test_target_keeps_lock_through_a_dropped_frame(ctx):   # mask flicker with a rival present
    rig = HunterRig(ctx)
    flail = flailing(40, x=12)
    walk = [rect(40 + (k % 12), 8, 50 + (k % 12), 36) for k in range(40)]
    rig.run(both(flail[:18], walk[:18]))
    assert rig.struck_id() == 0 and rig.lock() > 0.2       # flailer targeted, not yet struck
    tgt, before = rig.target(), rig.lock()
    rig.run([walk[18]])                                    # the flailer's blob is missed once
    rig.run(both(flail[19:21], walk[19:21]))
    assert rig.target() == tgt and (rig.lock() > before - 0.1 or rig.struck_id() != 0), (before, rig.lock())


# ── Claims 3 and 4 at the shipped scale: 480 × 480 masks and the default tracker ──

class BigRig(HunterRig):
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


def test_still_person_with_box_jitter_escapes(ctx):
    rig = BigRig(ctx)
    rig.run(jittery_still(60, 6))
    assert rig.target() is None and rig.struck_id() == 0


# (4, 40): a slow walk with a short stride. (8, 80): the most box motion a walker makes.
@pytest.mark.parametrize("speed,stride", [(4, 40), (8, 80)])
def test_striding_walker_never_strikes(ctx, speed, stride):
    rig = BigRig(ctx)
    n = min(60, int((480 - 40 - 80 - stride) / speed))     # stay inside the frame
    rig.run(big_walker(n, speed, stride))
    assert rig.struck_id() == 0 and rig.lock() < 0.3, (rig.t, rig.lock())


@pytest.mark.parametrize("one_sided", [False, True])
def test_big_flailer_strikes(ctx, one_sided):
    rig = BigRig(ctx)
    rig.run(big_flailer(50, 60, one_sided))                # 5 s
    assert rig.struck_id() != 0


# ── Claims 1, 3 and 4: the bird's mood (state; drawn in the Image tests below) ──

def test_eyes_are_drowsy_when_empty_wide_on_a_target_and_squint_when_it_freezes(ctx):
    rig = HunterRig(ctx)
    rig.run([EMPTY] * 30)
    drowsy = rig.lids()
    rig.run(walking(30))
    assert rig.target() is not None
    wide = rig.lids()
    rig.run(flickering(50))
    assert rig.target() is None
    squint = rig.lids()
    assert drowsy + 0.1 < squint < wide - 0.1, (drowsy, squint, wide)
    assert wide > 0.9


def test_smug_after_strike_then_drowsy_when_all_struck(ctx):
    rig = HunterRig(ctx)
    rig.run([EMPTY] * 30)
    drowsy = rig.lids()
    rig.run(flailing(45))
    assert rig.struck_id() != 0 and rig.since_strike() < 3.2
    smug = rig.lids()
    assert smug > drowsy + 0.05, (drowsy, smug)           # a little more open than drowsy
    rig.run(flailing(90))                                 # everyone present has been struck
    assert rig.lids() < smug - 0.05, (smug, rig.lids())   # drowsy again; a drowsy lid droops a little
    assert abs(rig.lids() - drowsy) < 0.1, (drowsy, rig.lids())


def test_newcomer_makes_the_leaves_shiver_and_a_blink_come(ctx):
    rig = HunterRig(ctx)
    rig.run([EMPTY] * 3)
    rig.run(standing(1), frames_per_camera=1)             # they appear this frame
    assert rig.shiver() > 0.9
    assert rig.blink_time() < 0                           # a blink is on its way


def test_reticle_follows_target_and_hides_when_empty(ctx):
    rig = HunterRig(ctx)
    rig.run([EMPTY] * 10)
    assert rig.reticle()[3] < 0.02
    rig.run(walking(30))
    r, box = rig.reticle(), rig.box()
    assert r[3] > 0.9
    assert abs(r[0] - (box[0] + box[2]) / 2) < 0.08       # on them, across ...
    assert abs(r[1] - (box[3] - 0.3 * (box[3] - box[1]))) < 0.08   # ... and at chest height


def test_stamp_lands_on_target(ctx):
    rig = HunterRig(ctx)
    rig.run(flailing(45))
    s, box = rig.stamp(), rig.box()
    assert abs(s[0] - (box[0] + box[2]) / 2) < 0.02 and abs(s[1] - (box[1] + box[3]) / 2) < 0.02


# ── Claim 2: footprints (state) ───────────────────────────────────────────────

def test_walking_leaves_prints(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(30))
    prints = rig.footprints()
    assert len(prints) >= 6
    assert (prints[:, 1] < rig.box()[1] + 0.02).all()     # at the person's feet
    assert len(set(np.round(prints[:, 1], 3))) >= 2       # left foot, right foot


def test_standing_leaves_no_prints(ctx):
    rig = HunterRig(ctx)
    rig.run(flickering(30))
    assert len(rig.footprints()) == 0


def test_prints_age_out(ctx):
    rig = HunterRig(ctx)
    rig.run(walking(30))
    rig.run([EMPTY] * 50)
    assert len(rig.footprints()) == 0


# ── Claim 6: a long stall ─────────────────────────────────────────────────────

def test_a_long_stall_leaves_the_scene_sane(ctx):
    rig = HunterRig(ctx)
    rig.r.render(200.0, (0, 0, 0, 0))                     # one huge dt
    rig.run([EMPTY] * 3)
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run([EMPTY] * 3)
    assert np.isfinite(rig.b()).all()
    assert rig.target() is None and rig.struck_id() == 0 and len(rig.footprints()) == 0
    assert rig.reticle()[3] < 0.02


# ── Claims 1 and 2: the world and the people in it (Image) ────────────────────
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


# The eyes at no lock, in BIG pixels.
EYE_R, EYE_SEP, EYE_LENS = BIG[1] * K["EYE_R"], BIG[1] * K["EYE_SEP"], K["EYE_LENS"]
EYE_ROW = int(BIG[1] * K["EYE_Y"])
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


# ── Claims 2, 3 and 4: field notes, the tag, the stamp, the reticle (Image) ───

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
    assert rig.target() == 0
    box = rig.box()
    r1, c1 = to_px(box[2], box[3])
    patch = rig.image()[r1 - 25:r1 + 2, c1 - 4:c1 + 30]
    assert count(patch, "yellow", 30) > 10


def test_stamp_appears_after_strike_then_clears(ctx):
    rig = HunterRig(ctx, BIG)
    for m in flailing(60):
        rig.run([m])
        if rig.struck_id() == 1:
            break
    assert rig.struck_id() == 1
    rig.run(flailing(5))                                  # 0.5 s after the strike
    sr, sc = to_px(*rig.stamp())
    assert count(rig.image()[sr - 25:sr + 25, sc - 25:sc + 25], "rust") > 30
    rig.run(flailing(40))                                 # 4.5 s after: gone
    sr, sc = to_px(*rig.stamp())
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


# ── Claims 1, 3 and 4: the eyes (Image) ───────────────────────────────────────

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
    assert rig.lids() > 0.9
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
    assert rig.lock() < 0.2
    patch = iris_patch(rig)
    assert count(patch, "yellow", 30) == 0 and bluish(patch) == 0   # world at lock 0
    for m in flailing(60)[9:]:
        rig.run([m])
        if rig.lock() > 0.9:
            break
    assert rig.lock() > 0.9
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
    assert rig.blink_time() < 0                           # a blink is on its way
    assert bluish(right_eye()) == 0
    for _ in range(15):
        render_records(rig, rec, frames=1)
        if 0.1 < rig.blink_time() < 0.22:                 # mid-blink: the lids are nearly shut
            assert bluish(right_eye()) > 5
            return
    pytest.fail("no blink")
