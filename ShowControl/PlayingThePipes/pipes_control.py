"""Playing the Pipes control: encoder detents in, reuben instrument values out.

What the Max patch's knobgrain / knobvelocity / wakemove / ComputeState did, as
plain Python driven by a 10 ms tick (#238). The bridge feeds `on_detents` from
the Picos and calls `tick` on a timer; reuben gets the results as OSC on the
instrument's input pipes, each set at `/<pipe name>/in`:

    /pipes/knobN/position/in     0..1     where in the grain buffer (detents since wake)
    /pipes/knobN/grain_size/in   ms       grain length (and period)
    /pipes/knobN/density/in      Hz       grains per second
    /pipes/knobN/spray/in        ms       random jitter of each grain's start
    /pipes/knobN/level/in        0..1     knob amplitude (fades, velocity volume)
    /pipes/loopN/level/in        0..1     loop amplitude (state crossfade), N = 1..13

Those addresses are the contract with ShowControl/PlayingThePipes/reuben/pipes.json:
both sides change together. Tuning lives in settings.json beside this file.

Fixed relative to the Max patch: re-waking during the fade-out no longer leaves a
knob silent, waking no longer starts with a velocity spike from the previous
wake, position holds through the fade-out instead of snapping to the middle, and
every knob counts as active for the same time (the Max patch gave e12 2 s).
"""

from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path

SETTINGS = Path(__file__).resolve().parent / "settings.json"
KNOBS = 12
LOOPS = 13


def knob_address(knob: int, param: str) -> str:
    # A reuben input pipe named `pipes/knob0/level` is set at `/pipes/knob0/level/in`.
    return f"/pipes/knob{knob}/{param}/in"


def loop_address(loop: int) -> str:
    """Loops are numbered 1-13, as in the Max patch and the instrument."""
    return f"/pipes/loop{loop}/level/in"


def lerp(lo: float, hi: float, t: float) -> float:
    return lo + (hi - lo) * t


def db_to_amp(db: float, floor_db: float) -> float:
    return 0.0 if db <= floor_db else 10.0 ** (db / 20.0)


# ── Settings ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Voice:
    grain_size_ms: tuple[float, float]
    grain_probability: tuple[float, float]
    spray_ms: tuple[float, float]
    volume: tuple[float, float]


@dataclass(frozen=True)
class Settings:
    tick_s: float
    alpha: float
    max_velocity: float
    sleep_after_s: float
    fade_s: float
    position_range: float
    position_out: tuple[float, float]
    level_scale: float
    knob_voices: tuple[Voice, ...]
    active_for_s: float
    per_active_knob: float
    max_state: int
    step_down_s: float
    crossfade_s: float
    floor_db: float
    presets_db: tuple[tuple[float, ...], ...]
    send_min_interval_s: float
    send_epsilon: float
    send_refresh_s: float

    @classmethod
    def load(cls, path: str | Path = SETTINGS) -> Settings:
        raw = json.loads(Path(path).read_text())
        voices = [
            Voice(tuple(v["grain_size_ms"]), tuple(v["grain_probability"]),
                  tuple(v["spray_ms"]), tuple(v["volume"]))
            for v in raw["voices"]
        ]
        knob_voice = raw["knob_voice"]
        if len(knob_voice) != KNOBS:
            raise ValueError(f"knob_voice needs {KNOBS} entries, has {len(knob_voice)}")
        mix = raw["mix"]
        presets = tuple(tuple(float(x) for x in row) for row in mix["presets_db"])
        if len(presets) != mix["max_state"] + 1 or any(len(r) != LOOPS for r in presets):
            raise ValueError(f"presets_db needs {mix['max_state'] + 1} rows of {LOOPS} loop levels")
        return cls(
            tick_s=raw["tick_s"],
            alpha=raw["velocity"]["alpha"],
            max_velocity=raw["velocity"]["max_detents_per_s"],
            sleep_after_s=raw["wake"]["sleep_after_s"],
            fade_s=raw["wake"]["fade_s"],
            position_range=raw["position"]["range_detents"],
            position_out=(raw["position"]["out_min"], raw["position"]["out_max"]),
            level_scale=raw["level_scale"],
            knob_voices=tuple(voices[i] for i in knob_voice),
            active_for_s=mix["active_for_s"],
            per_active_knob=mix["per_active_knob"],
            max_state=mix["max_state"],
            step_down_s=mix["step_down_s"],
            crossfade_s=mix["crossfade_s"],
            floor_db=mix["floor_db"],
            presets_db=presets,
            send_min_interval_s=raw["send"]["min_interval_s"],
            send_epsilon=raw["send"]["epsilon"],
            send_refresh_s=raw["send"]["refresh_s"],
        )


# ── One knob ──────────────────────────────────────────────────────────────────

@dataclass
class Knob:
    """knobgrain + wakemove + knobvelocity for one encoder."""

    voice: Voice
    s: Settings
    awake: bool = False
    acc: int = 0             # detents since wake
    prev_acc: int = 0        # acc at the previous tick
    velocity: float = 0.0    # smoothed detents/s, signed
    fade: float = 0.0        # 0..1, ramps toward awake over fade_s
    last_detent: float = -math.inf

    def on_detents(self, delta: int, now: float) -> None:
        if not self.awake:
            # A fresh wake starts from rest: no carry-over from the last one (the Max
            # patch's velocity spike), and grains resume even mid fade-out.
            self.awake = True
            self.acc = self.prev_acc = 0
            self.velocity = 0.0
        self.acc += delta
        self.last_detent = now

    def tick(self, now: float) -> None:
        s = self.s
        if self.awake and now - self.last_detent >= s.sleep_after_s:
            self.awake = False   # acc is kept, so position holds through the fade-out
        diff = self.acc - self.prev_acc
        self.prev_acc = self.acc
        self.velocity = s.alpha * (diff / s.tick_s) + (1 - s.alpha) * self.velocity
        step = s.tick_s / s.fade_s if s.fade_s > 0 else 1.0
        self.fade = min(1.0, self.fade + step) if self.awake else max(0.0, self.fade - step)

    def values(self) -> dict[str, float]:
        s, v = self.s, self.voice
        t = min(abs(self.velocity), s.max_velocity) / s.max_velocity
        size = lerp(*v.grain_size_ms, t)
        r = s.position_range
        pos = lerp(*s.position_out, (max(-r, min(r, self.acc)) + r) / (2 * r))
        vol = lerp(*v.volume, t)
        return {
            "position": pos,
            "grain_size": size,
            "density": 1000.0 / size * lerp(*v.grain_probability, t),
            "spray": lerp(*v.spray_ms, t),
            "level": s.level_scale * self.fade * vol * vol,
        }


# ── The loop mix ──────────────────────────────────────────────────────────────

@dataclass
class Mix:
    """ComputeState + the preset crossfade: busier pipes, more loops."""

    s: Settings
    state: int = 0
    target: int = 0
    next_step: float = math.inf
    preset_pos: float = 0.0      # fractional preset index the levels sit at
    fade_from: float = 0.0
    fade_start: float = -math.inf

    def update(self, active_knobs: int, now: float) -> None:
        s = self.s
        # Where the running fade is now, before any state change starts a new one from here.
        self._advance(now)
        target = int(min(s.max_state, active_knobs * s.per_active_knob))
        if target != self.target:
            self.target = target
            if target > self.state:
                self._set_state(target, now)
        if self.state > 0 and now >= self.next_step:
            self._set_state(self.state - 1, now)

    def _advance(self, now: float) -> None:
        if self.preset_pos != self.state:
            t = (now - self.fade_start) / self.s.crossfade_s if self.s.crossfade_s > 0 else 1.0
            self.preset_pos = self.state if t >= 1 else lerp(self.fade_from, self.state, t)

    def _set_state(self, state: int, now: float) -> None:
        self.state = state
        self.next_step = now + self.s.step_down_s if state > 0 else math.inf
        self.fade_from = self.preset_pos
        self.fade_start = now

    def levels(self) -> list[float]:
        s = self.s
        lo = int(math.floor(self.preset_pos))
        hi = min(lo + 1, s.max_state)
        t = self.preset_pos - lo
        return [db_to_amp(lerp(a, b, t), s.floor_db) for a, b in zip(s.presets_db[lo], s.presets_db[hi])]


# ── Everything, and what to send ──────────────────────────────────────────────

@dataclass
class Controller:
    s: Settings
    knobs: list[Knob] = field(init=False)
    mix: Mix = field(init=False)

    def __post_init__(self) -> None:
        self.knobs = [Knob(v, self.s) for v in self.s.knob_voices]
        self.mix = Mix(self.s)
        self._lock = threading.Lock()

    def on_detents(self, knob: int, delta: int, now: float) -> None:
        with self._lock:
            self.knobs[knob].on_detents(delta, now)

    def tick(self, now: float) -> dict[str, float]:
        """Advance one tick; every value the instrument should hold now, by OSC address."""
        with self._lock:
            for k in self.knobs:
                k.tick(now)
            active = sum(now - k.last_detent < self.s.active_for_s for k in self.knobs)
            self.mix.update(active, now)
            out = {knob_address(i, p): v for i, k in enumerate(self.knobs) for p, v in k.values().items()}
            out.update({loop_address(i + 1): v for i, v in enumerate(self.mix.levels())})
            return out

    def status(self) -> dict:
        with self._lock:
            return {"state": self.mix.state, "awake_knobs": sum(k.awake for k in self.knobs)}

    def snapshot(self) -> dict:
        """What the Dashboard's virtual encoder surface draws: each knob's awake, level
        and position (as sent to reuben), the loop levels, and the mix state."""
        with self._lock:
            knobs = []
            for k in self.knobs:
                v = k.values()
                knobs.append({"awake": k.awake, "level": v["level"], "position": v["position"]})
            return {
                "knobs": knobs,
                "loops": self.mix.levels(),
                "state": self.mix.state,
                "max_state": self.s.max_state,
                "position_range": list(self.s.position_out),
            }


class ChangeSender:
    """Sends a value when it has moved by more than epsilon (at most every
    min_interval_s per address), and everything every refresh_s."""

    def __init__(self, send, s: Settings) -> None:
        self._send = send
        self._s = s
        self._sent: dict[str, tuple[float, float]] = {}   # address -> (value, time)
        self._last_refresh = -math.inf

    def __call__(self, values: dict[str, float], now: float) -> int:
        s = self._s
        refresh = now - self._last_refresh >= s.send_refresh_s
        if refresh:
            self._last_refresh = now
        n = 0
        for addr, v in values.items():
            prev = self._sent.get(addr)
            due = (prev is None or refresh
                   or (abs(v - prev[0]) > s.send_epsilon and now - prev[1] >= s.send_min_interval_s)
                   # land exactly on rest values (silence, a finished fade) without waiting for a refresh
                   or (v != prev[0] and v in (0.0, 1.0) and now - prev[1] >= s.send_min_interval_s))
            if due:
                self._send(addr, v)
                self._sent[addr] = (v, now)
                n += 1
        return n
