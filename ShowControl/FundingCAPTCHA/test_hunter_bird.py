"""Behaviour tests for the hunter_bird Setup (shaders/hunter_bird/).

Records come from the real BodyBlobs tracker run on synthetic masks with a
fake clock (camera 10 Hz, render 30 Hz), so record noise is realistic.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from body_blobs import BlobConfig, BodyBlobs
from shadertoy import Renderer, load_setup, pack_body

SETUP = Path(__file__).parent / "shaders" / "hunter_bird"
SIZE  = (128, 72)                         # render; ≥ 96 wide for the PRINT row
BODY  = (64, 40)                          # camera ROI (w, h)
SLABS = [{"near_mm": 1000, "far_mm": 4000}]
DT    = 1 / 30
# The shipped defaults, except a smaller min_blob_pixels for the small test Body.
BLOBS = BlobConfig(min_blob_pixels=20)


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
    """Renderer + the real BodyBlobs on a fake clock: camera at 10 Hz, render at 30 Hz."""

    def __init__(self, ctx, size=SIZE):
        self.size = size
        self.r = Renderer(ctx, size, body_mode="camera")
        self.r.load(load_setup(SETUP))
        self.blobs = BodyBlobs(BLOBS)
        self.t = 0.0

    def run(self, masks, frames_per_camera=3):
        for m in masks:                                   # one mask per camera frame, row 0 = top
            fg = np.where(m, 2000, 0).astype(np.uint16)
            body = pack_body(fg, {"x": 0, "y": 0, "w": BODY[0], "h": BODY[1]}, SLABS)
            self.r.upload_body(body)
            self.blobs.update(body[..., 0] > 0, body[..., 1] / 255.0, now=self.t)
            for _ in range(frames_per_camera):
                self.r.upload_blobs(self.blobs.records(now=self.t))
                self.r.render(DT, (0, 0, 0, 0))
                self.t += DT

    def b(self) -> np.ndarray:
        """Buffer B as float32 (h, w, 4), row 0 = texel y 0."""
        t = self.r._buffers["buffer_b"].read_tex
        return np.frombuffer(t.read(), dtype=np.float16).astype(np.float32).reshape(t.size[1], t.size[0], 4)

    def slot(self, k):  return self.b()[0, k]             # id, motion, interest, stamped
    def head(self, k):  return self.b()[2, k]             # last print x, y, side, since
    def attn(self):     return self.b()[3, 0]             # target+1, lock, since strike, id struck
    def reticle(self):  return self.b()[3, 1]             # x, y, radius, alpha
    def mood(self):     return self.b()[3, 2]             # lids, shiver, anchor x, y
    def blink(self):    return self.b()[3, 3]             # since blink, idle countdown, all-stamped s
    def stamp(self):    return self.b()[3, 4]             # x, y
    def prints(self):   return self.b()[4, :8 * 12]       # x, y, age, angle

    def image(self) -> np.ndarray:
        """The Image as uint8 (h, w, 4), row 0 = bottom."""
        return np.frombuffer(self.r.output.read(components=4), np.uint8).reshape(self.size[1], self.size[0], 4)

    def release(self):
        self.r.release()


def rect(x0, y0, x1, y1):
    m = np.zeros(BODY[::-1], dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


EMPTY = np.zeros(BODY[::-1], dtype=bool)


def standing(n, x=36):
    return [rect(x, 8, x + 10, 36)] * n


def walking(n, step=1):
    """~0.28 screen heights/s here: motion ≈ 0.57, so lock stays < 1 for 6 s at the defaults."""
    return [rect(6 + (k * step) % 40, 8, 16 + (k * step) % 40, 36) for k in range(n)]


def flailing(n, x=30):
    """Arms out and in: the box width swings by 12 px at ~2 Hz."""
    return [rect(x - 6 * (k % 5 in (1, 2, 3)), 8, x + 10 + 6 * (k % 5 in (1, 2, 3)), 36) for k in range(n)]


def flickering(n, seed=0):
    """A still person whose 1-px border toggles randomly each camera frame."""
    rng = np.random.default_rng(seed)
    base = rect(36, 8, 46, 36)
    edge = rect(35, 7, 47, 37) & ~rect(37, 9, 45, 35)
    out = []
    for _ in range(n):
        m = base.copy()
        m[edge] = rng.random(edge.sum()) < 0.5
        out.append(m)
    return out


# ── Task 1: per-slot state ────────────────────────────────────────────────────

def test_slot_tracks_record_id(ctx):
    rig = Rig(ctx)
    rig.run(standing(8))
    assert rig.slot(0)[0] == 1


def test_walking_has_motion(ctx):
    rig = Rig(ctx)
    rig.run(walking(20))
    assert rig.slot(0)[1] > 0.3


def test_flickering_still_person_has_no_motion(ctx):     # Review Focus 1
    rig = Rig(ctx)
    rig.run(flickering(40))
    assert rig.slot(0)[1] < 0.05


def test_interest_rises_with_motion_and_drains_still(ctx):
    rig = Rig(ctx)
    rig.run(walking(30))
    hi = rig.slot(0)[2]
    rig.run([walking(31)[-1]] * 40)
    assert hi > 0.5 and rig.slot(0)[2] < hi - 0.5


def test_tentative_has_no_motion_or_interest(ctx):
    rig = Rig(ctx)
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
    rig = Rig(ctx)
    rig.run(flailing(45))                                 # 4.5 s
    a = rig.attn()
    assert a[3] == 1                                      # id 1 struck
    assert rig.slot(0)[3] == 1                            # stamped


def test_walking_alone_never_strikes(ctx):
    rig = Rig(ctx)
    rig.run(walking(60))
    assert rig.attn()[3] == 0 and rig.attn()[1] < 1


def test_freezing_loses_the_bird(ctx):                     # Review Focus 1
    rig = Rig(ctx)
    rig.run(walking(30))
    assert rig.attn()[0] == 1
    rig.run(flickering(40))                               # a flickering still person: target dropped
    assert rig.attn()[0] == 0


def test_strike_once_per_person(ctx):                      # Review Focus 2
    rig = Rig(ctx)
    rig.run(flailing(45))
    struck_at = rig.attn()[2]
    rig.run(flailing(90))
    a = rig.attn()
    assert a[0] == 0 and rig.slot(0)[2] == 0              # ignored after the stamp, despite flailing
    assert a[2] > struck_at + 8.5                         # and never struck again


def test_reused_slot_resets_stamp(ctx):                     # Review Focus 2
    rig = Rig(ctx)
    rig.run(flailing(45))
    rig.run([EMPTY] * 30)                                 # leaves; lost; slot frees
    assert rig.slot(0)[0] == 0
    rig.run(flailing(45))
    assert rig.slot(0)[0] == 2 and rig.slot(0)[3] == 1    # new id, stamped anew


def test_only_confirmed_unstamped_can_be_target(ctx):      # Review Focus 4
    rig = Rig(ctx)
    rig.run(flailing(2))                                  # tentative: never a target
    assert rig.attn()[0] == 0 and rig.slot(0)[2] == 0
    rig = Rig(ctx)
    rig.run(both(flailing(45, x=10), still(45, RIGHT)))   # the left one is stamped
    done = stamped_slot(rig)
    rig.run(both(flailing(30, x=10), pacing(30, RIGHT)))  # left keeps flailing, right paces
    a = rig.attn()
    assert a[0] != 0 and a[0] - 1 != done
    assert rig.slot(int(a[0]) - 1)[3] == 0


def test_mood(ctx):
    rig = Rig(ctx)
    rig.run([EMPTY] * 30)
    assert abs(rig.mood()[0] - 0.42) < 0.06               # drowsy
    rig.run(walking(30))
    assert rig.attn()[0] != 0 and rig.mood()[0] > 0.9     # hunting: wide
    rig.run(flickering(50))
    assert rig.attn()[0] == 0
    assert abs(rig.mood()[0] - 0.7) < 0.03                # suspicious squint


def test_smug_after_strike_then_drowsy_when_all_stamped(ctx):
    rig = Rig(ctx)
    rig.run(flailing(45))
    since = rig.attn()[2]
    assert since < 3.2 and rig.mood()[0] >= 0.58 - 0.05
    rig.run(flailing(90))                                 # everyone present is stamped
    assert abs(rig.mood()[0] - 0.42) < 0.06


def test_blink_scheduled_for_new_id(ctx):
    rig = Rig(ctx)
    rig.run([EMPTY] * 3)
    rig.run(standing(1), frames_per_camera=1)             # the id appears this frame
    assert -0.16 < rig.blink()[0] < 0.0
    assert rig.mood()[1] > 0.9                            # leaves shiver


def test_reticle_follows_target_and_hides_when_empty(ctx):
    rig = Rig(ctx)
    rig.run([EMPTY] * 10)
    assert rig.reticle()[3] < 0.02
    rig.run(walking(30))
    r = rig.reticle()
    assert r[3] > 0.9
    box = rig.blobs.records(now=rig.t)[0, 0]
    assert abs(r[0] - (box[0] + box[2]) / 2) < 0.08
    assert abs(r[1] - (box[3] - 0.3 * (box[3] - box[1]))) < 0.08


def test_stamp_lands_on_target(ctx):
    rig = Rig(ctx)
    rig.run(flailing(45))
    box = rig.blobs.records(now=rig.t)[0, 0]
    s = rig.stamp()
    assert abs(s[0] - (box[0] + box[2]) / 2) < 0.02 and abs(s[1] - (box[1] + box[3]) / 2) < 0.02


def test_state_stays_bounded_when_idle(ctx):               # Review Focus 3
    rig = Rig(ctx)
    rig.r.render(200.0, (0, 0, 0, 0))                     # one huge dt
    rig.run([EMPTY] * 3)
    rig.r.render(200.0, (0, 0, 0, 0))
    rig.run([EMPTY] * 3)
    assert np.isfinite(rig.b()).all() and np.abs(rig.b()).max() <= 99.0


# ── Task 3: footprints ────────────────────────────────────────────────────────

PRINT_LIFE_S = 4.0


def test_walking_leaves_prints(ctx):
    rig = Rig(ctx)
    rig.run(walking(30))
    p = rig.prints()
    fresh = p[p[:, 2] < PRINT_LIFE_S]
    assert len(fresh) >= 6
    box = rig.blobs.records(now=rig.t)[0, 0]
    assert (fresh[:, 1] < box[1] + 0.02).all()            # at the bottom of the box
    assert len(set(np.round(fresh[:, 1], 3))) >= 2        # alternating sides


def test_standing_leaves_no_prints(ctx):
    rig = Rig(ctx)
    rig.run(flickering(30))
    assert (rig.prints()[:, 2] >= PRINT_LIFE_S).all()


def test_prints_age_out(ctx):
    rig = Rig(ctx)
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


def test_person_has_white_fill_and_ink_outline(ctx):
    rig = Rig(ctx, BIG)
    rig.run(standing(10))                                 # rect(36, 8, 46, 36): UV x 0.5625–0.719, y 0.1–0.8
    img = rig.image()
    assert near(img[to_px(0.64, 0.62)], "white")          # upper body: fill
    row = to_px(0.64, 0.62)[0]
    left = to_px(0.5625, 0.62)[1]
    assert any(near(img[row, c], "ink") for c in range(left - 3, left + 1))   # outline just outside


def test_hatching_only_in_lower_box(ctx):
    rig = Rig(ctx, BIG)
    rig.run(standing(10))
    img = rig.image()
    r0, r1 = to_px(0, 0.14)[0], to_px(0, 0.36)[0]         # lower 40% of the box, inside its edges
    c0, c1 = to_px(0.58, 0)[1], to_px(0.70, 0)[1]
    lower = img[r0:r1, c0:c1].reshape(-1, 4)
    upper = img[to_px(0, 0.45)[0]:to_px(0, 0.75)[0], c0:c1].reshape(-1, 4)
    assert any(near(p, "slate", 30) for p in lower)
    assert not any(near(p, "slate", 30) for p in upper)


def test_canopy_stays_in_its_band(ctx):
    rig = Rig(ctx, BIG)
    rig.run([EMPTY] * 5)
    img = rig.image()
    assert near(img[BIG[1] // 2, BIG[0] // 2], "paper", 12)   # the screen centre is the clearing
    rig = Rig(ctx, BIG)
    rig.run(walking(30))                                  # lids wide: the top centre is in view
    top = rig.image()[BIG[1] - 4, int(BIG[0] * 0.3):int(BIG[0] * 0.7)]
    assert any(near(p, "ink") for p in top)               # the canopy along the top


# ── Task 5: field notes and attention ─────────────────────────────────────────

def fake_records(box, state, ident=7, vel=(0.0, 0.0), age=0.0):
    """One record in slot 0: box (x0, y0, x1, y1) Body UV. No Body behind it, so only notes draw."""
    from shadertoy import BLOB_ROWS, BLOB_SLOTS
    rec = np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32)
    rec[0, 0] = box
    rec[1, 0] = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, *vel)
    rec[2, 0] = (ident, state, age, 0.5)
    return rec


def render_records(rig, rec, frames=5):
    fg = np.zeros(BODY[::-1], dtype=np.uint16)
    rig.r.upload_body(pack_body(fg, {"x": 0, "y": 0, "w": BODY[0], "h": BODY[1]}, SLABS))
    for _ in range(frames):
        rig.r.upload_blobs(rec)
        rig.r.render(DT, (0, 0, 0, 0))
    return rig.image()


def count(img, name, tol=40):
    px = img[..., :3].reshape(-1, 3).astype(int)
    return int((np.abs(px - PALETTE[name]) <= tol).all(axis=1).sum())


def test_confirmed_box_has_ink_brackets(ctx):
    rig = Rig(ctx, BIG)
    box = (0.30, 0.30, 0.60, 0.80)
    img = render_records(rig, fake_records(box, 2))
    row, c0 = to_px(box[0], box[3])
    arm = range(c0 + 2, c0 + 8)                            # along the top-left bracket's arm
    assert min(int(img[r, c, :3].sum()) for r in range(row - 2, row + 2) for c in arm) < 3 * 140   # dark ink
    mid = to_px((box[0] + box[2]) / 2, box[3])            # the middle of the top edge is open
    assert near(img[mid], "paper", 12)


def test_tentative_box_is_slate_and_dashed(ctx):
    rig = Rig(ctx, BIG)
    box = (0.30, 0.30, 0.60, 0.80)
    img = render_records(rig, fake_records(box, 1))
    col = to_px(box[0], 0)[1]
    edge = [img[r, c] for r in range(to_px(0, 0.38)[0], to_px(0, 0.72)[0]) for c in (col - 1, col)]
    assert any(int(p[2]) - int(p[0]) > 12 and p[0] < 225 for p in edge)   # slate: bluish, not ink or paper
    assert any(near(p, "paper", 12) for p in edge[::2])    # gaps in the dashes


def test_target_tag_is_yellow(ctx):
    rig = Rig(ctx, BIG)
    rig.run(walking(30))
    assert rig.attn()[0] == 1
    box = rig.blobs.records(now=rig.t)[0, 0]
    r1, c1 = to_px(box[2], box[3])
    patch = rig.image()[r1 - 25:r1 + 2, c1 - 4:c1 + 30]
    assert count(patch, "yellow", 30) > 10


def test_stamp_appears_after_strike_then_clears(ctx):
    rig = Rig(ctx, BIG)
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
    rig = Rig(ctx, BIG)
    rig.run([EMPTY] * 10)
    assert count(rig.image(), "rust") == 0


def test_reticle_drawn_on_target(ctx):
    rig = Rig(ctx, BIG)
    rig.run(walking(30))
    r = rig.reticle()
    rr, rc = to_px(r[0], r[1])
    assert count(rig.image()[rr - 30:rr + 30, rc - 30:rc + 30], "rust") > 20


# ── Task 6: the eye ───────────────────────────────────────────────────────────

def lid_patch(rig):
    """Pixels 0.35 H above the screen centre."""
    img = rig.image()
    r, c = int(BIG[1] * 0.85), BIG[0] // 2
    return img[r - 3:r + 3, c - 12:c + 12]


def bluish(patch):
    px = patch[..., :3].reshape(-1, 3).astype(int)
    return int(((px[:, 2] - px[:, 0] > 5) & (px[:, 0] < 235)).sum())     # paper is b − r = −18


def test_lids_drowsy_when_empty(ctx):
    rig = Rig(ctx, BIG)
    rig.run([EMPTY] * 10)
    assert bluish(lid_patch(rig)) > 5                     # lid: paper with slate hatching


def test_lids_open_on_target(ctx):
    rig = Rig(ctx, BIG)
    rig.run(walking(30))
    assert rig.mood()[0] > 0.9
    patch = lid_patch(rig)
    assert bluish(patch) == 0 and all(near(p, "paper", 12) for p in patch.reshape(-1, 4))


def iris_patch(rig):
    """Pixels 0.72–0.80 H left of the screen centre, inside the lids when they're wide."""
    img = rig.image()
    c = BIG[0] // 2
    return img[BIG[1] // 2 - 2:BIG[1] // 2 + 2, c - int(0.80 * BIG[1]):c - int(0.72 * BIG[1])]


def test_iris_band_narrows_view_on_lock(ctx):
    rig = Rig(ctx, BIG)
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


def test_membrane_sweeps_during_blink(ctx):
    rig = Rig(ctx, BIG)
    rec = fake_records((0.02, 0.35, 0.12, 0.6), 1)        # a new id at the far left, no Body
    def right_half():
        img = rig.image()
        return img[BIG[1] // 2 - 3:BIG[1] // 2 + 3, BIG[0] // 2:]
    render_records(rig, rec, frames=2)
    assert -0.16 < rig.blink()[0] < 0.0                   # scheduled
    assert bluish(right_half()) == 0
    for _ in range(15):
        render_records(rig, rec, frames=1)
        if 0.1 < rig.blink()[0] < 0.22:                   # mid-blink: the sheet's streaks cross the view
            assert bluish(right_half()) > 3
            return
    pytest.fail("no blink")


# ── Review fixes ──────────────────────────────────────────────────────────────

def test_brisk_walking_never_strikes(ctx):                 # "walking about never does" (spec)
    rig = Rig(ctx)
    rig.run(walking(100, step=2))                         # ~0.56 screen heights/s for 10 s
    assert rig.attn()[3] == 0 and rig.attn()[1] < 0.2


def test_flailer_steals_target_from_moving_walker(ctx):
    rig = Rig(ctx)
    rig.run(both(walking(30, step=1)[:30], still(30, RIGHT)))
    walker = int(rig.attn()[0]) - 1
    assert walker >= 0
    moving = [rect(4 + (k % 12), 8, 14 + (k % 12), 36) for k in range(40)]   # keeps walking on the left
    rig.run(both(moving, flailing(40, x=48)))
    a = rig.attn()
    assert a[0] - 1 not in (walker, -1) or a[3] == rig.slot(1 - walker)[0]   # stolen (or already stamped)


class BigRig(Rig):
    """The shipped scale: a 480 × 480 Body (camera_roi) and the default BlobConfig."""
    def __init__(self, ctx):
        self.size = SIZE
        self.r = Renderer(ctx, SIZE, body_mode="camera")
        self.r.load(load_setup(SETUP))
        self.blobs = BodyBlobs(BlobConfig())
        self.t = 0.0

    def run(self, masks, frames_per_camera=3):
        for m in masks:
            fg = np.where(m, 2000, 0).astype(np.uint16)
            body = pack_body(fg, {"x": 0, "y": 0, "w": 480, "h": 480}, SLABS)
            self.r.upload_body(body)
            self.blobs.update(body[..., 0] > 0, body[..., 1] / 255.0, now=self.t)
            for _ in range(frames_per_camera):
                self.r.upload_blobs(self.blobs.records(now=self.t))
                self.r.render(DT, (0, 0, 0, 0))
                self.t += DT


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
