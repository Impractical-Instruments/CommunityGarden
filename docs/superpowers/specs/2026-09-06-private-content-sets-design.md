# Private content sets for BodyCaptcha

**Date:** 2026-09-06
**Status:** Approved, pending implementation

## Problem

BodyCaptcha loads exactly one level set from a fixed path, and every background
image lives in the public repo under Git LFS:

- `games/bodycaptcha.py:28-29` hardcodes `_IMAGES = _DIR / "images"` and
  `_LEVELS = _DIR / "bodycaptcha-levels.json"`.
- `bodycaptcha_editor.py:20-21` hardcodes the same two paths.
- `.gitattributes` tracks `*.jpg` in LFS, and `deploy/install.sh` provisions the
  Pi by cloning this public repo and running `git lfs pull`.

Some collaborations supply artwork that cannot be published. Today the only way
to run such a show is to drop unpublishable images into a tracked directory and
hand-edit `bodycaptcha-levels.json`, which risks committing the images to public
LFS storage and destroys the general level set in the process. Pushed history and
LFS objects are effectively permanent, so a single mistaken `git add -A` is not
recoverable.

This design adds a private content set: images plus their level definitions,
stored outside the public repo, versioned and backed up, selectable at launch.

## Goals

- Private images and their level definitions never enter this repo's history.
- Private content is versioned and backed up offsite, not just on one laptop.
- The general level set on `main` is unaffected and remains the default.
- A plain public clone still installs, launches, and runs.
- Adding a second private set later is a new directory, not a new mechanism.

## Non-goals

- Encrypting content at rest. Access control is the private remote's job.
- Multiple level sets active at once. One set is selected per launch.
- Migrating the existing public images out of LFS.

## Architecture

### Private companion repository

A separate private repository holds all unpublishable content, `*.jpg` tracked in
LFS, organised one directory per show:

```
<show-name>/levels.json
<show-name>/<background images>
```

It is cloned on the authoring machine and on the show Pi to:

```
ShowControl/FundingCAPTCHA/images/private/
```

The public repo ignores that path (see below). A nested `.git` directory inside
an ignored path is invisible to the outer repo: no submodule, no `.gitmodules`
entry, and nothing in the public repo names the collaboration.

Backup and version history come from pushing that private repo to its own remote.
Images and the level definitions that reference them version together, so a
restore is a single clone.

### Path resolution

`_IMAGES` remains `_DIR / "images"` and image loading is unchanged. Because the
clone lands *inside* `images/`, a private level entry refers to its background
with a path relative to `images/` exactly as public levels do:

```json
{ "image": "private/<show-name>/<file>.jpg" }
```

This is the reason for placing the clone under `images/` rather than beside it:
it keeps one image root and requires no change to `_load_bg`.

### Level set selection

`--levels PATH` selects a level set at launch; omitting it keeps today's
behaviour exactly.

- `app.py` (argument parser at `app.py:404-412`) gains `--levels`.
- `games/bodycaptcha.py` turns `_LEVELS` into an overridable module default.
  Both the initial read in `BodyCaptchaGame.__init__` (`games/bodycaptcha.py:168`)
  and the per-arc hot reload in `reset()` (`games/bodycaptcha.py:239`) must honour
  the override — the hot reload re-reads from the module default on every arc
  start, so setting the path only at construction time would silently revert the
  show to the public set at the first arc boundary.
- `bodycaptcha_editor.py` gains the same argument, so a private set is authored
  in the editor rather than by hand-editing JSON.

### Protection against accidental publication

Two layers, because `*.jpg` is LFS-tracked and `git add -A` is a common reflex:

1. `.gitignore` gains `ShowControl/FundingCAPTCHA/images/private/`.
2. A `pre-commit` hook fails the commit if any staged path falls under
   `ShowControl/FundingCAPTCHA/images/private/`.

The hook is the backstop for the case where the ignore rule is bypassed
(`git add -f`, or a future edit to `.gitignore`).

### Deployment

`deploy/install.sh` gains an optional private-assets step: if a read-only deploy
key for the private repo is present, clone or pull it into `images/private/`;
otherwise skip silently. A machine without the key still installs and runs the
public set.

The committed `deploy/captcha.service` is left unchanged and therefore defaults to
the public set. A show Pi selects its set with a systemd drop-in that appends
`--levels images/private/<show-name>/levels.json` to `ExecStart`. Keeping the
selection in a machine-local drop-in rather than the committed unit means the
public repo carries no show-specific configuration.

## Failure behaviour

Degradation is already graceful and should stay that way:

- `_load_bg` (`games/bodycaptcha.py:141-146`) logs a warning and returns `None`
  for a missing image, so a level whose background is absent plays without one.
- `_read_levels` (`games/bodycaptcha.py:97-106`) returns `None` on any failure,
  and callers fall back to the last good set or `_DEFAULT_LEVEL`.

So a machine that lacks the private clone, or has it half-pulled, falls back
rather than crashing. A `--levels` path that does not exist must behave the same
way as any other unreadable levels file: fall back, log, keep running. It must not
raise at startup, because that would take the show down at load-in.

An LFS pointer left unresolved in the private clone is caught by the existing
check in `_img_load` (`games/bodycaptcha.py:117-121`).

## Testing

- `--levels` override is honoured on initial load and across an arc-start hot
  reload.
- Omitting `--levels` resolves to `bodycaptcha-levels.json` unchanged.
- A `--levels` path that is missing or malformed falls back without raising.
- A level whose image is absent renders without a background.
- The `pre-commit` hook rejects a staged path under `images/private/` and permits
  an ordinary staged file.

## Migration

`bodycaptcha-levels.json` is not modified. Any in-progress private levels move
into the private repo's `<show-name>/levels.json`, and the working copy of
`bodycaptcha-levels.json` is restored with `git checkout`.
