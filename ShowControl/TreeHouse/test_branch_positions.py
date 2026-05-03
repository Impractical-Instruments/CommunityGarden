"""Tests for Coordinator._update_branch_positions — position math only, no hardware."""
import pytest

from coordinator import BranchConfig, BranchMotorConfig, Coordinator
from displays import GardenState


def _coord(*motors: BranchMotorConfig) -> Coordinator:
    return Coordinator([], branch_config=BranchConfig(motors=list(motors)))


def _positions(coord: Coordinator, **state_kwargs) -> list[tuple[int, float]]:
    state = GardenState(**state_kwargs)
    coord._update_branch_positions(state)
    return coord.get_branch_positions()


def test_all_signals_zero_gives_min_pos():
    motor = BranchMotorConfig(id=1, min_pos=10.0, max_pos=90.0)
    assert _positions(_coord(motor)) == [(1, 10.0)]


def test_all_signals_full_gives_max_pos():
    motor = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=90.0,
        weight_flowerbeds=1.0, weight_captcha=0.0, weight_pipes=0.0,
    )
    assert _positions(_coord(motor), flowerbeds_activity=1.0) == [(1, 90.0)]


def test_signal_clamped_when_weights_exceed_one():
    # Weights sum to 3.0; with all signals at 1.0 the raw sum is 3.0, must clamp to 1.0 → max_pos.
    motor = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=90.0,
        weight_flowerbeds=1.0, weight_captcha=1.0, weight_pipes=1.0,
    )
    result = _positions(_coord(motor), flowerbeds_activity=1.0, captcha_intensity=1.0, pipes_activity=1.0)
    assert result == [(1, 90.0)]


def test_captcha_blowup_overrides_to_recoil():
    motor = BranchMotorConfig(id=1, min_pos=0.0, max_pos=90.0, recoil_pos=-20.0)
    result = _positions(
        _coord(motor),
        captcha_blowup=True,
        flowerbeds_activity=1.0, captcha_intensity=1.0, pipes_activity=1.0,
    )
    assert result == [(1, -20.0)]


def test_partial_signal_interpolates():
    motor = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=100.0,
        weight_flowerbeds=1.0, weight_captcha=0.0, weight_pipes=0.0,
    )
    assert _positions(_coord(motor), flowerbeds_activity=0.5) == [(1, 50.0)]


def test_multiple_motors_computed_independently():
    motor_a = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=90.0,
        weight_flowerbeds=1.0, weight_captcha=0.0, weight_pipes=0.0,
    )
    motor_b = BranchMotorConfig(
        id=2, min_pos=10.0, max_pos=50.0,
        weight_flowerbeds=0.0, weight_captcha=1.0, weight_pipes=0.0,
    )
    result = _positions(_coord(motor_a, motor_b), flowerbeds_activity=1.0, captcha_intensity=0.5)
    assert result[0] == (1, 90.0)
    assert result[1] == (2, 30.0)  # 10 + 0.5 * 40


def test_no_motors_gives_empty_list():
    coord = Coordinator([], branch_config=BranchConfig(motors=[]))
    result = _positions(coord, flowerbeds_activity=1.0)
    assert result == []
