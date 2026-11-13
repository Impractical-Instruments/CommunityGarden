"""
The OSC bus to the FlowerBeds servo controllers: discovery from network.json, sending, diagnostics.
"""

from __future__ import annotations

import logging
from typing import Callable, Iterable, TypedDict

from pythonosc.udp_client import SimpleUDPClient  # type: ignore[import]

from diag import osc_ping, parse_found_ids

log = logging.getLogger("flower_beds")

# Cross-layer contract (AGENTS.md constraint 2): the firmware in
# Firmware/FlowerBeds_Follow_ServoController/ listens on this address.
OSC_ROT_ADDRESS = "/cg/ff/rot"

_CONTROLLER_PREFIX = "flowerbeds_controller_"


class ControllerEntry(TypedDict):
    name: str
    ip: str
    osc_port: int


def controllers_from_network(network: dict) -> list[ControllerEntry]:
    """Return every `flowerbeds_controller_*` firmware entry of network.json that has an ip and osc_port."""
    out: list[ControllerEntry] = []
    for name, fw in network.get("firmware", {}).items():
        if name.startswith(_CONTROLLER_PREFIX) and fw.get("ip") and fw.get("osc_port"):
            out.append({"name": name, "ip": fw["ip"], "osc_port": fw["osc_port"]})
    return out


class ControllerBus:
    """Every flowerbeds controller on the show network, addressed as one."""

    def __init__(
        self,
        entries: Iterable[ControllerEntry],
        client_factory: Callable[[str, int], SimpleUDPClient] | None = None,
    ) -> None:
        self.entries = list(entries)
        client_factory = client_factory or SimpleUDPClient
        self._clients = [client_factory(e["ip"], e["osc_port"]) for e in self.entries]

    @classmethod
    def from_network(cls, network: dict, **kwargs) -> "ControllerBus":
        return cls(controllers_from_network(network), **kwargs)

    def __len__(self) -> int:
        return len(self._clients)

    def send(self, motor_id: int, deg: float) -> None:
        """
        Send one motor command to every controller (controllers ignore IDs they
        don't own).  `deg` is in the software convention, CCW positive from above;
        the Dynamixel convention is CW positive, so this is the one place the sign flips.
        """
        for client in self._clients:
            client.send_message(OSC_ROT_ADDRESS, [motor_id, -deg])

    def diagnose(self, expected_motor_ids: set[int]) -> list[int]:
        """
        Ping every controller, log scanned servo IDs + packet counters, and
        return the expected motor IDs that no controller reported.

        Empty list = healthy.  Non-empty list = some configured motors will not move.
        """
        seen: set[int] = set()
        for entry in self.entries:
            name, ip, port = entry["name"], entry["ip"], entry["osc_port"]
            pong = osc_ping(ip, port, timeout=0.5)
            if pong is None:
                log.warning("ctrl %s (%s:%d) — no pong (offline or unreachable)", name, ip, port)
                continue
            ids = parse_found_ids(pong["found_ids"])
            seen |= ids
            log.info(
                "ctrl %s (%s) — baud=%d, %d servo(s): %s | rx=%d drop=%d",
                name, ip, pong["baud"], pong["found_count"],
                sorted(ids) or "-", pong["pkt_rx_count"], pong["pkt_drop_count"],
            )
        missing = sorted(expected_motor_ids - seen)
        if missing:
            log.warning(
                "Configured motor IDs not found on any controller: %s "
                "(these flowers will NOT move)", missing,
            )
        return missing
