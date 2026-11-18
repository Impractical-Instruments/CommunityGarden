"""Where BodyCaptcha's level file and level photos live, and how to read, write and load them."""
from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path

import pygame

from crop import crop_scale

log = logging.getLogger(__name__)

_DIR = Path(__file__).parent
DEFAULT_LEVELS_PATH = _DIR / "bodycaptcha-levels.json"
DEFAULT_IMAGES_DIR = _DIR / "images"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

# The built-in level: what the game plays when the levels file is unusable, and
# what the editor adds for "new level". Copy it (new_default_level) before mutating.
DEFAULT_LEVEL: dict = {"prompt": "Cover the center", "image": None, "difficulty": 1,
                       "grid": [3, 3], "valid_cells": [[1, 1]]}


def new_default_level() -> dict:
    return deepcopy(DEFAULT_LEVEL)


def read_levels(path: Path) -> list[dict] | None:
    """Read a levels file. Returns None on ANY failure — missing, bad JSON,
    empty, or not a non-empty list — so callers choose fallback vs keep-last-good.

    The game reloads levels at every arc start, so a malformed or half-pulled
    file must never silently collapse the show to a default level.
    """
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, list) and data else None


def level_sort_key(level: dict) -> tuple[str, str]:
    return (level.get("image") or "", level.get("prompt") or "")


def write_levels(path: Path, levels: list[dict]) -> None:
    """Write `levels` sorted by image then prompt, creating the parent directory.

    A typoed --levels path (e.g. a misspelled show directory) can point at a
    parent directory that was never created; creating it beats raising
    FileNotFoundError out of the editor. Anything else (OSError) propagates.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(levels, key=level_sort_key), indent=2) + "\n")


def load_image(path: Path) -> pygame.Surface:
    """Load an image via pygame, falling back to Pillow for formats SDL_image lacks (JPEG on the Pi).

    Raises RuntimeError for a Git LFS pointer file, which is not an image.
    """
    with open(path, "rb") as f:
        if f.read(20).startswith(b"version https://git-"):
            raise RuntimeError(
                f"Git LFS pointer at {path} — run `git lfs pull` in the repo root"
            )
    try:
        return pygame.image.load(str(path)).convert()
    except Exception:
        pass
    from PIL import Image as _PILImage
    pil = _PILImage.open(str(path)).convert("RGB")
    return pygame.image.frombuffer(pil.tobytes(), pil.size, "RGB").convert()


class Levels:
    """One levels file and the image directory its levels refer to.

    The game and the editor are each handed one, so the path is never a module
    global: the game's per-arc reload keeps reading the file it was given.
    """

    def __init__(self, path: Path | str | None = None,
                 images: Path | str | None = None) -> None:
        self.path = DEFAULT_LEVELS_PATH if path is None else Path(path)
        self.images = DEFAULT_IMAGES_DIR if images is None else Path(images)

    def read(self) -> list[dict] | None:
        return read_levels(self.path)

    def write(self, levels: list[dict]) -> None:
        write_levels(self.path, levels)

    def image_names(self) -> list[str]:
        """Every level photo under the image directory, as sorted '/'-separated relative paths."""
        return sorted(
            p.relative_to(self.images).as_posix()
            for p in self.images.rglob("*")
            if p.suffix.lower() in IMAGE_SUFFIXES
        )

    def background(self, name: str | None, w: int, h: int,
                   align: object = None) -> pygame.Surface | None:
        """A level photo cropped (never squashed) to w x h; None if absent or unloadable."""
        if not name:
            return None
        path = self.images / name
        if not path.exists():
            log.warning("Background image not found: %s", path)
            return None
        try:
            return crop_scale(load_image(path), w, h, align)
        except Exception as exc:
            log.warning("Failed to load background image %s: %s", path, exc)
            return None
