"""Shader player — Shadertoy Setups driven by the depth camera (ADR-0021).

Cycles through the Setups listed in shaders/setups.json, each for its
duration_s, feeding the Orbbec silhouette in as Buffer A (the Body).
Shares the camera, calibration, and settings of app.py; replaces its
game loop with an OpenGL one.

  python3 shader_app.py --camera                 # show
  python3 shader_app.py --mock-camera            # drifting fake bodies
  python3 shader_app.py --test-input --windowed  # mouse paints the Body, as in Shadertoy
  python3 shader_app.py --test-input --setup ripples   # pin one Setup

Keys: N / → next Setup · R reload current Setup from disk · Esc quit.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import queue
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("MESA_GL_VERSION_OVERRIDE", "3.3")
os.environ.setdefault("MESA_GLSL_VERSION_OVERRIDE", "330")

import moderngl
import pygame

from app import DIR, _camera_thread, load_settings
from arc import ShuffleBag
from shadertoy import BodyMouse, Renderer, VERT, js_keycode, load_setup, pack_body

try:
    from IIVision import MockCamera, OrbbecCamera
    _CV_AVAILABLE = True
except ImportError:
    _CV_AVAILABLE = False

log = logging.getLogger("shader_app")

SHADER_DIR = DIR / "shaders"

_BLIT_FRAG = """
#version 330
uniform sampler2D src;
uniform vec2 size;
out vec4 c;
void main() { c = vec4(texture(src, gl_FragCoord.xy / size).rgb, 1.0); }   // Shadertoy ignores Image alpha
"""


class _TestMouse:
    """pygame mouse → Shadertoy iMouse (pixels from bottom-left, click in zw)."""

    def __init__(self) -> None:
        self.state = (0.0, 0.0, 0.0, 0.0)
        self._down = False

    def update(self, win: tuple[int, int], res: tuple[int, int]) -> tuple:
        mx, my = pygame.mouse.get_pos()
        x = mx / win[0] * res[0]
        y = (win[1] - my) / win[1] * res[1]
        x0, y0, z, w = self.state
        if pygame.mouse.get_pressed()[0]:
            if not self._down:
                self.state = (x, y, x, y)
            else:
                self.state = (x, y, abs(z), -abs(w))
            self._down = True
        else:
            self.state = (x0, y0, -abs(z), -abs(w))
            self._down = False
        return self.state


class Rotation:
    """Which Setup plays: shuffle-bag order, each for its duration_s.

    A Setup that won't load is skipped; one that fails at render time is
    dropped from the rotation for the rest of the run.
    """

    def __init__(self, renderer: Renderer, names: list[str],
                 shader_dir: Path = SHADER_DIR, clock=time.monotonic) -> None:
        self.renderer = renderer
        self.names    = list(names)
        self._bag     = ShuffleBag(self.names)
        self._dir     = shader_dir
        self._clock   = clock
        self.started  = clock()

    def next(self) -> None:
        if len(self.names) == 1 and self.renderer.setup is not None:
            self.started = self._clock()              # nothing else to play; keep its state
            return
        for _ in range(max(1, len(self.names))):
            n = self._bag.next()
            if n is None:
                break
            if self._load(n):
                return
        log.error("No Setup compiled — keeping the current one")
        self.started = self._clock()

    def reload(self) -> None:
        """Re-read the current Setup from disk; a broken edit keeps the old one."""
        if self.renderer.setup is not None:
            self._load(self.renderer.setup.name)

    def tick(self) -> None:
        s = self.renderer.setup
        if s is not None and self._clock() - self.started >= s.duration_s:
            self.next()

    def failed(self, exc: Exception) -> None:
        name = self.renderer.setup.name if self.renderer.setup else "?"
        log.error("Setup %s failed while rendering, dropped: %s", name, exc)
        self.renderer.unload()
        if name in self.names:
            self.names.remove(name)
            self._bag = ShuffleBag(self.names)
        self.next()

    def _load(self, name: str) -> bool:
        try:
            self.renderer.load(load_setup(self._dir / name))
        except Exception as exc:                      # team-authored content: never fatal
            log.error("Setup %s skipped: %s", name, exc)
            return False
        self.started = self._clock()
        return True


def _setup_names() -> list[str]:
    try:
        return json.loads((SHADER_DIR / "setups.json").read_text())
    except Exception as exc:
        log.error("shaders/setups.json unreadable: %s", exc)
        return []


def main() -> None:
    ap = argparse.ArgumentParser(description="Shadertoy Setups driven by the depth camera")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--camera",      action="store_true")
    mode.add_argument("--mock-camera", action="store_true")
    mode.add_argument("--test-input",  action="store_true",
                      help="Mouse paints the Body with shaders/body_painter.glsl, as in Shadertoy")
    ap.add_argument("--setup", metavar="NAME", help="Pin one Setup (no cycling)")
    ap.add_argument("--windowed", action="store_true", help="1280×720 window instead of fullscreen")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    settings  = load_settings()
    cfg       = settings.get("shader_app", {})
    cam_cfg   = settings.get("camera", {})
    slabs     = settings.get("depth_slabs", [{"near_mm": 800, "far_mm": 2500}])
    roi       = settings.get("camera_roi",
                             {"x": 0, "y": 0, "w": cam_cfg.get("width", 640),
                                               "h": cam_cfg.get("height", 400)})
    fps       = int(cfg.get("fps", 30))
    scale     = float(cfg.get("render_scale", 0.5))

    if (args.camera or args.mock_camera) and not _CV_AVAILABLE:
        sys.exit("ERROR: CV libraries not available — pip install -r requirements.txt")

    # ── Display ───────────────────────────────────────────────────────────────
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    if args.windowed:
        win = (1280, 720)
        pygame.display.set_mode(win, pygame.OPENGL | pygame.DOUBLEBUF)
    else:
        info = pygame.display.Info()
        win  = (info.current_w, info.current_h)
        pygame.display.set_mode(win, pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)
    pygame.display.set_caption("Shader player")
    pygame.mouse.set_visible(args.test_input)

    ctx  = moderngl.create_context()        # also attaches to SDL's EGL context (kmsdrm)
    res  = (max(1, int(win[0] * scale)), max(1, int(win[1] * scale)))
    log.info("OpenGL %s · window %dx%d · render %dx%d", ctx.version_code, *win, *res)

    renderer = Renderer(ctx, res, body_mode="painter" if args.test_input else "camera")
    blit     = ctx.program(vertex_shader=VERT, fragment_shader=_BLIT_FRAG)
    blit_vao = ctx.vertex_array(blit, [(renderer.vbo, "2f", "in_vert")])
    blit["size"].value = (float(win[0]), float(win[1]))
    renderer.output_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)

    # ── Setups ────────────────────────────────────────────────────────────────
    rotation = Rotation(renderer, [args.setup] if args.setup else _setup_names())
    rotation.next()

    # ── Camera ────────────────────────────────────────────────────────────────
    cam_q   = queue.Queue(maxsize=32)
    stop    = threading.Event()
    collect = threading.Event()
    if args.camera or args.mock_camera:
        cam_args = dict(width=cam_cfg.get("width", 640), height=cam_cfg.get("height", 400),
                        fps=cam_cfg.get("fps", 10))
        camera = (MockCamera(**cam_args) if args.mock_camera
                  else OrbbecCamera(serial=cam_cfg.get("serial") or None, **cam_args))
        threading.Thread(target=_camera_thread,
                         args=(camera, settings, cam_q, stop, collect), daemon=True).start()
        # Hold off background collection so people can clear the ROI (ADR-0013).
        standback = float(settings.get("calibration_standback_s", 5.0))
        timer = threading.Timer(standback, collect.set)
        timer.daemon = True
        timer.start()
        log.info("Camera started (%s) — calibrating in %.0fs, keep the floor clear",
                 "mock" if args.mock_camera else "Orbbec", standback)

    body_mouse = BodyMouse(int(settings.get("min_foreground_pixels", 1)))
    test_mouse = _TestMouse()
    mouse      = (0.0, 0.0, 0.0, 0.0)

    # ── Loop ──────────────────────────────────────────────────────────────────
    clock     = pygame.time.Clock()
    fps_t, fps_n = time.monotonic(), 0
    running   = True
    while running:
        # Clamp spikes (Setup compile, stalls) without slowing a Setup that is
        # merely slow: anything under 4 fps is a stall, not a frame.
        dt = min(clock.tick(fps) / 1000.0, 0.25)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_n, pygame.K_RIGHT):
                    rotation.next()
                elif ev.key == pygame.K_r:
                    rotation.reload()
                code = js_keycode(ev.key)
                if code is not None:
                    renderer.keyboard.key_down(code)
            elif ev.type == pygame.KEYUP:
                code = js_keycode(ev.key)
                if code is not None:
                    renderer.keyboard.key_up(code)

        rotation.tick()

        # Drain to the newest foreground frame.
        fg = None
        while True:
            try:
                msg = cam_q.get_nowait()
            except queue.Empty:
                break
            if msg["type"] == "foreground":
                fg = msg["frame"]
            elif msg["type"] == "cal_done":
                log.info("Calibration done — Body live")
            elif msg["type"] == "error":
                log.error("Camera: %s", msg["msg"])
        if fg is not None:
            body = pack_body(fg, roi, slabs)
            renderer.upload_body(body)
            mouse = body_mouse.update(body, *res)
        if args.test_input:
            mouse = test_mouse.update(win, res)

        try:
            renderer.render(dt, mouse)
        except Exception as exc:
            rotation.failed(exc)
        mouse = (*mouse[:3], -abs(mouse[3]))          # click flag lasts one frame
        ctx.screen.use()
        ctx.viewport = (0, 0, *win)
        renderer.output_tex.use(location=0)
        blit["src"].value = 0
        blit_vao.render(moderngl.TRIANGLE_STRIP)
        pygame.display.flip()

        fps_n += 1
        if time.monotonic() - fps_t >= 10.0:
            log.info("%.1f fps · %s", fps_n / (time.monotonic() - fps_t),
                     renderer.setup.name if renderer.setup else "-")
            fps_t, fps_n = time.monotonic(), 0

    stop.set()
    blit_vao.release()
    blit.release()
    renderer.release()
    pygame.quit()


if __name__ == "__main__":
    main()
