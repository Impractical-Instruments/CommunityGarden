"""The Arc — FundingCAPTCHA's central game lifecycle (ADR-0012).

One Arc = one player's run: select a Game, play it through, end in a Blow-Up
(loss) or a survival (win), then hand back to the Screensaver. The app loop
drives the Arc through a single interface — `update(foreground, dt) → ArcStatus`
— and never sees the Game's internal `_State` machine or the `'loss'/'win'`
event strings; those are the Arc's private vocabulary.

ADR-0012 names `AppStateMachine` as an internal module of the unified pygame
process. The Arc is the slice of that module the diagram drew but the code kept
inline in the loop. No new process — one process, one more real module.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np
import pygame

# Matches app.DK_GREY — the blank-frame fill when no Game is loaded.
_DK_GREY = (28, 28, 28)


def blend_intensity(progress_5: float, elapsed: float, duration: float,
                    w_difficulty: float, w_time: float) -> float:
    """Blend difficulty and time-pressure into a 0–1 Intensity.

    `progress_5` is a 1–5 difficulty/level measure; `elapsed`/`duration` are the
    Game's own clock. Single source of truth for the Intensity formula shared by
    every Game (BodyCaptcha, BodyKeepaway) — the value the Arc reports to the
    TreeHouse over OSC.
    """
    return max(0.0, min(1.0,
        w_difficulty * progress_5 / 5.0 +
        w_time * elapsed / max(duration, 0.001)))


@dataclass(frozen=True)
class ArcStatus:
    """What the app loop needs after one Arc tick.

    intensity — 0–1 drive level, reported to the TreeHouse over OSC.
    blewup    — the Blow-Up Signal fired this tick (loss). Send it once.
    finished  — the Arc ended this tick (win or loss). Return to the Screensaver.
    """
    intensity: float
    blewup: bool
    finished: bool


class Game:
    """Interface every FundingCAPTCHA game satisfies.

    update(foreground, dt) → (intensity 0–1, event 'loss' | 'win' | None)
      foreground: uint16 H×W depth frame, or None.
    The event strings live behind the Arc; the app loop reads ArcStatus instead.
    """

    def update(self, foreground: np.ndarray | None, dt: float) -> tuple[float, str | None]:
        return 0.0, None

    def draw(self, surf: pygame.Surface) -> None:
        pass

    def reset(self) -> None:
        pass


class _NoGame(Game):
    """Stand-in when no Game loaded — keeps the Arc total even on a bare box."""

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(_DK_GREY)


class ShuffleBag:
    """Draw items in random order, refilling once the bag empties.

    No item repeats until every other item has been drawn — kills the
    clustering of plain `random.choice`. Used for both Games and Screensavers.
    """

    def __init__(self, items: list) -> None:
        self._items = list(items)
        self._bag:  list = []

    def next(self):
        if not self._items:
            return None
        if not self._bag:
            self._bag = list(self._items)
            random.shuffle(self._bag)
        return self._bag.pop()


class Arc:
    """The central lifecycle: select a Game, run it, surface a Blow-Up.

    The app loop calls `start()` when a player is detected, then `update()` once
    per tick until ArcStatus.finished, reading `intensity` for OSC and `blewup`
    to fire the Blow-Up Signal. Game selection, reset, and the loss/win → boolean
    mapping all live here.
    """

    def __init__(self, games: list) -> None:
        self._bag     = ShuffleBag(games)
        self._no_game = _NoGame()
        self._game: Game = self._no_game

    def start(self) -> str:
        """Begin a fresh Arc: select the next Game and reset it.

        Returns the Game's class name (for logging/monitoring).
        """
        self._game = self._bag.next() or self._no_game
        self._game.reset()
        return type(self._game).__name__

    def update(self, foreground: np.ndarray | None, dt: float) -> ArcStatus:
        intensity, event = self._game.update(foreground, dt)
        return ArcStatus(
            intensity = intensity,
            blewup    = (event == "loss"),
            finished  = (event in ("loss", "win")),
        )

    def draw(self, surf: pygame.Surface) -> None:
        self._game.draw(surf)
