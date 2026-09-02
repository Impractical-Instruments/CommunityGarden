"""
Sends Garden State to the ESP32-S3 location controllers over OSC (ADR-0020).

The controllers animate themselves, so this is the whole of the Pi's LED
responsibility for those locations: keep four microcontrollers told what the
garden is doing.  It sends state, never pixels.

Traffic discipline follows ADR-0007, the same rules the Elements use on the
Fabric: a value goes out when it moves by more than `change_epsilon`, and every
value is repeated at least once per `heartbeat_interval_s` whether it moved or
not.  The heartbeat matters more here than elsewhere — the controllers treat
silence as a dead Pi and fall back to an idle breathe after ten seconds.

Addresses are exactly the Fabric addresses (`/flowerbeds/activity`,
`/captcha/intensity`, `/captcha/blowup`, `/pipes/activity`, `/treehouse/mode`,
`/treehouse/brightness`), so a controller can be driven by hand with `oscsend`
without this module in the loop at all.
"""

import logging
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from displays.base import GardenState

log = logging.getLogger("treehouse")


@dataclass(frozen=True)
class LocationTarget:
    """One controller's address, resolved from network.json."""
    name: str
    ip: str
    port: int


class OSCClient(Protocol):
    def send_message(self, address: str, value) -> None: ...


def _default_client_factory(ip: str, port: int) -> OSCClient:
    from pythonosc.udp_client import SimpleUDPClient

    return SimpleUDPClient(ip, port)


class LocationSender:
    """
    Broadcasts Garden State to every location controller.

    Call `send()` once per frame; it decides internally whether anything
    actually goes on the wire.
    """

    def __init__(
        self,
        targets: list[LocationTarget],
        heartbeat_interval_s: float = 5.0,
        change_epsilon: float = 0.01,
        clock: Callable[[], float] | None = None,
        client_factory: Callable[[str, int], OSCClient] = _default_client_factory,
    ) -> None:
        self._targets = list(targets)
        self._heartbeat_interval = heartbeat_interval_s
        self._epsilon = change_epsilon
        self._clock = clock or time.monotonic
        self._client_factory = client_factory
        self._clients: list[tuple[LocationTarget, OSCClient]] = []
        self._last_sent: dict[str, float | str] = {}
        self._last_send_time: dict[str, float] = {}

    def connect(self) -> None:
        """
        Builds a UDP client per target.  A failure here is logged and skipped
        rather than raised: one unreachable controller must not stop the show
        for the other three.
        """
        for target in self._targets:
            try:
                self._clients.append((target, self._client_factory(target.ip, target.port)))
                log.info("Location controller %s at %s:%d", target.name, target.ip, target.port)
            except OSError as e:
                log.warning("Location controller %s unavailable (%s)", target.name, e)

    @property
    def target_names(self) -> list[str]:
        return [t.name for t in self._targets]

    def send(self, state: GardenState) -> int:
        """
        Sends whatever has changed (or gone stale) to every controller.
        Returns the number of OSC messages put on the wire.
        """
        if not self._clients:
            return 0

        now = self._clock()
        sent = 0

        for address, value in (
            ("/flowerbeds/activity", state.flowerbeds_activity),
            ("/captcha/intensity", state.captcha_intensity),
            ("/pipes/activity", state.pipes_activity),
            # Mirrors Coordinator.brightness: in dim mode this *is* the dim
            # level, which is what the firmware reads it as.
            ("/treehouse/brightness", state.brightness),
        ):
            if self._should_send_float(address, float(value), now):
                sent += self._broadcast(address, float(value))
                self._mark(address, float(value), now)

        mode = state.show_mode.value
        if self._should_send_string("/treehouse/mode", mode, now):
            sent += self._broadcast("/treehouse/mode", mode)
            self._mark("/treehouse/mode", mode, now)

        # One-shot, and the most time-sensitive thing here: never rate-limited.
        if state.captcha_blowup:
            sent += self._broadcast("/captcha/blowup", None)

        return sent

    def close(self) -> None:
        self._clients.clear()

    # -- internals ---------------------------------------------------------

    def _should_send_float(self, address: str, value: float, now: float) -> bool:
        previous = self._last_sent.get(address)
        if previous is None or not isinstance(previous, float):
            return True
        if abs(value - previous) > self._epsilon:
            return True
        return self._heartbeat_due(address, now)

    def _should_send_string(self, address: str, value: str, now: float) -> bool:
        if self._last_sent.get(address) != value:
            return True
        return self._heartbeat_due(address, now)

    def _heartbeat_due(self, address: str, now: float) -> bool:
        last = self._last_send_time.get(address)
        return last is None or (now - last) >= self._heartbeat_interval

    def _mark(self, address: str, value: float | str, now: float) -> None:
        self._last_sent[address] = value
        self._last_send_time[address] = now

    def _broadcast(self, address: str, value) -> int:
        sent = 0
        for target, client in self._clients:
            try:
                client.send_message(address, [] if value is None else value)
                sent += 1
            except OSError as e:
                log.warning("Location controller %s send failed: %s", target.name, e)
        return sent
