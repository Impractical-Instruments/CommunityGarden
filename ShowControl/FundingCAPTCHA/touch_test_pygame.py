#!/usr/bin/env python3
"""
FundingCAPTCHA pygame touch tester.

Connects to a running server.py via WebSocket and overlays a calibration grid
on the projected screen area.

Usage:
  python touch_test_pygame.py
  python touch_test_pygame.py --server ws://192.168.1.5:8080/ws
  python touch_test_pygame.py --cols 4 --rows 3
  python touch_test_pygame.py --aspect 4:3 --dwell 3

Without screen_corners in captcha-settings.json, the tool still shows blob
world-space positions so you can determine corner coordinates by touch.

Once you have the three corner coordinates, add to captcha-settings.json:
  "screen_corners": {
    "bottom_left":  [x, y, z],
    "bottom_right": [x, y, z],
    "top_left":     [x, y, z]
  }
  Units: cm. World space: X=right, Y=forward, Z=up.
  The fourth corner (top_right) is derived.

Press Q or Escape to quit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import queue
import sys
import threading
from pathlib import Path

import numpy as np
import pygame
import websockets

DIR           = Path(__file__).parent
SETTINGS_PATH = DIR / "captcha-settings.json"

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
    status: list[str],   # status[0] mutated in-place
    stop: threading.Event,
) -> None:
    async def _run() -> None:
        while not stop.is_set():
            try:
                status[0] = "connecting"
                async with websockets.connect(url, ping_interval=10, open_timeout=5) as ws:
                    status[0] = "connected"
                    async for raw in ws:
                        if stop.is_set():
                            return
                        try:
                            msg = json.loads(raw)
                        except Exception:
                            continue
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


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="FundingCAPTCHA pygame touch tester")
    ap.add_argument("--server", default="ws://localhost:8080/ws", metavar="URL",
                    help="WebSocket URL of running server.py")
    ap.add_argument("--cols",   type=int, default=5,   metavar="N")
    ap.add_argument("--rows",   type=int, default=4,   metavar="N")
    ap.add_argument("--aspect", default="4:3",          metavar="W:H",
                    help="Fallback screen aspect ratio (used when screen_corners absent)")
    ap.add_argument("--dwell",  type=int, default=None, metavar="N",
                    help="Frames to confirm a tap (default: from settings, else 3)")
    args = ap.parse_args()

    # Parse fallback aspect ratio
    try:
        aw, ah = (int(x) for x in args.aspect.split(":"))
        fallback_aspect = aw / ah
    except Exception:
        print(f"Bad --aspect '{args.aspect}', expected W:H e.g. 4:3", file=sys.stderr)
        sys.exit(1)

    # Load settings
    settings: dict = {}
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text())
        except Exception as exc:
            print(f"Warning: {SETTINGS_PATH}: {exc}", file=sys.stderr)

    # Screen projector (optional until corners are configured)
    projector: ScreenProjector | None = None
    corners = settings.get("screen_corners")
    # Treat null placeholder values as absent
    if corners and all(corners.get(k) is not None for k in ("bottom_left", "bottom_right", "top_left")):
        try:
            projector = ScreenProjector(
                corners["bottom_left"],
                corners["bottom_right"],
                corners["top_left"],
            )
        except Exception as exc:
            print(f"Warning: bad screen_corners: {exc}", file=sys.stderr)

    aspect = projector.aspect if projector else fallback_aspect

    dwell_frames = args.dwell if args.dwell is not None else settings.get("blob_dwell_frames", 3)

    # Pygame
    pygame.init()
    info  = pygame.display.Info()
    WW, WH = info.current_w, info.current_h
    screen = pygame.display.set_mode((WW, WH), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("Touch Tester")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    font_hud = pygame.font.SysFont("monospace", 20, bold=True)
    font_lbl = pygame.font.SysFont("monospace", 18)
    font_big = pygame.font.SysFont("monospace", 32, bold=True)

    gx, gy, gw, gh = letterbox(WW, WH, aspect)

    # WebSocket thread
    blob_q:    queue.Queue[list] = queue.Queue(maxsize=8)
    ws_status: list[str]         = ["connecting"]
    stop       = threading.Event()
    threading.Thread(
        target=_ws_thread,
        args=(args.server, blob_q, ws_status, stop),
        daemon=True,
    ).start()

    dwell         = DwellTracker(dwell_frames)
    current_blobs: list[dict] = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop.set(); pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                stop.set(); pygame.quit(); sys.exit(0)

        # Drain to latest blob frame
        try:
            while True:
                current_blobs = blob_q.get_nowait()
        except queue.Empty:
            pass

        # ── Project blobs ────────────────────────────────────────────────────
        live_cells: list[tuple[int, int, int]] = []
        blob_info:  list[dict]                 = []

        for b in current_blobs:
            xyz = [b["x"], b["y"], b["z"]]
            if projector:
                u, v   = projector.project(xyz)
                in_b   = projector.in_bounds(u, v)
                col, row = projector.uv_to_cell(u, v, args.cols, args.rows) if in_b else (None, None)
                if in_b:
                    live_cells.append((b["id"], col, row))
            else:
                u = v = None
                in_b  = False
                col = row = None
            blob_info.append({"id": b["id"], "xyz": xyz,
                               "u": u, "v": v, "in_bounds": in_b,
                               "col": col, "row": row})

        dwell.update(live_cells)

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BLACK)
        draw_grid(screen, gx, gy, gw, gh, args.cols, args.rows)

        if not projector:
            # Prompt: tell user what's missing
            m1 = font_big.render("screen_corners not configured", True, YELLOW)
            m2 = font_lbl.render("Touch screen corners and read world coords below,", True, LT_GREY)
            m3 = font_lbl.render(f"then set screen_corners in {SETTINGS_PATH.name}", True, LT_GREY)
            cx = gx + gw // 2
            cy = gy + gh // 2
            screen.blit(m1, (cx - m1.get_width() // 2, cy - 50))
            screen.blit(m2, (cx - m2.get_width() // 2, cy + 10))
            screen.blit(m3, (cx - m3.get_width() // 2, cy + 38))

        # Cell highlights
        for col, row in dwell.immediate:
            highlight_cell(screen, gx, gy, gw, gh, args.cols, args.rows,
                           col, row, CYAN, 55)
        for col, row in dwell.flashing:
            highlight_cell(screen, gx, gy, gw, gh, args.cols, args.rows,
                           col, row, CYAN, 190)

        # Blob dots + labels
        for bi in blob_info:
            xyz    = bi["xyz"]
            in_b   = bi["in_bounds"]
            dot_color = CYAN if in_b else ORANGE

            if projector and bi["u"] is not None:
                px, py = uv_to_px(bi["u"], bi["v"], gx, gy, gw, gh)
                px = max(8, min(WW - 8, px))
                py = max(8, min(WH - 8, py))
            else:
                # No projector: stack dots in top-left margin
                idx    = blob_info.index(bi)
                px, py = 20, 60 + idx * 90

            draw_blob_dot(screen, px, py, dot_color)

            line1 = f"#{bi['id']}  x={xyz[0]:+.1f} y={xyz[1]:+.1f} z={xyz[2]:+.1f}"
            if bi["u"] is not None:
                state = "IN" if in_b else "OUT"
                line2 = f"    u={bi['u']:.2f} v={bi['v']:.2f}  {state}"
                if bi["col"] is not None:
                    line2 += f"  col={bi['col']} row={bi['row']}"
            else:
                line2 = ""

            lbl1 = font_lbl.render(line1, True, WHITE)
            lbl2 = font_lbl.render(line2, True, dot_color) if line2 else None

            tx = min(px + 16, WW - lbl1.get_width() - 4)
            ty = py - 18
            screen.blit(lbl1, (tx, ty))
            if lbl2:
                screen.blit(lbl2, (tx, ty + 20))

        # ── Status bar ────────────────────────────────────────────────────────
        connected  = ws_status[0] == "connected"
        bar_color  = GREEN if connected else RED
        status_str = ws_status[0] if connected else f"DISCONNECTED — reconnecting…  ({args.server})"
        bar        = font_hud.render(status_str, True, bar_color)
        screen.blit(bar, (8, WH - bar.get_height() - 6))

        # ── HUD (top-right) ───────────────────────────────────────────────────
        hud_lines = [
            f"grid {args.cols}×{args.rows}  dwell {dwell_frames}f",
            f"blobs: {len(current_blobs)}",
            f"corners: {'OK' if projector else 'MISSING'}",
        ]
        for i, line in enumerate(hud_lines):
            lbl = font_hud.render(line, True, YELLOW)
            screen.blit(lbl, (WW - lbl.get_width() - 8, 8 + i * 24))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
