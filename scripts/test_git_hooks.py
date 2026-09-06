"""The pre-commit guard that keeps private content out of public history."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "scripts" / "git-hooks" / "pre-commit"
PRIVATE = "ShowControl/FundingCAPTCHA/images/private"
LEVELS_FILE = "ShowControl/FundingCAPTCHA/bodycaptcha-levels.json"


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


def _commit_levels(repo: Path, levels: list) -> None:
    """Commit an initial bodycaptcha-levels.json so a later edit produces a real diff."""
    p = repo / LEVELS_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(levels, indent=2) + "\n")
    subprocess.run(["git", "add", LEVELS_FILE], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "levels"], cwd=repo, check=True)


def _stage_levels_edit(repo: Path, levels: list) -> None:
    p = repo / LEVELS_FILE
    p.write_text(json.dumps(levels, indent=2) + "\n")
    subprocess.run(["git", "add", LEVELS_FILE], cwd=repo, check=True)


def _stage_gitlink(repo: Path, rel: str) -> None:
    """Stage `rel` as a nested repo (gitlink) — what `git add -f` on a directory
    containing its own .git produces: the bare directory name, no trailing slash."""
    nested = repo / rel
    nested.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=nested, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=nested, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=nested, check=True)
    (nested / "f.txt").write_bytes(b"x")
    subprocess.run(["git", "add", "f.txt"], cwd=nested, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=nested, check=True)
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


def test_hook_allows_a_similarly_named_prefix_elsewhere(tmp_path: Path):
    """Unanchored matching used to also block backup/<prefix>/x; it must not."""
    repo = _scratch_repo(tmp_path)
    _stage(repo, f"backup/{PRIVATE}/cover.jpg")
    assert _run_hook(repo).returncode == 0


def test_hook_rejects_the_private_directory_staged_as_a_gitlink(tmp_path: Path):
    """`git add -f` on the private directory (a nested repo) stages the bare
    directory name with no trailing slash — the substring match must still
    catch it."""
    repo = _scratch_repo(tmp_path)
    _stage_gitlink(repo, PRIVATE)
    result = _run_hook(repo)
    assert result.returncode != 0
    assert "private" in (result.stdout + result.stderr).lower()


def test_hook_rejects_levels_json_gaining_a_private_image_reference(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _commit_levels(repo, [{"prompt": "P", "image": "public.jpg", "grid": [3, 3], "valid_cells": []}])
    _stage_levels_edit(repo, [
        {"prompt": "P", "image": "public.jpg", "grid": [3, 3], "valid_cells": []},
        {"prompt": "Q", "image": "private/someshow/cover.jpg", "grid": [3, 3], "valid_cells": []},
    ])
    result = _run_hook(repo)
    assert result.returncode != 0
    assert "private" in (result.stdout + result.stderr).lower()


def test_hook_allows_an_ordinary_levels_json_edit(tmp_path: Path):
    repo = _scratch_repo(tmp_path)
    _commit_levels(repo, [{"prompt": "P", "image": "public.jpg", "grid": [3, 3], "valid_cells": []}])
    _stage_levels_edit(repo, [
        {"prompt": "P edited", "image": "public.jpg", "grid": [3, 3], "valid_cells": [[0, 0]]},
        {"prompt": "New level", "image": "another_public.jpg", "grid": [2, 2], "valid_cells": []},
    ])
    assert _run_hook(repo).returncode == 0
