"""pipes_control: the Max patch's knob and loop-mix behaviour, as a tick-driven controller (#238)."""
from __future__ import annotations

import json
import math

import pytest

import pipes_control as pc

S = pc.Settings.load()
TICK = S.tick_s


def run(ctrl: pc.Controller, start: float, seconds: float) -> tuple[float, dict]:
    """Tick from `start` for `seconds`; returns (time after, last values)."""
    now, out = start, {}
    for _ in range(round(seconds / TICK)):
        now += TICK
        out = ctrl.tick(now)
    return now, out


def turn(ctrl: pc.Controller, knob: int, start: float, seconds: float, detents_per_tick: int = 1):
    now, out = start, {}
    for _ in range(round(seconds / TICK)):
        now += TICK
        ctrl.on_detents(knob, detents_per_tick, now)
        out = ctrl.tick(now)
    return now, out


def k(n: int, p: str) -> str:
    return pc.knob_address(n, p)


# ── Settings ──────────────────────────────────────────────────────────────────

def test_settings_match_the_max_patch():
    assert S.tick_s == 0.01 and S.alpha == 0.1 and S.max_velocity == 400
    assert S.sleep_after_s == 4.0 and S.fade_s == 0.3 and S.active_for_s == 20.0
    assert S.knob_voices[0] == S.knob_voices[6]          # board 1 mirrors board 0
    assert S.knob_voices[0].grain_size_ms == (500, 80)
    assert len(S.presets_db) == 13 and all(len(r) == 13 for r in S.presets_db)


def test_settings_reject_a_wrong_preset_table(tmp_path):
    raw = json.loads(pc.SETTINGS.read_text())
    raw["mix"]["presets_db"] = raw["mix"]["presets_db"][:5]
    bad = tmp_path / "settings.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="presets_db"):
        pc.Settings.load(bad)


# ── Knobs ─────────────────────────────────────────────────────────────────────

def test_a_resting_knob_is_silent_at_its_rest_values():
    out = pc.Controller(S).tick(1.0)
    assert out[k(0, "level")] == 0.0
    assert out[k(0, "grain_size")] == 500
    assert out[k(0, "density")] == pytest.approx(1000 / 500 * 0.75)
    assert out[k(0, "spray")] == 0
    assert out[k(0, "position")] == pytest.approx(0.25)    # 0 detents → middle of 0..0.5


def test_turning_fast_moves_every_parameter_to_its_fast_end():
    ctrl = pc.Controller(S)
    _, out = turn(ctrl, 0, 0.0, 1.0, detents_per_tick=5)   # 500 detents/s > 400
    assert out[k(0, "grain_size")] == pytest.approx(80, abs=1)
    assert out[k(0, "density")] == pytest.approx(1000 / 80 * 1.0, rel=0.02)
    assert out[k(0, "spray")] == pytest.approx(100, abs=1)
    assert out[k(0, "level")] == pytest.approx(0.5 * 1.0 * 1.0, abs=0.01)   # level_scale * fade * vol²


def test_velocity_is_the_smoothed_detent_rate():
    ctrl = pc.Controller(S)
    turn(ctrl, 3, 0.0, 2.0, detents_per_tick=2)            # 200 detents/s, settled
    assert ctrl.knobs[3].velocity == pytest.approx(200, rel=0.01)


def test_position_follows_detents_since_wake_and_clips():
    ctrl = pc.Controller(S)
    now, out = turn(ctrl, 1, 0.0, 0.5, detents_per_tick=5)  # 250 detents
    assert out[k(1, "position")] == pytest.approx(0.25 + 250 / 500 * 0.25)
    now, out = turn(ctrl, 1, now, 1.0, detents_per_tick=5)  # 750 > 500: clipped
    assert out[k(1, "position")] == pytest.approx(0.5)


def test_level_fades_in_over_300_ms():
    ctrl = pc.Controller(S)
    now, out = turn(ctrl, 2, 0.0, 0.15)
    assert 0.3 < ctrl.knobs[2].fade < 0.7
    turn(ctrl, 2, now, 0.2)
    assert ctrl.knobs[2].fade == 1.0


def test_a_knob_sleeps_4_s_after_its_last_detent_and_fades_out():
    ctrl = pc.Controller(S)
    now, _ = turn(ctrl, 4, 0.0, 0.5)
    now, _ = run(ctrl, now, 3.9)
    assert ctrl.knobs[4].awake
    now, _ = run(ctrl, now, 0.15)
    assert not ctrl.knobs[4].awake
    now, out = run(ctrl, now, 0.35)
    assert out[k(4, "level")] == 0.0


def test_position_holds_through_the_fade_out():
    ctrl = pc.Controller(S)
    now, out = turn(ctrl, 5, 0.0, 0.5, detents_per_tick=4)
    held = out[k(5, "position")]
    now, out = run(ctrl, now, 4.1)                           # asleep, fading
    assert out[k(5, "position")] == held


def test_waking_during_the_fade_out_brings_the_knob_back():
    """The Max patch's armed onebang turned grains off here until the next sleep/wake."""
    ctrl = pc.Controller(S)
    now, _ = turn(ctrl, 6, 0.0, 0.5)
    now, _ = run(ctrl, now, 4.05)                            # just asleep, fading out
    assert not ctrl.knobs[6].awake and ctrl.knobs[6].fade > 0
    now, _ = turn(ctrl, 6, now, 0.5)
    assert ctrl.knobs[6].awake and ctrl.knobs[6].fade == 1.0


def test_a_new_wake_starts_without_a_velocity_spike():
    """The Max patch carried the last wake's position into the first velocity tick."""
    ctrl = pc.Controller(S)
    now, _ = turn(ctrl, 7, 0.0, 1.0, detents_per_tick=3)   # acc = 300
    now, _ = run(ctrl, now, 5.0)                             # asleep
    ctrl.on_detents(7, 1, now + TICK)
    ctrl.tick(now + TICK)
    assert abs(ctrl.knobs[7].velocity) <= S.alpha * (1 / TICK) + 1e-9   # one detent's worth


def test_knobs_are_independent():
    ctrl = pc.Controller(S)
    _, out = turn(ctrl, 0, 0.0, 0.5)
    assert out[k(0, "level")] > 0 and out[k(1, "level")] == 0


# ── The loop mix ──────────────────────────────────────────────────────────────

def loops(out: dict) -> list[float]:
    return [out[pc.loop_address(i)] for i in range(1, 14)]


def test_at_rest_only_loop_1_plays():
    out = pc.Controller(S).tick(0.0)
    assert loops(out) == [1.0] + [0.0] * 12


@pytest.mark.parametrize("active, target", [(1, 1), (2, 3), (3, 4), (4, 6), (5, 7), (6, 9), (7, 10), (8, 12), (12, 12)])
def test_active_knobs_set_the_target_state(active, target):
    ctrl = pc.Controller(S)
    for n in range(active):
        ctrl.on_detents(n, 1, 0.0)
    ctrl.tick(0.0)
    assert ctrl.mix.state == target


def test_the_state_steps_down_every_5_s_even_while_knobs_stay_active():
    ctrl = pc.Controller(S)
    for n in range(4):
        ctrl.on_detents(n, 1, 0.0)
    ctrl.tick(0.0)
    assert ctrl.mix.state == 6
    now = 0.0
    for _ in range(round(5.05 / TICK)):         # keep all four turning, just past 5 s
        now += TICK
        for n in range(4):
            ctrl.on_detents(n, 1, now)
        ctrl.tick(now)
    assert ctrl.mix.state == 5


def test_a_higher_target_raises_the_state_a_lower_one_does_not():
    ctrl = pc.Controller(S)
    ctrl.on_detents(0, 1, 0.0)
    ctrl.tick(0.0)
    assert ctrl.mix.state == 1
    for n in range(1, 4):
        ctrl.on_detents(n, 1, 1.0)
    ctrl.tick(1.0)
    assert ctrl.mix.state == 6


def test_a_knob_stops_counting_20_s_after_its_last_detent():
    ctrl = pc.Controller(S)
    ctrl.on_detents(11, 1, 0.0)                  # e12: 2 s in the Max patch, 20 s here
    ctrl.tick(0.0)
    ctrl.on_detents(0, 1, 19.0)
    ctrl.tick(19.0)
    assert ctrl.mix.target == 3                  # both still active
    ctrl.tick(20.5)
    assert ctrl.mix.target == 1


def test_a_state_change_crossfades_over_10_s_linear_in_db():
    ctrl = pc.Controller(S)
    ctrl.on_detents(0, 1, 0.0)
    ctrl.tick(0.0)                               # state 1: loop 2 heads from -70 to 0 dB over 10 s
    out = ctrl.tick(2.5)                         # a quarter of the way: -52.5 dB
    assert loops(out)[1] == pytest.approx(10 ** (-52.5 / 20), rel=1e-3)


def test_one_knob_never_reaches_its_full_preset():
    """As in the Max patch: the state steps down after 5 s, halfway through the 10 s fade,
    and the fade turns back from where it is."""
    ctrl = pc.Controller(S)
    ctrl.on_detents(0, 1, 0.0)
    ctrl.tick(0.0)
    halfway = loops(ctrl.tick(5.0))[1]
    assert ctrl.mix.state == 0
    assert halfway == pytest.approx(10 ** (-35 / 20), rel=1e-3)
    assert loops(ctrl.tick(7.5))[1] < halfway
    assert loops(ctrl.tick(15.0))[1] == 0.0


def test_a_crossfade_completes_when_the_state_holds():
    s = pc.Settings(**{**S.__dict__, "step_down_s": 30.0})     # the state holds past the fade
    ctrl = pc.Controller(s)
    ctrl.on_detents(0, 1, 0.0)
    ctrl.tick(0.0)
    assert loops(ctrl.tick(10.0))[1] == pytest.approx(1.0)


def test_the_floor_is_silence():
    assert pc.db_to_amp(-70, -70) == 0.0
    assert pc.db_to_amp(-69.4, -70) == pytest.approx(10 ** (-69.4 / 20))


# ── Sending ───────────────────────────────────────────────────────────────────

class Sent(list):
    def __call__(self, addr, v):
        self.append((addr, v))


def test_sender_sends_everything_first_then_only_changes():
    sent = Sent()
    send = pc.ChangeSender(sent, S)
    assert send({"/a": 1.0, "/b": 2.0}, 0.0) == 2
    assert send({"/a": 1.0, "/b": 2.0}, 0.1) == 0
    assert send({"/a": 1.5, "/b": 2.0}, 0.2) == 1
    assert sent[-1] == ("/a", 1.5)


def test_sender_rate_limits_each_address():
    sent = Sent()
    send = pc.ChangeSender(sent, S)
    send({"/a": 0.1}, 0.0)
    assert send({"/a": 0.2}, 0.01) == 0          # under min_interval_s
    assert send({"/a": 0.3}, 0.02) == 1


def test_sender_lands_on_silence_without_waiting():
    sent = Sent()
    send = pc.ChangeSender(sent, S)
    send({"/a": 0.0003}, 0.0)
    assert send({"/a": 0.0}, 0.05) == 1          # below epsilon, but 0 is a rest value


def test_sender_refreshes_everything_for_a_restarted_reuben():
    sent = Sent()
    send = pc.ChangeSender(sent, S)
    send({"/a": 1.0, "/b": 2.0}, 0.0)
    assert send({"/a": 1.0, "/b": 2.0}, S.send_refresh_s) == 2


def test_every_tick_covers_the_whole_contract():
    out = pc.Controller(S).tick(0.0)
    expected = {k(n, p) for n in range(12) for p in ("position", "grain_size", "density", "spray", "level")}
    expected |= {pc.loop_address(i) for i in range(1, 14)}
    assert set(out) == expected
    assert all(math.isfinite(v) for v in out.values())


def test_every_address_sets_a_pipe_of_the_instrument():
    """The contract with reuben/pipes.json: each address is `/<pipe name>/in` for a pipe it declares."""
    instrument = json.loads((pc.SETTINGS.parent / "reuben" / "pipes.json").read_text())
    pipes = set(instrument["interface"]["inputs"])
    for addr in pc.Controller(S).tick(0.0):
        assert addr.endswith("/in"), addr
        assert addr[1:-len("/in")] in pipes, addr
