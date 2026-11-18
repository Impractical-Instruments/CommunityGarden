"""scripts/deploy.sh, run against a "show machine" that is a directory on this one.

A stand-in `ssh` runs the remote command locally, so the pushes and the remote
checkout are real git; only `sudo` (the installer run) is stubbed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
    # The submodule is cloned from a local path.
    "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "protocol.file.allow", "GIT_CONFIG_VALUE_0": "always",
}


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, env={**os.environ, **GIT_ENV},
                          check=True, capture_output=True, text=True)
    return done.stdout.strip()


def _commit(repo: Path, name: str) -> str:
    (repo / name).write_text(name)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", name)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def garden(tmp_path):
    """A laptop clone with a vendor/reuben submodule, and a box cloned from it before the
    laptop moved on. Returns (laptop, box, env for deploy.sh, sudo log)."""
    upstream = tmp_path / "reuben-upstream"
    upstream.mkdir()
    _git(upstream, "init", "-q", "-b", "main")
    _commit(upstream, "one")

    laptop = tmp_path / "laptop"
    laptop.mkdir()
    _git(laptop, "init", "-q", "-b", "main")
    (laptop / "scripts").mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "deploy.sh", laptop / "scripts" / "deploy.sh")
    _git(laptop, "submodule", "add", "-q", str(upstream), "vendor/reuben")
    _commit(laptop, "first")

    box = tmp_path / "box"
    _git(tmp_path, "clone", "-q", "--recurse-submodules", str(laptop), str(box))
    _git(box, "config", "receive.denyCurrentBranch", "updateInstead")
    # The box can no longer reach where reuben came from: a deploy must not need it.
    shutil.rmtree(upstream)

    bin_dir, log = tmp_path / "bin", tmp_path / "sudo.log"
    bin_dir.mkdir()
    log.touch()
    # ssh [-t] <host> <command>: run the command here. git calls it the same way.
    (bin_dir / "ssh").write_text('#!/bin/sh\n[ "$1" = -t ] && shift\nshift\nexec sh -c "$*"\n')
    (bin_dir / "sudo").write_text(f'#!/bin/sh\necho "$*" >> "{log}"\n')
    for stub in bin_dir.iterdir():
        stub.chmod(0o755)
    env = {**os.environ, **GIT_ENV, "PATH": f"{bin_dir}:{os.environ['PATH']}",
           "GIT_SSH": str(bin_dir / "ssh"), "GIT_SSH_VARIANT": "simple", "CG_REMOTE_REPO": str(box)}
    return laptop, box, env, log


def _deploy(laptop: Path, env: dict, element: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "scripts/deploy.sh", "pipes", element], cwd=laptop, env=env,
                          capture_output=True, text=True)


def test_pipes_deploy_carries_a_reuben_commit_the_box_cannot_fetch(garden):
    laptop, box, env, log = garden
    pin = _commit(laptop / "vendor" / "reuben", "two")      # exists only on the laptop
    head = _commit(laptop, "bump reuben")

    done = _deploy(laptop, env, "PlayingThePipes")

    assert done.returncode == 0, done.stderr
    assert _git(box, "rev-parse", "HEAD") == head
    assert _git(box / "vendor" / "reuben", "rev-parse", "HEAD") == pin
    assert (box / "vendor" / "reuben" / "two").exists()
    assert log.read_text().split() == ["bash", f"{box}/ShowControl/PlayingThePipes/deploy/install.sh"]


def test_pipes_deploy_sends_the_pinned_commit_not_uncommitted_submodule_work(garden):
    laptop, box, env, _ = garden
    pin = _git(laptop, "rev-parse", "HEAD:vendor/reuben")
    _commit(laptop, "something else")
    _commit(laptop / "vendor" / "reuben", "not pinned")     # checked out, but the branch does not pin it

    done = _deploy(laptop, env, "PlayingThePipes")

    assert done.returncode == 0, done.stderr
    assert "not at the commit" in done.stderr
    assert _git(box / "vendor" / "reuben", "rev-parse", "HEAD") == pin


def test_other_elements_leave_the_submodule_alone(garden):
    laptop, box, env, _ = garden
    before = _git(box / "vendor" / "reuben", "rev-parse", "HEAD")
    _commit(laptop / "vendor" / "reuben", "two")
    head = _commit(laptop, "bump reuben")

    done = _deploy(laptop, env, "FlowerBeds")

    assert done.returncode == 0, done.stderr
    assert "pushing reuben" not in done.stdout
    assert _git(box, "rev-parse", "HEAD") == head
    assert _git(box / "vendor" / "reuben", "rev-parse", "HEAD") == before
