"""Every key in the shipped settings.json is read by some TreeHouse module."""
import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # club_screen defaults it to wayland on import

import club_screen  # noqa: E402

HERE = Path(__file__).parent


def _keys(node) -> set[str]:
    """Every dict key at any depth, except _comment-style keys."""
    if isinstance(node, dict):
        found = {k for k in node if not k.startswith("_")}
        for value in node.values():
            found |= _keys(value)
        return found
    if isinstance(node, list):
        return set().union(*map(_keys, node)) if node else set()
    return set()


def test_every_settings_key_has_a_reader():
    settings = json.loads((HERE / "settings.json").read_text())
    source = "\n".join(p.read_text() for p in HERE.rglob("*.py") if not p.name.startswith("test_"))
    orphans = sorted(k for k in _keys(settings) if f'"{k}"' not in source)
    assert not orphans, f"settings.json keys nothing reads: {orphans}"


def test_club_screen_loads_the_config_it_is_given(tmp_path):
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"club_screen": {"font_size_max": 12}}))
    assert club_screen._load_config(other) == {"font_size_max": 12}
    assert club_screen._load_config(tmp_path / "missing.json") == {}
