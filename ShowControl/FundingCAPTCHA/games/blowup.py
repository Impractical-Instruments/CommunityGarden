"""The confetti blow-up a game plays when the Player runs out of time."""
from __future__ import annotations

import math
import random

import pygame

from games.grid import Grid
from games.shell import GREEN, YELLOW, RED, CYAN, ORANGE, WHITE

BLOWUP_S = 2.8

_COLORS = [GREEN, YELLOW, RED, CYAN, ORANGE, WHITE, (200, 50, 255), (255, 100, 0)]


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "life", "max_life")

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: tuple, size: int, life: float) -> None:
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.color = color; self.size = size
        self.life = life; self.max_life = life

    def update(self, dt: float) -> None:
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.vy  += 500 * dt  # gravity
        self.life -= dt


class Blowup:
    """Confetti burst from every cell of a Grid; `done` once BLOWUP_S has passed."""

    def __init__(self) -> None:
        self._particles: list[_Particle] = []
        self._t = 0.0
        self._started = False

    def start(self, grid: Grid | None) -> None:
        self._t = 0.0
        self._started = True
        self._particles = self._spawn(grid)

    def update(self, dt: float) -> None:
        self._t += dt
        for p in self._particles:
            p.update(dt)
        self._particles = [p for p in self._particles if p.life > 0]

    @property
    def particle_count(self) -> int:
        return len(self._particles)

    @property
    def done(self) -> bool:
        return self._started and self._t >= BLOWUP_S

    def draw(self, surf: pygame.Surface) -> None:
        for p in self._particles:
            alpha = max(0, int(255 * p.life / p.max_life))
            s     = p.size
            tile  = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            tile.fill((*p.color, alpha))
            surf.blit(tile, (int(p.x) - s, int(p.y) - s))

    @staticmethod
    def _spawn(g: Grid | None) -> list[_Particle]:
        if g is None:
            return []
        result = []
        for r in range(g.rows):
            for c in range(g.cols):
                rect   = g.cell_rect(c, r)
                cx, cy = rect.centerx, rect.centery
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(60, 400)
                    vx    = math.cos(angle) * speed
                    vy    = math.sin(angle) * speed - 200
                    color = random.choice(_COLORS)
                    size  = random.randint(4, 16)
                    life  = random.uniform(1.2, BLOWUP_S)
                    result.append(_Particle(cx, cy, vx, vy, color, size, life))
        return result
