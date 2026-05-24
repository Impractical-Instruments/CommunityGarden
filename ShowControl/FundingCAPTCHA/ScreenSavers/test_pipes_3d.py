"""Smoke tests for the 3D vines screensaver."""
from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import numpy as np
import pytest

_HERE = Path(__file__).parent
_SRC  = _HERE / "pipes_3d.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("ss_pipes_3d", _SRC)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules["ss_pipes_3d"] = mod    # dataclass field resolution needs this
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_module()


@pytest.fixture(autouse=True)
def _seed():
    random.seed(1234)


def test_pipe_spawns_with_starting_joint(mod):
    occupied: set = set()
    p = mod._Pipe(occupied)
    assert p.alive
    assert len(p.boxes) == 1                 # the initial knuckle
    assert len(occupied) == 1


def test_pipe_step_adds_segment_and_occupies_cell(mod):
    occupied: set = set()
    p = mod._Pipe(occupied)
    before = len(p.boxes)
    cells_before = len(occupied)
    p.step()
    assert len(p.boxes) >= before + 1        # at least one segment box
    assert len(occupied) == cells_before + 1


def test_pipe_stops_after_max_segments(mod):
    occupied: set = set()
    p = mod._Pipe(occupied)
    for _ in range(mod._MAX_SEGS_PER_PIPE * 2):
        p.step()
    assert not p.alive
    # final knuckle is appended on termination
    assert any(np.array_equal(b.half, np.full(3, mod._JOINT_HALF, dtype=np.float32))
               for b in p.boxes)


def test_pipe_respects_bounds(mod):
    occupied: set = set()
    p = mod._Pipe(occupied)
    for _ in range(mod._MAX_SEGS_PER_PIPE):
        p.step()
        cell = p._cell
        assert np.all(cell >= -mod._GRID_HALF)
        assert np.all(cell <  mod._GRID_HALF)


def test_pipes_do_not_collide(mod):
    occupied: set = set()
    pipes = [mod._Pipe(occupied) for _ in range(4)]
    for _ in range(40):
        for p in pipes:
            p.step()
    cells_claimed = sum(p._segs_made + 1 for p in pipes if hasattr(p, "_segs_made"))
    assert len(occupied) == cells_claimed     # no double-occupancy


def test_seg_box_geometry(mod):
    a = np.array([0, 0, 0], dtype=np.int32)
    b = np.array([1, 0, 0], dtype=np.int32)
    box = mod._seg_box(a, b, (0, 0, 0))
    assert np.allclose(box.center, [0.5, 0.0, 0.0])
    assert box.half[0] == pytest.approx(mod._CELL_SIZE * 0.5)
    assert box.half[1] == pytest.approx(mod._PIPE_HALF_W)
    assert box.half[2] == pytest.approx(mod._PIPE_HALF_W)


def test_create_returns_screensaver(mod):
    saver = mod.create({})
    assert hasattr(saver, "update")
    assert hasattr(saver, "draw")
    # update() runs without a frame argument
    saver.update(0.05, None)
