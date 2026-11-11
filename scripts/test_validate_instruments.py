"""scripts/validate-instruments.sh fails an instrument on any reuben error or
warning (a missing sample is only a warning to reuben). A fake reuben stands in
for the real one, so this runs without Rust."""
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "validate-instruments.sh"


def fake_reuben(tmp_path: Path, report: dict | str, rc: int = 0) -> Path:
    body = report if isinstance(report, str) else json.dumps(report)
    exe = tmp_path / "reuben"
    exe.write_text(f"#!/usr/bin/env bash\ncat <<'EOF'\n{body}\nEOF\nexit {rc}\n")
    exe.chmod(0o755)
    return exe


def run(reuben: Path, *instruments: str):
    return subprocess.run(["bash", str(SCRIPT), str(reuben), *instruments],
                          capture_output=True, text=True)


def test_no_instruments_passes(tmp_path):
    result = run(fake_reuben(tmp_path, "unused", rc=1))
    assert result.returncode == 0
    assert "No instruments" in result.stdout


def test_a_clean_instrument_passes(tmp_path):
    result = run(fake_reuben(tmp_path, {"ok": True, "errors": [], "warnings": []}), "a.json")
    assert result.returncode == 0
    assert "ok   a.json" in result.stdout


def test_a_warning_fails(tmp_path):
    report = {"ok": True, "errors": [],
              "warnings": [{"node": "/loop3", "message": "sample not found: media/x.wav"}]}
    result = run(fake_reuben(tmp_path, report), "a.json")
    assert result.returncode == 1
    assert "FAIL a.json" in result.stdout
    assert "warning /loop3: sample not found: media/x.wav" in result.stdout


def test_an_error_report_with_a_failing_exit_is_formatted(tmp_path):
    report = {"ok": False, "errors": [{"message": "invalid JSON"}], "warnings": []}
    result = run(fake_reuben(tmp_path, report, rc=1), "a.json")
    assert result.returncode == 1
    assert "error   -: invalid JSON" in result.stdout


def test_output_that_is_not_a_report_is_shown_as_is(tmp_path):
    result = run(fake_reuben(tmp_path, "thread 'main' panicked", rc=101), "a.json")
    assert result.returncode == 1
    assert "  thread 'main' panicked" in result.stdout


def test_every_instrument_is_checked_even_after_a_failure(tmp_path):
    report = {"ok": True, "errors": [], "warnings": [{"node": "/x", "message": "w"}]}
    result = run(fake_reuben(tmp_path, report), "a.json", "b.json")
    assert result.returncode == 1
    assert "FAIL a.json" in result.stdout and "FAIL b.json" in result.stdout
