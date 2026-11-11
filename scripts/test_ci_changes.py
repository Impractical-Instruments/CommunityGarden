"""The CI path filter (.github/scripts/ci-changes.sh) must never skip a test job
for a path that job's tests can depend on."""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "ci-changes.sh"


def jobs(*paths: str) -> dict[str, bool]:
    out = subprocess.run(["bash", str(SCRIPT)], input="\n".join(paths) + "\n",
                         capture_output=True, text=True, check=True).stdout
    return {k: v == "true" for k, v in (line.split("=") for line in out.splitlines())}


NEITHER = {"code": False, "gl": False}
FAST    = {"code": True,  "gl": False}
BOTH    = {"code": True,  "gl": True}


@pytest.mark.parametrize("path", [
    "docs/agents/firmware.md",
    "README.md",
    "ShowControl/FundingCAPTCHA/README.md",
    "LICENSE",
    "TouchOSC/FlowerBedTester.tosc",
    "Firmware/TreeHouse_Controllers/src/main.cpp",
    ".gitignore",
    ".gitattributes",
])
def test_paths_no_test_reads_run_nothing(path):
    assert jobs(path) == NEITHER


@pytest.mark.parametrize("path", [
    "ShowControl/FlowerBeds/main.py",
    "ShowControl/TreeHouse/settings.json",
    "ShowControl/Dashboard/serve.py",
    "ShowControl/PlayingThePipes/main.py",
])
def test_other_elements_run_only_the_fast_job(path):
    assert jobs(path) == FAST


@pytest.mark.parametrize("path", [
    "ShowControl/FundingCAPTCHA/shadertoy.py",
    "ShowControl/FundingCAPTCHA/shaders/watering_can/image.glsl",
    "IIVision/blob_stabilizer.py",
    "ShowControl/OSCFabric/client.py",
    "ShowControl/network.json",
    "Makefile",
    ".github/workflows/tests.yml",
    ".github/scripts/ci-changes.sh",
    "scripts/install-git-hooks.sh",
    "SomethingNew/thing.py",
    "pyproject.toml",
])
def test_shared_and_unrecognised_paths_run_everything(path):
    assert jobs(path) == BOTH


def test_one_relevant_path_among_many_is_enough():
    assert jobs("docs/a.md", "Firmware/x/y.cpp", "ShowControl/TreeHouse/led.py") == FAST
    assert jobs("docs/a.md", "ShowControl/TreeHouse/led.py", "IIVision/pipeline.py") == BOTH


def test_no_changed_files_runs_nothing():
    assert jobs() == NEITHER
