#!/usr/bin/env python3
"""
TouchTest — Orbbec Gemini 336L touch detection for projected screen.

Workflow:
  1. BG_CAL     — collect background depth model (keep screen clear)
  2. CORNER_CAL — touch 4 screen corners in order to calibrate perspective
  3. LIVE        — detect and show touches on grid

Corner order: TOP-LEFT → TOP-RIGHT → BOTTOM-RIGHT → BOTTOM-LEFT

Keys:
  Q / Escape — quit
  R          — wipe calibration, restart
  D          — toggle debug overlay (foreground mask)
"""

from __future__ import annotations

import argparse
import queue
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import cv2
import numpy as np
import pygame

DIR      = Path(__file__).parent
CAL_PATH = DIR / "calibration.npz"

# ── Colours ──────────────────────────────────────────────────────────────────
BLACK    = (  0,   0,   0)
WHITE    = (255, 255, 255)
DK_GREY  = ( 28,  28,  28)
MID_GREY = ( 75,  75,  75)
LT_GREY  = (140, 140, 140)
GREEN    = (  0, 200,  75)
YELLOW   = (240, 200,   0)
CYAN     = (  0, 200, 220)
RED      = (220,  40,  40)

FPS = 30

MIN_DEPTH_MM = 100
MAX_DEPTH_MM = 3000
MIN_VALID_FRAMES = 10

# Corner order: TL TR BR BL
# UV: u=0 left, u=1 right, v=0 bottom, v=1 top
CORNERS    = ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-RIGHT", "BOTTOM-LEFT"]
CORNER_UV  = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]


class State(Enum):
    BG_CAL     = auto()
    CORNER_CAL = auto()
    LIVE       = auto()


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class Config:
    serial: str | None = None
    cam_w: int         = 640
    cam_h: int         = 400
    cam_fps: int       = 30
    screen_w_cm: float = 162.56
    screen_h_cm: float = 121.92
    cols: int          = 4
    rows: int          = 4
    hover_mm: int      = 20
    bg_frames: int     = 60
    max_touches: int   = 5
    min_blob_px: int   = 200
    dwell_frames: int  = 45     # frames to hold still before corner accepted (~1.5s @30fps)
    stable_px: float   = 8.0    # max centroid jitter during dwell
    fullscreen: bool   = True
    debug: bool        = False
    recalibrate: bool  = False


# ── Calibration data ──────────────────────────────────────────────────────────

@dataclass
class CalData:
    cam_w: int
    cam_h: int
    background: np.ndarray   # uint16 (H, W) — per-pixel median depth
    valid_mask: np.ndarray   # bool   (H, W) — pixels with reliable background
    homography: np.ndarray   # float64 (3, 3) — camera pixels → screen UV
    screen_mask: np.ndarray  # uint8  (H, W) — 255 inside calibrated screen quad
    hover_mm: int

    def save(self, path: Path) -> None:
        np.savez_compressed(
            path,
            background=self.background,
            valid_mask=self.valid_mask,
            homography=self.homography,
            screen_mask=self.screen_mask,
            meta=np.array([self.cam_w, self.cam_h, self.hover_mm], dtype=np.int32),
        )
        print(f"Calibration saved → {path}")

    @classmethod
    def load(cls, path: Path) -> "CalData":
        d = np.load(path)
        cam_w, cam_h, hover_mm = int(d["meta"][0]), int(d["meta"][1]), int(d["meta"][2])
        return cls(
            cam_w=cam_w,
            cam_h=cam_h,
            background=d["background"],
            valid_mask=d["valid_mask"].astype(bool),
            homography=d["homography"],
            screen_mask=d["screen_mask"],
            hover_mm=hover_mm,
        )


# ── Background calibration ────────────────────────────────────────────────────

class BgCal:
    def __init__(self, n: int) -> None:
        self._n = max(1, n)
        self._frames: list[np.ndarray] = []

    @property
    def progress(self) -> float:
        return min(1.0, len(self._frames) / self._n)

    def push(self, depth: np.ndarray) -> bool:
        self._frames.append(depth.astype(np.uint16))
        return len(self._frames) >= self._n

    def build(self) -> tuple[np.ndarray, np.ndarray]:
        """Returns (background uint16 H×W, valid_mask bool H×W)."""
        frames = np.stack(self._frames, axis=0)          # (N, H, W)
        valid  = (frames >= MIN_DEPTH_MM) & (frames <= MAX_DEPTH_MM)
        num_valid = valid.sum(axis=0)                    # (H, W)
        valid_mask = num_valid >= MIN_VALID_FRAMES

        sentinel = np.iinfo(np.uint16).max
        masked   = np.where(valid, frames, sentinel)
        masked.sort(axis=0)                               # valid values first

        median_idx = (num_valid // 2).clip(0, len(self._frames) - 1)
        H, W = frames.shape[1], frames.shape[2]
        ii, jj = np.indices((H, W))
        background = masked[median_idx, ii, jj]
        background[~valid_mask] = 0
        return background, valid_mask


# ── Foreground mask ───────────────────────────────────────────────────────────

_MORPH_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))


def foreground(
    depth: np.ndarray,       # uint16 (H, W)
    background: np.ndarray,  # uint16 (H, W)
    valid_mask: np.ndarray,  # bool   (H, W)
    hover_mm: int,
    screen_mask: np.ndarray | None = None,  # uint8 (H, W)
) -> np.ndarray:
    """Binary foreground mask (H, W) uint8 — pixels closer than background by hover_mm."""
    d   = depth.astype(np.int32)
    b   = background.astype(np.int32)
    fg  = (
        valid_mask
        & (d > MIN_DEPTH_MM)
        & (d < MAX_DEPTH_MM)
        & ((b - d) > hover_mm)
    ).astype(np.uint8) * 255
    if screen_mask is not None:
        fg &= (screen_mask > 0).astype(np.uint8) * 255
    # Opening (erode then dilate) removes isolated noise pixels and thin speckle.
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, _MORPH_KERNEL)
    return fg


# ── Touch detection ───────────────────────────────────────────────────────────

@dataclass
class Touch:
    cam_cx: float    # centroid in camera pixels
    cam_cy: float
    u: float         # screen UV: 0=left,   1=right
    v: float         # screen UV: 0=bottom, 1=top
    px_count: int


def detect_touches(
    fg: np.ndarray,
    H: np.ndarray,
    min_px: int,
    max_touches: int,
) -> list[Touch]:
    n, _, stats, centroids = cv2.connectedComponentsWithStats(fg, connectivity=8)
    candidates: list[tuple[int, float, float]] = []
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area >= min_px:
            candidates.append((area, float(centroids[i][0]), float(centroids[i][1])))
    candidates.sort(reverse=True)

    touches: list[Touch] = []
    for area, cx, cy in candidates[:max_touches * 2]:
        uv = cv2.perspectiveTransform(
            np.array([[[cx, cy]]], dtype=np.float32),
            H.astype(np.float32),
        )[0][0]
        u, v = float(uv[0]), float(uv[1])
        if 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0:
            touches.append(Touch(cam_cx=cx, cam_cy=cy, u=u, v=v, px_count=area))
            if len(touches) >= max_touches:
                break
    return touches


# ── Corner calibration ────────────────────────────────────────────────────────

# For each corner, score foreground pixels so the one AT the screen corner
# scores highest.  Higher score = closer to that corner in camera frame.
# TL: min(px+py)  TR: max(px-py)  BR: max(px+py)  BL: max(py-px)
_CORNER_SCORE_FN = [
    lambda xs, ys: -(xs + ys),   # TL
    lambda xs, ys:   xs - ys,    # TR
    lambda xs, ys:   xs + ys,    # BR
    lambda xs, ys:   ys - xs,    # BL
]
_CAL_TOP_FRAC = 0.03   # centroid of the top 3% most-extreme pixels
_CAL_TOP_MAX  = 40     # never average more than this many pixels (keeps focus on fingertip)
_CAL_MIN_PX   = 20     # minimum pixels for that centroid


def _corner_contact_point(fg: np.ndarray, corner_idx: int) -> tuple[float, float] | None:
    """
    Return the camera-pixel (cx, cy) of the actual contact point for the given
    corner, ignoring the rest of the arm/hand blob.

    Works by scoring every foreground pixel toward the expected camera-frame
    corner (TL→top-left of frame, etc.) and averaging the top 10%.
    This finds the fingertip even when the whole arm is visible.
    """
    ys, xs = np.where(fg > 0)
    if len(xs) < _CAL_MIN_PX:
        return None
    scores   = _CORNER_SCORE_FN[corner_idx](xs.astype(np.float32), ys.astype(np.float32))
    top_n    = max(_CAL_MIN_PX, min(_CAL_TOP_MAX, int(len(xs) * _CAL_TOP_FRAC)))
    top_idx  = np.argpartition(scores, -top_n)[-top_n:]
    return float(xs[top_idx].mean()), float(ys[top_idx].mean())


class CornerCal:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self.idx  = 0                               # next corner to collect
        self._pts: list[tuple[float, float]] = []
        self._dcx: float | None = None
        self._dcy: float | None = None
        self._df  = 0
        self.just_accepted = False
        self.detected_pt: tuple[float, float] | None = None  # current contact estimate

    @property
    def name(self) -> str:
        return CORNERS[self.idx] if not self.done else "Done!"

    @property
    def dwell_progress(self) -> float:
        return min(1.0, self._df / self._cfg.dwell_frames)

    @property
    def done(self) -> bool:
        return len(self._pts) == 4

    def push_fg(self, fg: np.ndarray) -> None:
        """Feed a foreground mask. Sets self.just_accepted = True when a corner is captured."""
        self.just_accepted = False
        self.detected_pt   = None
        if self.done:
            return

        pt = _corner_contact_point(fg, self.idx)
        if pt is None:
            self._dcx = self._dcy = None
            self._df  = 0
            return

        best_cx, best_cy = pt
        self.detected_pt = pt

        moved = (
            self._dcx is None
            or abs(best_cx - self._dcx) > self._cfg.stable_px
            or abs(best_cy - self._dcy) > self._cfg.stable_px
        )
        if moved:
            self._dcx, self._dcy = best_cx, best_cy
            self._df = 1
        else:
            self._df += 1

        if self._df >= self._cfg.dwell_frames:
            self._pts.append((self._dcx, self._dcy))
            self.idx += 1
            self._dcx = self._dcy = None
            self._df  = 0
            self.just_accepted = True

    def build(self, cam_h: int, cam_w: int) -> tuple[np.ndarray, np.ndarray]:
        """Returns (homography 3×3, screen_mask H×W uint8)."""
        src = np.float32(self._pts)
        dst = np.float32(CORNER_UV)
        H   = cv2.getPerspectiveTransform(src, dst)
        mask = np.zeros((cam_h, cam_w), dtype=np.uint8)
        poly = np.float32(self._pts).reshape(-1, 1, 2).astype(np.int32)
        cv2.fillPoly(mask, [poly], 255)
        return H, mask


# ── Camera thread ─────────────────────────────────────────────────────────────

def camera_thread(cfg: Config, q: "queue.Queue[np.ndarray]", stop: threading.Event) -> None:
    try:
        from pyorbbecsdk import Config as OBC, Context, OBFormat, OBSensorType, Pipeline
    except ImportError:
        print("ERROR: pyorbbecsdk not installed. Run: pip install pyorbbecsdk", file=sys.stderr)
        return

    while not stop.is_set():
        pipeline = None
        try:
            if cfg.serial:
                ctx      = Context()
                dev_list = ctx.query_devices()
                device   = dev_list.get_device_by_serial_number(cfg.serial)
                pipeline = Pipeline(device)
            else:
                pipeline = Pipeline()

            pl   = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            prof = pl.get_video_stream_profile(cfg.cam_w, cfg.cam_h, OBFormat.Y16, cfg.cam_fps)
            obc  = OBC()
            obc.enable_stream(prof)
            pipeline.start(obc)
            print("Camera started.")

            while not stop.is_set():
                fs = pipeline.wait_for_frames(100)
                if fs is None:
                    continue
                df = fs.get_depth_frame()
                if df is None:
                    continue
                raw   = np.frombuffer(bytes(df.get_data()), dtype=np.uint16)
                depth = raw.reshape(df.get_height(), df.get_width()).copy()
                if q.full():
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        pass
                q.put_nowait(depth)

        except Exception as e:
            print(f"Camera error: {e}", file=sys.stderr)
        finally:
            if pipeline is not None:
                try:
                    pipeline.stop()
                except Exception:
                    pass
        if not stop.is_set():
            time.sleep(2.0)


# ── Pygame helpers ────────────────────────────────────────────────────────────

def letterbox(win_w: int, win_h: int, aspect: float) -> tuple[int, int, int, int]:
    if win_w / win_h > aspect:
        gh = win_h
        gw = int(gh * aspect)
    else:
        gw = win_w
        gh = int(gw / aspect)
    return (win_w - gw) // 2, (win_h - gh) // 2, gw, gh


def uv_to_px(u: float, v: float, gx: int, gy: int, gw: int, gh: int) -> tuple[int, int]:
    return int(gx + u * gw), int(gy + (1.0 - v) * gh)


def corner_screen_px(idx: int, gx: int, gy: int, gw: int, gh: int) -> tuple[int, int]:
    u, v = CORNER_UV[idx]
    return uv_to_px(u, v, gx, gy, gw, gh)


def draw_grid(surf: pygame.Surface, gx: int, gy: int, gw: int, gh: int,
              cols: int, rows: int) -> None:
    pygame.draw.rect(surf, DK_GREY, (gx, gy, gw, gh))
    for c in range(1, cols):
        x = int(gx + c * gw / cols)
        pygame.draw.line(surf, MID_GREY, (x, gy), (x, gy + gh))
    for r in range(1, rows):
        y = int(gy + r * gh / rows)
        pygame.draw.line(surf, MID_GREY, (gx, y), (gx + gw, y))
    pygame.draw.rect(surf, GREEN, (gx, gy, gw, gh), 2)


def highlight_cell(surf: pygame.Surface, gx: int, gy: int, gw: int, gh: int,
                   cols: int, rows: int, col: int, row: int,
                   color: tuple, alpha: int) -> None:
    cw = gw // cols
    ch = gh // rows
    s  = pygame.Surface((cw, ch), pygame.SRCALPHA)
    s.fill((*color, alpha))
    surf.blit(s, (gx + col * cw, gy + row * ch))


def depth_surface(depth: np.ndarray, tw: int, th: int) -> pygame.Surface:
    """Normalize depth to greyscale pygame surface scaled to (tw, th)."""
    valid = depth[depth > 0]
    if len(valid) == 0:
        s = pygame.Surface((tw, th))
        s.fill(BLACK)
        return s
    lo, hi = int(valid.min()), int(valid.max())
    if hi == lo:
        norm = np.zeros_like(depth, dtype=np.uint8)
    else:
        norm = ((depth.astype(np.float32) - lo) / (hi - lo) * 255).clip(0, 255).astype(np.uint8)
    rgb  = np.stack([norm, norm, norm], axis=-1)           # (H, W, 3)
    surf = pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))  # expects (W, H, 3)
    return pygame.transform.scale(surf, (tw, th))


def fg_overlay_surface(fg: np.ndarray, tw: int, th: int) -> pygame.Surface:
    """Foreground mask as semi-transparent cyan surface scaled to (tw, th)."""
    fg_s  = cv2.resize(fg, (tw, th), interpolation=cv2.INTER_NEAREST)
    surf  = pygame.Surface((tw, th), pygame.SRCALPHA)
    mask  = fg_s.T > 0        # (W, H) — surfarray is column-major
    pix   = pygame.surfarray.pixels3d(surf)
    alp   = pygame.surfarray.pixels_alpha(surf)
    pix[mask] = [0, 220, 200]
    alp[mask] = 140
    del pix, alp               # unlock surface
    return surf


def draw_dwell_arc(surf: pygame.Surface, cx: int, cy: int,
                   progress: float, radius: int = 36) -> None:
    if progress <= 0:
        return
    angle = int(progress * 360)
    for a in range(0, angle, 4):
        rad = np.radians(a - 90)
        ex  = int(cx + radius * np.cos(rad))
        ey  = int(cy + radius * np.sin(rad))
        pygame.draw.circle(surf, GREEN, (ex, ey), 3)


# ── Draw states ───────────────────────────────────────────────────────────────

def draw_bg_cal(surf: pygame.Surface, fonts: dict, WW: int, WH: int, progress: float) -> None:
    cx, cy = WW // 2, WH // 2
    t1 = fonts["big"].render("Calibrating background…", True, YELLOW)
    t2 = fonts["med"].render("Keep the screen clear — no hands", True, LT_GREY)
    surf.blit(t1, (cx - t1.get_width() // 2, cy - 70))
    surf.blit(t2, (cx - t2.get_width() // 2, cy - 20))
    bw, bh = 420, 24
    bx, by = cx - bw // 2, cy + 30
    pygame.draw.rect(surf, MID_GREY, (bx, by, bw, bh))
    pygame.draw.rect(surf, GREEN,    (bx, by, int(bw * progress), bh))
    pygame.draw.rect(surf, WHITE,    (bx, by, bw, bh), 2)
    pct = fonts["med"].render(f"{int(progress * 100)}%", True, WHITE)
    surf.blit(pct, (cx - pct.get_width() // 2, by + bh + 10))


def draw_corner_cal(
    surf: pygame.Surface, fonts: dict,
    WW: int, WH: int, gx: int, gy: int, gw: int, gh: int,
    corner_cal: CornerCal, cfg: Config,
    depth: np.ndarray | None, fg: np.ndarray | None,
) -> None:
    # Camera feed in the grid area
    if depth is not None:
        surf.blit(depth_surface(depth, gw, gh), (gx, gy))
    if fg is not None:
        surf.blit(fg_overlay_surface(fg, gw, gh), (gx, gy))
    pygame.draw.rect(surf, MID_GREY, (gx, gy, gw, gh), 2)

    # Target corner indicator (pulsing ring at the expected screen grid corner)
    if not corner_cal.done:
        tx, ty = corner_screen_px(corner_cal.idx, gx, gy, gw, gh)
        pulse  = int(abs(pygame.time.get_ticks() % 1000 - 500) / 500 * 60 + 195)
        pygame.draw.circle(surf, (pulse, pulse, 0), (tx, ty), 28, 4)
        pygame.draw.circle(surf, YELLOW, (tx, ty), 7)
        draw_dwell_arc(surf, tx, ty, corner_cal.dwell_progress)

    # Detected contact point — shown in camera-frame coordinates scaled to grid
    if corner_cal.detected_pt is not None:
        dpx = gx + int(corner_cal.detected_pt[0] * gw / cfg.cam_w)
        dpy = gy + int(corner_cal.detected_pt[1] * gh / cfg.cam_h)
        # Scale properly from camera pixels to grid pixels
        pygame.draw.circle(surf, GREEN, (dpx, dpy), 8)
        pygame.draw.circle(surf, WHITE, (dpx, dpy), 8, 2)

    # Instructions
    msg  = f"Touch {corner_cal.name} corner — fingertip only"
    sub  = f"Corner {min(corner_cal.idx + 1, 4)} of 4  |  keep arm off-screen"
    t1   = fonts["big"].render(msg, True, YELLOW)
    t2   = fonts["sml"].render(sub, True, LT_GREY)
    surf.blit(t1, (WW // 2 - t1.get_width() // 2, 18))
    surf.blit(t2, (WW // 2 - t2.get_width() // 2, 60))

    # Dwell bar at bottom
    prog = corner_cal.dwell_progress
    bw   = 320
    bx   = WW // 2 - bw // 2
    by   = WH - 44
    pygame.draw.rect(surf, MID_GREY, (bx, by, bw, 18))
    pygame.draw.rect(surf, GREEN,    (bx, by, int(bw * prog), 18))
    pygame.draw.rect(surf, WHITE,    (bx, by, bw, 18), 1)


def draw_live(
    surf: pygame.Surface, fonts: dict,
    WW: int, WH: int, gx: int, gy: int, gw: int, gh: int,
    cfg: Config, touches: list[Touch],
    flash_cells: dict[tuple[int, int], int], fg: np.ndarray | None,
    debug: bool,
) -> None:
    draw_grid(surf, gx, gy, gw, gh, cfg.cols, cfg.rows)

    if debug and fg is not None:
        surf.blit(fg_overlay_surface(fg, gw, gh), (gx, gy))

    flash_max = FPS * 2

    # Live touch cells
    live_cells: set[tuple[int, int]] = set()
    for t in touches:
        col = min(cfg.cols - 1, int(t.u * cfg.cols))
        row = min(cfg.rows - 1, int((1.0 - t.v) * cfg.rows))
        live_cells.add((col, row))

    # Highlights: live = bright, fading flash = dim
    for (col, row), frames_left in flash_cells.items():
        if (col, row) in live_cells:
            alpha = 190
        else:
            alpha = max(30, int(150 * frames_left / flash_max))
        highlight_cell(surf, gx, gy, gw, gh, cfg.cols, cfg.rows, col, row, CYAN, alpha)

    # Touch dots
    for t in touches:
        px, py = uv_to_px(t.u, t.v, gx, gy, gw, gh)
        pygame.draw.circle(surf, CYAN,  (px, py), 14)
        pygame.draw.circle(surf, WHITE, (px, py), 14, 2)
        col = min(cfg.cols - 1, int(t.u * cfg.cols))
        row = min(cfg.rows - 1, int((1.0 - t.v) * cfg.rows))
        lbl = fonts["sml"].render(f"({col},{row})", True, WHITE)
        surf.blit(lbl, (px + 18, py - 10))

    # HUD top-right
    hud = [
        f"touches: {len(touches)}",
        f"grid: {cfg.cols}×{cfg.rows}",
        f"hover: {cfg.hover_mm}mm",
        f"debug: {'ON' if debug else 'off'}",
        "D=debug  R=recal  Q=quit",
    ]
    for i, line in enumerate(hud):
        color = YELLOW if i < 4 else LT_GREY
        lbl   = fonts["sml"].render(line, True, color)
        surf.blit(lbl, (WW - lbl.get_width() - 8, 8 + i * 22))


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> Config:
    ap = argparse.ArgumentParser(description="TouchTest — depth-camera screen touch detection")
    ap.add_argument("--serial",       default=None,  help="Orbbec device serial (auto-detect if omitted)")
    ap.add_argument("--cam-w",        type=int,   default=640,   metavar="PX")
    ap.add_argument("--cam-h",        type=int,   default=400,   metavar="PX")
    ap.add_argument("--cam-fps",      type=int,   default=30,    metavar="N")
    ap.add_argument("--screen-w",     type=float, default=150.0, metavar="CM", dest="screen_w_cm")
    ap.add_argument("--screen-h",     type=float, default=80.0,  metavar="CM", dest="screen_h_cm")
    ap.add_argument("--cols",         type=int,   default=5)
    ap.add_argument("--rows",         type=int,   default=4)
    ap.add_argument("--hover-mm",     type=int,   default=20,    metavar="MM")
    ap.add_argument("--bg-frames",    type=int,   default=60,    metavar="N")
    ap.add_argument("--max-touches",  type=int,   default=5,     metavar="N")
    ap.add_argument("--min-blob-px",  type=int,   default=200,   metavar="PX")
    ap.add_argument("--dwell-frames", type=int,   default=45,    metavar="N",
                    help="Frames to hold corner still before accepting (~1.5s at 30fps)")
    ap.add_argument("--no-fullscreen", action="store_false", dest="fullscreen")
    ap.add_argument("--debug",        action="store_true")
    ap.add_argument("--recalibrate",  action="store_true", help="Wipe saved calibration and restart")
    args = ap.parse_args()
    return Config(**{k: v for k, v in vars(args).items()})


def touch_to_cell(t: Touch, cols: int, rows: int) -> tuple[int, int]:
    col = min(cols - 1, int(t.u * cols))
    row = min(rows - 1, int((1.0 - t.v) * rows))
    return col, row


def main() -> None:
    cfg = parse_args()

    if cfg.recalibrate:
        CAL_PATH.unlink(missing_ok=True)
        print("Calibration cleared.")

    # Camera thread
    frame_q: queue.Queue[np.ndarray] = queue.Queue(maxsize=4)
    stop    = threading.Event()
    threading.Thread(target=camera_thread, args=(cfg, frame_q, stop), daemon=True).start()

    # Pygame init
    pygame.init()
    info  = pygame.display.Info()
    if cfg.fullscreen:
        WW, WH = info.current_w, info.current_h
        screen = pygame.display.set_mode((WW, WH), pygame.FULLSCREEN | pygame.NOFRAME)
    else:
        WW, WH = 1280, 720
        screen = pygame.display.set_mode((WW, WH))
    pygame.display.set_caption("TouchTest")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    fonts = {
        "big": pygame.font.SysFont("monospace", 36, bold=True),
        "med": pygame.font.SysFont("monospace", 24, bold=True),
        "sml": pygame.font.SysFont("monospace", 18),
    }

    aspect = cfg.screen_w_cm / cfg.screen_h_cm
    gx, gy, gw, gh = letterbox(WW, WH, aspect)

    debug = cfg.debug

    # ── Initial state ─────────────────────────────────────────────────────────
    cal_data: CalData | None = None
    if not cfg.recalibrate and CAL_PATH.exists():
        try:
            cal_data = CalData.load(CAL_PATH)
            print("Calibration loaded.")
        except Exception as e:
            print(f"Could not load calibration ({e}), recalibrating.")

    if cal_data is not None:
        state      = State.LIVE
        bg_cal     = None
        corner_cal = None
    else:
        state      = State.BG_CAL
        bg_cal     = BgCal(cfg.bg_frames)
        corner_cal = None

    current_depth: np.ndarray | None = None
    current_fg:    np.ndarray | None = None
    touches:       list[Touch]       = []
    flash_cells:   dict[tuple[int, int], int] = {}
    FLASH_DURATION = FPS * 2

    running = True
    while running:
        # ── Events ───────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif ev.key == pygame.K_r:
                    CAL_PATH.unlink(missing_ok=True)
                    cal_data = corner_cal = None
                    state    = State.BG_CAL
                    bg_cal   = BgCal(cfg.bg_frames)
                    touches  = []
                    flash_cells.clear()
                    current_fg = None
                    print("Recalibrating.")
                elif ev.key == pygame.K_d:
                    debug = not debug

        # ── Latest frame ──────────────────────────────────────────────────────
        try:
            while True:
                current_depth = frame_q.get_nowait()
        except queue.Empty:
            pass

        # ── State machine ─────────────────────────────────────────────────────
        if current_depth is not None:
            if state == State.BG_CAL:
                assert bg_cal is not None
                done = bg_cal.push(current_depth)
                if done:
                    background, valid_mask = bg_cal.build()
                    corner_cal = CornerCal(cfg)
                    state      = State.CORNER_CAL
                    bg_cal     = None
                    print("Background ready. Starting corner calibration.")

            elif state == State.CORNER_CAL:
                assert corner_cal is not None
                fg = foreground(current_depth, background, valid_mask, cfg.hover_mm)
                current_fg = fg
                corner_cal.push_fg(fg)
                if corner_cal.just_accepted:
                    prev = corner_cal.idx - 1
                    print(f"  ✓ {CORNERS[prev]} captured.")
                if corner_cal.done:
                    H, smask = corner_cal.build(cfg.cam_h, cfg.cam_w)
                    cal_data  = CalData(
                        cam_w=cfg.cam_w, cam_h=cfg.cam_h,
                        background=background, valid_mask=valid_mask,
                        homography=H, screen_mask=smask,
                        hover_mm=cfg.hover_mm,
                    )
                    cal_data.save(CAL_PATH)
                    corner_cal = None
                    state      = State.LIVE
                    print("Calibration complete!")

            elif state == State.LIVE:
                assert cal_data is not None
                fg = foreground(
                    current_depth,
                    cal_data.background, cal_data.valid_mask,
                    cal_data.hover_mm, cal_data.screen_mask,
                )
                current_fg = fg
                touches    = detect_touches(fg, cal_data.homography, cfg.min_blob_px, cfg.max_touches)
                for t in touches:
                    cell = touch_to_cell(t, cfg.cols, cfg.rows)
                    flash_cells[cell] = FLASH_DURATION
                for cell in list(flash_cells):
                    flash_cells[cell] -= 1
                    if flash_cells[cell] <= 0:
                        del flash_cells[cell]

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BLACK)

        if state == State.BG_CAL:
            assert bg_cal is not None
            draw_bg_cal(screen, fonts, WW, WH, bg_cal.progress)

        elif state == State.CORNER_CAL:
            assert corner_cal is not None
            draw_corner_cal(
                screen, fonts, WW, WH, gx, gy, gw, gh,
                corner_cal, cfg, current_depth, current_fg,
            )

        elif state == State.LIVE:
            draw_live(
                screen, fonts, WW, WH, gx, gy, gw, gh,
                cfg, touches, flash_cells, current_fg, debug,
            )

        # Waiting-for-camera indicator
        if current_depth is None:
            msg = fonts["med"].render("Waiting for camera…", True, RED)
            screen.blit(msg, (WW // 2 - msg.get_width() // 2, WH - 50))

        pygame.display.flip()
        clock.tick(FPS)

    stop.set()
    pygame.quit()


if __name__ == "__main__":
    main()
