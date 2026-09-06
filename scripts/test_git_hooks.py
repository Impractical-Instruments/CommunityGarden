"""The pre-commit guard that keeps private content out of public history."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "scripts" / "git-hooks" / "pre-commit"
PRIVATE = "ShowControl/FundingCAPTCHA/images/private"


def _scratch_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path


def _stage(repo: Path, rel: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    subprocess.run(["git", "add", "-f", rel], cwd=repo, check=True)


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(HOOK)], cwd=repo, capture_output=True, text=True)


def test_hook_is_executable():
    assert HOOK.exists(), f"missing hook: {HOOK}"
    assert HOOK.stat().st_mode & 0o111, "hook must be executable"


def test_hook_allows_an_ordinary_file(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _stage(repo, "ShowControl/FundingCAPTCHA/app.py")
    assert _run_hook(repo).returncode == 0


def test_hook_allows_a_public_image(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _stage(repo, "ShowControl/FundingCAPTCHA/images/public.jpg")
    assert _run_hook(repo).returncode == 0


def test_hook_rejects_a_private_image(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _stage(repo, f"{PRIVATE}/someshow/cover.jpg")
    result = _run_hook(repo)
    assert result.returncode != 0
    assert "private" in (result.stdout + result.stderr).lower()


def test_hook_rejects_a_private_levels_file(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _stage(repo, f"{PRIVATE}/someshow/levels.json")
    assert _run_hook(repo).returncode != 0


def test_hook_rejects_a_path_with_spaces(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _stage(repo, f"{PRIVATE}/someshow/a cover image.jpg")
    assert _run_hook(repo).returncode != 0


def test_hook_rejects_when_mixed_with_allowed_files(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _stage(repo, "ShowControl/FundingCAPTCHA/app.py")
    _stage(repo, f"{PRIVATE}/someshow/cover.jpg")
    assert _run_hook(repo).returncode != 0


def test_hook_allows_a_similarly_named_sibling(tmp_path: Path):
    """images/private-notes.txt is not inside images/private/."""
    repo = _scratch_repo(tmp_path)
    _stage(repo, "ShowControl/FundingCAPTCHA/images/private-notes.txt")
    assert _run_hook(repo).returncode == 0
