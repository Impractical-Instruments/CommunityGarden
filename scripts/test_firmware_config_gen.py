"""Firmware network headers are generated from network.json, and the committed ones are current."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKETCH = (
    REPO_ROOT / "Firmware" / "FlowerBeds_Follow_ServoController"
    / "FlowerBeds_Follow_ServoController.ino"
)

_spec = importlib.util.spec_from_file_location(
    "firmware_config_gen", REPO_ROOT / "scripts" / "hooks" / "firmware_config_gen.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

NETWORK = json.loads(gen.NETWORK_JSON.read_text())


def _network(**boards) -> dict:
    return {"firmware": {f"flowerbeds_controller_{n}": entry for n, entry in boards.items()}}


BOARD_1 = {"ip": "192.0.2.50", "mac": "de:ad:be:ef:15:00", "osc_port": 9000}
BOARD_2 = {"ip": "192.0.2.51", "mac": "DE:AD:BE:EF:15:01", "osc_port": 9001}


@pytest.mark.parametrize("path", list(gen.HEADERS), ids=lambda p: p.name)
def test_committed_header_matches_network_json(path):
    assert path.read_text() == gen.HEADERS[path](NETWORK), (
        f"{path.relative_to(REPO_ROOT)} is stale: run python3 scripts/hooks/firmware_config_gen.py"
    )


def test_flowerbeds_header_has_one_branch_per_board():
    header = gen.render_flowerbeds_header(_network(**{"1": BOARD_1, "2": BOARD_2}))
    assert "#if FLOWERBEDS_BOARD == 1\n" in header
    assert "#define CG_MAC { 0xDE, 0xAD, 0xBE, 0xEF, 0x15, 0x00 }\n" in header
    assert "#define CG_IP 192, 0, 2, 50\n" in header
    assert "#elif FLOWERBEDS_BOARD == 2\n" in header
    assert "#define CG_IP 192, 0, 2, 51\n" in header
    assert "#define CG_OSC_PORT 9001\n" in header
    assert '#error "Set FLOWERBEDS_BOARD to 1 or 2' in header


def test_flowerbeds_boards_are_ordered_by_number_not_by_name():
    header = gen.render_flowerbeds_header(_network(**{"10": BOARD_2, "2": BOARD_1}))
    assert header.index("FLOWERBEDS_BOARD == 2") < header.index("FLOWERBEDS_BOARD == 10")


@pytest.mark.parametrize("broken, message", [
    ({**BOARD_1, "mac": None}, "needs 'ip', 'mac' and 'osc_port'"),
    ({**BOARD_1, "ip": None}, "needs 'ip', 'mac' and 'osc_port'"),
    ({**BOARD_1, "mac": "DE:AD:BE:EF:15"}, "is not a MAC address"),
    ({**BOARD_1, "mac": "DE:AD:BE:EF:15:ZZ"}, "is not a MAC address"),
    ({**BOARD_1, "ip": "192.0.2"}, "is not a dotted-quad"),
])
def test_flowerbeds_header_rejects_a_bad_entry(broken, message):
    with pytest.raises(ValueError, match=message):
        gen.render_flowerbeds_header(_network(**{"1": broken}))


def test_flowerbeds_header_needs_at_least_one_board():
    with pytest.raises(ValueError, match="no firmware.flowerbeds_controller"):
        gen.render_flowerbeds_header({"firmware": {"treehouse_jess": BOARD_1}})


def test_sketch_holds_no_address_from_network_json():
    sketch = SKETCH.read_text()
    assert '#include "config.h"' in sketch
    for key, entry in NETWORK["firmware"].items():
        if not key.startswith("flowerbeds_controller_"):
            continue
        ip_args = r",\s*".join(entry["ip"].split("."))
        mac_bytes = r",\s*".join(f"0x{b}" for b in entry["mac"].split(":"))
        assert not re.search(ip_args, sketch), f"the sketch hardcodes {key}'s IP"
        assert not re.search(mac_bytes, sketch, re.I), f"the sketch hardcodes {key}'s MAC"
        assert entry["ip"] not in sketch


# ── What the compiler sees ────────────────────────────────────────────────────
# The sketch's network block, compiled against a stand-in for Arduino's IPAddress.

_PROBE = r'''
#include <cstdint>
#include <cstdio>
typedef uint8_t byte;
struct IPAddress { int o[4]; IPAddress(int a, int b, int c, int d) : o{a, b, c, d} {} };
%s
int main() {
    std::printf("%%02X:%%02X:%%02X:%%02X:%%02X:%%02X %%d.%%d.%%d.%%d %%d\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5],
                ip.o[0], ip.o[1], ip.o[2], ip.o[3], (int)localPort);
}
'''


def _network_block() -> str:
    sketch = SKETCH.read_text()
    start = sketch.index("// --- Network config ---")
    return sketch[start:sketch.index("EthernetUDP Udp;", start)]


def _compile(tmp_path: Path, *flags: str) -> subprocess.CompletedProcess:
    cxx = shutil.which("c++") or shutil.which("g++")
    if cxx is None:
        pytest.skip("no C++ compiler on PATH")
    (tmp_path / "config.h").write_text(gen.FLOWERBEDS_HEADER.read_text())
    (tmp_path / "probe.cpp").write_text(_PROBE % _network_block())
    return subprocess.run(
        [cxx, "-std=c++11", *flags, "probe.cpp", "-o", "probe"],
        cwd=tmp_path, capture_output=True, text=True,
    )


@pytest.mark.parametrize("board", [1, 2])
def test_sketch_compiles_to_the_selected_boards_addresses(board, tmp_path):
    built = _compile(tmp_path, f"-DFLOWERBEDS_BOARD={board}")
    assert built.returncode == 0, built.stderr
    out = subprocess.run([str(tmp_path / "probe")], capture_output=True, text=True).stdout
    entry = NETWORK["firmware"][f"flowerbeds_controller_{board}"]
    assert out.strip() == f"{entry['mac']} {entry['ip']} {entry['osc_port']}"


def test_sketch_does_not_compile_until_a_board_is_chosen(tmp_path):
    built = _compile(tmp_path)
    assert built.returncode != 0
    assert "Set FLOWERBEDS_BOARD to 1 or 2" in built.stderr
