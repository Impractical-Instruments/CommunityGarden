#!/usr/bin/env python3
"""Build a standalone BodyCaptchaEditor executable using PyInstaller.

Output: dist/BodyCaptchaEditor.exe (Windows) — a single-file binary that
bundles Python, pygame, and Pillow. The editor reads/writes data files
next to the .exe at runtime (see frozen-path handling in
bodycaptcha_editor.py).

Run after any change to bodycaptcha_editor.py:
    pip install pyinstaller
    python build.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE   = Path(__file__).resolve().parent
ROOT   = HERE.parent
EDITOR = ROOT / "bodycaptcha_editor.py"
DIST   = HERE / "dist"
WORK   = HERE / "build_work"


def main() -> int:
    if not EDITOR.exists():
        print(f"ERROR: editor not found at {EDITOR}", file=sys.stderr)
        return 1

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed. Run:", file=sys.stderr)
        print("    pip install pyinstaller", file=sys.stderr)
        return 1

    for d in (DIST, WORK):
        if d.exists():
            shutil.rmtree(d)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "BodyCaptchaEditor",
        "--onefile",
        "--distpath", str(DIST),
        "--workpath", str(WORK),
        "--specpath", str(WORK),
        "--collect-submodules", "pygame",
        "--hidden-import", "PIL.Image",
        str(EDITOR),
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        return result.returncode

    suffix = ".exe" if sys.platform == "win32" else ""
    exe = DIST / f"BodyCaptchaEditor{suffix}"
    print(f"\nBuilt: {exe}")
    print("Next: `python package.py` to make a shippable zip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
