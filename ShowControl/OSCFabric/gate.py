"""Decides, per signal key, whether a value is due on the wire under ADR-0007's send rule."""
from __future__ import annotations

import time
from typing import Callable


class SignalGate:
    """
    ADR-0007's send rule, in one place: a value is due when it moves by more
    than `change_epsilon` (strings: when it differs at all), or when
    `heartbeat_interval_s` has elapsed since that key was last marked.

    Heartbeats are tracked per key.  The gate never sends anything: ask
    `due(key, value)`, send, then `mark(key, value)`.
    """

    def __init__(
        self,
        heartbeat_interval_s: float,
        change_epsilon: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._heartbeat_interval = heartbeat_interval_s
        self._epsilon = change_epsilon
        self._clock = clock
        self._last_value: dict[str, float | str] = {}
        self._last_time: dict[str, float] = {}

    def due(self, key: str, value: float | str) -> bool:
        if key not in self._last_value:
            return True
        previous = self._last_value[key]
        if isinstance(value, str) or isinstance(previous, str):
            if value != previous:
                return True
        elif abs(value - previous) > self._epsilon:
            return True
        return (self._clock() - self._last_time[key]) >= self._heartbeat_interval

    def mark(self, key: str, value: float | str) -> None:
        self._last_value[key] = value
        self._last_time[key] = self._clock()
