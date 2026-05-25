"""
FlowerBeds firmware diagnostics — OSC ping/pong client.

Firmware (Firmware/FlowerBeds_Follow_ServoController) replies to /cg/ff/ping
with /cg/ff/pong carrying its boot-scan results and packet counters.  Both
the layout tool and the main app use this to verify which servos each
controller actually sees and whether OSC traffic is reaching it.
"""
from __future__ import annotations

import socket
from typing import TypedDict

from pythonosc.osc_message import OscMessage  # type: ignore[import]
from pythonosc.osc_message_builder import OscMessageBuilder  # type: ignore[import]


class ControllerStatus(TypedDict):
    ctrl_id: int
    baud: int
    found_count: int
    found_ids: str        # comma-separated, e.g. "13,25,29,42"
    pkt_rx_count: int
    pkt_drop_count: int
    last_motor_id: int
    last_motor_deg: float


def osc_ping(ip: str, port: int, timeout: float = 0.5) -> ControllerStatus | None:
    """
    Send /cg/ff/ping to (ip, port) and wait up to `timeout` seconds for
    /cg/ff/pong.  Returns the parsed payload or None on timeout/parse error.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("", 0))
        sock.settimeout(timeout)
        ping = OscMessageBuilder(address="/cg/ff/ping").build()
        sock.sendto(ping.dgram, (ip, port))
        data, _ = sock.recvfrom(1024)
        pong = OscMessage(data)
        if pong.address != "/cg/ff/pong" or len(pong.params) < 8:
            return None
        p = pong.params
        return {
            "ctrl_id":         int(p[0]),
            "baud":            int(p[1]),
            "found_count":     int(p[2]),
            "found_ids":       str(p[3]),
            "pkt_rx_count":    int(p[4]),
            "pkt_drop_count":  int(p[5]),
            "last_motor_id":   int(p[6]),
            "last_motor_deg":  float(p[7]),
        }
    except (OSError, ValueError, IndexError):
        return None
    finally:
        sock.close()


def parse_found_ids(csv: str) -> set[int]:
    """Parse the comma-separated 'found_ids' field from a pong into a set of ints."""
    if not csv:
        return set()
    out: set[int] = set()
    for part in csv.split(","):
        part = part.strip()
        if part:
            try:
                out.add(int(part))
            except ValueError:
                pass
    return out
