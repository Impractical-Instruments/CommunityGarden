"""Tests for branch_positions and BranchController — position math only, no hardware."""

from branches import BranchController, branch_positions
from config import BranchConfig, BranchMotorConfig
from controllables import Controllable, GardenState


def _positions(*motors: BranchMotorConfig, **state_kwargs) -> list[tuple[int, float]]:
    return branch_positions(list(motors), GardenState(**state_kwargs))


def test_all_signals_zero_gives_min_pos():
    motor = BranchMotorConfig(id=1, min_pos=10.0, max_pos=90.0)
    assert _positions(motor) == [(1, 10.0)]


def test_all_signals_full_gives_max_pos():
    motor = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=90.0,
        weight_flowerbeds=1.0, weight_captcha=0.0, weight_pipes=0.0,
    )
    assert _positions(motor, flowerbeds_activity=1.0) == [(1, 90.0)]


def test_signal_clamped_when_weights_exceed_one():
    # Weights sum to 3.0; with all signals at 1.0 the raw sum is 3.0, must clamp to 1.0 → max_pos.
    motor = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=90.0,
        weight_flowerbeds=1.0, weight_captcha=1.0, weight_pipes=1.0,
    )
    result = _positions(motor, flowerbeds_activity=1.0, captcha_intensity=1.0, pipes_activity=1.0)
    assert result == [(1, 90.0)]


def test_captcha_blowup_overrides_to_recoil():
    motor = BranchMotorConfig(id=1, min_pos=0.0, max_pos=90.0, recoil_pos=-20.0)
    result = _positions(
        motor,
        captcha_blowup=True,
        flowerbeds_activity=1.0, captcha_intensity=1.0, pipes_activity=1.0,
    )
    assert result == [(1, -20.0)]


def test_partial_signal_interpolates():
    motor = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=100.0,
        weight_flowerbeds=1.0, weight_captcha=0.0, weight_pipes=0.0,
    )
    assert _positions(motor, flowerbeds_activity=0.5) == [(1, 50.0)]


def test_multiple_motors_computed_independently():
    motor_a = BranchMotorConfig(
        id=1, min_pos=0.0, max_pos=90.0,
        weight_flowerbeds=1.0, weight_captcha=0.0, weight_pipes=0.0,
    )
    motor_b = BranchMotorConfig(
        id=2, min_pos=10.0, max_pos=50.0,
        weight_flowerbeds=0.0, weight_captcha=1.0, weight_pipes=0.0,
    )
    result = _positions(motor_a, motor_b, flowerbeds_activity=1.0, captcha_intensity=0.5)
    assert result[0] == (1, 90.0)
    assert result[1] == (2, 30.0)  # 10 + 0.5 * 40


def test_no_motors_gives_empty_list():
    assert _positions(flowerbeds_activity=1.0) == []


class _RecordingDriver:
    def __init__(self):
        self.sent = []

    def set_position(self, motor_id, degrees):
        self.sent.append((motor_id, degrees))


def test_branch_controller_is_a_controllable_that_drives_the_motors():
    driver = _RecordingDriver()
    motor = BranchMotorConfig(
        id=3, min_pos=0.0, max_pos=100.0,
        weight_flowerbeds=1.0, weight_captcha=0.0, weight_pipes=0.0,
    )
    branches = BranchController(BranchConfig(motors=[motor]), driver)
    assert isinstance(branches, Controllable)

    branches.update(0.1, GardenState(flowerbeds_activity=0.5))

    assert driver.sent == [(3, 50.0)]
    assert branches.positions == [(3, 50.0)]
    assert branches.get_state().params == {"positions": [[3, 50.0]]}
