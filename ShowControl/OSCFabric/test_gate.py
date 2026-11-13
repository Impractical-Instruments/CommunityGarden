"""Tests for SignalGate on its own, driven by a fake clock."""
from __future__ import annotations

from OSCFabric.gate import SignalGate


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


def _gate(clock: FakeClock, interval: float = 5.0, epsilon: float = 0.01) -> SignalGate:
    return SignalGate(interval, epsilon, clock)


def test_first_value_is_due():
    assert _gate(FakeClock()).due("a", 0.5)


def test_unchanged_value_is_not_due_before_interval():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("a", 0.5)
    clock.now += 4.9
    assert not gate.due("a", 0.5)


def test_delta_within_epsilon_is_not_due():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("a", 0.5)
    assert not gate.due("a", 0.505)


def test_delta_beyond_epsilon_is_due():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("a", 0.5)
    assert gate.due("a", 0.52)


def test_heartbeat_due_at_interval_even_if_unchanged():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("a", 0.5)
    clock.now += 5.0
    assert gate.due("a", 0.5)


def test_mark_restarts_that_keys_heartbeat():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("a", 0.5)
    clock.now += 4.0
    gate.mark("a", 0.5)
    clock.now += 4.0
    assert not gate.due("a", 0.5)
    clock.now += 1.0
    assert gate.due("a", 0.5)


def test_heartbeats_are_per_key():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("a", 0.5)
    clock.now += 3.0
    gate.mark("b", 0.5)
    clock.now += 2.0
    assert gate.due("a", 0.5)
    assert not gate.due("b", 0.5)


def test_due_does_not_mark():
    clock = FakeClock()
    gate = _gate(clock)
    assert gate.due("a", 0.5)
    assert gate.due("a", 0.5)


def test_strings_due_on_any_change():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("mode", "active")
    assert not gate.due("mode", "active")
    assert gate.due("mode", "dim")


def test_string_heartbeat():
    clock = FakeClock()
    gate = _gate(clock)
    gate.mark("mode", "active")
    clock.now += 5.0
    assert gate.due("mode", "active")


def test_switching_between_string_and_float_is_due():
    gate = _gate(FakeClock())
    gate.mark("k", "x")
    assert gate.due("k", 0.5)
    gate.mark("k", 0.5)
    assert gate.due("k", "x")
