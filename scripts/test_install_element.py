"""The shared Element installer (scripts/lib/install-element.sh) and the units it renders."""
from __future__ import annotations

import getpass
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
UNITS = [(element, unit) for element, (units, _) in sorted(ELEMENTS.items()) for unit in units]
# Every command an installer runs that needs root or a real show machine.
STUBBED = ["pip3", "systemctl", "apt-get", "usermod", "ln", "ldconfig", "udevadm", "git", "hostname",
           "loginctl", "sudo"]


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
    }
    env.pop("PRIVATE_ASSETS_REPO", None)
    done = subprocess.run(["bash", str(installer)], env=env, capture_output=True, text=True)
    return unit_dir, log.read_text().splitlines(), done.returncode


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

    assert f"pip3 install --break-system-packages --no-build-isolation -e {root}[{extras}]" in log
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
    assert not any(line.startswith(("systemctl", "pip3")) for line in log)
    assert list(unit_dir.iterdir()) == []


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
        for shared in ("pip3 install", "daemon-reload", "systemctl enable", "/etc/systemd/system"):
            if element == "TreeHouse" and shared == "systemctl enable":
                continue  # `systemctl enable --now seatd` is TreeHouse's own step
            assert shared not in text, f"{element}/deploy/install.sh repeats {shared!r}"
