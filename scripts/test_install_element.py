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
    # Element: (unit file, installed service name, pyproject extras)
    "Dashboard": ("dashboard.service", "cg-dashboard", "dashboard"),
    "FlowerBeds": ("flowerbeds.service", "flowerbeds", "flowerbeds,camera"),
    "FundingCAPTCHA": ("captcha.service", "captcha", "fundingcaptcha,camera"),
    "TreeHouse": ("treehouse.service", "treehouse", "treehouse"),
}
# Every command an installer runs that needs root or a real Pi.
STUBBED = ["pip3", "systemctl", "apt-get", "usermod", "ln", "ldconfig", "udevadm", "git", "hostname"]


def _clone_at(root: Path, element: str) -> Path:
    """Copy the installer pieces to `root`, standing in for a clone at another path."""
    shutil.copytree(REPO_ROOT / "scripts" / "lib", root / "scripts" / "lib")
    deploy = Path("ShowControl") / element / "deploy"
    shutil.copytree(REPO_ROOT / deploy, root / deploy)
    return root / deploy / "install.sh"


def _run(installer: Path, tmp_path: Path) -> tuple[Path, list[str]]:
    """Run an installer with the root-only commands stubbed. Returns (unit dir, command log)."""
    bin_dir, unit_dir, log = tmp_path / "bin", tmp_path / "units", tmp_path / "log"
    bin_dir.mkdir()
    unit_dir.mkdir()
    for name in STUBBED:
        stub = bin_dir / name
        stub.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n')
        stub.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "SUDO_USER": getpass.getuser(),
        "SYSTEMD_UNIT_DIR": str(unit_dir),
    }
    env.pop("PRIVATE_ASSETS_REPO", None)
    subprocess.run(["bash", str(installer)], env=env, check=True, capture_output=True, text=True)
    return unit_dir, log.read_text().splitlines()


@pytest.mark.parametrize("element", sorted(ELEMENTS))
def test_installs_from_a_clone_at_any_path(element, tmp_path):
    unit_file, service, extras = ELEMENTS[element]
    # A space and an ampersand: both would corrupt a naive sed replacement.
    root = tmp_path / "some where & else" / "Garden"
    installer = _clone_at(root, element)
    # FundingCAPTCHA writes a udev rule under /etc; point it at the scratch directory.
    if element == "FundingCAPTCHA":
        text = installer.read_text().replace("/etc/udev/rules.d", str(tmp_path))
        installer.write_text(text)

    unit_dir, log = _run(installer, tmp_path)

    unit = (unit_dir / f"{service}.service").read_text()
    assert f"WorkingDirectory={root}/ShowControl/{element}\n" in unit
    assert f"User={getpass.getuser()}\n" in unit
    assert not re.search(r"@[A-Z_]+@", unit), "an unfilled placeholder is left in the unit"
    assert "/home/ii" not in unit

    assert f"pip3 install --break-system-packages --no-build-isolation -e {root}[{extras}]" in log
    systemd = [line for line in log if line.startswith("systemctl ") and "seatd" not in line]
    assert systemd == [
        "systemctl daemon-reload",
        f"systemctl enable {service}.service",
        f"systemctl restart {service}.service",
    ]


@pytest.mark.parametrize("element", sorted(ELEMENTS))
def test_unit_uses_only_known_placeholders(element):
    unit = (REPO_ROOT / "ShowControl" / element / "deploy" / ELEMENTS[element][0]).read_text()
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
