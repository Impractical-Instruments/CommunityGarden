"""The shared Element installer (scripts/lib/install-element.sh) and the units it renders."""
from __future__ import annotations

import getpass
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ELEMENTS = {
    # Element: ({unit file: installed service name}, pyproject extras)
    "Dashboard": ({"dashboard.service": "cg-dashboard"}, "dashboard"),
    "FlowerBeds": ({"flowerbeds.service": "flowerbeds"}, "flowerbeds,camera"),
    "FundingCAPTCHA": ({"captcha.service": "captcha"}, "fundingcaptcha,camera"),
    "PlayingThePipes": (
        {"pipes-reuben.service": "pipes-reuben", "pipes-bridge.service": "pipes-bridge"},
        "pipes",
    ),
    "TreeHouse": ({"treehouse.service": "treehouse"}, "treehouse"),
}
# Elements whose installer sets PYTHON_DEPS=pip; the rest install with uv.
PIP_ELEMENTS = {"FundingCAPTCHA", "TreeHouse"}
UNITS = [(element, unit) for element, (units, _) in sorted(ELEMENTS.items()) for unit in units]
# Every command an installer runs that needs root or a real show machine.
STUBBED = ["pip3", "systemctl", "apt-get", "usermod", "ln", "ldconfig", "udevadm", "git", "hostname",
           "loginctl", "sudo", "chown", "uv"]


def _clone_at(root: Path, element: str) -> Path:
    """Copy the installer pieces to `root`, standing in for a clone at another path."""
    shutil.copytree(REPO_ROOT / "scripts" / "lib", root / "scripts" / "lib")
    deploy = Path("ShowControl") / element / "deploy"
    shutil.copytree(REPO_ROOT / deploy, root / deploy)
    installer = root / deploy / "install.sh"
    if element == "PlayingThePipes":
        # It builds the reuben submodule with the service user's cargo; stand in for both.
        (root / "vendor" / "reuben").mkdir(parents=True)
        (root / "vendor" / "reuben" / "Cargo.toml").touch()
        shutil.copy(REPO_ROOT / "ShowControl" / "network.json", root / "ShowControl" / "network.json")
        installer.write_text(installer.read_text().replace('"$USER_HOME/.cargo/bin/cargo"', "/bin/true"))
    return installer


def _run(installer: Path, tmp_path: Path, fail: str | None = None) -> tuple[Path, list[str], int]:
    """Run an installer with the root-only commands stubbed; a command line containing `fail`
    exits 1. Returns (unit dir, command log, exit status)."""
    bin_dir, unit_dir, log = tmp_path / "bin", tmp_path / "units", tmp_path / "log"
    bin_dir.mkdir()
    unit_dir.mkdir()
    for name in STUBBED:
        stub = bin_dir / name
        failing = f'case "$*" in *"{fail}"*) exit 1;; esac\n' if fail else ""
        stub.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n{failing}')
        stub.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "SUDO_USER": getpass.getuser(),
        "SYSTEMD_UNIT_DIR": str(unit_dir),
        "PIPES_REUBEN_ENV_FILE": str(_env_file(tmp_path)),
        "CG_UV": str(bin_dir / "uv"),
    }
    env.pop("PRIVATE_ASSETS_REPO", None)
    done = subprocess.run(["bash", str(installer)], env=env, capture_output=True, text=True)
    return unit_dir, log.read_text().splitlines(), done.returncode


def _uv_sync(root: Path, extras: str, tmp_path: Path) -> str:
    """The uv sync line the installer runs as the service user, as the sudo stub logs it."""
    flags = " ".join(f"--extra {extra}" for extra in extras.split(","))
    return (f"sudo -u {getpass.getuser()} -H {tmp_path / 'bin' / 'uv'} --directory {root}"
            f" sync --locked --no-dev --inexact {flags}")


def _env_file(tmp_path: Path) -> Path:
    """Where pipes-reuben's EnvironmentFile goes in a test run."""
    return tmp_path / "etc" / "community-garden" / "pipes-reuben.env"


@pytest.mark.parametrize("element", sorted(ELEMENTS))
def test_installs_from_a_clone_at_any_path(element, tmp_path):
    units, extras = ELEMENTS[element]
    services = list(units.values())
    # A space and an ampersand: both would corrupt a naive sed replacement.
    root = tmp_path / "some where & else" / "Garden"
    installer = _clone_at(root, element)
    # FundingCAPTCHA writes a udev rule under /etc; point it at the scratch directory.
    if element == "FundingCAPTCHA":
        text = installer.read_text().replace("/etc/udev/rules.d", str(tmp_path))
        installer.write_text(text)

    unit_dir, log, status = _run(installer, tmp_path)

    assert status == 0
    assert sorted(p.name for p in unit_dir.iterdir()) == sorted(f"{s}.service" for s in services)
    for service in services:
        unit = (unit_dir / f"{service}.service").read_text()
        assert f"WorkingDirectory={root}/ShowControl/{element}\n" in unit
        assert f"User={getpass.getuser()}\n" in unit
        assert not re.search(r"@[A-Z_]+@", unit), "an unfilled placeholder is left in the unit"
        assert "/home/ii" not in unit

    if element in PIP_ELEMENTS:
        assert f"pip3 install --break-system-packages --no-build-isolation -e {root}[{extras}]" in log
    else:
        assert _uv_sync(root, extras, tmp_path) + " --offline" in log
        assert not any(line.startswith("pip3") for line in log)
    systemd = [line for line in log if line.startswith("systemctl ") and "seatd" not in line]
    assert systemd == [
        "systemctl daemon-reload",
        *(f"systemctl enable {service}.service" for service in services),
        *(f"systemctl restart {service}.service" for service in services),
    ]


def test_pipes_builds_reuben_as_the_service_user_before_any_restart(tmp_path):
    root = tmp_path / "Garden"
    _, log, status = _run(_clone_at(root, "PlayingThePipes"), tmp_path)

    assert status == 0
    build = (f"sudo -u {getpass.getuser()} -H /bin/true build --release --locked --offline"
             " -p reuben-native --bin reuben")
    assert build in log
    assert log.index(build) < log.index("systemctl daemon-reload")


def test_pipes_failed_build_leaves_the_services_untouched(tmp_path):
    root = tmp_path / "Garden"
    unit_dir, log, status = _run(_clone_at(root, "PlayingThePipes"), tmp_path, fail="build --release")

    assert status != 0
    assert not any(line.startswith(("systemctl", "pip3")) or " sync " in line for line in log)
    assert list(unit_dir.iterdir()) == []


def _env(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines())


def test_uv_goes_online_only_when_its_cache_falls_short(tmp_path):
    root = tmp_path / "Garden"
    _, log, status = _run(_clone_at(root, "Dashboard"), tmp_path, fail="--offline")

    assert status == 0
    sync = _uv_sync(root, "dashboard", tmp_path)
    assert log.index(sync + " --offline") < log.index(sync) < log.index("systemctl daemon-reload")


def test_no_uv_stops_before_any_service_changes(tmp_path):
    installer = _clone_at(tmp_path / "Garden", "Dashboard")
    bin_dir, unit_dir, log = tmp_path / "bin", tmp_path / "units", tmp_path / "log"
    bin_dir.mkdir()
    unit_dir.mkdir()
    for name in STUBBED:
        (bin_dir / name).write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n')
        (bin_dir / name).chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "SUDO_USER": getpass.getuser(),
           "SYSTEMD_UNIT_DIR": str(unit_dir), "CG_UV": str(tmp_path / "no-uv-here")}

    done = subprocess.run(["bash", str(installer)], env=env, capture_output=True, text=True)

    assert done.returncode != 0
    assert "astral.sh/uv/install.sh" in done.stderr
    assert not log.exists() or not any(line.startswith("systemctl") for line in log.read_text().splitlines())
    assert list(unit_dir.iterdir()) == []


@pytest.mark.parametrize("element,unit_file", UNITS)
def test_python_units_run_the_python_their_installer_sets_up(element, unit_file):
    unit = (REPO_ROOT / "ShowControl" / element / "deploy" / unit_file).read_text()
    installer = (REPO_ROOT / "ShowControl" / element / "deploy" / "install.sh").read_text()
    assert ("PYTHON_DEPS=pip" in installer) == (element in PIP_ELEMENTS)
    exec_start = re.search(r"^ExecStart=(\S+)", unit, flags=re.M).group(1)
    if "reuben" in exec_start:
        return
    expected = "/usr/bin/python3" if element in PIP_ELEMENTS else "@REPO_ROOT@/.venv/bin/python"
    assert exec_start == expected


def test_pipes_writes_the_structure_channel_token_and_address(tmp_path):
    _, log, status = _run(_clone_at(tmp_path / "Garden", "PlayingThePipes"), tmp_path)

    assert status == 0
    env_file = _env_file(tmp_path)
    port = json.loads((REPO_ROOT / "ShowControl" / "network.json").read_text())["elements"]["pipes"]["reuben_structure_port"]
    env = _env(env_file)
    assert env["PIPES_STRUCTURE_ADDR"] == f"0.0.0.0:{port}"
    assert re.fullmatch(r"[0-9a-f]{32}", env["REUBEN_STRUCTURE_TOKEN"])
    assert env_file.stat().st_mode & 0o777 == 0o640, "the token must not be world-readable"
    assert f"chown root:{getpass.getuser()} {env_file}.new" in log
    assert log.index(f"chown root:{getpass.getuser()} {env_file}.new") < log.index("systemctl daemon-reload")


def test_pipes_keeps_the_token_across_deploys(tmp_path):
    env_file = _env_file(tmp_path)
    env_file.parent.mkdir(parents=True)
    env_file.write_text("REUBEN_STRUCTURE_TOKEN=0123456789abcdef0123456789abcdef\nPIPES_STRUCTURE_ADDR=0.0.0.0:1\n")

    _, _, status = _run(_clone_at(tmp_path / "Garden", "PlayingThePipes"), tmp_path)

    assert status == 0
    env = _env(env_file)
    assert env["REUBEN_STRUCTURE_TOKEN"] == "0123456789abcdef0123456789abcdef"
    assert env["PIPES_STRUCTURE_ADDR"] != "0.0.0.0:1", "the address follows network.json on every deploy"


def test_pipes_reuben_unit_reads_the_installers_environment_file():
    unit = (REPO_ROOT / "ShowControl" / "PlayingThePipes" / "deploy" / "pipes-reuben.service").read_text()
    installer = (REPO_ROOT / "ShowControl" / "PlayingThePipes" / "deploy" / "install.sh").read_text()
    path = re.search(r"^EnvironmentFile=(\S+)$", unit, flags=re.M).group(1)
    assert f'PIPES_REUBEN_ENV_FILE:-{path}}}' in installer
    assert "--structure-addr ${PIPES_STRUCTURE_ADDR}" in unit


def test_pipes_refuses_a_sample_that_is_still_an_lfs_pointer(tmp_path):
    root = tmp_path / "Garden"
    installer = _clone_at(root, "PlayingThePipes")
    media = root / "ShowControl" / "PlayingThePipes" / "Lamplight2026" / "media"
    media.mkdir(parents=True)
    (media / "real.wav").write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    (media / "pointer.wav").write_text("version https://git-lfs.github.com/spec/v1\noid sha256:0\nsize 1\n")

    unit_dir, log, status = _run(installer, tmp_path)

    assert status != 0
    assert any("lfs pull" in line for line in log), "it should try to pull before giving up"
    assert not any(line.startswith("systemctl") for line in log)
    assert list(unit_dir.iterdir()) == []


def test_several_units_need_one_file_per_service(tmp_path):
    root = tmp_path / "Garden"
    installer = _clone_at(root, "PlayingThePipes")
    (installer.parent / "stray.service").write_text("[Unit]\n")

    unit_dir, log, status = _run(installer, tmp_path)

    assert status != 0
    assert list(unit_dir.iterdir()) == []


@pytest.mark.skipif(shutil.which("systemd-analyze") is None, reason="needs systemd-analyze")
@pytest.mark.parametrize("unit", ["pipes-reuben", "pipes-bridge"])
def test_pipes_units_pass_systemd_analyze(unit, tmp_path):
    """The rendered unit, with its executable swapped for one that exists on this machine."""
    lib = REPO_ROOT / "scripts" / "lib" / "install-element.sh"
    source = REPO_ROOT / "ShowControl" / "PlayingThePipes" / "deploy" / f"{unit}.service"
    script = f'DEPLOY_DIR=x; . "{lib}" >/dev/null; REPO_ROOT="{REPO_ROOT}"; render_unit "{source}"'
    env = {**os.environ, "SUDO_USER": getpass.getuser()}
    rendered = subprocess.run(["bash", "-c", script], env=env, check=True, capture_output=True, text=True).stdout
    rendered = re.sub(r'^ExecStart="?\S+', "ExecStart=/bin/true", rendered, flags=re.M)
    assert "ExecStart=/bin/true" in rendered
    path = tmp_path / f"{unit}.service"
    path.write_text(rendered)

    done = subprocess.run(["systemd-analyze", "verify", str(path)], capture_output=True, text=True)

    complaints = [line for line in done.stderr.splitlines() if path.name in line]
    assert done.returncode == 0 and not complaints, done.stderr


@pytest.mark.parametrize("element,unit_file", UNITS)
def test_unit_uses_only_known_placeholders(element, unit_file):
    unit = (REPO_ROOT / "ShowControl" / element / "deploy" / unit_file).read_text()
    assert set(re.findall(r"@[A-Z_]+@", unit)) <= {"@REPO_ROOT@", "@SERVICE_USER@", "@SERVICE_UID@"}
    assert "WorkingDirectory=@REPO_ROOT@/" in unit
    assert "User=@SERVICE_USER@" in unit


def test_no_installer_repeats_the_shared_steps():
    for element in ELEMENTS:
        text = (REPO_ROOT / "ShowControl" / element / "deploy" / "install.sh").read_text()
        assert "scripts/lib/install-element.sh" in text
        for shared in ("pip3 install", "uv sync", " sync --locked", "daemon-reload", "systemctl enable", "/etc/systemd/system"):
            if element == "TreeHouse" and shared == "systemctl enable":
                continue  # `systemctl enable --now seatd` is TreeHouse's own step
            assert shared not in text, f"{element}/deploy/install.sh repeats {shared!r}"
