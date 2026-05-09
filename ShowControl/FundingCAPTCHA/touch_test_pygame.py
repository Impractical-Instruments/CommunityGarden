#!/usr/bin/env python3
"""
FundingCAPTCHA pygame touch tester — no browser required.

Usage:
  python touch_test_pygame.py --mock-camera
  python touch_test_pygame.py --camera
  python touch_test_pygame.py --camera --cols 4 --rows 5
  python touch_test_pygame.py --camera --width 1280 --height 720

Exit: press q or Ctrl+C.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import threading
from pathlib import Path

# Must be set before pygame import
if "SDL_VIDEODRIVER" not in os.environ:
    os.environ["SDL_VIDEODRIVER"] = "kmsdrm"

import pygame

DIR           = Path(__file__).parent
SETTINGS_PATH = DIR / "captcha-settings.json"

_REPO = (DIR / "../..").resolve()
sys.path.insert(0, str(_REPO))

try:
    import numpy as np
    from IIVision import (
        Calibrator, MockCamera, OrbbecCamera, StabilizerConfig, Transform, Rotator,
        build_calibration, run_pipeline,
    )
except ImportError as e:
    print(f"ERROR: IIVision not available: {e}", file=sys.stderr)
    sys.exit(1)

BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
GREY   = (80,  80,  80)
GREEN  = (0,   220, 80)
YELLOW = (255, 220, 0)
CYAN   = (0,   200, 220)
RED    = (220, 40,  40)


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text())
    return {}


def world_to_px(x_cm: float, z_cm: float, rect: dict, W: int, H: int) -> tuple[int, int]:
    px = int((x_cm - rect["x0"]) / (rect["x1"] - rect["x0"]) * W)
    py = int((1.0 - (z_cm - rect["z0"]) / (rect["z1"] - rect["z0"])) * H)
    return px, py


def blob_to_cell(x_cm: float, z_cm: float, rect: dict, cols: int, rows: int) -> tuple[int, int]:
    col = int((x_cm - rect["x0"]) / (rect["x1"] - rect["x0"]) * cols)
    row = int((1.0 - (z_cm - rect["z0"]) / (rect["z1"] - rect["z0"])) * rows)
    return max(0, min(cols - 1, col)), max(0, min(rows - 1, row))


def draw_grid(surf: pygame.Surface, cols: int, rows: int, W: int, H: int) -> None:
    for c in range(1, cols):
        x = c * W // cols
        pygame.draw.line(surf, GREY, (x, 0), (x, H))
    for r in range(1, rows):
        y = r * H // rows
        pygame.draw.line(surf, GREY, (0, y), (W, y))


def draw_border(surf: pygame.Surface, W: int, H: int) -> None:
    pygame.draw.rect(surf, GREEN, (0, 0, W, H), 3)


def draw_blobs(
    surf: pygame.Surface,
    blobs: list[dict],
    rect: dict,
    cols: int,
    rows: int,
    W: int,
    H: int,
    font: pygame.font.Font,
) -> None:
    cw, ch = W // cols, H // rows
    for b in blobs:
        x, z = b["x"], b["z"]
        px, py = world_to_px(x, z, rect, W, H)
        col, row = blob_to_cell(x, z, rect, cols, rows)

        cell_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        cell_surf.fill((0, 200, 220, 60))
        surf.blit(cell_surf, (col * cw, row * ch))

        pygame.draw.circle(surf, CYAN, (px, py), 16)
        pygame.draw.circle(surf, WHITE, (px, py), 16, 2)

        label = font.render(f"#{b['id']}  z={z:.1f}", True, WHITE)
        surf.blit(label, (px + 20, py - 12))


def _calibration_worker(
    camera: object,
    num_frames: int,
    result_q: queue.Queue,
    progress_q: queue.Queue,
) -> None:
    try:
        calibrator = Calibrator(num_frames)
        count = 0
        with camera:
            for frame in camera.frames():
                count += 1
                progress_q.put(count)
                if calibrator.push_frame(frame):
                    break
        result_q.put(("ok", calibrator.build()))
    except Exception as exc:
        result_q.put(("err", str(exc)))


def _pipeline_worker(
    camera: object,
    cam_tf: Transform,
    calibration: object,
    stab_cfg: StabilizerConfig,
    blob_q: queue.Queue,
    stop: threading.Event,
) -> None:
    try:
        for tracked in run_pipeline(camera, cam_tf, calibration, stab_cfg):
            if stop.is_set():
                return
            blobs = [
                {"id": int(t.stable_id),
                 "x": float(t.world_pos_cm[0]),
                 "y": float(t.world_pos_cm[1]),
                 "z": float(t.world_pos_cm[2])}
                for t in tracked
            ]
            try:
                blob_q.put_nowait(blobs)
            except queue.Full:
                pass
    except Exception:
        pass


def show_error(screen: pygame.Surface, font: pygame.font.Font, msg: str, W: int, H: int) -> None:
    screen.fill(BLACK)
    label = font.render(f"ERROR: {msg}", True, RED)
    screen.blit(label, (W // 2 - label.get_width() // 2, H // 2 - label.get_height() // 2))
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN):
                pygame.quit()
                sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="FundingCAPTCHA pygame touch tester")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--camera",      action="store_true", help="Real Orbbec camera")
    group.add_argument("--mock-camera", action="store_true", help="Mock camera (no hardware)")
    parser.add_argument("--cols",   type=int, default=5,    metavar="N")
    parser.add_argument("--rows",   type=int, default=5,    metavar="N")
    parser.add_argument("--width",  type=int, default=1920, metavar="PX")
    parser.add_argument("--height", type=int, default=1080, metavar="PX")
    args = parser.parse_args()

    settings   = load_settings()
    rect       = settings.get("screen_rect", {"x0": -150, "x1": 150, "z0": 50, "z1": 200})
    stab_d     = settings.get("stabilizer", {})
    cam_cfg    = settings.get("camera", {})
    cal_frames = settings.get("calibration_frames", 60)

    stab_cfg = StabilizerConfig(
        max_match_dist_cm  = stab_d.get("max_match_dist_cm",  80.0),
        smoothing_alpha    = stab_d.get("smoothing_alpha",     0.3),
        max_miss_frames    = stab_d.get("max_miss_frames",     8),
        min_confirm_frames = stab_d.get("min_confirm_frames",  2),
    )

    pos_cm = cam_cfg.get("pos_cm", [0.0, 0.0, 200.0])
    rot    = cam_cfg.get("rotation", {})
    cam_tf = Transform(
        translation=np.array(pos_cm, dtype=float),
        rotation=Rotator(
            pitch=rot.get("pitch", 0.0),
            yaw=rot.get("yaw",     0.0),
            roll=rot.get("roll",   0.0),
        ),
    )

    if args.mock_camera:
        camera: object = MockCamera(
            width  = cam_cfg.get("width",  640),
            height = cam_cfg.get("height", 400),
            fps    = cam_cfg.get("fps",     10),
        )
        mode_label = "MOCK"
    else:
        camera = OrbbecCamera(
            serial = cam_cfg.get("serial") or None,
            width  = cam_cfg.get("width",  640),
            height = cam_cfg.get("height", 400),
            fps    = cam_cfg.get("fps",     10),
        )
        mode_label = "ORBBEC"

    W, H = args.width, args.height

    pygame.init()
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("CAPTCHA Touch Tester")
    pygame.mouse.set_visible(False)

    font_big = pygame.font.SysFont("monospace", 52, bold=True)
    font_sm  = pygame.font.SysFont("monospace", 28)
    clock    = pygame.time.Clock()

    # ── Phase 1: calibration ───────────────────────────────────────────────────
    progress_q: queue.Queue[int] = queue.Queue()
    result_q:   queue.Queue      = queue.Queue()

    threading.Thread(
        target=_calibration_worker,
        args=(camera, cal_frames, result_q, progress_q),
        daemon=True,
    ).start()

    progress    = 0
    calibration = None

    while calibration is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit(); sys.exit(0)

        try:
            while True:
                progress = progress_q.get_nowait()
        except queue.Empty:
            pass

        try:
            status, payload = result_q.get_nowait()
            if status == "err":
                show_error(screen, font_big, payload, W, H)
            calibration = payload
        except queue.Empty:
            pass

        screen.fill(BLACK)
        bar_w = int(progress / cal_frames * W)
        pygame.draw.rect(screen, GREY,  (0, H // 2 - 30, W, 60))
        pygame.draw.rect(screen, GREEN, (0, H // 2 - 30, bar_w, 60))
        txt = font_big.render(f"Calibrating…  {progress} / {cal_frames}", True, WHITE)
        screen.blit(txt, (W // 2 - txt.get_width() // 2, H // 2 - txt.get_height() // 2))
        pygame.display.flip()
        clock.tick(30)

    # ── Phase 2: live blob display ─────────────────────────────────────────────
    blob_q: queue.Queue[list] = queue.Queue(maxsize=4)
    stop    = threading.Event()

    threading.Thread(
        target=_pipeline_worker,
        args=(camera, cam_tf, calibration, stab_cfg, blob_q, stop),
        daemon=True,
    ).start()

    current_blobs: list[dict] = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop.set(); pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                stop.set(); pygame.quit(); sys.exit(0)

        try:
            while True:
                current_blobs = blob_q.get_nowait()
        except queue.Empty:
            pass

        screen.fill(BLACK)
        draw_grid(screen, args.cols, args.rows, W, H)
        draw_border(screen, W, H)
        draw_blobs(screen, current_blobs, rect, args.cols, args.rows, W, H, font_sm)

        hud = font_sm.render(
            f"{mode_label}  grid={args.cols}×{args.rows}  blobs={len(current_blobs)}  [q] quit",
            True, YELLOW,
        )
        screen.blit(hud, (10, 10))

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()
