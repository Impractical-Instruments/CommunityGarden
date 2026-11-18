"""The level editor's model: every edit it can make, with no drawing and no display."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from editor.level_model import LevelModel
from levels import DEFAULT_LEVEL, Levels


@pytest.fixture
def model(tmp_path: Path) -> LevelModel:
    """A model with one level, saving to a file under tmp_path."""
    return LevelModel([{"prompt": "P", "image": "two_tone.png", "grid": [3, 3],
                        "valid_cells": []}], Levels(tmp_path / "levels.json"))


# ── The crop_align field ───────────────────────────────────────────────────────

def test_align_defaults_to_center_when_absent(model):
    assert model.align() == "center"


def test_align_reads_the_stored_value(model):
    model.level["crop_align"] = "bottom-right"
    assert model.align() == "bottom-right"


def test_align_ignores_an_unknown_anchor(model):
    model.level["crop_align"] = "sideways"
    assert model.align() == "center"


def test_set_align_stores_the_anchor_and_marks_dirty(model):
    model.set_align("top")
    assert model.level["crop_align"] == "top"
    assert model.dirty is True


def test_set_align_center_omits_the_key(model):
    """Center is the default — writing it would add a key to every level."""
    model.level["crop_align"] = "top"
    model.set_align("center")
    assert "crop_align" not in model.level
    assert model.dirty is True


# ── Opening ────────────────────────────────────────────────────────────────────

def test_open_reads_the_store(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    levels = [{"prompt": "P", "image": "private/x/a.jpg", "grid": [2, 2], "valid_cells": []}]
    p.write_text(json.dumps(levels))
    assert LevelModel.open(Levels(p)).levels == levels


def test_open_missing_file_gives_one_default_level(tmp_path: Path):
    assert LevelModel.open(Levels(tmp_path / "nope.json")).levels == [DEFAULT_LEVEL]


def test_a_new_default_level_is_a_copy(tmp_path: Path):
    m = LevelModel.open(Levels(tmp_path / "nope.json"))
    m.toggle((0, 0))
    assert DEFAULT_LEVEL["valid_cells"] == [[1, 1]]


# ── Cells and fields ───────────────────────────────────────────────────────────

def test_toggle_adds_then_removes_a_cell(model):
    model.toggle((1, 2))
    assert model.valid_cells == {(1, 2)} and model.dirty
    model.toggle((1, 2))
    assert model.valid_cells == set()


def test_clear_cells(model):
    model.toggle((0, 0))
    model.clear_cells()
    assert model.level["valid_cells"] == []


def test_shrinking_the_grid_drops_cells_outside_it(model):
    model.level["valid_cells"] = [[2, 0], [0, 2], [0, 0]]
    model.adj_cols(-1)
    assert model.valid_cells == {(0, 2), (0, 0)}
    model.adj_rows(-1)
    assert model.valid_cells == {(0, 0)}


def test_grid_size_is_clamped_to_2_through_8(model):
    for _ in range(10):
        model.adj_cols(-1)
        model.adj_rows(+1)
    assert model.grid_dims() == (2, 8)


def test_difficulty_is_clamped_to_1_through_5(model):
    for _ in range(10):
        model.adj_difficulty(+1)
    assert model.level["difficulty"] == 5
    for _ in range(10):
        model.adj_difficulty(-1)
    assert model.level["difficulty"] == 1


def test_timer_has_a_floor_of_5s(model):
    for _ in range(20):
        model.adj_timer(-5)
    assert model.level["timer_s"] == 5


def test_hold_can_be_added_adjusted_and_removed(model):
    model.add_hold()
    assert model.level["hold_s"] == 1.0
    model.adj_hold(-0.5)
    model.adj_hold(-0.5)
    assert model.level["hold_s"] == 0.5
    model.remove_hold()
    assert "hold_s" not in model.level


def test_set_image_and_prompt_mark_dirty(model):
    model.set_image(None)
    assert model.level["image"] is None and model.dirty
    model.dirty = False
    model.set_prompt("Q")
    assert model.level["prompt"] == "Q" and model.dirty


# ── The list ───────────────────────────────────────────────────────────────────

def test_new_level_is_inserted_after_the_current_one_and_selected(model):
    model.new_level()
    assert len(model.levels) == 2 and model.idx == 1
    assert model.level == DEFAULT_LEVEL
    assert model.take_notice() == "New level added"
    assert model.take_notice() == ""


def test_nav_wraps_around(model):
    model.new_level()
    model.nav(+1)
    assert model.idx == 0
    model.nav(-1)
    assert model.idx == 1


def test_cannot_delete_the_only_level(model):
    model.delete_level()
    assert len(model.levels) == 1 and not model.dirty
    assert "only level" in model.take_notice()


def test_delete_level_keeps_the_index_in_range(model):
    model.new_level()
    model.delete_level()
    assert len(model.levels) == 1 and model.idx == 0 and model.dirty


# ── Saving ─────────────────────────────────────────────────────────────────────

def test_save_writes_to_its_store_and_clears_dirty(model):
    model.set_prompt("Saved prompt")
    model.save()
    assert json.loads(model.store.path.read_text())[0]["prompt"] == "Saved prompt"
    assert model.dirty is False
    assert model.take_notice() == "Saved!"


def test_save_keeps_the_same_level_selected_after_sorting(tmp_path: Path):
    m = LevelModel([{"prompt": "z", "image": "b.png"}, {"prompt": "a", "image": "a.png"}],
                   Levels(tmp_path / "l.json"))
    m.save()
    assert m.level["prompt"] == "z" and m.idx == 1


def test_save_creates_a_missing_parent_directory(tmp_path: Path, model):
    """A typoed --levels path (missing parent dir) must not crash the editor on Ctrl+S."""
    p = tmp_path / "shwo" / "levels.json"
    model.store = Levels(p)
    model.save()
    assert p.exists()
    assert "Saved" in model.take_notice()


def test_save_survives_an_unwritable_target(tmp_path: Path, model):
    """Anything else the write can throw is reported, not raised."""
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x")
    model.store = Levels(blocker / "levels.json")  # "parent" is a file, mkdir fails
    model.set_prompt("keep me")
    model.save()  # must not raise
    assert "FAILED" in model.take_notice()
    assert model.dirty is True
