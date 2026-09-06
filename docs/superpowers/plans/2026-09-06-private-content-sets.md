# Private Content Sets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let BodyCaptcha run a level set whose images and level definitions live outside this public repo, without those files ever entering public history.

**Architecture:** A private companion repo is cloned into `ShowControl/FundingCAPTCHA/images/private/`, which the public repo ignores. Because the clone lands inside the existing image root, background paths resolve unchanged. A new `--levels PATH` argument selects the set at launch and must survive the per-arc hot reload. A committed git hook plus the ignore rule keep private files out of `git add`.

**Tech Stack:** Python 3, pygame, pytest, argparse, Git LFS, bash, systemd.

**Spec:** `docs/superpowers/specs/2026-09-06-private-content-sets-design.md`

## Global Constraints

- **Never name a collaboration in this repo.** Directory names, code, comments, tests, docs, commit messages, and branch names use generic terms (`private`, `<show-name>`). Verbatim from the spec: content is organised "one directory per show".
- **The private clone path is exactly** `ShowControl/FundingCAPTCHA/images/private/`. Nothing else may be added to that directory by tracked code.
- **Never commit directly to `main`** (`docs/agents/git-workflow.md`). All work happens on the current feature branch.
- **Test command is `make test`** — runs `node --test` then `python3 -m pytest`. `pytest.ini` sets `testpaths = ShowControl IIVision`. Run pytest from the repo root, not from `ShowControl/FundingCAPTCHA/`.
- **Graceful degradation is mandatory.** A missing, malformed, or empty levels file must fall back and log; it must never raise at startup, because that takes the show down at load-in.
- **Existing default behaviour must not change.** With no `--levels` argument, the app resolves `bodycaptcha-levels.json` exactly as it does today.

---

## File Structure

| File | Responsibility |
|---|---|
| `games/bodycaptcha.py` (modify) | Owns the module-level levels path and the `set_levels_path()` override that both initial load and hot reload read through. |
| `app.py` (modify) | Parses `--levels` and applies it to the game module before games are loaded. |
| `bodycaptcha_editor.py` (modify) | Parses `--levels` so a private set is authored in the editor, not by hand. |
| `.gitignore` (modify) | Ignores the private clone path. |
| `scripts/git-hooks/pre-commit` (create) | Rejects any staged path under the private clone path. |
| `scripts/install-git-hooks.sh` (create) | Symlinks the tracked hook into `.git/hooks/`, leaving the Git LFS hooks alone. |
| `ShowControl/FundingCAPTCHA/deploy/install.sh` (modify) | Optionally clones/pulls the private repo when a deploy key is present. |
| `docs/FundingCAPTCHA.md` (modify) | Documents the mechanism for a future operator. |
| `test_bodycaptcha_levels.py` (modify) | Covers the path override, hot-reload persistence, and fallback. |
| `test_bodycaptcha_editor.py` (modify) | Covers the editor's `--levels` parsing. |
| `scripts/test_git_hooks.py` (create) | Covers the pre-commit hook's accept/reject behaviour. |

Paths in tasks below are relative to the repo root unless the task says otherwise. `ShowControl/FundingCAPTCHA/` is abbreviated `FC/` in prose but written in full in commands.

---

### Task 1: Levels path override in the game module

The pivotal change. `_reload_data()` re-reads levels at **every arc start** by calling `_read_levels()` with its default argument, which resolves the module global at call time. If the override were stored only on the `BodyCaptchaGame` instance, the private set would play for exactly one arc and then silently revert to the public set mid-show. The override therefore lives on the module.

**Files:**
- Modify: `ShowControl/FundingCAPTCHA/games/bodycaptcha.py:26-29` (module path constants), `:97` (`_read_levels` signature)
- Test: `ShowControl/FundingCAPTCHA/test_bodycaptcha_levels.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `set_levels_path(path: Path | str | None) -> None` — sets the module-level levels path. `None` restores the default.
  - `get_levels_path() -> Path` — returns the path currently in effect.
  - `_LEVELS_DEFAULT: Path` — the unchanged `_DIR / "bodycaptcha-levels.json"`.
  - `_read_levels(path: Path | None = None) -> list[dict] | None` — when `path` is `None`, resolves `get_levels_path()` **at call time**.

- [ ] **Step 1: Write the failing tests**

Append to `ShowControl/FundingCAPTCHA/test_bodycaptcha_levels.py`:

```python
# ── levels path override ────────────────────────────────────────────────────────

from games.bodycaptcha import get_levels_path, set_levels_path, _LEVELS_DEFAULT


@pytest.fixture(autouse=True)
def _restore_levels_path():
    """Every test in this module leaves the module-level path as it found it."""
    yield
    set_levels_path(None)


def test_default_levels_path_is_unchanged():
    assert get_levels_path() == _LEVELS_DEFAULT


def test_set_levels_path_overrides_default(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    set_levels_path(p)
    assert get_levels_path() == p


def test_set_levels_path_none_restores_default(tmp_path: Path):
    set_levels_path(tmp_path / "private-levels.json")
    set_levels_path(None)
    assert get_levels_path() == _LEVELS_DEFAULT


def test_set_levels_path_accepts_str(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    set_levels_path(str(p))
    assert get_levels_path() == Path(p)


def test_read_levels_follows_override(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    levels = [{"prompt": "P", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1}]
    p.write_text(json.dumps(levels))
    set_levels_path(p)
    assert _read_levels() == levels


def test_read_levels_resolves_override_at_call_time(tmp_path: Path):
    """The override must be read per call, not captured as a default argument —
    _reload_data() calls _read_levels() with no argument at every arc start."""
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps([{"prompt": "A", "grid": [2, 2], "valid_cells": [[0, 0]]}]))
    b.write_text(json.dumps([{"prompt": "B", "grid": [2, 2], "valid_cells": [[0, 0]]}]))
    set_levels_path(a)
    assert _read_levels()[0]["prompt"] == "A"
    set_levels_path(b)
    assert _read_levels()[0]["prompt"] == "B"


def test_read_levels_missing_override_returns_none(tmp_path: Path):
    """A --levels path that does not exist must fall back, never raise."""
    set_levels_path(tmp_path / "nope.json")
    assert _read_levels() is None


def test_read_levels_explicit_arg_still_wins(tmp_path: Path):
    """Existing callers that pass a path explicitly are unaffected by the override."""
    override = tmp_path / "override.json"
    override.write_text(json.dumps([{"prompt": "override"}]))
    explicit = tmp_path / "explicit.json"
    explicit.write_text(json.dumps([{"prompt": "explicit"}]))
    set_levels_path(override)
    assert _read_levels(explicit)[0]["prompt"] == "explicit"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest ShowControl/FundingCAPTCHA/test_bodycaptcha_levels.py -v`
Expected: FAIL at import with `ImportError: cannot import name 'get_levels_path' from 'games.bodycaptcha'`

- [ ] **Step 3: Implement the override**

In `ShowControl/FundingCAPTCHA/games/bodycaptcha.py`, replace the `_LEVELS` constant (line 29):

```python
_LEVELS_DEFAULT = _DIR / "bodycaptcha-levels.json"
_levels_path: Path = _LEVELS_DEFAULT


def set_levels_path(path: "Path | str | None") -> None:
    """Point the game at an alternate levels file, or None to restore the default.

    Module-level on purpose: _reload_data() re-reads levels at every arc start,
    so an instance-level override would revert the show to the default set at
    the first arc boundary.
    """
    global _levels_path
    _levels_path = _LEVELS_DEFAULT if path is None else Path(path)


def get_levels_path() -> Path:
    return _levels_path
```

Then change `_read_levels` (line 97) to resolve at call time:

```python
def _read_levels(path: Path | None = None) -> list[dict] | None:
    """Read the levels file. Returns None on ANY failure — missing, bad JSON,
    empty, or not a non-empty list — so callers choose fallback vs keep-last-good.

    `path` defaults to whatever set_levels_path() last selected, resolved per
    call rather than bound as a default argument, because _reload_data() calls
    this with no argument at every arc start.

    Reloaded at every arc start (BodyCaptchaGame.reset), so a malformed or
    half-pulled file must never silently collapse the show to a default level.
    """
    if path is None:
        path = get_levels_path()
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, list) and data else None
```

- [ ] **Step 4: Fix the stale log message in `_reload_data`**

The warning at `games/bodycaptcha.py:242-243` hardcodes the filename, which is now wrong for a private set. Replace it:

```python
            log.warning("%s missing/invalid — keeping %d loaded levels",
                        get_levels_path().name, len(self._all_levels))
```

- [ ] **Step 5: Check for other `_LEVELS` references**

Run: `grep -rn "_LEVELS" ShowControl/FundingCAPTCHA/games/ ShowControl/FundingCAPTCHA/app.py`
Expected: no remaining references to the old `_LEVELS` name in `games/bodycaptcha.py`. If `grep` finds one, update it to `get_levels_path()`.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest ShowControl/FundingCAPTCHA/test_bodycaptcha_levels.py -v`
Expected: PASS, all tests including the pre-existing `_read_levels`/`_read_taunts` ones.

- [ ] **Step 7: Run the full suite for regressions**

Run: `make test`
Expected: PASS.

The spec's test list also asks that "a level whose image is absent renders
without a background". That is already covered by
`test_bodycaptcha_bg.py:63 test_load_bg_missing_image_returns_none` — confirm it
still passes and do **not** write a duplicate:

Run: `python3 -m pytest ShowControl/FundingCAPTCHA/test_bodycaptcha_bg.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add ShowControl/FundingCAPTCHA/games/bodycaptcha.py ShowControl/FundingCAPTCHA/test_bodycaptcha_levels.py
git commit -m "Add module-level levels path override to bodycaptcha

_reload_data() re-reads the levels file at every arc start, so the
override lives on the module and is resolved per call — an instance-level
override would revert to the default set at the first arc boundary."
```

---

### Task 2: `--levels` argument in the app

**Files:**
- Modify: `ShowControl/FundingCAPTCHA/app.py:404-413` (parser), and the call site of `_load_games` in `main()`
- Test: `ShowControl/FundingCAPTCHA/test_app_games.py`

**Interfaces:**
- Consumes: `games.bodycaptcha.set_levels_path` from Task 1.
- Produces: `--levels PATH` CLI argument on `app.py`. No new Python symbol.

Ordering matters: `_load_games` (`app.py:345`) imports and executes `games/bodycaptcha.py` fresh via `importlib`, then calls `mod.create(settings)`, which reads levels immediately in `BodyCaptchaGame.__init__`. So the override has to be applied to the freshly loaded module, not to a separately imported one — a module loaded by `spec.loader.exec_module` is a *different object* from one imported with `import games.bodycaptcha`. Apply it inside `_load_games`.

- [ ] **Step 1: Write the failing test**

Append to `ShowControl/FundingCAPTCHA/test_app_games.py`:

Use the module's existing `SETTINGS` constant, not `{}` — the file header notes
that "Games size themselves against the live display surface at construction
time", and construction reads real settings keys.

```python
def test_load_games_applies_levels_override(tmp_path: Path) -> None:
    """_load_games must set the override on the module it actually loaded —
    importlib gives each load a distinct module object."""
    p = tmp_path / "private-levels.json"
    p.write_text(json.dumps(
        [{"prompt": "PRIVATE", "grid": [2, 2], "valid_cells": [[0, 0]], "difficulty": 1}]
    ))

    games = app._load_games(SETTINGS, levels_path=p)

    assert games, "expected bodycaptcha to load"
    assert [lv.get("prompt") for lv in games[0]._all_levels] == ["PRIVATE"]


def test_load_games_without_override_uses_default() -> None:
    games = app._load_games(SETTINGS)

    assert games, "expected bodycaptcha to load"
    prompts = [lv.get("prompt") for lv in games[0]._all_levels]
    assert prompts != ["PRIVATE"], "override leaked from a previous test"
    assert prompts, "expected the default level set"
```

`_load_games` does `sys.modules[spec.name] = mod` (`app.py:357`), so the
overridden module stays in `sys.modules` under `games.bodycaptcha` after the
first test. Ordering the assertions as above catches that leak rather than
depending on it; both tests already pass `SETTINGS`, and neither imports
`games.bodycaptcha` directly.

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest ShowControl/FundingCAPTCHA/test_app_games.py -v -k levels`
Expected: FAIL with `TypeError: _load_games() got an unexpected keyword argument 'levels_path'`

- [ ] **Step 3: Add the parameter to `_load_games`**

In `ShowControl/FundingCAPTCHA/app.py`, change the signature at line 345 and apply the override after the module is executed but before `create()`:

```python
def _load_games(settings: dict, levels_path: "Path | None" = None) -> list[Game]:
```

Inside the `try` block, between `spec.loader.exec_module(mod)` and `games.append(mod.create(settings))`:

```python
            spec.loader.exec_module(mod)                  # type: ignore[union-attr]
            if levels_path is not None and hasattr(mod, "set_levels_path"):
                mod.set_levels_path(levels_path)
                log.info("Levels override for %s: %s", name, levels_path)
            games.append(mod.create(settings))
```

Ensure `from pathlib import Path` is imported in `app.py`; add it if `grep -n "^from pathlib" ShowControl/FundingCAPTCHA/app.py` finds nothing.

- [ ] **Step 4: Add the CLI argument**

In `main()`, after the `--port` argument (`app.py:412`):

```python
    ap.add_argument("--levels", type=Path, default=None, metavar="PATH",
                    help="Alternate BodyCaptcha levels JSON (default: bodycaptcha-levels.json). "
                         "A missing or malformed file falls back to the default set.")
```

Then pass it at the `_load_games` call site in `main()`:

```python
    games = _load_games(settings, levels_path=args.levels)
```

Run `grep -n "_load_games(" ShowControl/FundingCAPTCHA/app.py` first to find the exact call site line.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest ShowControl/FundingCAPTCHA/test_app_games.py -v`
Expected: PASS.

- [ ] **Step 6: Verify the fallback by hand**

Run: `cd ShowControl/FundingCAPTCHA && timeout 10 python3 app.py --test-input --levels /nonexistent/levels.json; cd -`
Expected: the app starts and logs a warning about the missing/invalid levels file. It must **not** traceback. `timeout` returning 124 is success here.

- [ ] **Step 7: Run the full suite**

Run: `make test`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add ShowControl/FundingCAPTCHA/app.py ShowControl/FundingCAPTCHA/test_app_games.py
git commit -m "Add --levels argument selecting an alternate BodyCaptcha level set

Applied inside _load_games, because importlib gives each load a distinct
module object and the override must land on the one create() runs against."
```

---

### Task 3: `--levels` argument in the editor

**Files:**
- Modify: `ShowControl/FundingCAPTCHA/bodycaptcha_editor.py:20` (constant), `:74-91` (`_load`/`_save`), `:492` (`__main__` block)
- Test: `ShowControl/FundingCAPTCHA/test_bodycaptcha_editor.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (the editor is standalone and does not import `games.bodycaptcha`).
- Produces:
  - `set_levels_path(path: Path | str | None) -> None` and `get_levels_path() -> Path` on `bodycaptcha_editor`, mirroring Task 1's names deliberately so the two modules read alike.
  - `_LEVELS_DEFAULT: Path`.

`_save` must write back to the overridden path, or editing a private set would overwrite the public one. That is the failure this task's tests exist to catch.

- [ ] **Step 1: Write the failing tests**

Append to `ShowControl/FundingCAPTCHA/test_bodycaptcha_editor.py`:

```python
# ── levels path override ────────────────────────────────────────────────────────

import json


@pytest.fixture(autouse=True)
def _restore_editor_levels_path():
    yield
    ed.set_levels_path(None)


def test_editor_default_levels_path_is_unchanged():
    assert ed.get_levels_path() == ed._LEVELS_DEFAULT


def test_editor_load_follows_override(tmp_path: Path):
    p = tmp_path / "private-levels.json"
    levels = [{"prompt": "P", "image": "private/x/a.jpg", "grid": [2, 2], "valid_cells": []}]
    p.write_text(json.dumps(levels))
    ed.set_levels_path(p)
    assert ed._load() == levels


def test_editor_save_writes_to_override_not_default(tmp_path: Path):
    """Saving a private set must never touch the public levels file."""
    p = tmp_path / "private-levels.json"
    ed.set_levels_path(p)
    ed._save([{"prompt": "P", "image": "private/x/a.jpg", "grid": [2, 2], "valid_cells": []}])
    assert json.loads(p.read_text())[0]["prompt"] == "P"


def test_editor_load_missing_override_returns_default_level(tmp_path: Path):
    ed.set_levels_path(tmp_path / "nope.json")
    loaded = ed._load()
    assert loaded == [ed.DEFAULT_LEVEL]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest ShowControl/FundingCAPTCHA/test_bodycaptcha_editor.py -v -k "override or levels_path"`
Expected: FAIL with `AttributeError: module 'bodycaptcha_editor' has no attribute 'set_levels_path'`

- [ ] **Step 3: Implement the override**

In `ShowControl/FundingCAPTCHA/bodycaptcha_editor.py`, replace the `_LEVELS` constant (line 20):

```python
_LEVELS_DEFAULT = _DIR / "bodycaptcha-levels.json"
_levels_path: Path = _LEVELS_DEFAULT


def set_levels_path(path: "Path | str | None") -> None:
    """Edit an alternate levels file, or None to restore the default."""
    global _levels_path
    _levels_path = _LEVELS_DEFAULT if path is None else Path(path)


def get_levels_path() -> Path:
    return _levels_path
```

Change `_load` (line 74) to read `get_levels_path().read_text()` instead of `_LEVELS.read_text()`, and `_save` (line 89) to write `get_levels_path().write_text(...)` instead of `_LEVELS.write_text(...)`.

- [ ] **Step 4: Parse the argument at entry**

Replace the `__main__` block at the end of the file:

```python
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="BodyCaptcha level editor")
    ap.add_argument("--levels", type=Path, default=None, metavar="PATH",
                    help="Alternate levels JSON to edit (default: bodycaptcha-levels.json)")
    args = ap.parse_args()
    set_levels_path(args.levels)
    Editor().run()
```

- [ ] **Step 5: Verify no stale `_LEVELS` references remain**

Run: `grep -n "_LEVELS\b" ShowControl/FundingCAPTCHA/bodycaptcha_editor.py`
Expected: only `_LEVELS_DEFAULT` matches. Any bare `_LEVELS` is a bug — fix it before continuing.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest ShowControl/FundingCAPTCHA/test_bodycaptcha_editor.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add ShowControl/FundingCAPTCHA/bodycaptcha_editor.py ShowControl/FundingCAPTCHA/test_bodycaptcha_editor.py
git commit -m "Add --levels argument to the BodyCaptcha editor

_save follows the override too, so editing an alternate set cannot
overwrite the default levels file."
```

---

### Task 4: Ignore rule and pre-commit guard

`*.jpg` is LFS-tracked in `.gitattributes`, and pushed LFS objects are effectively permanent. The ignore rule is the primary protection; the hook is the backstop for `git add -f` or a future edit to `.gitignore`.

The hook is installed by symlink into `.git/hooks/`, **not** by setting `core.hooksPath`: that setting makes git ignore `.git/hooks` entirely, which would disable the four Git LFS hooks already installed there (`post-checkout`, `post-commit`, `post-merge`, `pre-push`).

Note `scripts/hooks/` already exists and holds *Claude Code* hooks. Git hooks go in a separate `scripts/git-hooks/` to avoid conflating the two.

**Files:**
- Modify: `.gitignore`
- Create: `scripts/git-hooks/pre-commit`, `scripts/install-git-hooks.sh`
- Test: `scripts/test_git_hooks.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `scripts/git-hooks/pre-commit`, an executable bash script reading staged paths from `git diff --cached --name-only` and exiting non-zero on a match. `scripts/test_git_hooks.py` invokes it as a subprocess inside a scratch repo.

- [ ] **Step 1: Write the failing test**

Create `scripts/test_git_hooks.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest scripts/test_git_hooks.py -v`
Expected: FAIL on `test_hook_is_executable` with "missing hook".

Note: `pytest.ini` sets `testpaths = ShowControl IIVision`, so this file is not picked up by a bare `make test`. That is addressed in Step 6.

- [ ] **Step 3: Write the hook**

Create `scripts/git-hooks/pre-commit`:

```bash
#!/usr/bin/env bash
# pre-commit — refuse to stage private show content into this public repo.
#
# ShowControl/FundingCAPTCHA/images/private/ holds a clone of the private
# assets repo. .gitignore keeps it out of `git add`; this hook is the backstop
# for `git add -f` and for a future edit that drops the ignore rule.
#
# *.jpg is LFS-tracked and pushed LFS objects are effectively permanent, so a
# mistaken commit here is not recoverable by amending.
#
# Install: bash scripts/install-git-hooks.sh
set -euo pipefail

PRIVATE_PREFIX="ShowControl/FundingCAPTCHA/images/private/"

offenders="$(git diff --cached --name-only -z \
    | tr '\0' '\n' \
    | grep -F "$PRIVATE_PREFIX" || true)"

if [ -n "$offenders" ]; then
    echo "pre-commit: refusing to commit private show content." >&2
    echo "" >&2
    echo "These staged paths are under $PRIVATE_PREFIX:" >&2
    echo "$offenders" | sed 's/^/  /' >&2
    echo "" >&2
    echo "That directory is a clone of the private assets repo and must never" >&2
    echo "enter this public repository. Unstage them:" >&2
    echo "" >&2
    echo "  git restore --staged -- '$PRIVATE_PREFIX'" >&2
    echo "" >&2
    exit 1
fi

exit 0
```

Make it executable: `chmod +x scripts/git-hooks/pre-commit`

`grep -F` on the prefix (with its trailing slash) is what makes `images/private-notes.txt` pass while `images/private/x.jpg` fails.

- [ ] **Step 4: Write the installer**

Create `scripts/install-git-hooks.sh`:

```bash
#!/usr/bin/env bash
# install-git-hooks.sh — symlink this repo's tracked git hooks into .git/hooks.
#
# Symlinks rather than setting core.hooksPath: that setting makes git ignore
# .git/hooks entirely, which would disable the Git LFS hooks installed there
# (post-checkout, post-commit, post-merge, pre-push).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC="$REPO_ROOT/scripts/git-hooks"
DEST="$(git rev-parse --git-path hooks)"

for hook in "$SRC"/*; do
    name="$(basename "$hook")"
    ln -sf "$hook" "$DEST/$name"
    echo "installed: $DEST/$name -> $hook"
done

echo ""
echo "Done. Verify with: ls -l $DEST"
```

Make it executable: `chmod +x scripts/install-git-hooks.sh`

- [ ] **Step 5: Add the ignore rule**

Append to `.gitignore`, after the existing "Backup settings" block:

```
# Private show content — a clone of the private assets repo lives here.
# Never commit anything under this path; scripts/git-hooks/pre-commit enforces it.
ShowControl/FundingCAPTCHA/images/private/
```

- [ ] **Step 6: Make pytest collect the scripts tests**

`pytest.ini` currently reads `testpaths = ShowControl IIVision`. Change it to:

```ini
[pytest]
testpaths = ShowControl IIVision scripts
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python3 -m pytest scripts/test_git_hooks.py -v`
Expected: PASS, all eight tests.

- [ ] **Step 8: Install the hook and verify it fires for real**

```bash
bash scripts/install-git-hooks.sh
mkdir -p ShowControl/FundingCAPTCHA/images/private/scratch
echo x > ShowControl/FundingCAPTCHA/images/private/scratch/probe.txt
git add -f ShowControl/FundingCAPTCHA/images/private/scratch/probe.txt
git commit -m "should be refused" && echo "HOOK FAILED TO BLOCK" || echo "hook blocked as expected"
git restore --staged -- ShowControl/FundingCAPTCHA/images/private/
rm -rf ShowControl/FundingCAPTCHA/images/private/scratch
```

Expected: "hook blocked as expected", and `git status` afterwards shows nothing staged under that path.

- [ ] **Step 9: Verify the ignore rule**

```bash
mkdir -p ShowControl/FundingCAPTCHA/images/private/scratch
echo x > ShowControl/FundingCAPTCHA/images/private/scratch/probe.jpg
git status --short --untracked-files=all | grep private && echo "IGNORE RULE FAILED" || echo "ignored as expected"
rm -rf ShowControl/FundingCAPTCHA/images/private/scratch
```

Expected: "ignored as expected".

- [ ] **Step 10: Run the full suite**

Run: `make test`
Expected: PASS, now including `scripts/test_git_hooks.py`.

- [ ] **Step 11: Commit**

```bash
git add .gitignore pytest.ini scripts/git-hooks/pre-commit scripts/install-git-hooks.sh scripts/test_git_hooks.py
git commit -m "Ignore private show content and add a pre-commit guard

*.jpg is LFS-tracked and pushed LFS objects are permanent, so the ignore
rule gets a backstop that fails the commit on any staged path under
images/private/. Installed by symlink to leave the Git LFS hooks intact."
```

---

### Task 5: Deploy support

**Files:**
- Modify: `ShowControl/FundingCAPTCHA/deploy/install.sh:28-32` (after the Git LFS block)
- Create: `ShowControl/FundingCAPTCHA/deploy/private-assets.example.env`
- Test: manual — this task provisions a machine and has no unit test.

**Interfaces:**
- Consumes: the ignore rule from Task 4 (the clone target must be ignored before anything clones into it).
- Produces: `install.sh` honouring two environment variables, `PRIVATE_ASSETS_REPO` (an SSH clone URL) and `PRIVATE_ASSETS_KEY` (path to a read-only deploy key, default `~/.ssh/private_assets_ed25519`).

- [ ] **Step 1: Add the optional clone step**

In `ShowControl/FundingCAPTCHA/deploy/install.sh`, insert after the Git LFS block (which ends with `git -C "$REPO_ROOT" lfs pull`):

```bash
# ── Private show content (optional) ───────────────────────────────────────────
# Set PRIVATE_ASSETS_REPO to an SSH clone URL to pull unpublishable show content
# into images/private/. Skipped silently when unset or when no key is present, so
# a plain public clone still installs and runs the default level set.
PRIVATE_DIR="$APP_DIR/images/private"
PRIVATE_KEY="${PRIVATE_ASSETS_KEY:-$HOME/.ssh/private_assets_ed25519}"

if [ -n "${PRIVATE_ASSETS_REPO:-}" ] && [ -f "$PRIVATE_KEY" ]; then
    echo "→ Syncing private show content..."
    export GIT_SSH_COMMAND="ssh -i $PRIVATE_KEY -o IdentitiesOnly=yes"
    if [ -d "$PRIVATE_DIR/.git" ]; then
        sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
            git -C "$PRIVATE_DIR" pull --ff-only
        sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
            git -C "$PRIVATE_DIR" lfs pull
    else
        sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
            git clone "$PRIVATE_ASSETS_REPO" "$PRIVATE_DIR"
        sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
            git -C "$PRIVATE_DIR" lfs pull
    fi
    unset GIT_SSH_COMMAND
    echo "   synced: $PRIVATE_DIR"
else
    echo "→ No private show content configured — skipping."
fi
```

`sudo -u "$SERVICE_USER"` matters: `install.sh` runs under `sudo`, so an unqualified clone would leave the tree owned by root and the service user could not `git pull` it later.

- [ ] **Step 2: Document the environment variables**

Create `ShowControl/FundingCAPTCHA/deploy/private-assets.example.env`:

```bash
# Copy to private-assets.env on the show machine and source it before install.sh:
#
#   set -a; . ./private-assets.env; set +a
#   sudo -E bash install.sh
#
# Both are optional. Without them install.sh skips private content entirely and
# the kiosk runs the default level set.

# SSH clone URL of the private assets repo.
PRIVATE_ASSETS_REPO=git@github.com:ORG/REPO.git

# Read-only deploy key with access to that repo.
PRIVATE_ASSETS_KEY=$HOME/.ssh/private_assets_ed25519
```

Note `sudo -E` in that comment: without it, `sudo` strips the variables and the step silently skips.

- [ ] **Step 3: Syntax-check the script**

Run: `bash -n ShowControl/FundingCAPTCHA/deploy/install.sh`
Expected: no output, exit 0.

- [ ] **Step 4: Verify the skip path**

Run: `env -u PRIVATE_ASSETS_REPO bash -c 'PRIVATE_DIR=/tmp/x; PRIVATE_KEY=/nonexistent; if [ -n "${PRIVATE_ASSETS_REPO:-}" ] && [ -f "$PRIVATE_KEY" ]; then echo CLONE; else echo SKIP; fi'`
Expected: `SKIP`.

- [ ] **Step 5: Commit**

```bash
git add ShowControl/FundingCAPTCHA/deploy/install.sh ShowControl/FundingCAPTCHA/deploy/private-assets.example.env
git commit -m "Optionally sync private show content during Pi install

Skipped silently when unconfigured so a plain public clone still installs.
Clones as the service user — install.sh runs under sudo, and a root-owned
tree could not be pulled later."
```

---

### Task 6: Operator documentation

**Files:**
- Modify: `docs/FundingCAPTCHA.md`
- Test: manual review.

**Interfaces:**
- Consumes: every prior task. This is the last task and documents the finished mechanism.
- Produces: nothing consumed by code.

- [ ] **Step 1: Read the existing document to match its structure and tone**

Run: `cat docs/FundingCAPTCHA.md`

Note its heading levels and whether it uses a table-of-contents that needs a new entry.

- [ ] **Step 2: Add the section**

Append to `docs/FundingCAPTCHA.md`, adjusting the heading level to match its siblings:

```markdown
## Private content sets

Some shows use artwork that cannot be published. That content lives in a
separate **private** repository, never in this one.

### Layout

The private repo tracks `*.jpg` in Git LFS and holds one directory per show:

```
<show-name>/levels.json
<show-name>/<background images>
```

It is cloned into `ShowControl/FundingCAPTCHA/images/private/`, which
`.gitignore` excludes. Because the clone lands inside the existing image root,
level entries reference backgrounds exactly as public levels do:

```json
{ "image": "private/<show-name>/<file>.jpg" }
```

Push the private repo to its own remote — that is both the backup and the
version history, and it keeps images and their level definitions in step.

### Running a private set

```bash
python3 app.py --camera --levels images/private/<show-name>/levels.json
```

Authoring works the same way:

```bash
python3 bodycaptcha_editor.py --levels images/private/<show-name>/levels.json
```

Without `--levels`, both use `bodycaptcha-levels.json` as before. A missing or
malformed file falls back to the default set with a warning rather than failing
to start, so a half-pulled clone never takes the show down at load-in.

### On the show Pi

Configure the clone with `deploy/private-assets.example.env` (see that file),
then select the set with a systemd drop-in rather than editing the committed
unit, which stays on the default set:

```bash
sudo systemctl edit captcha
```

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 app.py --camera --port 8080 --levels images/private/<show-name>/levels.json
```

The empty `ExecStart=` is required — without it systemd appends rather than
replaces.

### Keeping it private

`*.jpg` is LFS-tracked, and pushed LFS objects are effectively permanent — a
mistaken commit cannot be undone by amending. Two guards:

1. `.gitignore` excludes `ShowControl/FundingCAPTCHA/images/private/`.
2. `scripts/git-hooks/pre-commit` fails any commit that stages a path under it.

Install the hook once per clone:

```bash
bash scripts/install-git-hooks.sh
```
```

- [ ] **Step 3: Verify no collaboration name leaked into the branch**

Do not write the name into this file — pass it in the shell instead:

```bash
read -r -p "collaboration name to scan for: " NAME
git diff main...HEAD | grep -i -- "$NAME" && echo "LEAK — fix before pushing" || echo "clean"
git log main..HEAD --format='%s%n%b' | grep -i -- "$NAME" && echo "LEAK in commit messages" || echo "messages clean"
git rev-parse --abbrev-ref HEAD | grep -i -- "$NAME" && echo "LEAK in branch name" || echo "branch name clean"
```

Expected: `clean`, `messages clean`, `branch name clean`.

- [ ] **Step 4: Run the full suite one last time**

Run: `make test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/FundingCAPTCHA.md
git commit -m "Document private content sets for BodyCaptcha"
```

---

## Migration (perform after Task 6, not as part of it)

These steps move the in-progress work and touch content that must not be committed here. Do them by hand.

1. Create the private repo, enable LFS for `*.jpg`, and clone it to `ShowControl/FundingCAPTCHA/images/private/`.
2. Move the untracked images from `ShowControl/FundingCAPTCHA/images/<show-dir>/` into `images/private/<show-name>/`.
3. Move the working-tree levels from `ShowControl/FundingCAPTCHA/bodycaptcha-levels.json` into `images/private/<show-name>/levels.json`, rewriting each `"image"` value to the `private/<show-name>/...` prefix.
4. Restore the public levels file: `git checkout -- ShowControl/FundingCAPTCHA/bodycaptcha-levels.json`
5. Confirm the public file is back to its committed state: `git status --short ShowControl/FundingCAPTCHA/bodycaptcha-levels.json` should print nothing.
6. Commit and push the private repo.
7. Smoke-test: `cd ShowControl/FundingCAPTCHA && python3 app.py --test-input --levels images/private/<show-name>/levels.json`
