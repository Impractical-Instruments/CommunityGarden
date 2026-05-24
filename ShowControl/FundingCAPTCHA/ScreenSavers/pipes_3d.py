"""Garden-themed 3D vines — reskin of the Win95 pipes screensaver.

Vines random-walk through a 3D cell grid, dropping a leaf-bud knuckle at each bend.
Pure pygame software 3D: axis-aligned cuboids, projected per frame, painter-sorted,
flat-shaded by a fixed world-space light. No GPU dependency.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np
import pygame


# ── tuning ────────────────────────────────────────────────────────────────────
_BG_RGB = (8, 14, 8)

_VINE_PALETTE = [
    ( 60, 140,  70), ( 50, 110,  50), ( 90, 160,  80),
    ( 40, 100,  60), (110, 170,  90), ( 70, 130, 100),
    (150, 180,  80), ( 95, 155,  65),
]

_LIGHT_DIR = np.array([0.4, -0.8, 0.5], dtype=np.float32)
_LIGHT_DIR /= np.linalg.norm(_LIGHT_DIR)
_AMBIENT = 0.35

_GRID_HALF        = 5            # grid cells span [-5, 5)
_CELL_SIZE        = 1.0
_PIPE_HALF_W      = 0.18         # vine half-thickness
_JOINT_HALF       = 0.28         # leaf-bud knuckle half-size

_MAX_PIPES_ALIVE  = 4
_MAX_SEGS_PER_PIPE = 60
_STEP_HZ          = 12.0         # growth steps per second
_FULL_RESET_S     = 30.0         # blank canvas + respawn cadence

_CAM_DIST         = 14.0
_CAM_HEIGHT       = 5.0
_CAM_SPIN_HZ      = 1.0 / 48.0   # one revolution / 48s
_FOV_DEG          = 50.0
_NEAR             = 0.5

_STRAIGHT_BIAS    = 0.72         # P(keep going straight) when both options exist


# unit cube centred at origin, half-extent 1
_UNIT_CUBE_VERTS = np.array([
    [-1, -1, -1], [ 1, -1, -1], [ 1,  1, -1], [-1,  1, -1],
    [-1, -1,  1], [ 1, -1,  1], [ 1,  1,  1], [-1,  1,  1],
], dtype=np.float32)

_CUBE_FACES: list[tuple[tuple[int, int, int, int], np.ndarray]] = [
    ((0, 1, 2, 3), np.array([ 0,  0, -1], dtype=np.float32)),
    ((4, 7, 6, 5), np.array([ 0,  0,  1], dtype=np.float32)),
    ((0, 3, 7, 4), np.array([-1,  0,  0], dtype=np.float32)),
    ((1, 5, 6, 2), np.array([ 1,  0,  0], dtype=np.float32)),
    ((0, 4, 5, 1), np.array([ 0, -1,  0], dtype=np.float32)),
    ((3, 2, 6, 7), np.array([ 0,  1,  0], dtype=np.float32)),
]

_DIRS = [
    np.array([ 1, 0, 0], dtype=np.int32),
    np.array([-1, 0, 0], dtype=np.int32),
    np.array([ 0, 1, 0], dtype=np.int32),
    np.array([ 0,-1, 0], dtype=np.int32),
    np.array([ 0, 0, 1], dtype=np.int32),
    np.array([ 0, 0,-1], dtype=np.int32),
]


@dataclass
class _Box:
    center: np.ndarray
    half:   np.ndarray
    color:  tuple[int, int, int]


def _shift(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    return tuple(max(0, min(255, c + delta)) for c in color)


def _seg_box(a_cell: np.ndarray, b_cell: np.ndarray,
             color: tuple[int, int, int]) -> _Box:
    a = a_cell.astype(np.float32) * _CELL_SIZE
    b = b_cell.astype(np.float32) * _CELL_SIZE
    center = (a + b) * 0.5
    half = np.full(3, _PIPE_HALF_W, dtype=np.float32)
    long_axis = int(np.argmax(np.abs(b - a)))
    half[long_axis] = _CELL_SIZE * 0.5
    return _Box(center, half, color)


def _joint_box(cell: np.ndarray, color: tuple[int, int, int]) -> _Box:
    c = cell.astype(np.float32) * _CELL_SIZE
    half = np.full(3, _JOINT_HALF, dtype=np.float32)
    return _Box(c, half, color)


class _Pipe:
    """One vine random-walking through the grid."""

    def __init__(self, occupied: set[tuple[int, int, int]]) -> None:
        self._occupied = occupied
        self._color    = random.choice(_VINE_PALETTE)
        self._joint_color = _shift(self._color, 25)
        cell = self._spawn_cell()
        if cell is None:
            self.alive = False
            self.boxes: list[_Box] = []
            return
        self._cell = cell
        self._dir  = random.choice(_DIRS).copy()
        self._occupied.add(tuple(int(v) for v in cell))
        self.alive = True
        self.boxes = [_joint_box(cell, self._joint_color)]
        self._segs_made = 0

    def _spawn_cell(self) -> np.ndarray | None:
        for _ in range(80):
            c = np.array([
                random.randint(-_GRID_HALF, _GRID_HALF - 1),
                random.randint(-_GRID_HALF, _GRID_HALF - 1),
                random.randint(-_GRID_HALF, _GRID_HALF - 1),
            ], dtype=np.int32)
            if tuple(int(v) for v in c) not in self._occupied:
                return c
        return None

    def step(self) -> None:
        if not self.alive:
            return
        chosen = self._choose_dir()
        if chosen is None:
            self.boxes.append(_joint_box(self._cell, self._joint_color))
            self.alive = False
            return
        bent = not np.array_equal(chosen, self._dir)
        new_cell = self._cell + chosen
        self.boxes.append(_seg_box(self._cell, new_cell, self._color))
        if bent:
            self.boxes.append(_joint_box(self._cell, self._joint_color))
        self._cell = new_cell
        self._dir  = chosen
        self._occupied.add(tuple(int(v) for v in new_cell))
        self._segs_made += 1
        if self._segs_made >= _MAX_SEGS_PER_PIPE:
            self.boxes.append(_joint_box(new_cell, self._joint_color))
            self.alive = False

    def _choose_dir(self) -> np.ndarray | None:
        straight_ok = self._free(self._cell + self._dir)
        turn_options = [
            d for d in _DIRS
            if not np.array_equal(d, -self._dir)
            and not np.array_equal(d,  self._dir)
            and self._free(self._cell + d)
        ]
        if straight_ok and (random.random() < _STRAIGHT_BIAS or not turn_options):
            return self._dir
        if turn_options:
            return random.choice(turn_options)
        if straight_ok:
            return self._dir
        return None

    def _free(self, cell: np.ndarray) -> bool:
        if np.any(cell < -_GRID_HALF) or np.any(cell >= _GRID_HALF):
            return False
        return tuple(int(v) for v in cell) not in self._occupied


class VinesScreensaver:
    def __init__(self, settings: dict) -> None:
        self._t          = 0.0
        self._step_acc   = 0.0
        self._reset_t    = 0.0
        self._occupied: set[tuple[int, int, int]] = set()
        self._pipes: list[_Pipe] = []
        self._title_font: pygame.font.Font | None = None
        self._sub_font:   pygame.font.Font | None = None
        self._spawn_initial()

    # ── lifecycle ────────────────────────────────────────────────────────────
    def _spawn_initial(self) -> None:
        self._occupied = set()
        self._pipes = [_Pipe(self._occupied) for _ in range(_MAX_PIPES_ALIVE)]

    def update(self, dt: float, foreground_frame) -> None:
        self._t        += dt
        self._reset_t  += dt
        self._step_acc += dt
        step_interval = 1.0 / _STEP_HZ
        while self._step_acc >= step_interval:
            self._step_acc -= step_interval
            self._tick_pipes()
        if self._reset_t >= _FULL_RESET_S:
            self._reset_t = 0.0
            self._spawn_initial()

    def _tick_pipes(self) -> None:
        for p in self._pipes:
            if p.alive:
                p.step()
        alive = sum(1 for p in self._pipes if p.alive)
        for _ in range(_MAX_PIPES_ALIVE - alive):
            self._pipes.append(_Pipe(self._occupied))

    # ── rendering ────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(_BG_RGB)
        WW, WH = surf.get_size()

        cam_pos, R = _camera(self._t)
        focal = (WH * 0.5) / math.tan(math.radians(_FOV_DEG) * 0.5)
        cx, cy = WW * 0.5, WH * 0.5

        face_records: list[tuple[float, list, tuple[int, int, int]]] = []
        for p in self._pipes:
            for box in p.boxes:
                _project_box(box, cam_pos, R, focal, cx, cy, face_records)

        face_records.sort(key=lambda r: -r[0])
        for _z, pts, col in face_records:
            pygame.draw.polygon(surf, col, pts)

        self._draw_overlay(surf)

    def _draw_overlay(self, surf: pygame.Surface) -> None:
        WW, WH = surf.get_size()
        if self._title_font is None:
            self._title_font = pygame.font.SysFont("monospace", 42, bold=True)
            self._sub_font   = pygame.font.SysFont("monospace", 20)

        pulse = int(190 + 50 * math.sin(self._t * 1.2))
        color = (pulse, pulse, pulse)

        title = self._title_font.render("FundingCAPTCHA", True, color)
        rect  = title.get_rect(center=(WW // 2, WH // 2))
        shadow = self._title_font.render("FundingCAPTCHA", True, (0, 0, 0))
        surf.blit(shadow, rect.move(3, 3))
        surf.blit(title, rect)

        sub_rect = pygame.Rect(0, 0, 0, 0)
        sub = self._sub_font.render("Step into frame to begin", True, (210, 210, 210))
        sub_rect = sub.get_rect(center=(WW // 2, WH // 2 + 60))
        sub_shadow = self._sub_font.render("Step into frame to begin", True, (0, 0, 0))
        surf.blit(sub_shadow, sub_rect.move(2, 2))
        surf.blit(sub, sub_rect)


def _camera(t: float) -> tuple[np.ndarray, np.ndarray]:
    angle = t * _CAM_SPIN_HZ * math.tau
    cam_pos = np.array(
        [math.cos(angle) * _CAM_DIST, _CAM_HEIGHT, math.sin(angle) * _CAM_DIST],
        dtype=np.float32,
    )
    forward = -cam_pos / np.linalg.norm(cam_pos)
    right = np.cross(forward, np.array([0, 1, 0], dtype=np.float32))
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    # rows: world→camera basis. cam_local[:,2] = dot(point, forward) is positive in front.
    R = np.stack([right, up, forward], axis=0)
    return cam_pos, R


def _project_box(box: _Box, cam_pos: np.ndarray, R: np.ndarray,
                 focal: float, cx: float, cy: float,
                 out: list[tuple[float, list, tuple[int, int, int]]]) -> None:
    verts_world = _UNIT_CUBE_VERTS * box.half + box.center
    cam_local = (verts_world - cam_pos) @ R.T
    zs = cam_local[:, 2]
    if not np.any(zs > _NEAR):
        return
    inv_z = np.where(zs > _NEAR, 1.0 / zs, 0.0)
    xs2 = cam_local[:, 0] * focal * inv_z + cx
    ys2 = -cam_local[:, 1] * focal * inv_z + cy

    for face_idx, normal in _CUBE_FACES:
        face_center = verts_world[list(face_idx)].mean(axis=0)
        if np.dot(face_center - cam_pos, normal) >= 0:
            continue
        z_face = zs[list(face_idx)]
        if np.any(z_face <= _NEAR):
            continue
        pts = [(float(xs2[i]), float(ys2[i])) for i in face_idx]
        lambert = max(0.0, float(np.dot(normal, _LIGHT_DIR)))
        shade = _AMBIENT + (1.0 - _AMBIENT) * lambert
        col = (
            int(box.color[0] * shade),
            int(box.color[1] * shade),
            int(box.color[2] * shade),
        )
        out.append((float(z_face.mean()), pts, col))


def create(settings: dict) -> VinesScreensaver:
    return VinesScreensaver(settings)


# ── standalone runner ────────────────────────────────────────────────────────
# Run this file directly to preview the screensaver in a window without launching
# the rest of FundingCAPTCHA: `python ScreenSavers/pipes_3d.py [--fullscreen]`.
if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Preview the 3D vines screensaver")
    ap.add_argument("--fullscreen", action="store_true")
    ap.add_argument("--width",  type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    args = ap.parse_args()

    pygame.init()
    flags  = pygame.FULLSCREEN if args.fullscreen else 0
    size   = (args.width, args.height)
    screen = pygame.display.set_mode(size, flags)
    pygame.display.set_caption("FundingCAPTCHA — Vines preview")
    clock  = pygame.time.Clock()

    saver = create({})
    while True:
        dt = clock.tick(30) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                pygame.quit(); sys.exit(0)
        saver.update(dt, None)
        saver.draw(screen)
        pygame.display.flip()
