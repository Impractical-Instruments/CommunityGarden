#!/usr/bin/env python3
"""Build the universal teammate distribution zip for the BodyCaptcha editor.

Requires `build.py` to have run first (the .exe must exist in dist/).

Run:
    python package.py

Output:
    dist/BodyCaptchaEditor.zip

Zip layout:
    BodyCaptchaEditor/
        BodyCaptchaEditor.exe
        bodycaptcha-levels.json     (one blank starter level)
        images/
            README.txt              (tells the teammate to make a subfolder)
        README.txt                  (teammate quick-start)
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

HERE   = Path(__file__).resolve().parent
DIST   = HERE / "dist"
EXE    = DIST / "BodyCaptchaEditor.exe"
README = HERE / "TEAMMATE_README.txt"

DEFAULT_LEVELS = [{
    "prompt": "Select all ...",
    "image": None,
    "difficulty": 1,
    "grid": [3, 3],
    "valid_cells": [],
    "timer_s": 40,
}]

IMAGES_README = """\
This is the images folder.

Before adding any images, create a SUBFOLDER inside this one
named after yourself (lowercase, no spaces). Charlie will have
told you what to call it -- usually your first name.

Examples:
    images/alice/
    images/bob/
    images/charlie/

Then drop your image files (.jpg / .jpeg / .png / .webp) into
your subfolder. The editor will pick them up automatically.

DO NOT skip this step. Two contributors using the same image
filename ("cat.jpg") will collide when their work is merged
together -- unless each one is tucked inside their own subfolder.
"""


def main() -> int:
    if not EXE.exists():
        print(f"ERROR: editor not built -- expected {EXE}", file=sys.stderr)
        print("Run `python build.py` first.", file=sys.stderr)
        return 1
    if not README.exists():
        print(f"ERROR: missing {README}", file=sys.stderr)
        return 1

    staging = DIST / "BodyCaptchaEditor"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    shutil.copy2(EXE, staging / EXE.name)
    shutil.copy2(README, staging / "README.txt")
    (staging / "bodycaptcha-levels.json").write_text(
        json.dumps(DEFAULT_LEVELS, indent=2) + "\n"
    )
    images = staging / "images"
    images.mkdir()
    (images / "README.txt").write_text(IMAGES_README)

    zip_path = DIST / "BodyCaptchaEditor.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(staging.rglob("*")):
            zf.write(p, p.relative_to(staging.parent))

    print(f"Built: {zip_path}")
    print("Send this zip to everyone. Tell each person what subfolder name")
    print("to use under images/ -- one unique name per person so contributor")
    print("merges don't collide on image paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
