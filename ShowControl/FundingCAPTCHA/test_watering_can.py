"""Behaviour tests for the watering_can Setup (shaders/watering_can/).

Records come from the real BodyBlobs tracker run on synthetic masks with a
fake clock (camera 10 Hz, render at DT), so record noise is realistic.
GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

import copy
import math
import re
from pathlib import Path

import numpy as np
import pytest

from body_blobs import BlobConfig, BodyBlobs
from shadertoy import Renderer, load_setup, pack_body

SETUP = Path(__file__).parent / "shaders" / "watering_can"


def glsl_consts(path=SETUP / "common.glsl") -> dict:
    """Every `const float|int|vec2|vec3 NAME = <expr>, ...;` in common.glsl, evaluated: simple arithmetic,
    earlier constants, max/min/ceil, float(...)/int(...); vec2/vec3 become tuples."""
    src = re.sub(r"//[^\n]*", "", path.read_text())
    env = {"max": max, "min": min, "ceil": math.ceil, "float": float, "int": int,
           "vec2": lambda *a: tuple(float(x) for x in a), "vec3": lambda *a: tuple(float(x) for x in a)}
    out = {}
    for m in re.finditer(r"\bconst\s+(?:float|int|vec2|vec3)\s+([^;]*);", src):
        depth, start, decls = 0, 0, []
        body = m.group(1)
        for i, ch in enumerate(body + ","):                 # split on top-level commas only
            depth += (ch == "(") - (ch == ")")
            if ch == "," and depth == 0:
                decls.append(body[start:i]); start = i + 1
        for d in decls:
            name, expr = (x.strip() for x in d.split("=", 1))
            out[name] = env[name] = eval(expr, {"__builtins__": {}}, env)
    return out


class _Consts(dict):
    def __getitem__(self, name):
        if name not in self:
            raise KeyError(f"{name} is not a constant in common.glsl")
        return dict.__getitem__(self, name)


K = _Consts(glsl_consts())
SIZE  = (128, 72)                         # render
BODY  = (64, 48)                          # camera ROI (w, h)
SLABS = [{"near_mm": 1000, "far_mm": 4000}]
DT    = 1 / 30
LEAVE_S = K["LEAVE_S"]
BLOBS = BlobConfig(min_blob_pixels=20)    # the shipped defaults, but for the small test Body


class Rig:
    """Renderer + the real BodyBlobs on a fake clock: camera at 10 Hz, render at `dt`."""

    def __init__(self, ctx, size=SIZE, dt=DT, slot=0):
        self.size, self.dt, self.slot = size, dt, slot   # slot: move the tracker's records there (owner = slot + 1)
        self.r = Renderer(ctx, size, body_mode="camera")
        self.r.load(load_setup(SETUP))
        self.r.defer_image = True                         # most tests read buffers: image() draws the Image on demand
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
        self.r.draw_deferred_image()
        return np.frombuffer(self.r.output.read(components=4), np.uint8).reshape(self.size[1], self.size[0], 4)

    def release(self):
        self.r.release()

    def _state_textures(self):
        """Every texture a frame reads or writes: the feedback buffers (both halves), the Image, the inputs."""
        r = self.r
        return [*(t for b in r._buffers.values() for t in b.tex), r.output_tex, r._body_tex, r._blobs_tex]

    def snapshot(self):
        """All state the next run() or read depends on, for restore()."""
        r = self.r
        return {"tex":   [t.read() for t in self._state_textures()],
                "reads": {n: b.read for n, b in r._buffers.items()},
                "clock": (r.time, r.frame, self.t),
                "image": (r._deferred, r._deferred_lost),
                "blobs": copy.deepcopy(self.blobs)}

    def restore(self, snap):
        r = self.r
        for t, data in zip(self._state_textures(), snap["tex"], strict=True):
            t.write(data)
        for n, read in snap["reads"].items():
            r._buffers[n].read = read
        r.time, r.frame, self.t = snap["clock"]
        r._deferred, r._deferred_lost = snap["image"]
        self.blobs = copy.deepcopy(snap["blobs"])


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


# ── Task 1: Body memory (Buffer B) ────────────────────────────────────────────

def b_at(rig, col, row):
    """B texel under Body pixel (col, row), row 0 = top."""
    w, h = rig.size
    return rig.buf("buffer_b")[int((1 - (row + 0.5) / BODY[1]) * h), int((col + 0.5) / BODY[0] * w)]


def test_presence_ignores_edge_flicker(ctx):
    rig = Rig(ctx)
    rig.run(flickering(30))
    edge = []
    for k in range(10):
        rig.run(flickering(1, seed=k + 5))
        assert b_at(rig, 32, 20)[0] > 0.95            # torso centre
        assert b_at(rig, 22, 20)[0] < 0.05            # 3 px outside the flickering border
        edge.append(b_at(rig, 25, 20)[0])             # on the flickering border itself
    # Blur, hole fill and easing average the flicker out: ~0.12 as shipped; 0.26 without the easing,
    # ~1 without all three (the texel toggles between empty and body).
    assert max(edge) - min(edge) < 0.2, edge
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


def test_walker_leaves_no_hold_trail(ctx):
    rig = Rig(ctx)
    rig.run(walking(20))
    b = rig.buf("buffer_b")
    gone = b[..., 0] < 0.05
    assert gone.any() and (b[..., 3][gone] == 0).all()
    body = b[..., 0] > 0.95                           # under the walker now: owned, and held at ~1 (present
    assert body.any()                                 # texels decode to floor(0.9 / HOLD_Q) * HOLD_Q / 0.9)
    assert (b[..., 3][body] >= 1).all()
    assert (np.abs((b[..., 3][body] % 1.0) / 0.9 - 1) < 0.01).all(), np.unique(b[..., 3][body])
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


@pytest.mark.parametrize("dt, per_cam", [(1 / 30, 3), (1 / 240, 24)])
def test_hold_fade_independent_of_render_rate(ctx, dt, per_cam):
    """A lost person's hold falls by 1/LEAVE_S per second, +/- 15%, at any render rate.
    Measured as the slope of the mean hold over the torso between 0.5 s and 1.5 s into the fade.
    In slot 7 (owner 8): the hold is stored as owner + 0.9 * hold, so owner 8 has the coarsest half-float
    spacing; the quantisation is otherwise the same for every owner."""
    rig = Rig(ctx, dt=dt, slot=7)
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


def test_fading_hold_agrees_along_a_run(ctx):
    """Every texel of a lost person's run fades in step, so the Image rebuilds each vine tip from one value:
    the hold's peak-to-peak down a torso column stays within 2 * HOLD_Q at every point of the fade.
    (The fade's step offset is per frame, not per texel, at any render rate: one rate is enough.)"""
    size, per_cam = (640, 360), 3
    rig = Rig(ctx, size=size, dt=1 / 30)
    rig.run([person()] * 20, frames_per_camera=per_cam)
    seen = []
    for k in range(28):                                # coasting (0.8 s), then the whole LEAVE_S fade
        rig.run([EMPTY], frames_per_camera=per_cam)
        col = rig.buf("buffer_b")[:, int(32.5 / BODY[0] * size[0])]
        held = col[col[:, 3] > 0]
        if len(held) < 50:
            continue
        f = held[:, 3] % 1.0
        if f.max() < 0.89:                             # mid-fade
            seen.append(round((k + 1) / 10, 1))
            assert np.ptp(f) <= 2 * K["HOLD_Q"] + 1e-6, ((k + 1) / 10, np.ptp(f) / K["HOLD_Q"])
    assert len(seen) >= 10, seen
    rig.release()


# ── Task 2: Garden state (Buffer C) ───────────────────────────────────────────

GROW_S, INHERIT_S, SUN_EASE_S = K["GROW_S"], K["INHERIT_S"], K["SUN_EASE_S"]
EARLY, EARLY_S = K["GROW_EARLY"], K["GROW_EARLY_S"]
LATE_RATE = (1 - EARLY) / (GROW_S - EARLY_S)       # growth per second once past GROW_EARLY


def grown(t):
    """Growth after t seconds planted from bare: fast to GROW_EARLY, then slower to full bloom at GROW_S."""
    return min(1.0, EARLY / EARLY_S * t if t <= EARLY_S else EARLY + LATE_RATE * (t - EARLY_S))


def seconds_to(g):
    """Seconds planted from bare to reach growth g (the inverse of grown)."""
    return g / EARLY * EARLY_S if g <= EARLY else EARLY_S + (g - EARLY) / LATE_RATE
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
    assert abs(levels[9] - grown(10)) < 0.06 and levels[-1] > 0.98, levels
    assert all(b >= a - 1e-3 for a, b in zip(levels, levels[1:])), levels
    assert footprints(rig) == []                    # flicker is not walking
    rig.release()


def test_arm_waving_does_not_rewind(ctx):
    rig = Rig(ctx)
    rig.run([person(arm=("down", "out", "up")[k // 5 % 3]) for k in range(100)])
    assert abs(rig.person(0)[1] - grown(10)) < 0.06, rig.person(0)
    assert footprints(rig) == []                    # nor is waving
    rig.release()


def test_weight_shift_does_not_rewind(ctx):
    rig = Rig(ctx)
    rig.run([person(lift=(None, "L", None, "R")[k // 3 % 4]) for k in range(100)])
    assert abs(rig.person(0)[1] - grown(10)) < 0.06, rig.person(0)
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


def test_walking_sideways_rewinds_then_growth_resumes(ctx):
    rig = Rig(ctx)
    rig.run([person(x=WALK_X)] * 100)
    g0 = rig.person(0)[1]
    walk = walking(30, x=WALK_X)
    rig.run(walk)
    g1 = rig.person(0)[1]
    assert abs((g0 - g1) - 3.0 / K["REWIND_S"]) < 0.05, (g0, g1)    # 3 s of walking rewinds 3 s' worth ...
    assert abs(g1 - (grown(10) - 3.0 / K["REWIND_S"])) < 0.1, g1    # ... not a reset
    levels = []
    for _ in range(3):
        rig.run([walk[-1]] * 10)
        levels.append(rig.person(0)[1])
    # Walking lasts WALK_HOLD_S (plus easing) past the last step, so the first ~0.6 s still
    # rewinds a little; then it grows at the full rate from where the rewind got to, not from 0.
    assert all(g >= g1 - 0.05 for g in levels), (g1, levels)
    assert abs((levels[-1] - levels[0]) - 2.0 * LATE_RATE) < 0.02, (g1, levels)
    rig.release()


def test_neighbour_walking_does_not_rewind_still_person(ctx):
    rig = Rig(ctx)
    rig.run(both([person(x=46)] * 100, walking(100, x=4, bounce=(4, 20))))
    assert len(live_slots(rig)) == 2
    still, walker = slot_near(rig, 52), slot_near(rig, 4)
    assert still != walker
    assert abs(rig.person(still)[1] - grown(10)) < 0.06, rig.person(still)
    assert rig.person(walker)[1] < 0.1, rig.person(walker)
    rig.release()


def test_merge_then_split_both_inherit(ctx):
    # A has grown far more than B, so B starting from the merged level is told apart from B keeping its own.
    rig = Rig(ctx)
    rig.run([person(x=4)] * 150)                                       # A alone, 15 s
    rig.run(both([person(x=4)] * 30, [person(x=40)] * 30))             # B arrives, 3 s
    assert len(live_slots(rig)) == 2
    ga, gb = rig.person(slot_near(rig, 10))[1], rig.person(slot_near(rig, 46))[1]
    assert ga > 0.8 and gb < 0.45, (ga, gb)
    # B slides left into A until their masks overlap (one blob), and they stand merged for 3 s
    rig.run(both([person(x=4)] * 26, [person(x=max(40 - k, 14)) for k in range(26)]))
    rig.run(both([person(x=4)] * 30, [person(x=14)] * 30))
    merged = max(rig.person(k)[1] for k in live_slots(rig))
    assert merged > ga
    # then B jumps back out: two blobs again
    rig.run(both([person(x=4)] * 8, [person(x=22)] * 8))
    live = live_slots(rig)
    assert len(live) == 2, live
    for k in live:
        assert rig.person(k)[1] >= merged - 0.05, (merged, gb, [rig.person(j) for j in live])
    rig.release()


def confirmed_near(rig, x_px):
    """The level of the confirmed track whose base is nearest Body column x_px (a coasting or lost record of
    the same person, left over from a merge or split, doesn't count)."""
    ks = [k for k in live_slots(rig) if rig.base(k)[3] == 2]
    assert ks, [rig.base(k) for k in live_slots(rig)]
    return float(rig.person(min(ks, key=lambda k: abs(rig.base(k)[0] - x_px / BODY[0])))[1])


@pytest.mark.parametrize("contact", ["every 0.3 s", "every 1 s", "50% of frames"])
def test_touching_still_people_keep_growing(ctx, contact):
    # Two people planted side by side with a 1-px gap. The tracker merges them into one blob whenever the
    # gap is bridged; neither moves, so neither may lose growth to the box swelling and shrinking.
    rng = np.random.default_rng(1)
    a, b = person(x=10), person(x=23)
    rig = Rig(ctx)
    rig.run([a | b] * 60)
    before = confirmed_near(rig, 16), confirmed_near(rig, 29)
    frames = []
    for k in range(100):
        m = a | b
        if {"every 0.3 s": k // 3 % 2 == 0, "every 1 s": k // 10 % 2 == 0, "50% of frames": rng.random() < 0.5}[contact]:
            m[:, 22] = True                                   # bridged: one blob
        frames.append(m)
    rig.run(frames + [a | b] * 8)
    after = confirmed_near(rig, 16), confirmed_near(rig, 29)
    want = 10.8 * LATE_RATE                                   # still for 10.8 s, past the early spurt
    for g0, g1 in zip(before, after):
        assert abs((g1 - g0) - want) < 0.15 * want, (contact, before, after)
    rig.release()


def test_passer_by_costs_nothing_once_past(ctx):
    # Someone walks across in front of planted A (merging with them on the way). Merged, they share a level;
    # once the passer-by is clear, A loses nothing more and grows at the full rate straight away.
    feet = 44
    rig = Rig(ctx)
    a = person(x=26)                                          # spans Body columns 26..38
    rig.run([a] * 100)
    xs = list(range(-12, 64, 2))                              # 2 px per camera frame: a brisk walk
    clear = xs.index(40)                                      # the passer-by's left edge 2 px past A's right edge
    rig.run([a | person(x=x, feet=feet) for x in xs[:clear]])
    levels = []
    for m in [a | person(x=x, feet=feet) for x in xs[clear:]] + [a] * 20:
        rig.run([m])
        levels.append(confirmed_near(rig, 32))
    assert all(y >= x - 1e-3 for x, y in zip(levels, levels[1:])), str(np.round(levels, 3))
    want = (len(levels) - 1) / 10 * LATE_RATE
    assert levels[-1] - levels[0] > 0.85 * want, (want, levels)
    rig.release()


def test_merged_neighbour_stepping_nearer_leaves_a_planted_base(ctx):
    # B stands touching planted A, nearer the camera, long enough that the merge's re-plant is over, then steps
    # nearer still. The merged box's bottom is B's feet and moves with them; A's base must stay on A's own feet
    # (BASE_FEET: no feet at the box bottom in A's window, so A's lowest body row). Following the box bottom
    # would read B's step as A's, and rewind A.
    rig = Rig(ctx)
    a = person(x=26)                                          # Body columns 26..37: A's feet window is ~27..37
    rig.run([a] * 100)
    rig.run([a | person(x=38, feet=45)] * 20)                 # touching, so one blob; B's feet at 40..47
    levels = []
    for f in [46, 47, 48] + [48] * 15:
        rig.run([a | person(x=38, feet=f)])
        levels.append(confirmed_near(rig, 32))
    assert all(y >= x - 1e-3 for x, y in zip(levels, levels[1:])), str(np.round(levels, 3))
    want = (len(levels) - 1) / 10 * LATE_RATE
    assert levels[-1] - levels[0] > 0.85 * want, (want, levels)
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
    assert abs(g0 - grown(10)) < 0.06, g0
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
    assert rig.person(b)[1] < grown(1.0) + 0.02, rig.person(b)   # its own second of growth, nothing inherited
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
    assert rig.person(b)[1] < grown(1.0) + 0.02, rig.person(b)   # its own second of growth, nothing inherited
    rig.release()


def test_sun_tracks_growth(ctx):                     # at 30 fps a half float already stalls naive easing short of full
    per_cam = 3
    rig = Rig(ctx, dt=1 / 30)
    rig.run([EMPTY] * 30, frames_per_camera=per_cam)
    assert rig.sun()[0] < 0.02
    rig.run([person()] * 300, frames_per_camera=per_cam)   # full bloom from ~21 s, then 6 SUN_EASE_S to catch up
    assert rig.person(0)[1] == 1.0 and rig.sun()[0] > 0.99, rig.sun()
    rig.run([EMPTY] * int(round((COAST_S + LEAVE_S + 3 * SUN_EASE_S) * 10)), frames_per_camera=per_cam)
    assert rig.sun()[0] < 0.05, rig.sun()
    rig.release()


def test_growth_independent_of_render_rate(ctx):     # a half float stalls small steps: 240 fps has the smallest
    a = Rig(ctx, dt=1 / 30)
    a.run([person()] * 150, frames_per_camera=3)              # 15 s: through the coarser steps above 0.5
    b = Rig(ctx, dt=1 / 240)
    b.run([person()] * 150, frames_per_camera=24)
    assert abs(a.person(0)[1] - grown(15)) < 0.06, a.person(0)
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
FLOWER_R, REACH = K["FLOWER_R"], K["REACH"]
TWIG_REACH = (1 + K["FORK_LEN"]) * K["TWIG_LEN"] + K["SPRIG_LEN"]   # a forked twig and its sprig, from its node
SUN_POS, SUN_R, RAY_LEN = K["SUN_POS"], K["SUN_R"], K["RAY_LEN"]
FLOWER_RGB = np.array([[251, 233, 160], [113, 154, 173], [232, 134, 47]])   # pale yellow, light blue, orange
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


def _all_state(rig):
    rig.r.draw_deferred_image()
    return [*(t.read() for t in rig._state_textures()), rig.r.time, rig.r.frame, rig.t]


def test_shared_grown_rig_is_as_fresh_after_another_test_ran_it(ctx, shared_rig):
    # A test that runs a shared rig further must not leak into the next one: restore() has to undo it all.
    frames = round(10 * seconds_to(0.3))
    shared_rig(frames).run([EMPTY] * 10 + [person(arm="up")] * 5)    # the "previous test" dirties it
    shared = shared_rig(frames)
    fresh = grown_rig(ctx, frames)
    try:
        for rig in (shared, fresh):                # and both carry on identically, tracker included
            rig.run([person(arm="out")] * 3 + [EMPTY] * 3)
        assert all(a == b for a, b in zip(_all_state(shared), _all_state(fresh), strict=True))
    finally:
        fresh.release()


def column_runs(b):
    """Each vertical run of body texels in B (h, w, 4) as its texels' (bottom, top) arrays."""
    member = (b[..., 1] > 0) | (b[..., 2] > 0)
    for c in range(b.shape[1]):
        col, r = member[:, c], 0
        while r < len(col):
            if not col[r]:
                r += 1
                continue
            s = r
            while r < len(col) and col[r]:
                r += 1
            yield b[s:r, c, 1], b[s:r, c, 2]


def swinging_arm(angle_deg, dx=0):
    """person() on a 4x finer Body (256 x 192), right arm a 12 px bar from the shoulder at angle_deg
    (0 hanging, 90 out, 180 up), shifted dx px sideways."""
    m = np.roll(np.kron(person(), np.ones((4, 4), dtype=bool)), dx, axis=1)
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    a = np.radians(angle_deg)
    px, py = xx - (36 * 4 + dx), yy - 14 * 4                     # from the right shoulder, y down
    along = px * np.sin(a) + py * np.cos(a)
    return m | ((along > 0) & (along < 60) & (np.abs(-px * np.cos(a) + py * np.sin(a)) < 6))


def test_run_ends_agree_while_moving(ctx):          # a waving arm, a swaying body: the plants don't tear
    rig = Rig(ctx, size=(320, 240))
    rig.run([swinging_arm(20)] * 30)
    worst = []
    for k in range(16):                             # down to up over 1.6 s, drifting a Body px a frame
        rig.run([swinging_arm(20 + 160 * (0.5 - 0.5 * np.cos(np.pi * k / 15)), dx=k % 4)])
        spreads = [max(np.ptp(g), np.ptp(t)) for g, t in column_runs(rig.buf("buffer_b"))]
        worst.append(max(spreads))
    assert max(worst) < 2.0 / 240, worst            # every texel of a run finds the same ends, to a texel or two
    rig.release()


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


TREE_CELL = K["TREE_CELL"]


def test_tree_grid_marks_body_and_neighbourhood(ctx):
    rig = Rig(ctx)                                  # SIZE: 4 + 48 grid rows fit in 72
    rig.run([person()] * 10)
    c = rig.buf("buffer_c")
    aspect = SIZE[0] / SIZE[1]
    reach = K["TREE_R"] * TREE_CELL

    def cell(x_sh, y_sh):                           # the tree cell holding screen point (x, y), screen heights
        return c[4 + int(y_sh / TREE_CELL), int(x_sh / TREE_CELL)]

    y = 1 - 18 / BODY[1]                            # torso height
    edge = 38 / BODY[0] * aspect                    # the figure's right edge (arm hanging at x 35..38)
    torso = cell(32 / BODY[0] * aspect, y)
    assert torso[0] >= 0 and owner(torso[[0, 1, 3, 2]]) == 1     # on the body, owned by slot 0
    assert torso[0] < K["TREE_FAR"]                              # a path reaches it from the root
    near = cell(edge + 0.5 * reach, y)
    assert near[0] < 0 and near[1] == 1             # just outside: no body, but near one
    far = cell(edge + reach + 2.5 * TREE_CELL, y)
    assert far[0] < 0 and far[1] == 0               # beyond what a pixel there could draw
    assert cell(0.05, 0.05)[1] == 0 and cell(aspect - 0.05, 0.5)[1] == 0
    rig.release()


def feet_apart_arm_up():
    """A figure standing feet apart (a gap between the legs to the crotch), right arm raised overhead."""
    m = rect(28, 4, 33, 11)                         # head, touching the torso
    m |= rect(26, 10, 36, 26)                       # torso
    m |= rect(24, 26, 28, 44) | rect(34, 26, 38, 44)   # legs, 6 px apart
    m |= rect(36, 0, 39, 12)                        # right arm, raised (hand at the top of the frame)
    return m


def tree_cells(rig, mask):
    """Path distances of slot 0's tree cells whose centres fall in Body mask region `mask`."""
    c = rig.buf("buffer_c")[4:4 + K["TREE_ROWS"]]
    aspect = SIZE[0] / SIZE[1]
    out = []
    for j in range(c.shape[0]):
        for i in range(int(aspect / TREE_CELL)):
            t = c[j, i]
            if t[0] < 0 or int(np.floor(t[2])) != 1:
                continue
            x, y = (i + 0.5) * TREE_CELL / aspect, (j + 0.5) * TREE_CELL      # UV
            r, col = int((1 - y) * BODY[1]), int(x * BODY[0])
            if 0 <= r < BODY[1] and 0 <= col < BODY[0] and mask[r, col]:
                out.append(t[0])
    return np.array(out)


def test_one_root_at_the_feet(ctx):                 # one tree from the base: no roots in the arms or elsewhere
    rig = Rig(ctx)
    rig.run([feet_apart_arm_up()] * 40)
    far = rig.buf("buffer_c")[3, K["TREE_P_X"], 0]
    left, right = tree_cells(rig, rect(24, 40, 28, 44)), tree_cells(rig, rect(34, 40, 38, 44))
    assert len(left) and len(right)
    assert left.min() < 0.15 * far and right.min() < 0.15 * far, (left.min(), right.min(), far)   # both feet root
    above = tree_cells(rig, rect(0, 0, BODY[0], 38))
    assert above.min() > 0.15 * far, (above.min(), far)     # nothing above the feet is a root
    hand = tree_cells(rig, rect(36, 0, 39, 3))
    assert hand.min() > 0.8 * far, (hand.min(), far)       # the raised hand is reached last, via the shoulder
    tp = rig.buf("buffer_c")[3, K["TREE_P_X"]]
    front = tp[2] * tp[0]                           # growth × the farthest path distance
    assert left.max() < front < hand.min(), (left.max(), front, hand.min())   # mid growth: legs grown, hand not
    rig.release()


def test_still_trunk_and_root_hold_steady_under_flicker(ctx):   # no fidgeting root or trunk
    rig = Rig(ctx, size=(240, 180))
    rig.run(flickering(150, seed=3))
    rows = K["TREE_ROWS"]

    def state():
        c = rig.buf("buffer_c")
        return c[4:4 + rows, :int(240 / 180 / TREE_CELL)].copy(), c[3, K["TREE_P_X"]].copy()

    prev, root_moves, width_moves, flips = state(), [], [], []
    for k in range(20):
        rig.run(flickering(1, seed=100 + k), frames_per_camera=1)
        (g, tp), (pg, ptp) = state(), prev
        trunk = (g[..., 0] >= 0) & (pg[..., 0] >= 0) & (pg[..., 1] >= 8)    # 8+ seeds above: trunk and main branches
        root_moves.append(np.hypot(tp[3] - ptp[3], tp[1] - ptp[1]))
        width_moves.append(np.abs(g[..., 1] - pg[..., 1])[trunk].mean())
        flips.append((np.round(np.modf(g[..., 2])[0] * 16) != np.round(np.modf(pg[..., 2])[0] * 16))[trunk].sum())
        prev = (g, tp)
    assert max(root_moves) < 0.5 / 180, root_moves          # under half a pixel a frame
    assert max(width_moves) < 0.2, width_moves              # seed counts (widths) barely move
    assert sum(flips) == 0, flips                           # the trunk keeps its way back to the root
    rig.release()


def test_nothing_drawn_before_growth(ctx):         # anti-goal: never draw the silhouette
    rig = grown_rig(ctx, 4)
    assert 0 < rig.person(0)[1] < 0.03, rig.person(0)          # growing, barely
    assert drawn(rig.image()).mean() < 0.002
    rig.release()


def test_bloom_fills_the_silhouette(shared_rig):
    rig = shared_rig(220)
    assert rig.person(0)[1] > 0.99
    d, fig = drawn(rig.image()), on_screen(person(), IMG)
    assert d[fig].mean() >= 0.7, d[fig].mean()
    # Overhang is twigs, sprigs and flowers only: within a twig's or a daisy's reach (plus sway and a pixel
    # of antialiasing) of the figure.
    x, y = screen_xy(IMG)
    fx, fy = x[fig], y[fig]
    out = d & ~fig
    far = [np.hypot(fx - x[r, c], fy - y[r, c]).min() for r, c in np.argwhere(out)]
    assert out.sum() > 0 and max(far) <= max(TWIG_REACH, REACH) + K["SWAY_AMP"] + 1.5 / IMG[1], max(far)


def test_growth_climbs_from_the_feet(shared_rig):
    rig = shared_rig(round(10 * seconds_to(0.3)))
    assert abs(rig.person(0)[1] - 0.3) < 0.05, rig.person(0)
    d, fig = drawn(rig.image()), person()
    top, bottom = on_screen(fig & rows(6, 19), IMG), on_screen(fig & rows(31, 44), IMG)   # thirds of rows 6..44
    assert d[bottom].mean() > 0.25, d[bottom].mean()       # a sparse tree, but clearly there ...
    assert d[top].mean() < 0.05, d[top].mean()             # ... and the top still bare


def coloured(img):
    """Flower pixels: drawn and not grey. The wood and leaves are ink on paper; only flowers carry colour."""
    rgb = img[..., :3].astype(int)
    return drawn(img) & (rgb.max(axis=-1) - rgb.min(axis=-1) > 20)


def test_colour_ripens_flowers_pale_low_then_bold_high(shared_rig):
    fig = on_screen(person(), IMG)
    _, y = screen_xy(IMG)
    top, bottom = y[fig].max(), y[fig].min()
    low = y < bottom + (top - bottom) / 3                  # the figure's lower and upper thirds
    high = y > top - (top - bottom) / 3
    early = shared_rig(round(10 * seconds_to(0.3)))         # 2 s in
    assert abs(early.person(0)[1] - 0.3) < 0.05, early.person(0)
    img = early.image()
    sat_early = saturation(img[..., :3][drawn(img)]).mean()
    c = coloured(img)
    assert c[low].sum() > 20, c[low].sum()                  # flowers already open, low on the body ...
    assert (flower_pixels(img) & drawn(img)).sum() < 5      # ... and pale: hardly a pixel in full colour yet
    full = shared_rig(220)
    assert full.person(0)[1] > 0.99, full.person(0)
    img = full.image()
    sat_full = saturation(img[..., :3][drawn(img)]).mean()
    assert sat_full > 1.5 * sat_early, (sat_early, sat_full)   # rises clearly: the palette is pastel, the wood ink
    bold = flower_pixels(img) & drawn(img)
    assert bold.sum() > 30                                  # bold flowers at full bloom (only the outer ones: few at this size)
    assert bold[high].sum() > 2 * bold[low].sum(), (bold[high].sum(), bold[low].sum())   # and mostly high up


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


# ── Footprints: a walker leaves plants on the floor where they step ──────────

FOOTPRINTS, FOOT_GAP, FOOT_LIFE = K["FOOTPRINTS"], K["FOOT_GAP"], K["FOOT_LIFE"]


def footprints(rig):
    """The live footprints: (x, y UV, seconds since dropped) of each."""
    c = rig.buf("buffer_c")
    return [tuple(c[3, 1 + f, :3]) for f in range(FOOTPRINTS) if c[3, 1 + f, 2] < FOOT_LIFE]


def test_walker_leaves_footprints_that_grow_then_rewind_away(ctx):
    rig = Rig(ctx, size=IMG)
    rig.run([person(x=WALK_X)] * 30)
    rig.run(walking(30, x=WALK_X))                  # 30 px right in 3 s
    feet = 1 - 44 / BODY[1]                         # the feet's row, UV y
    fps = sorted(footprints(rig))
    assert len(fps) >= 4, fps
    xs = [x for x, _, _ in fps]
    assert all(abs(y - feet) < 0.04 for _, y, _ in fps), fps
    assert WALK_X / BODY[0] - 0.05 < xs[0] and xs[-1] < (WALK_X + 42) / BODY[0], fps   # on the path
    assert all((b - a) * IMG[0] / IMG[1] >= FOOT_GAP - 1e-3 for a, b in zip(xs, xs[1:])), fps    # spaced
    ages = [t for _, _, t in fps]
    assert ages == sorted(ages, reverse=True), ages  # dropped in walking order: oldest first
    rig.run([EMPTY] * 15)                           # the walker leaves; their own plants rewind away
    assert footprints(rig)
    # Off the body, where the walker passed: footprint plants, standing up off the floor at the feet's row.
    x, y = screen_xy(IMG)
    floor = (y > feet - 0.03) & (y < feet + 0.12)
    n0 = drawn(rig.image(), floor).sum()
    assert n0 > 200, n0
    counts = []
    for _ in range(int(FOOT_LIFE * 10)):            # then they rewind away, without popping
        rig.run([EMPTY])
        counts.append(drawn(rig.image()).sum())
    assert footprints(rig) == [] and counts[-1] == 0, counts
    prev = [n0] + counts[:-1]
    assert all(p - c <= max(0.3 * p, 0.1 * n0) for p, c in zip(prev, counts)), (n0, counts)
    rig.release()


# ── Task 4: the crayon sun (Image) ────────────────────────────────────────────

def sun_patch(img):
    """(disc, ring) masks: pixels inside the sun's disc, and in the ring where its rays reach."""
    size = (img.shape[1], img.shape[0])
    x, y = screen_xy(size)
    r = np.hypot(x - (size[0] / size[1] + SUN_POS[0]), y - SUN_POS[1])
    return r <= 0.85 * SUN_R, (r >= 1.2 * SUN_R) & (r <= SUN_R + RAY_LEN)


def test_sun_is_muted_when_empty(ctx):
    rig = Rig(ctx, size=IMG)
    rig.run([EMPTY] * 30)
    img = rig.image()
    disc, ring = sun_patch(img)
    d = drawn(img, disc)
    assert d.sum() > 0.3 * disc.sum(), (d.sum(), disc.sum())          # the sun is drawn, not paper
    assert saturation(img[..., :3][d]).mean() < 0.35
    assert drawn(img, ring).sum() == 0                                 # no rays
    rig.release()


def test_sun_brightens_and_grows_rays_with_bloom(shared_rig):
    rig = shared_rig(220)
    img = rig.image()
    disc, ring = sun_patch(img)
    d = drawn(img, disc)
    assert saturation(img[..., :3][d]).mean() > 0.7
    assert drawn(img, ring).sum() > 0.15 * ring.sum(), (drawn(img, ring).sum(), ring.sum())


def seam_extents(img):
    """Farthest drawn radius from the sun's centre in the two pixel rows of the left-pointing ray that are just above
    and just below atan's branch cut (the ray's axis when it hasn't drifted). 0 where the ray isn't drawn in a row."""
    size = (img.shape[1], img.shape[0])
    x, y = screen_xy(size)
    dx, dy = x - (size[0] / size[1] + SUN_POS[0]), y - SUN_POS[1]
    r = np.hypot(dx, dy)
    ray = (dx < 0) & (r > 1.3 * SUN_R) & (r < SUN_R + RAY_LEN + 0.02)
    d = (np.abs(img[..., :3].astype(int) - PAPER) > 12).any(axis=-1)
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
