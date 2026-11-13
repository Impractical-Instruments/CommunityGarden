"""The shipped settings.json loads, and names only what the Pi itself drives."""
from pathlib import Path

from config import load_config
from coordinator import build_controllables

SETTINGS = Path(__file__).parent / "settings.json"


def test_shipped_settings_load():
    config = load_config(str(SETTINGS))
    assert config.looking_glass.scene == "bloom"
    assert config.branch.motors, "the Branch controller needs at least one motor"
    assert [t.name for t in config.locations.targets] == [
        "treehouse_swannatopia", "treehouse_julia", "treehouse_jess",
        "treehouse_dormer", "treehouse_garage",
    ]


def test_controllers_resolve_wherever_settings_json_lives(tmp_path):
    # network.json is found from the OSCFabric package, not from the --config path.
    elsewhere = tmp_path / "settings.json"
    elsewhere.write_text(SETTINGS.read_text())
    config = load_config(str(elsewhere))
    assert len(config.locations.targets) == 5


def test_pi_drives_the_looking_glass_and_the_branches():
    # The LED locations are ESP32-S3 controllers (ADR-0020), reached through
    # LocationSender; the Pi has no LED Controllables of its own.
    names = [c.name for c in build_controllables(load_config(str(SETTINGS)))]
    assert names == ["Looking Glass", "Branches"]
