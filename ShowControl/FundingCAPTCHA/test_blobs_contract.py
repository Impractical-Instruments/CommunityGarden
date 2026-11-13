"""The GLSL shaders restate the blob-records layout; it must agree with blobs_contract.py (ADR-0022)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import blobs_contract as bc

SHADERS = Path(__file__).resolve().parent / "shaders"
STATES = {"EMPTY": bc.BLOB_EMPTY, "TENTATIVE": bc.BLOB_TENTATIVE, "CONFIRMED": bc.BLOB_CONFIRMED,
          "COASTING": bc.BLOB_COASTING, "LOST": bc.BLOB_LOST}


def _glsl(paths):
    return {p: re.sub(r"//[^\n]*", "", p.read_text()) for p in paths}


def _assigned(src: str, name: str):
    """Every integer/float literal assigned to `name` in a const declaration list, e.g. `SLOTS = 8`."""
    return [float(v) for v in re.findall(rf"\b{name}\s*=\s*(-?\d+(?:\.\d*)?)", src)]


def test_every_shader_that_declares_slots_uses_the_contract_count():
    found = {p: _assigned(s, "SLOTS") for p, s in _glsl(SHADERS.rglob("*.glsl")).items()}
    found = {p: v for p, v in found.items() if v}
    assert len(found) >= 5, "expected the blob-reading shaders to declare SLOTS"
    for path, values in found.items():
        assert values == [bc.BLOB_SLOTS], f"{path.relative_to(SHADERS)} declares SLOTS = {values}"


@pytest.mark.parametrize("prefix", ["S_", ""])
def test_glsl_state_values_match_the_contract(prefix):
    checked = 0
    for path, src in _glsl(SHADERS.rglob("*.glsl")).items():
        if not re.search(rf"\b{prefix}EMPTY\s*=", src):
            continue
        if prefix == "" and path.name != "blob_painter.glsl":
            continue
        for state, value in STATES.items():
            assert _assigned(src, f"{prefix}{state}") == [float(value)], f"{path.relative_to(SHADERS)} {prefix}{state}"
        checked += 1
    assert checked >= (4 if prefix else 1)
