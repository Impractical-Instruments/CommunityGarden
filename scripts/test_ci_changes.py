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


NEITHER  = {"code": False, "gl": False, "firmware": False}
FAST     = {"code": True,  "gl": False, "firmware": False}
BOTH     = {"code": True,  "gl": True,  "firmware": False}   # both Python jobs
FIRMWARE = {"code": False, "gl": False, "firmware": True}
ALL      = {"code": True,  "gl": True,  "firmware": True}


@pytest.mark.parametrize("path", [
    "docs/agents/firmware.md",
    "README.md",
    "ShowControl/FundingCAPTCHA/README.md",
    "LICENSE",
    "Firmware/TreeHouse_BranchController/TreeHouse_BranchController.ino",
    "Firmware/PlayingThePipes_EncoderPico/main.py",
    "Firmware/TreeHouse_Controllers/README.md",
    ".gitignore",
    ".gitattributes",
])
def test_paths_no_test_reads_run_nothing(path):
    assert jobs(path) == NEITHER


@pytest.mark.parametrize("path", [
    "Firmware/TreeHouse_Controllers/src/main.cpp",
    "Firmware/TreeHouse_Controllers/src/signsoflife/main.cpp",
    "Firmware/TreeHouse_Controllers/lib/Weld/Weld.cpp",
    "Firmware/TreeHouse_Controllers/test/test_weld/test_weld.cpp",
    "Firmware/TreeHouse_Controllers/platformio.ini",
])
def test_treehouse_controllers_run_only_the_firmware_job(path):
    assert jobs(path) == FIRMWARE


def test_generated_treehouse_header_runs_its_python_test_and_the_firmware_job():
    assert jobs("Firmware/TreeHouse_Controllers/include/net_config.h") == {
        "code": True, "gl": False, "firmware": True,
    }


@pytest.mark.parametrize("path", [
    "Firmware/FlowerBeds_Follow_ServoController/config.h",
    "Firmware/FlowerBeds_Follow_ServoController/FlowerBeds_Follow_ServoController.ino",
])
def test_firmware_a_test_reads_runs_the_fast_job(path):
    assert jobs(path) == FAST


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
    "ShowControl/SomethingNew/thing.py",
    "scripts/install-git-hooks.sh",
    "scripts/hooks/firmware_config_gen.py",
    "pyproject.toml",
])
def test_shared_python_runs_both_python_jobs(path):
    assert jobs(path) == BOTH


@pytest.mark.parametrize("path", [
    "Makefile",
    ".github/workflows/tests.yml",
    ".github/scripts/ci-changes.sh",
    "SomethingNew/thing.py",
])
def test_ci_config_and_unrecognised_paths_run_everything(path):
    assert jobs(path) == ALL


def test_one_relevant_path_among_many_is_enough():
    assert jobs("docs/a.md", "Firmware/x/y.cpp", "ShowControl/TreeHouse/led.py") == FAST
    assert jobs("docs/a.md", "Firmware/TreeHouse_Controllers/lib/Rng/Rng.h", "ShowControl/TreeHouse/led.py") == {
        "code": True, "gl": False, "firmware": True,
    }
    assert jobs("docs/a.md", "ShowControl/TreeHouse/led.py", "IIVision/pipeline.py") == BOTH


def test_no_changed_files_runs_nothing():
    assert jobs() == NEITHER
