"""Finds the kiosk's Games and screensavers on disk and loads them.

    games  = load_games(settings)           # games/<name>.py for each name in GAMES
    savers = load_screensavers(settings)    # each path listed in screensavers.json

Each is a Python file with a `create(settings)` function. One that is missing
or fails to load is logged and skipped. Choosing and running them is not done
here: Games are the Arc's job (arc.py), screensavers the kiosk loop's.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pygame

from arc import Game
from settings import DIR

log = logging.getLogger("captcha.plugins")

GAMES = ("bodycaptcha",)


def _load_module(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod  = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[spec.name] = mod                  # dataclass field resolution needs this
    spec.loader.exec_module(mod)                  # type: ignore[union-attr]
    return mod


def load_games(settings: dict, levels_path: Path | None = None) -> list[Game]:
    """`levels_path` overrides the levels file of any Game that has one (app.py --levels)."""
    games: list[Game] = []
    for name in GAMES:
        path = DIR / "games" / f"{name}.py"
        if not path.exists():
            log.warning("Game not found: %s", path)
            continue
        try:
            mod = _load_module(f"games.{name}", path)
            if levels_path is not None and hasattr(mod, "set_levels_path"):
                mod.set_levels_path(levels_path)
                log.info("Levels override for %s: %s", name, levels_path)
            games.append(mod.create(settings))
            log.info("Loaded game: %s", name)
        except Exception as exc:
            log.warning("Could not load game %s: %s", name, exc)
    return games


class NoSaver:
    """Stand-in when no screensaver loads: a dark grey screen."""

    def update(self, dt: float, foreground: np.ndarray | None) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill((28, 28, 28))


def load_screensavers(settings: dict) -> list:
    try:
        names = json.loads((DIR / "screensavers.json").read_text())
    except Exception:
        names = []

    savers = []
    for name in names:
        path = DIR / name
        if not path.exists():
            log.warning("Screensaver not found: %s", path)
            continue
        try:
            mod = _load_module(f"ss.{Path(name).stem}", path)
            savers.append(mod.create(settings))
            log.info("Loaded screensaver: %s", name)
        except Exception as exc:
            log.warning("Could not load screensaver %s: %s", name, exc)
    return savers
