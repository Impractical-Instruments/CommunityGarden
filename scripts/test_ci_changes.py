"""The CI path filter (.github/scripts/ci-changes.sh) must never skip a test job
for a path that job's tests can depend on."""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "ci-changes.sh"


def outputs(*paths: str) -> dict[str, str]:
    out = subprocess.run(["bash", str(SCRIPT)], input="\n".join(paths) + "\n",
                         capture_output=True, text=True, check=True).stdout
    return dict(line.split("=", 1) for line in out.splitlines())


def jobs(*paths: str) -> dict[str, bool]:
    return {k: v == "true" for k, v in outputs(*paths).items() if k in ("code", "gl")}


def force(*paths: str) -> str:
    """The changed path that turns testmon selection off, or ''."""
    return outputs(*paths)["force"]


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
    "requirements-dev.txt",
    "pytest.ini",
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


# The force-run list (.github/scripts/shader-force-run.txt): paths testmon cannot
# see, which must run every shader test.

@pytest.mark.parametrize("path", [
    "ShowControl/FundingCAPTCHA/shaders/watering_can/image.glsl",
    "ShowControl/FundingCAPTCHA/shaders/watering_can/setup.json",
    "ShowControl/FundingCAPTCHA/shaders/setups.json",
    "ShowControl/FundingCAPTCHA/images/bg.png",
    "ShowControl/FundingCAPTCHA/captcha-settings.json",
    "ShowControl/FundingCAPTCHA/playlist.json",
    "ShowControl/network.json",
    "requirements-dev.txt",
    "pyproject.toml",
    "pytest.ini",
    "Makefile",
    ".github/workflows/tests.yml",
    ".github/workflows/testmon-data.yml",
    ".github/scripts/ci-changes.sh",
    ".github/scripts/shader-force-run.txt",
])
def test_paths_testmon_cannot_see_force_every_shader_test(path):
    assert jobs(path) == BOTH
    assert force(path) == path


@pytest.mark.parametrize("path", [
    "ShowControl/OSCFabric/test_client.py",
    "ShowControl/OSCFabric/client.py",
    "IIVision/blob_stabilizer.py",
    "ShowControl/FundingCAPTCHA/shadertoy.py",
    "ShowControl/FundingCAPTCHA/games/grid.py",
    "SomethingNew/thing.py",
])
def test_python_code_is_left_to_testmon(path):
    assert jobs(path) == BOTH
    assert force(path) == ""


@pytest.mark.parametrize("path", [
    "docs/a.md",
    "ShowControl/TreeHouse/settings.json",
    "Firmware/x/y.cpp",
])
def test_paths_outside_the_shader_tests_force_nothing(path):
    assert force(path) == ""


def test_first_forcing_path_is_reported():
    assert force("IIVision/pipeline.py", "pytest.ini", "requirements-dev.txt") == "pytest.ini"


def test_no_changed_files_forces_nothing():
    assert force() == ""


def test_force_list_comments_and_blank_lines_are_not_globs():
    lines = (SCRIPT.parent / "shader-force-run.txt").read_text().splitlines()
    assert "" in lines and any(l.startswith("#") for l in lines)
    assert force("#", "# Data the shader tests read.") == ""
