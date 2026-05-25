"""Tests for diag.py — controller ping/pong helpers."""
from __future__ import annotations

import socket
import threading

from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import OscMessageBuilder

from diag import osc_ping, parse_found_ids


# ---------------------------------------------------------------------------
# parse_found_ids
# ---------------------------------------------------------------------------

def test_parse_empty():
    assert parse_found_ids("") == set()


def test_parse_single():
    assert parse_found_ids("42") == {42}


def test_parse_csv():
    assert parse_found_ids("13,25,29,42") == {13, 25, 29, 42}


def test_parse_with_spaces_and_trailing_comma():
    assert parse_found_ids("1, 2 , 3,") == {1, 2, 3}


def test_parse_ignores_garbage():
    assert parse_found_ids("1,foo,2") == {1, 2}


# ---------------------------------------------------------------------------
# osc_ping
# ---------------------------------------------------------------------------

def test_osc_ping_timeout_returns_none():
    # No listener on this port — ping must time out and return None.
    # Use TEST-NET-1 (RFC 5737) to guarantee no response.
    result = osc_ping("192.0.2.1", 9999, timeout=0.1)
    assert result is None


def test_osc_ping_parses_valid_pong():
    """Spin up a tiny UDP echo that mimics firmware /cg/ff/pong reply."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind(("127.0.0.1", 0))
    server_port = server_sock.getsockname()[1]
    server_sock.settimeout(2.0)

    def fake_firmware():
        try:
            data, sender = server_sock.recvfrom(1024)
            ping = OscMessage(data)
            assert ping.address == "/cg/ff/ping"
            b = OscMessageBuilder(address="/cg/ff/pong")
            b.add_arg(1, "i")                   # ctrl_id
            b.add_arg(1000000, "i")             # baud
            b.add_arg(4, "i")                   # found_count
            b.add_arg("13,25,29,42", "s")       # found_ids
            b.add_arg(123, "i")                 # pkt_rx_count
            b.add_arg(0, "i")                   # pkt_drop_count
            b.add_arg(42, "i")                  # last_motor_id
            b.add_arg(-12.5, "f")               # last_motor_deg
            server_sock.sendto(b.build().dgram, sender)
        finally:
            server_sock.close()

    t = threading.Thread(target=fake_firmware, daemon=True)
    t.start()

    result = osc_ping("127.0.0.1", server_port, timeout=2.0)
    t.join(timeout=2.0)

    assert result is not None
    assert result["ctrl_id"] == 1
    assert result["baud"] == 1000000
    assert result["found_count"] == 4
    assert result["found_ids"] == "13,25,29,42"
    assert parse_found_ids(result["found_ids"]) == {13, 25, 29, 42}
    assert result["pkt_rx_count"] == 123
    assert result["pkt_drop_count"] == 0
    assert result["last_motor_id"] == 42
    assert result["last_motor_deg"] == -12.5
