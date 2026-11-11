"""The submodule pin check (.github/scripts/check-reuben-pin.sh) passes only when
vendor/reuben points at a commit already on reuben's dev branch (#236).

A fake `gh` on PATH stands in for the GitHub compare API."""
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "check-reuben-pin.sh"
SHA = "0123456789abcdef0123456789abcdef01234567"


def run(tmp_path: Path, *, status: str = "", gh_fails: bool = False, args=(SHA,)):
    """Run the check with a fake gh that answers the compare call with `status`
    (or exits 1 like a 404), recording the arguments it was called with."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    calls = tmp_path / "gh-calls"
    body = 'echo "gh: Not Found (HTTP 404)" >&2; exit 1' if gh_fails else f'echo "{status}"'
    gh.write_text(f'#!/usr/bin/env bash\necho "$@" >> "{calls}"\n{body}\n')
    gh.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env)
    return result, calls.read_text() if calls.exists() else ""


@pytest.mark.parametrize("status", ["identical", "behind"])
def test_a_commit_on_dev_passes(tmp_path, status):
    result, calls = run(tmp_path, status=status)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"repos/Impractical-Instruments/reuben/compare/dev...{SHA}" in calls


@pytest.mark.parametrize("status", ["ahead", "diverged"])
def test_a_commit_not_on_dev_fails(tmp_path, status):
    result, _ = run(tmp_path, status=status)
    assert result.returncode == 1
    assert "not on Impractical-Instruments/reuben dev" in result.stdout


def test_a_commit_github_does_not_have_fails(tmp_path):
    result, _ = run(tmp_path, gh_fails=True)
    assert result.returncode == 1
    assert "A 404 means" in result.stdout
    assert "HTTP 404" in result.stderr


def test_no_submodule_in_head_passes_without_calling_github(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "empty"], check=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text("#!/usr/bin/env bash\nexit 99\n")
    (bin_dir / "gh").chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run(["bash", str(SCRIPT)], cwd=repo, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "nothing to check" in result.stdout


def test_reads_the_pin_from_head_when_no_sha_is_given(tmp_path):
    """The real repo's gitlink is what gets checked."""
    pinned = subprocess.run(["git", "ls-tree", "HEAD", "vendor/reuben"], capture_output=True,
                            text=True, cwd=SCRIPT.parents[2]).stdout.split()
    if not pinned:
        pytest.skip("vendor/reuben is not committed in HEAD yet")
    result, calls = run(tmp_path, status="identical", args=())
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"compare/dev...{pinned[2]}" in calls
