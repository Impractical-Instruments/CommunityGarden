from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from .gate import SignalGate

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
    - tick(dt) accumulates elapsed time and re-sends each tracked signal
      once per heartbeat_interval_s since it was last sent (by report() or
      by an earlier heartbeat), even if unchanged.

    The rule itself lives in SignalGate; this class owns the addresses and
    the transport.

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
        self._transport: Transport = transport if transport is not None else _build_osc_transport(config)
        self._now: float = 0.0
        self._gate = SignalGate(
            float(config.get("heartbeat_interval_s", 5.0)),
            float(config.get("change_epsilon", 0.01)),
            clock=lambda: self._now,
        )
        self._last_sent: dict[str, float] = {}

    def report(self, signal: str, value: float) -> None:
        if self._gate.due(signal, value):
            self._send(signal, value)

    def send_event(self, event: str) -> None:
        self._transport.send(f"/{self._element}/{event}")

    def tick(self, dt: float) -> None:
        self._now += dt
        for signal, value in list(self._last_sent.items()):
            if self._gate.due(signal, value):
                self._send(signal, value)

    def _send(self, signal: str, value: float) -> None:
        self._transport.send(f"/{self._element}/{signal}", value)
        self._gate.mark(signal, value)
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
