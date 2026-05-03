from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

_log = logging.getLogger("osc_fabric")


@runtime_checkable
class Transport(Protocol):
    def send(self, address: str, *args) -> None: ...


class FabricClient:
    """Sends OSC Fabric signals to the TreeHouse on behalf of one Element.

    Implements on-change + heartbeat fire semantics per ADR-0007:
    - report() sends immediately on first call and whenever the value
      changes by more than change_epsilon; otherwise suppresses.
    - send_event() always sends with no args (one-shot events).
    - tick(dt) accumulates elapsed time and re-sends all tracked signals
      once per heartbeat_interval_s, even if unchanged.

    Inject a Transport for testing; omit it to build a real OSC UDP client
    targeting the TreeHouse address in network_config.
    """

    def __init__(
        self,
        element: str,
        config: dict,
        transport: Transport | None = None,
    ) -> None:
        self._element = element
        self._heartbeat_interval: float = float(config.get("heartbeat_interval_s", 5.0))
        self._epsilon: float = float(config.get("change_epsilon", 0.01))
        self._transport: Transport = transport if transport is not None else _build_osc_transport(config)
        self._last_sent: dict[str, float] = {}
        self._elapsed: float = 0.0

    def report(self, signal: str, value: float) -> None:
        last = self._last_sent.get(signal)
        if last is None or abs(value - last) > self._epsilon:
            self._send(signal, value)

    def send_event(self, event: str) -> None:
        self._transport.send(f"/{self._element}/{event}")

    def tick(self, dt: float) -> None:
        self._elapsed += dt
        if self._elapsed >= self._heartbeat_interval:
            for signal, value in self._last_sent.items():
                self._transport.send(f"/{self._element}/{signal}", value)
            self._elapsed = 0.0

    def _send(self, signal: str, value: float) -> None:
        self._transport.send(f"/{self._element}/{signal}", value)
        self._last_sent[signal] = value


def _build_osc_transport(config: dict) -> Transport:
    from pythonosc.udp_client import SimpleUDPClient  # type: ignore[import]

    th = config.get("elements", {}).get("treehouse", {})
    ip: str = th.get("ip", "127.0.0.1")
    port: int = int(th.get("osc_port", 9001))
    _client = SimpleUDPClient(ip, port)

    class _OscTransport:
        def send(self, address: str, *args) -> None:
            try:
                _client.send_message(address, list(args) if args else [])
            except Exception as exc:
                _log.warning("OSC send error (%s %s): %s", address, args, exc)

    return _OscTransport()
