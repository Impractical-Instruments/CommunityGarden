"""settings.py: one set of defaults, equal to the committed file; merging; unknown-key warnings."""
import json
import logging

import pytest

import settings
from settings import DEFAULTS, load_settings, slab_color, unknown_keys, with_defaults


def _without_comments(node):
    if isinstance(node, dict):
        return {k: _without_comments(v) for k, v in node.items() if not k.startswith("_")}
    return node


def test_defaults_equal_the_committed_settings_file():
    committed = json.loads(settings.SETTINGS.read_text())
    assert DEFAULTS == _without_comments(committed)


def test_the_committed_settings_file_has_no_unknown_keys():
    assert unknown_keys(json.loads(settings.SETTINGS.read_text())) == []


def test_with_defaults_fills_what_is_left_out_and_keeps_what_is_given():
    s = with_defaults({"camera": {"serial": "ABC123"}, "attract_dwell_s": 2})
    assert s["camera"]["serial"] == "ABC123"
    assert s["camera"]["height"] == DEFAULTS["camera"]["height"], "the rest of the block survives"
    assert s["attract_dwell_s"] == 2
    assert s["detection"] == DEFAULTS["detection"]


def test_with_defaults_replaces_lists_whole():
    slabs = [{"near_mm": 500, "far_mm": 900, "slab_id": 0}, {"near_mm": 900, "far_mm": 1500, "slab_id": 1}]
    assert with_defaults({"depth_slabs": slabs})["depth_slabs"] == slabs


def test_with_defaults_does_not_change_defaults_or_its_argument():
    given = {"camera": {"width": 320}}
    out = with_defaults(given)
    out["camera"]["rotation"]["pitch"] = 99
    out["depth_slabs"].append("x")
    assert given == {"camera": {"width": 320}}
    assert DEFAULTS["camera"]["rotation"]["pitch"] == -25
    assert len(DEFAULTS["depth_slabs"]) == 1


def test_unknown_keys_finds_typos_at_any_depth():
    raw = {
        "atract_dwell_s": 2,
        "camera": {"widht": 320, "rotation": {"pich": 1}},
        "shader_app": {"blobs": {"min_confirm_frame": 2, "ease_s": 0.1}},
    }
    assert unknown_keys(raw) == ["atract_dwell_s", "camera.widht", "camera.rotation.pich",
                                 "shader_app.blobs.min_confirm_frame"]


def test_unknown_keys_skips_comments_and_slab_ids():
    raw = {"_comment": "x", "camera": {"_comment": "y"},
           "slab_styles": {"1": {"color": [1, 2, 3]}}}
    assert unknown_keys(raw) == []


@pytest.fixture
def files(tmp_path, monkeypatch):
    main, local = tmp_path / "captcha-settings.json", tmp_path / "captcha-settings.local.json"
    monkeypatch.setattr(settings, "SETTINGS", main)
    monkeypatch.setattr(settings, "SETTINGS_LOCAL", local)
    return main, local


def test_load_with_no_files_is_the_defaults(files):
    assert load_settings() == DEFAULTS


def test_local_file_overrides_part_of_a_block_and_keeps_the_rest(files):
    main, local = files
    main.write_text(json.dumps({"camera": {"fps": 30, "width": 320}}))
    local.write_text(json.dumps({"camera": {"serial": "ABC123", "width": 800}}))
    cam = load_settings()["camera"]
    assert (cam["serial"], cam["width"], cam["fps"]) == ("ABC123", 800, 30)
    assert cam["pos_cm"] == DEFAULTS["camera"]["pos_cm"]


def test_misspelt_key_in_the_local_file_warns(files, caplog):
    _, local = files
    local.write_text(json.dumps({"shader_app": {"blobs": {"min_confirm_frame": 2}}}))
    with caplog.at_level(logging.WARNING):
        load_settings()
    assert "captcha-settings.local.json" in caplog.text
    assert "shader_app.blobs.min_confirm_frame" in caplog.text


def test_local_file_that_does_not_parse_is_skipped_with_a_warning(files, caplog):
    main, local = files
    main.write_text(json.dumps({"attract_dwell_s": 7}))
    local.write_text("{not json")
    with caplog.at_level(logging.WARNING):
        s = load_settings()
    assert s["attract_dwell_s"] == 7
    assert "unreadable" in caplog.text


def test_slab_color():
    assert slab_color(DEFAULTS) == (0, 220, 100)
    assert slab_color(with_defaults({"slab_styles": {"1": {"color": [9, 8, 7]}}}), 1) == (9, 8, 7)
