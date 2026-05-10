#!/usr/bin/env python3
"""
FundingCAPTCHA pygame client.

Usage:
  python captcha.py                  # no camera, mouse clicks → grid taps
  python captcha.py --mock-camera    # blobs from server mock-camera WS
  python captcha.py --camera         # blobs from server real-camera WS
  python captcha.py --width 1280 --height 720   # windowed (dev)

The server (server.py) must already be running for WS blob streaming,
photo loading (/api/photos, /api/pairs), and OSC relay (/api/game-event).
"""
from __future__ import annotations

import argparse
import json
import queue
import random
import sys
import threading
import time
from enum import Enum, auto
from pathlib import Path

import pygame
import requests

DIR              = Path(__file__).parent
SETTINGS_PATH    = DIR / "captcha-settings.json"
SETTINGS_LOCAL   = DIR / "captcha-settings.local.json"
DEFAULT_SERVER   = "http://localhost:8080"
FPS              = 60
LOBBY_AUTO_S     = 5.0   # seconds before lobby auto-starts a game
RESULT_LINGER_S  = 2.5   # seconds to show win/lose overlay before advancing

# ── Settings ───────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    s = json.loads(SETTINGS_PATH.read_text()) if SETTINGS_PATH.exists() else {}
    if SETTINGS_LOCAL.exists():
        s.update(json.loads(SETTINGS_LOCAL.read_text()))
    return s

# ── State machine ──────────────────────────────────────────────────────────────

class State(Enum):
    LOBBY   = auto()
    PLAYING = auto()
    WIN     = auto()
    LOSE    = auto()

# ── Shuffle bag ────────────────────────────────────────────────────────────────

class ShuffleBag:
    def __init__(self, items: list) -> None:
        self._items = list(items)
        self._bag: list = []

    def next(self) -> str:
        if not self._bag:
            self._bag = self._items[:]
            random.shuffle(self._bag)
        return self._bag.pop()

# ── WebSocket blob thread ──────────────────────────────────────────────────────

def _start_ws_thread(
    ws_url: str,
    blob_q: "queue.Queue[list]",
    stop: threading.Event,
) -> None:
    from touch_calibration import _ws_thread
    status    = ["connecting"]
    cv_status = [{"state": "unknown"}]
    threading.Thread(
        target=_ws_thread,
        args=(ws_url, blob_q, status, cv_status, stop),
        daemon=True,
    ).start()

# ── OSC relay ──────────────────────────────────────────────────────────────────

def _post_game_event(server: str, **kwargs) -> None:
    try:
        requests.post(f"{server}/api/game-event", json=kwargs, timeout=1)
    except Exception:
        pass

# ── Rendering helpers ──────────────────────────────────────────────────────────

def _draw_lobby(surf: pygame.Surface, W: int, H: int,
                font_xl: pygame.font.Font, font_md: pygame.font.Font) -> None:
    title = font_xl.render("FundingCAPTCHA", True, (200, 170, 255))
    hint  = font_md.render("Touch to play", True, (130, 100, 200))
    surf.blit(title, title.get_rect(centerx=W // 2, centery=H // 2 - 50))
    surf.blit(hint,  hint.get_rect(centerx=W // 2,  centery=H // 2 + 30))

def _draw_overlay(surf: pygame.Surface, W: int, H: int,
                  text: str, font: pygame.font.Font,
                  color: tuple) -> None:
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    surf.blit(overlay, (0, 0))
    label = font.render(text, True, color[:3])
    surf.blit(label, label.get_rect(centerx=W // 2, centery=H // 2))

# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="FundingCAPTCHA pygame client")
    ap.add_argument("--camera",       action="store_true",
                    help="Connect to server real-camera WS")
    ap.add_argument("--mock-camera",  action="store_true",
                    help="Connect to server mock-camera WS")
    ap.add_argument("--server",  default=DEFAULT_SERVER,
                    help="Server base URL (default: http://localhost:8080)")
    ap.add_argument("--width",   type=int, default=0,
                    help="Window width  (0 = fullscreen)")
    ap.add_argument("--height",  type=int, default=0,
                    help="Window height (0 = fullscreen)")
    args = ap.parse_args()

    use_camera = args.camera or args.mock_camera
    ws_url     = args.server.replace("http://", "ws://").replace("https://", "wss://") + "/ws"

    settings   = load_settings()

    # Deferred import so background.py can check moderngl availability first
    from background import BackgroundRenderer, NEEDS_OPENGL

    pygame.init()
    disp_flags = pygame.DOUBLEBUF
    if NEEDS_OPENGL:
        disp_flags |= pygame.OPENGL
    if args.width == 0:
        disp_flags |= pygame.FULLSCREEN
        info = pygame.display.Info()
        W, H = info.current_w, info.current_h
    else:
        W, H = args.width, args.height

    pygame.display.set_mode((W, H), disp_flags)
    pygame.display.set_caption("FundingCAPTCHA")
    pygame.mouse.set_visible(False)

    bg        = BackgroundRenderer(W, H)
    game_surf = pygame.Surface((W, H), pygame.SRCALPHA)

    # Fonts
    font_xl = pygame.font.SysFont("sans", 80, bold=True)
    font_lg = pygame.font.SysFont("sans", 56, bold=True)
    font_md = pygame.font.SysFont("sans", 34)

    # Touch input
    touch = None
    blob_q: "queue.Queue[list]" = queue.Queue(maxsize=5)
    ws_stop = threading.Event()

    if use_camera:
        corners = settings.get("screen_corners")
        if corners:
            from touch_input import TouchInput
            touch = TouchInput(
                cols=4, rows=4,
                screen_corners=corners,
                dwell_frames=settings.get("blob_dwell_frames", 3),
                max_plane_dist_cm=settings.get("max_plane_dist_cm", 30.0),
            )
        else:
            print("WARNING: screen_corners missing from captcha-settings.json — "
                  "camera blobs ignored. Run touch_calibration.py first.", flush=True)
        _start_ws_thread(ws_url, blob_q, ws_stop)

    # Game registry (import here so games/ is on path)
    sys.path.insert(0, str(DIR))
    from games import REGISTRY
    bag   = ShuffleBag(list(REGISTRY.keys()))

    # State
    state:         State         = State.LOBBY
    active_game:   object | None = None
    active_id:     str | None    = None
    state_timer:   float         = 0.0
    pending_tap:   tuple | None  = None

    def on_tap(col: int, row: int) -> None:
        nonlocal pending_tap
        pending_tap = (col, row)

    if touch:
        touch.on_tap = on_tap

    def start_game(game_id: str) -> None:
        nonlocal active_game, active_id, state, state_timer
        cls  = REGISTRY[game_id]
        game = cls(settings, server_url=args.server)
        if touch:
            touch.resize(cls.COLS, cls.ROWS)
        active_game  = game
        active_id    = game_id
        state        = State.PLAYING
        state_timer  = 0.0
        bg.set_game(game_id)
        bg.set_intensity(0.0)
        threading.Thread(
            target=_post_game_event,
            args=(args.server,),
            kwargs={"game": game_id, "event": "start"},
            daemon=True,
        ).start()

    clock = pygame.time.Clock()
    running = True

    while running:
        dt          = clock.tick(FPS) / 1000.0
        pending_tap = None

        # ── Drain blob queue ──────────────────────────────────────────────────
        if use_camera and touch:
            while True:
                try:
                    blobs = blob_q.get_nowait()
                    touch.update(blobs)
                except queue.Empty:
                    break

        # ── Pygame events ─────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and not use_camera:
                mx, my = pygame.mouse.get_pos()
                if state == State.PLAYING and active_game is not None:
                    gr = active_game.grid_rect(W, H)
                    if gr.collidepoint(mx, my):
                        col = int((mx - gr.x) / gr.width  * active_game.COLS)
                        row = int((my - gr.y) / gr.height * active_game.ROWS)
                        pending_tap = (col, row)
                    else:
                        pending_tap = None
                else:
                    pending_tap = (0, 0)   # any click in non-PLAYING states advances

        # ── State machine ─────────────────────────────────────────────────────
        if state == State.LOBBY:
            state_timer += dt
            if pending_tap or state_timer >= LOBBY_AUTO_S:
                start_game(bag.next())

        elif state == State.PLAYING and active_game is not None:
            if pending_tap:
                active_game.on_tap(*pending_tap)
                bg.on_event("tap")
                threading.Thread(
                    target=_post_game_event,
                    args=(args.server,),
                    kwargs={"game": active_id, "event": "tap",
                            **active_game.event_data()},
                    daemon=True,
                ).start()

            result = active_game.update(dt)
            bg.set_intensity(active_game.intensity())

            if result in ("win", "lose"):
                state       = State.WIN if result == "win" else State.LOSE
                state_timer = 0.0
                bg.on_event(result)
                threading.Thread(
                    target=_post_game_event,
                    args=(args.server,),
                    kwargs={"game": active_id, "event": result,
                            **active_game.event_data()},
                    daemon=True,
                ).start()

            # Check internal win flag (all pairs matched inside on_tap)
            elif hasattr(active_game, "_won") and active_game._won:
                state       = State.WIN
                state_timer = 0.0
                bg.on_event("win")
                threading.Thread(
                    target=_post_game_event,
                    args=(args.server,),
                    kwargs={"game": active_id, "event": "win",
                            **active_game.event_data()},
                    daemon=True,
                ).start()

        elif state in (State.WIN, State.LOSE):
            state_timer += dt
            if state_timer >= RESULT_LINGER_S:
                if state == State.WIN and active_game is not None:
                    active_game.next_level()
                    state       = State.PLAYING
                    state_timer = 0.0
                    bg.set_game(active_id)
                else:
                    if active_game is not None:
                        active_game.destroy()
                    start_game(bag.next())

        # ── Render ────────────────────────────────────────────────────────────
        game_surf.fill((0, 0, 0, 0))

        if state == State.LOBBY:
            _draw_lobby(game_surf, W, H, font_xl, font_md)

        elif state == State.PLAYING and active_game is not None:
            active_game.render(game_surf, W, H)
            active_game.render_hud(game_surf, W, H)

        elif state in (State.WIN, State.LOSE) and active_game is not None:
            active_game.render(game_surf, W, H)
            active_game.render_hud(game_surf, W, H)
            if state == State.WIN:
                _draw_overlay(game_surf, W, H, "YOU DID IT!", font_lg, (80, 255, 120, 255))
            else:
                _draw_overlay(game_surf, W, H, "TIME'S UP!", font_lg, (255, 80, 80, 255))

        bg.render(dt, game_surf)
        pygame.display.flip()

    ws_stop.set()
    pygame.quit()


if __name__ == "__main__":
    main()
