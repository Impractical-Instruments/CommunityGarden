# BodyCaptcha Editor — Distribution Workflow

Tooling for shipping [`../bodycaptcha_editor.py`](../bodycaptcha_editor.py) to teammates who aren't git-savvy, and merging their level contributions back into the repo.

## One-time setup

```
pip install pyinstaller pygame pillow
```

## Build the editor

```
python build.py
```

Produces `dist/BodyCaptchaEditor.exe` — a single-file Windows executable that bundles Python, pygame, and Pillow (~50MB). The editor's data paths (`bodycaptcha-levels.json`, `images/`) resolve relative to the `.exe` location at runtime, so each teammate's installation is self-contained.

Re-run after any change to `bodycaptcha_editor.py`.

## Package the teammate zip

```
python package.py
```

Produces a single universal `dist/BodyCaptchaEditor.zip` containing:

- `BodyCaptchaEditor.exe`
- starter `bodycaptcha-levels.json`
- empty `images/` folder with a README telling the teammate to create their own subfolder
- `README.txt` (a copy of [`TEAMMATE_README.txt`](TEAMMATE_README.txt))

Send the same zip to everyone. **Tell each person individually what subfolder name to use** under `images/` (`alice`, `bob`, etc.) — one unique name per person so contributor merges don't collide on image paths. The teammate README is firm about creating the subfolder, but the name itself has to come from you.

When the editor changes, rebuild and resend the same single zip.

## Merge contributions back

When a teammate sends back their zip:

1. Unzip somewhere outside the repo (e.g. `~/Downloads/from-alice/BodyCaptchaEditor-alice/`).
2. Copy their `images/alice/` folder into [`../images/`](../images/) in the repo.
3. Merge their levels into the master JSON:

```
python merge_levels.py ../bodycaptcha-levels.json \
    ~/Downloads/from-alice/BodyCaptchaEditor-alice/bodycaptcha-levels.json \
    -o ../bodycaptcha-levels.json
```

Multiple contributors in one shot:

```
python merge_levels.py ../bodycaptcha-levels.json \
    from-alice/bodycaptcha-levels.json \
    from-bob/bodycaptcha-levels.json \
    -o ../bodycaptcha-levels.json
```

The script:

- Identifies levels by `(image, prompt)`.
- Silently deduplicates exact matches.
- Reports conflicts (same identity, different cells/grid/timer) to stderr. **First source wins** — since master is listed first, the master always beats contributors on a tie; you fix the rest by hand and re-run.
- Writes output sorted by `(image, prompt)` for clean git diffs.

Add `--dry-run` to see the conflict report without writing anything. Exit code is non-zero if any conflicts were detected, so the merge is easy to gate in a script or CI step.

## Conflict prevention

The per-teammate-subfolder convention (`images/<name>/`) means contributors never reference the same image path, so `(image, prompt)` identities can't collide. Real conflicts should only happen if a teammate touches an image outside their subfolder — which the README tells them not to do.

## When the editor itself changes

There's no auto-update mechanism. Re-run `build.py` + `package.py` and resend the zip. Ask teammates to copy their `images/<name>/` and `bodycaptcha-levels.json` from their old folder into the new one before launching.
