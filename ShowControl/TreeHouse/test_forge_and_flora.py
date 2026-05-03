"""Tests for ForgeAndFloraDisplay GardenState reactivity — no hardware."""
import pytest

from displays import GardenState
from displays.effect import ForgeAndFloraConfig, ForgeAndFloraDisplay


def _display(**kwargs) -> ForgeAndFloraDisplay:
    defaults = dict(arc_pin=2, bloom_pin=3)
    defaults.update(kwargs)
    return ForgeAndFloraDisplay(ForgeAndFloraConfig(**defaults))


def _state(**kwargs) -> GardenState:
    return GardenState(**kwargs)


def _step(display: ForgeAndFloraDisplay, state: GardenState, dt: float = 0.1) -> None:
    display.update(dt, state)


# ---------------------------------------------------------------------------
# Blend target — pipes_activity drives the arc→bloom crossfade
# ---------------------------------------------------------------------------

def test_pipes_zero_targets_arc():
    d = _display()
    _step(d, _state(pipes_activity=0.0))
    assert d._target_blend == 0.0


def test_pipes_full_targets_bloom():
    d = _display()
    _step(d, _state(pipes_activity=1.0))
    assert d._target_blend == 1.0


def test_pipes_partial_targets_midpoint():
    d = _display()
    _step(d, _state(pipes_activity=0.4))
    assert d._target_blend == pytest.approx(0.4)


def test_blend_moves_toward_target_at_transition_speed():
    # transition_speed=1.0 → blend moves 1.0 units/s; dt=0.1 → moves 0.1
    d = _display(transition_speed=1.0)
    _step(d, _state(pipes_activity=1.0), dt=0.1)
    assert d.blend == pytest.approx(0.1)


def test_blend_does_not_overshoot():
    d = _display(transition_speed=10.0)
    _step(d, _state(pipes_activity=0.3), dt=1.0)
    assert d.blend == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# Flicker intensity — driven by combined captcha + flowerbeds activity
# ---------------------------------------------------------------------------

def test_flicker_at_base_when_garden_quiet():
    d = _display(base_flicker_intensity=0.1, max_flicker_intensity=0.6)
    _step(d, _state())  # all signals zero
    assert d.flicker_intensity == pytest.approx(0.1)


def test_flicker_at_max_when_garden_full():
    d = _display(base_flicker_intensity=0.1, max_flicker_intensity=0.6)
    _step(d, _state(captcha_intensity=1.0, flowerbeds_activity=1.0))
    assert d.flicker_intensity == pytest.approx(0.6)


def test_flicker_interpolates_at_half_intensity():
    d = _display(base_flicker_intensity=0.0, max_flicker_intensity=1.0)
    _step(d, _state(captcha_intensity=0.5, flowerbeds_activity=0.5))
    # combined = (0.5 + 0.5) / 2 = 0.5
    assert d.flicker_intensity == pytest.approx(0.5)


def test_flicker_clamped_when_signals_exceed_one():
    # Each signal at 1.0 → combined = (1.0 + 1.0) / 2 = 1.0 → max flicker
    d = _display(base_flicker_intensity=0.0, max_flicker_intensity=0.8)
    _step(d, _state(captcha_intensity=1.0, flowerbeds_activity=1.0))
    assert d.flicker_intensity == pytest.approx(0.8)


def test_pipes_activity_does_not_affect_flicker():
    # pipes drives blend only; flicker should stay at base when only pipes is active
    d = _display(base_flicker_intensity=0.1, max_flicker_intensity=0.6)
    _step(d, _state(pipes_activity=1.0))
    assert d.flicker_intensity == pytest.approx(0.1)


# ---------------------------------------------------------------------------
# Disabled display — update is a no-op
# ---------------------------------------------------------------------------

def test_disabled_display_does_not_update():
    d = _display()
    d.disable()
    _step(d, _state(pipes_activity=1.0, captcha_intensity=1.0, flowerbeds_activity=1.0))
    assert d._target_blend == 0.0
    assert d.blend == 0.0
    assert d.flicker_intensity == pytest.approx(d._base_flicker)


# ---------------------------------------------------------------------------
# get_state reflects live flicker_intensity
# ---------------------------------------------------------------------------

def test_get_state_includes_flicker_intensity():
    d = _display(base_flicker_intensity=0.2, max_flicker_intensity=0.8)
    _step(d, _state(captcha_intensity=1.0, flowerbeds_activity=1.0))
    assert d.get_state().params["flicker_intensity"] == pytest.approx(0.8, abs=0.001)
