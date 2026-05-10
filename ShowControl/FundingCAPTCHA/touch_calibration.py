#!/usr/bin/env python3
"""
FundingCAPTCHA pygame touch calibration tool.

Connects to a running server.py via WebSocket and overlays a calibration grid
on the projected screen area.

Usage:
  python touch_calibration.py
  python touch_calibration.py --server ws://192.168.1.5:8080/ws
  python touch_calibration.py --cols 4 --rows 3
  python touch_calibration.py --recalibrate

Corner calibration:
  If screen_corners are missing or --recalibrate is passed, the tool enters
  an interactive calibration mode. Touch each screen corner in order
  (BOTTOM-LEFT → BOTTOM-RIGHT → TOP-LEFT) and hold still; the tool detects
  the blob, waits for dwell stability, then saves coordinates automatically.

Keys:
  Q / Escape — quit
  R          — wipe corners, restart calibration
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import queue
import sys
import threading
from enum import Enum, auto
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pygame
import websockets

DIR                = Path(__file__).parent
SETTINGS_PATH      = DIR / "captcha-settings.json"
SETTINGS_LOCAL_PATH = DIR / "captcha-settings.local.json"

# ── Colours ────────────────────────────────────────────────────────────────────
BLACK    = (  0,   0,   0)
WHITE    = (255, 255, 255)
DK_GREY  = ( 28,  28,  28)
MID_GREY = ( 75,  75,  75)
LT_GREY  = (140, 140, 140)
GREEN    = (  0, 200,  75)
YELLOW   = (240, 200,   0)
CYAN     = (  0, 200, 220)
ORANGE   = (240, 130,   0)
RED      = (220,  40,  40)

FPS = 30


class State(Enum):
    CORNER_CAL = auto()
    LIVE       = auto()


# ── Corner calibration ────────────────────────────────────────────────────────

# Order matches captcha-settings.json keys; ScreenProjector needs exactly these three.
_CAL_CORNERS   = ["BOTTOM-LEFT", "BOTTOM-RIGHT", "TOP-LEFT"]
_CAL_KEYS      = ["bottom_left", "bottom_right", "top_left"]
# UV position of each corner on the grid display (u=0 left, u=1 right, v=0 bottom, v=1 top)
_CAL_CORNER_UV = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]


class CornerCal:
    """
    Detects three screen corners from server blobs (world-space cm).

    Requires exactly one blob at a time. When it has been stable within
    stable_cm for dwell_frames consecutive frames, the position is accepted.
    """

    def __init__(self, dwell_frames: int, stable_cm: float = 15.0) -> None:
        self._dwell      = max(1, dwell_frames)
        self._stable     = stable_cm
        self.idx         = 0
        self._pts: list[list[float]] = []
        self._last_xyz: list[float] | None = None
        self._df         = 0
        self.just_accepted  = False
        self.detected_xyz: list[float] | None = None
        self.blob_count   = 0

    @property
    def name(self) -> str:
        return _CAL_CORNERS[self.idx] if not self.done else "Done!"

    @property
    def done(self) -> bool:
        return len(self._pts) == 3

    @property
    def dwell_progress(self) -> float:
        return min(1.0, self._df / self._dwell)

    def push_blobs(self, blobs: list[dict]) -> None:
        self.just_accepted = False
        self.detected_xyz  = None
        self.blob_count    = len(blobs)
        if self.done:
            return

        if len(blobs) != 1:
            self._last_xyz = None
            self._df       = 0
            return

        xyz = [blobs[0]["x"], blobs[0]["y"], blobs[0]["z"]]
        self.detected_xyz = xyz

        if self._last_xyz is None:
            moved = True
        else:
            dist  = math.sqrt(sum((a - b) ** 2 for a, b in zip(xyz, self._last_xyz)))
            moved = dist > self._stable

        if moved:
            self._last_xyz = xyz
            self._df       = 1
        else:
            self._df += 1

        if self._df >= self._dwell:
            self._pts.append(xyz[:])
            self.idx      += 1
            self._last_xyz = None
            self._df       = 0
            self.just_accepted = True

    def result(self) -> dict:
        assert self.done
        return {k: v for k, v in zip(_CAL_KEYS, self._pts)}

    def reset(self) -> None:
        self.idx          = 0
        self._pts         = []
        self._last_xyz    = None
        self._df          = 0
        self.just_accepted = False
        self.detected_xyz  = None
        self.blob_count    = 0


# ── Screen projection ──────────────────────────────────────────────────────────

class ScreenProjector:
    """
    Orthographic projection from world space onto the screen plane.

    Defined by three world-space corners (cm):
      bottom_left  — origin of screen UV space (u=0, v=0)
      bottom_right — right edge (u=1, v=0)
      top_left     — top edge   (u=0, v=1)

    project() returns (u, v) in [0,1]². Values outside that range are off-screen.
    """

    def __init__(
        self,
        bottom_left:  list[float],
        bottom_right: list[float],
        top_left:     list[float],
    ) -> None:
        bl = np.array(bottom_left,  dtype=float)
        br = np.array(bottom_right, dtype=float)
        tl = np.array(top_left,     dtype=float)

        U = br - bl
        V = tl - bl
        self._w  = float(np.linalg.norm(U))
        self._h  = float(np.linalg.norm(V))
        self._U  = U / self._w
        self._V  = V / self._h
        n        = np.cross(self._U, self._V)
        self._n  = n / np.linalg.norm(n)
        self._bl = bl

    @property
    def aspect(self) -> float:
        return self._w / self._h

    def project(self, xyz: list[float]) -> tuple[float, float]:
        p        = np.array(xyz, dtype=float)
        p_plane  = p - np.dot(p - self._bl, self._n) * self._n
        u        = float(np.dot(p_plane - self._bl, self._U) / self._w)
        v        = float(np.dot(p_plane - self._bl, self._V) / self._h)
        return u, v

    def plane_distance(self, xyz: list[float]) -> float:
        """Signed distance (cm) from point to screen plane. Positive = camera side."""
        return float(np.dot(np.array(xyz, dtype=float) - self._bl, self._n))

    def in_bounds_3d(self, xyz: list[float], max_dist: float) -> bool:
        """True if point is within the screen UV rectangle and ≤ max_dist cm in front."""
        d = self.plane_distance(xyz)
        if not (0.0 < d <= max_dist):
            return False
        u, v = self.project(xyz)
        return self.in_bounds(u, v)

    @staticmethod
    def in_bounds(u: float, v: float) -> bool:
        return 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0

    @staticmethod
    def uv_to_cell(u: float, v: float, cols: int, rows: int) -> tuple[int, int]:
        col = int(u * cols)
        row = int((1.0 - v) * rows)   # v=1 → top of screen → row 0
        return max(0, min(cols - 1, col)), max(0, min(rows - 1, row))


# ── Dwell tracker ──────────────────────────────────────────────────────────────

class DwellTracker:
    """
    Tracks per-blob dwell in grid cells.

    update() takes a list of (blob_id, col, row) for in-bounds blobs.
    .immediate  → cells currently occupied (dim highlight)
    .flashing   → cells with a recently confirmed dwell tap (bright flash)
    """

    def __init__(self, dwell_frames: int) -> None:
        self._target = dwell_frames
        self._state:  dict[int, dict]           = {}  # blob_id → {col, row, frames}
        self._flash:  dict[tuple[int,int], int] = {}  # cell → frames_remaining

    def update(self, live: list[tuple[int, int, int]]) -> None:
        live_ids = {bid for bid, _, _ in live}

        for bid in list(self._state):
            if bid not in live_ids:
                del self._state[bid]

        for bid, col, row in live:
            s = self._state.get(bid)
            if s is None or s["col"] != col or s["row"] != row:
                self._state[bid] = {"col": col, "row": row, "frames": 1}
            else:
                s["frames"] += 1
                if s["frames"] == self._target:
                    self._flash[(col, row)] = self._target * 5  # visible duration

        for cell in list(self._flash):
            self._flash[cell] -= 1
            if self._flash[cell] <= 0:
                del self._flash[cell]

    @property
    def immediate(self) -> set[tuple[int, int]]:
        return {(s["col"], s["row"]) for s in self._state.values()}

    @property
    def flashing(self) -> set[tuple[int, int]]:
        return set(self._flash)


# ── WebSocket client ───────────────────────────────────────────────────────────

def _ws_thread(
    url: str,
    blob_q: "queue.Queue[list]",
    status: list[str],      # status[0] mutated in-place: "connecting"/"connected"/...
    cv_status: list[dict],  # cv_status[0] mutated in-place: {"state":..., "progress":...}
    stop: threading.Event,
) -> None:
    async def _run() -> None:
        while not stop.is_set():
            try:
                status[0] = "connecting"
                cv_status[0] = {"state": "unknown"}
                async with websockets.connect(url, ping_interval=10, open_timeout=5) as ws:
                    status[0] = "connected"
                    async for raw in ws:
                        if stop.is_set():
                            return
                        try:
                            msg = json.loads(raw)
                        except Exception:
                            continue
                        if "status" in msg:
                            cv_status[0] = {
                                "state":    msg["status"],
                                "progress": float(msg.get("progress", 1.0)),
                            }
                        blobs = msg.get("blobs")
                        if isinstance(blobs, list):
                            # Drop oldest frame if queue is full so latency stays low
                            if blob_q.full():
                                try:
                                    blob_q.get_nowait()
                                except queue.Empty:
                                    pass
                            blob_q.put_nowait(blobs)
            except Exception as exc:
                status[0] = f"disconnected ({type(exc).__name__})"
                cv_status[0] = {"state": "unknown"}
            if not stop.is_set():
                await asyncio.sleep(2.0)

    asyncio.run(_run())


# ── Layout ────────────────────────────────────────────────────────────────────

def letterbox(win_w: int, win_h: int, aspect: float) -> tuple[int, int, int, int]:
    """Return (x, y, w, h) centred in the window with the given aspect ratio."""
    if win_w / win_h > aspect:
        gh = win_h
        gw = int(gh * aspect)
    else:
        gw = win_w
        gh = int(gw / aspect)
    return (win_w - gw) // 2, (win_h - gh) // 2, gw, gh


def uv_to_px(u: float, v: float, gx: int, gy: int, gw: int, gh: int) -> tuple[int, int]:
    return int(gx + u * gw), int(gy + (1.0 - v) * gh)


# ── Drawing ────────────────────────────────────────────────────────────────────

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
                   color: tuple[int, int, int], alpha: int) -> None:
    cw = gw // cols
    ch = gh // rows
    s  = pygame.Surface((cw, ch), pygame.SRCALPHA)
    s.fill((*color, alpha))
    surf.blit(s, (gx + col * cw, gy + row * ch))


def draw_blob_dot(surf: pygame.Surface, px: int, py: int,
                  color: tuple[int, int, int], radius: int = 12) -> None:
    pygame.draw.circle(surf, color,  (px, py), radius)
    pygame.draw.circle(surf, WHITE,  (px, py), radius, 2)


def draw_dwell_arc(surf: pygame.Surface, cx: int, cy: int,
                   progress: float, radius: int = 36) -> None:
    if progress <= 0:
        return
    angle = int(progress * 360)
    for a in range(0, angle, 4):
        rad = math.radians(a - 90)
        ex  = int(cx + radius * math.cos(rad))
        ey  = int(cy + radius * math.sin(rad))
        pygame.draw.circle(surf, GREEN, (ex, ey), 3)


def draw_corner_cal(
    surf: pygame.Surface,
    fonts: dict,
    WW: int, WH: int,
    gx: int, gy: int, gw: int, gh: int,
    cal: CornerCal,
) -> None:
    pygame.draw.rect(surf, DK_GREY, (gx, gy, gw, gh))
    pygame.draw.rect(surf, MID_GREY, (gx, gy, gw, gh), 2)

    if not cal.done:
        # Pulsing ring at the target grid corner
        u, v   = _CAL_CORNER_UV[cal.idx]
        tx, ty = uv_to_px(u, v, gx, gy, gw, gh)
        pulse  = int(abs(pygame.time.get_ticks() % 1000 - 500) / 500 * 60 + 195)
        pygame.draw.circle(surf, (pulse, pulse, 0), (tx, ty), 28, 4)
        pygame.draw.circle(surf, YELLOW, (tx, ty), 7)
        draw_dwell_arc(surf, tx, ty, cal.dwell_progress)

    # Previously accepted corners
    for i in range(cal.idx):
        u, v   = _CAL_CORNER_UV[i]
        px, py = uv_to_px(u, v, gx, gy, gw, gh)
        pygame.draw.circle(surf, GREEN, (px, py), 10)
        lbl = fonts["sml"].render(f"✓ {_CAL_CORNERS[i]}", True, GREEN)
        surf.blit(lbl, (px + 14, py - 9))

    # Title
    msg = (f"Touch {cal.name} corner  ({min(cal.idx + 1, 3)}/3)"
           if not cal.done else "Calibration complete!")
    t1  = fonts["big"].render(msg, True, YELLOW)
    surf.blit(t1, (WW // 2 - t1.get_width() // 2, 18))

    # Blob status
    if cal.detected_xyz is not None:
        x, y, z = cal.detected_xyz
        info = fonts["sml"].render(
            f"blob  x={x:+.1f}  y={y:+.1f}  z={z:+.1f} cm  |  hold still…",
            True, CYAN)
        surf.blit(info, (WW // 2 - info.get_width() // 2, 62))
    elif cal.blob_count == 0:
        t = fonts["sml"].render("No blob detected — step into camera view", True, LT_GREY)
        surf.blit(t, (WW // 2 - t.get_width() // 2, 62))
    else:
        t = fonts["sml"].render(
            f"{cal.blob_count} blobs detected — one person only", True, ORANGE)
        surf.blit(t, (WW // 2 - t.get_width() // 2, 62))

    # Dwell bar
    prog = cal.dwell_progress
    bw   = 320
    bx   = WW // 2 - bw // 2
    by   = WH - 44
    pygame.draw.rect(surf, MID_GREY, (bx, by, bw, 18))
    pygame.draw.rect(surf, GREEN,    (bx, by, int(bw * prog), 18))
    pygame.draw.rect(surf, WHITE,    (bx, by, bw, 18), 1)

    # Sub-instruction
    sub = fonts["sml"].render("R=restart  Q=quit", True, LT_GREY)
    surf.blit(sub, (WW // 2 - sub.get_width() // 2, WH - 20))


# ── Main ───────────────────────────────────────────────────────────────────────

def _projector_from_corners(corners: dict) -> ScreenProjector | None:
    """Build a ScreenProjector from a settings corners dict; returns None on failure."""
    if not corners:
        return None
    if not all(corners.get(k) is not None for k in ("bottom_left", "bottom_right", "top_left")):
        return None
    try:
        return ScreenProjector(
            corners["bottom_left"],
            corners["bottom_right"],
            corners["top_left"],
        )
    except Exception as exc:
        print(f"Warning: bad screen_corners: {exc}", file=sys.stderr)
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description="FundingCAPTCHA pygame touch tester")
    ap.add_argument("--server",      default="ws://localhost:8080/ws", metavar="URL",
                    help="WebSocket URL of running server.py")
    ap.add_argument("--cols",        type=int, default=4,   metavar="N")
    ap.add_argument("--rows",        type=int, default=4,   metavar="N")
    ap.add_argument("--aspect",      default="4:3",          metavar="W:H",
                    help="Fallback screen aspect ratio (used when screen_corners absent)")
    ap.add_argument("--dwell",       type=int, default=None, metavar="N",
                    help="Frames to confirm a tap (default: from settings, else 3)")
    ap.add_argument("--cal-dwell",   type=int, default=20,   metavar="N",
                    help="Frames blob must be stable to accept a calibration corner (~2s at 10fps)")
    ap.add_argument("--stable-cm",   type=float, default=15.0, metavar="CM",
                    help="Max blob movement (cm) allowed during corner dwell")
    ap.add_argument("--max-plane-dist", type=float, default=None, metavar="CM",
                    help="Max distance (cm) in front of screen plane to register a touch "
                         "(default: from settings max_plane_dist_cm, else 30)")
    ap.add_argument("--recalibrate", action="store_true",
                    help="Wipe saved corners and redo corner calibration")
    ap.add_argument("--osc-port",   type=int, default=9003, metavar="N",
                    help="OSC port server.py listens on for /captcha/restart (default: 9003)")
    args = ap.parse_args()

    # Parse fallback aspect ratio
    try:
        aw, ah = (int(x) for x in args.aspect.split(":"))
        fallback_aspect = aw / ah
    except Exception:
        print(f"Bad --aspect '{args.aspect}', expected W:H e.g. 4:3", file=sys.stderr)
        sys.exit(1)

    # Load settings (base + local overlay)
    settings: dict = {}
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text())
        except Exception as exc:
            print(f"Warning: {SETTINGS_PATH}: {exc}", file=sys.stderr)
    if SETTINGS_LOCAL_PATH.exists():
        try:
            settings.update(json.loads(SETTINGS_LOCAL_PATH.read_text()))
        except Exception as exc:
            print(f"Warning: {SETTINGS_LOCAL_PATH}: {exc}", file=sys.stderr)

    dwell_frames     = args.dwell if args.dwell is not None else settings.get("blob_dwell_frames", 3)
    max_plane_dist   = args.max_plane_dist if args.max_plane_dist is not None else settings.get("max_plane_dist_cm", 30.0)

    # Determine initial state
    projector: ScreenProjector | None = None
    corner_cal: CornerCal | None = None

    server_host = urlparse(args.server).hostname or "localhost"

    def _send_osc_restart() -> None:
        try:
            from pythonosc.udp_client import SimpleUDPClient
            SimpleUDPClient(server_host, args.osc_port).send_message("/captcha/restart", [])
            print(f"Sent /captcha/restart to {server_host}:{args.osc_port}")
        except Exception as exc:
            print(f"Warning: could not send OSC restart: {exc}", file=sys.stderr)

    if args.recalibrate:
        _send_osc_restart()
        settings.pop("screen_corners", None)
        SETTINGS_LOCAL_PATH.write_text(json.dumps({}, indent=2))

    projector = _projector_from_corners(settings.get("screen_corners"))
    if projector is None:
        state      = State.CORNER_CAL
        corner_cal = CornerCal(args.cal_dwell, args.stable_cm)
    else:
        state = State.LIVE

    aspect = projector.aspect if projector else fallback_aspect

    # Pygame
    pygame.init()
    info   = pygame.display.Info()
    WW, WH = info.current_w, info.current_h
    screen = pygame.display.set_mode((WW, WH), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("Touch Tester")
    pygame.mouse.set_visible(False)
    clock  = pygame.time.Clock()

    fonts = {
        "big": pygame.font.SysFont("monospace", 32, bold=True),
        "med": pygame.font.SysFont("monospace", 24, bold=True),
        "sml": pygame.font.SysFont("monospace", 18),
        "hud": pygame.font.SysFont("monospace", 20, bold=True),
    }

    gx, gy, gw, gh = letterbox(WW, WH, aspect)

    # WebSocket thread
    blob_q:    queue.Queue[list] = queue.Queue(maxsize=8)
    ws_status: list[str]         = ["connecting"]
    cv_status: list[dict]        = [{"state": "unknown"}]
    stop       = threading.Event()
    threading.Thread(
        target=_ws_thread,
        args=(args.server, blob_q, ws_status, cv_status, stop),
        daemon=True,
    ).start()

    dwell          = DwellTracker(dwell_frames)
    current_blobs: list[dict] = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop.set(); pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    stop.set(); pygame.quit(); sys.exit(0)
                elif event.key == pygame.K_r:
                    _send_osc_restart()
                    settings.pop("screen_corners", None)
                    SETTINGS_LOCAL_PATH.write_text(json.dumps({}, indent=2))
                    projector  = None
                    corner_cal = CornerCal(args.cal_dwell, args.stable_cm)
                    state      = State.CORNER_CAL
                    dwell      = DwellTracker(dwell_frames)
                    gx, gy, gw, gh = letterbox(WW, WH, fallback_aspect)

        # Drain to latest blob frame
        try:
            while True:
                current_blobs = blob_q.get_nowait()
        except queue.Empty:
            pass

        screen.fill(BLACK)

        # ── Corner calibration state ──────────────────────────────────────────
        if state == State.CORNER_CAL:
            assert corner_cal is not None
            corner_cal.push_blobs(current_blobs)

            if corner_cal.just_accepted and not corner_cal.done:
                print(f"  ✓ {_CAL_CORNERS[corner_cal.idx - 1]} accepted.")

            if corner_cal.done:
                corners_result = corner_cal.result()
                settings["screen_corners"] = corners_result
                SETTINGS_LOCAL_PATH.write_text(json.dumps({"screen_corners": corners_result}, indent=2))
                print(f"Corners saved to {SETTINGS_LOCAL_PATH}")

                projector = _projector_from_corners(settings["screen_corners"])
                gx, gy, gw, gh = letterbox(WW, WH, projector.aspect if projector else fallback_aspect)
                state      = State.LIVE
                corner_cal = None

            draw_corner_cal(screen, fonts, WW, WH, gx, gy, gw, gh, corner_cal or CornerCal(1))

        # ── Live state ────────────────────────────────────────────────────────
        elif state == State.LIVE:
            live_cells: list[tuple[int, int, int]] = []
            blob_info:  list[dict]                 = []

            for b in current_blobs:
                xyz = [b["x"], b["y"], b["z"]]
                if projector:
                    u, v     = projector.project(xyz)
                    dist     = projector.plane_distance(xyz)
                    in_b     = projector.in_bounds_3d(xyz, max_plane_dist)
                    col, row = projector.uv_to_cell(u, v, args.cols, args.rows) if in_b else (None, None)
                    if in_b:
                        live_cells.append((b["id"], col, row))
                else:
                    u = v = dist = None
                    in_b  = False
                    col = row = None
                blob_info.append({"id": b["id"], "xyz": xyz,
                                   "u": u, "v": v, "dist": dist, "in_bounds": in_b,
                                   "col": col, "row": row})

            dwell.update(live_cells)

            draw_grid(screen, gx, gy, gw, gh, args.cols, args.rows)

            # Cell highlights
            for col, row in dwell.immediate:
                highlight_cell(screen, gx, gy, gw, gh, args.cols, args.rows,
                               col, row, CYAN, 55)
            for col, row in dwell.flashing:
                highlight_cell(screen, gx, gy, gw, gh, args.cols, args.rows,
                               col, row, CYAN, 190)

            # Blob dots + labels
            for bi in blob_info:
                xyz       = bi["xyz"]
                in_b      = bi["in_bounds"]
                dot_color = CYAN if in_b else ORANGE

                if projector and bi["u"] is not None:
                    px, py = uv_to_px(bi["u"], bi["v"], gx, gy, gw, gh)
                    px = max(8, min(WW - 8, px))
                    py = max(8, min(WH - 8, py))
                else:
                    idx    = blob_info.index(bi)
                    px, py = 20, 60 + idx * 90

                draw_blob_dot(screen, px, py, dot_color)

                line1 = f"#{bi['id']}  x={xyz[0]:+.1f} y={xyz[1]:+.1f} z={xyz[2]:+.1f}"
                if bi["u"] is not None:
                    in_str  = "IN" if in_b else "OUT"
                    dist_str = f"d={bi['dist']:+.1f}cm" if bi["dist"] is not None else ""
                    line2  = f"    u={bi['u']:.2f} v={bi['v']:.2f}  {dist_str}  {in_str}"
                    if bi["col"] is not None:
                        line2 += f"  col={bi['col']} row={bi['row']}"
                else:
                    line2 = ""

                lbl1 = fonts["sml"].render(line1, True, WHITE)
                lbl2 = fonts["sml"].render(line2, True, dot_color) if line2 else None
                tx   = min(px + 16, WW - lbl1.get_width() - 4)
                ty   = py - 18
                screen.blit(lbl1, (tx, ty))
                if lbl2:
                    screen.blit(lbl2, (tx, ty + 20))

            # HUD top-right
            hud_lines = [
                f"grid {args.cols}×{args.rows}  dwell {dwell_frames}f",
                f"blobs: {len(current_blobs)}  plane ≤{max_plane_dist:.0f}cm",
                f"corners: {'OK' if projector else 'MISSING'}",
                "R=recalibrate  Q=quit",
            ]
            for i, line in enumerate(hud_lines):
                color = YELLOW if i < 3 else LT_GREY
                lbl   = fonts["hud"].render(line, True, color)
                screen.blit(lbl, (WW - lbl.get_width() - 8, 8 + i * 24))

        # ── Status bar (both states) ──────────────────────────────────────────
        connected = ws_status[0] == "connected"
        cvs       = cv_status[0]
        cv_state  = cvs.get("state", "unknown")

        if not connected:
            bar_color  = RED
            status_str = f"DISCONNECTED — reconnecting…  ({args.server})"
            bar = fonts["hud"].render(status_str, True, bar_color)
            screen.blit(bar, (8, WH - bar.get_height() - 6))
        elif cv_state == "calibrating":
            progress   = cvs.get("progress", 0.0)
            bar_color  = YELLOW
            status_str = f"CAMERA CALIBRATING  {int(progress * 100):3d}%  — do not touch"
            bar = fonts["hud"].render(status_str, True, bar_color)
            by  = WH - bar.get_height() - 6
            screen.blit(bar, (8, by))
            # Progress fill bar to the right of the text
            bx  = 8 + bar.get_width() + 12
            bw  = WW - bx - 8
            if bw > 0:
                pygame.draw.rect(screen, MID_GREY, (bx, by + 2, bw, bar.get_height() - 4))
                pygame.draw.rect(screen, YELLOW,   (bx, by + 2, int(bw * progress), bar.get_height() - 4))
                pygame.draw.rect(screen, LT_GREY,  (bx, by + 2, bw, bar.get_height() - 4), 1)
        elif cv_state == "active":
            bar_color  = GREEN
            status_str = "camera active — ready to touch"
            bar = fonts["hud"].render(status_str, True, bar_color)
            screen.blit(bar, (8, WH - bar.get_height() - 6))
        else:
            # Connected but server hasn't sent a status yet (no camera mode, or pre-first-frame)
            bar_color  = LT_GREY
            status_str = "connected — waiting for camera…"
            bar = fonts["hud"].render(status_str, True, bar_color)
            screen.blit(bar, (8, WH - bar.get_height() - 6))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
