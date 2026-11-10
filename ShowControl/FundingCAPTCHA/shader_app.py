"""Shader player — Shadertoy Setups driven by the depth camera (ADR-0021).

Cycles through the Setups listed in shaders/setups.json, each for its
duration_s, feeding the Orbbec silhouette in as Buffer A (the Body).
Shares the camera, self-learning background (ADR-0023), and settings of
app.py; replaces its game loop with an OpenGL one. Bodies show from launch:
there is no standback or calibration wait.

  python3 shader_app.py --camera                 # show
  python3 shader_app.py --mock-camera            # drifting fake bodies
  python3 shader_app.py --test-input --windowed  # mouse paints the Body, as in Shadertoy
  python3 shader_app.py --test-input --setup ripples   # pin one Setup

Keys: N / → next Setup · R reload current Setup from disk · Esc quit.

While the current Setup reads the "blobs" source (ADR-0022), blobs are tracked
in the Body at camera rate — in --test-input, in the painted Body read back
from the GPU — and their records uploaded every render frame.
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
import numpy as np
import pygame

from app import DIR, _camera_thread, load_settings
from arc import ShuffleBag
from body_blobs import BlobConfig, BodyBlobs
from shadertoy import (BodyMouse, Renderer, ShaderError, VERT, decode_image, js_keycode,
                       load_setup, pack_body)

try:
    from IIVision import MockCamera, OrbbecCamera
    _CV_AVAILABLE = True
except ImportError:
    _CV_AVAILABLE = False

log = logging.getLogger("shader_app")

SHADER_DIR = DIR / "shaders"
PAINTER_TRACK_S = 0.1      # --test-input: read the painted Body back at camera rate

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


class SetupImages:
    """The "image" source's pictures (ADR-0024): a shuffle bag per Setup, one image per load.

    Shared by Rotation and playlist_app.Playlist. Images keep enough pixels to
    cover `cover` (the window), with no side beyond `max_side` (the GPU's limit).
    """

    def __init__(self, cover: tuple[int, int] = (4096, 4096), max_side: int = 16384) -> None:
        self._cover    = cover
        self._max_side = max_side
        self._bags: dict[str, tuple] = {}             # name → (files, ShuffleBag, undecodable)

    def next(self, setup) -> np.ndarray | None:
        """Decode the next image from this Setup's bag; None if none decode."""
        files, bag, bad = self._bags.get(setup.name, (None, None, set()))
        if files != setup.images:                     # first load, or images/ changed (R)
            files, bag = list(setup.images), ShuffleBag([p for p in setup.images if p not in bad])
        for _ in range(len(files)):
            path = bag.next()
            if path is None:
                break
            try:
                image = decode_image(path, self._cover, self._max_side)
            except ShaderError as exc:
                log.error("%s: image dropped: %s", setup.name, exc)
                bad.add(path)
                bag = ShuffleBag([p for p in files if p not in bad])
                continue
            self._bags[setup.name] = (files, bag, bad)
            return image
        self._bags[setup.name] = (files, bag, bad)
        return None


class Rotation:
    """Which Setup plays: shuffle-bag order, each for its duration_s.

    A Setup that won't load is skipped; one that fails at render time is
    dropped from the rotation for the rest of the run.
    """

    def __init__(self, renderer: Renderer, names: list[str],
                 shader_dir: Path = SHADER_DIR, clock=time.monotonic, on_load=None,
                 image_max: tuple[int, int] = (4096, 4096), image_max_side: int = 16384) -> None:
        self.renderer = renderer
        self._images  = SetupImages(image_max, image_max_side)
        self._on_load = on_load                       # called after every successful load
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
            setup = load_setup(self._dir / name)
            image = self._images.next(setup) if setup.uses_image else None
            self.renderer.load(setup, image=image)
        except Exception as exc:                      # team-authored content: never fatal
            log.error("Setup %s skipped: %s", name, exc)
            return False
        self.started = self._clock()
        if self._on_load is not None:
            self._on_load()
        return True


def pick_display(sizes: list[tuple[int, int]], index: int) -> tuple[int, tuple[int, int]]:
    """(display index, its desktop size). An index with no display falls back to the first."""
    if not 0 <= index < len(sizes):
        log.warning("No display %d (%d connected) — using display 0", index, len(sizes))
        index = 0
    return index, tuple(sizes[index])


def _setup_names() -> list[str]:
    try:
        return json.loads((SHADER_DIR / "setups.json").read_text())
    except Exception as exc:
        log.error("shaders/setups.json unreadable: %s", exc)
        return []


# ── Pieces shared with playlist_app.py ────────────────────────────────────────

def add_mode_args(ap: argparse.ArgumentParser) -> None:
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--camera",      action="store_true")
    mode.add_argument("--mock-camera", action="store_true")
    mode.add_argument("--test-input",  action="store_true",
                      help="Mouse paints the Body with shaders/body_painter.glsl, as in Shadertoy")
    ap.add_argument("--windowed", action="store_true", help="1280×720 window instead of fullscreen")
    ap.add_argument("--display", type=int, metavar="N",
                    help="Display to go fullscreen on (0 = first); overrides shader_app.display")


def display_index(args, settings: dict) -> int:
    """--display N, else shader_app.display, else the first display."""
    if args.display is not None:
        return args.display
    return int(settings.get("shader_app", {}).get("display", 0))


def open_display(windowed: bool, caption: str, mouse_visible: bool, display: int = 0):
    """pygame window with a GL 3.3 core context → (moderngl ctx, window size).

    Fullscreen goes on `display` (0 = first); a missing one falls back to the first.
    """
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    if windowed:
        win = (1280, 720)
        pygame.display.set_mode(win, pygame.OPENGL | pygame.DOUBLEBUF)
    else:
        sizes = pygame.display.get_desktop_sizes()
        display, win = pick_display(sizes, display)
        pygame.display.set_mode(win, pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN,
                                display=display)
        log.info("Fullscreen on display %d of %d", display, len(sizes))
    pygame.display.set_caption(caption)
    pygame.mouse.set_visible(mouse_visible)
    ctx = moderngl.create_context()        # also attaches to SDL's EGL context (kmsdrm)
    return ctx, win


def start_camera(args, settings: dict) -> tuple[queue.Queue, threading.Event]:
    """Start the camera thread for --camera / --mock-camera (else an idle queue).

    The thread blocks once the queue is full: drain it every frame.
    """
    cam_q = queue.Queue(maxsize=32)
    stop  = threading.Event()
    if not (args.camera or args.mock_camera):
        return cam_q, stop
    if not _CV_AVAILABLE:
        sys.exit("ERROR: CV libraries not available — pip install -r requirements.txt")
    cam_cfg  = settings.get("camera", {})
    cam_args = dict(width=cam_cfg.get("width", 640), height=cam_cfg.get("height", 400),
                    fps=cam_cfg.get("fps", 10))
    camera = (MockCamera(**cam_args) if args.mock_camera
              else OrbbecCamera(serial=cam_cfg.get("serial") or None, **cam_args))
    threading.Thread(target=_camera_thread,
                     args=(camera, settings, cam_q, stop), daemon=True).start()
    log.info("Camera started (%s) — background learns from the first frame",
             "mock" if args.mock_camera else "Orbbec")
    return cam_q, stop


def drain_camera(cam_q: queue.Queue):
    """Empty the camera queue; return the newest foreground frame, or None."""
    fg = None
    while True:
        try:
            msg = cam_q.get_nowait()
        except queue.Empty:
            return fg
        if msg["type"] == "foreground":
            fg = msg["frame"]
        elif msg["type"] == "error":
            log.error("Camera: %s", msg["msg"])


class ShaderStage:
    """Body in, current Setup rendered, upscaled to the screen."""

    def __init__(self, ctx, win: tuple[int, int], settings: dict, test_input: bool) -> None:
        cfg   = settings.get("shader_app", {})
        cam_cfg = settings.get("camera", {})
        scale = float(cfg.get("render_scale", 0.5))
        self.ctx, self.win = ctx, win
        self.max_texture_side = int(ctx.info["GL_MAX_TEXTURE_SIZE"])
        self.res   = (max(1, int(win[0] * scale)), max(1, int(win[1] * scale)))
        self.slabs = settings.get("depth_slabs", [{"near_mm": 800, "far_mm": 2500}])
        self.roi   = settings.get("camera_roi",
                                  {"x": 0, "y": 0, "w": cam_cfg.get("width", 640),
                                                    "h": cam_cfg.get("height", 400)})
        self.test_input = test_input
        log.info("OpenGL %s · window %dx%d · render %dx%d", ctx.version_code, *win, *self.res)

        self.renderer = Renderer(ctx, self.res, body_mode="painter" if test_input else "camera")
        self._blit     = ctx.program(vertex_shader=VERT, fragment_shader=_BLIT_FRAG)
        self._blit_vao = ctx.vertex_array(self._blit, [(self.renderer.vbo, "2f", "in_vert")])
        self._blit["size"].value = (float(win[0]), float(win[1]))
        self.renderer.output_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # A load (or R reload) restarts the Setup's buffers, so the tracker restarts
        # with them: Setups that remember people by id must not meet ids from before.
        self.blobs       = BodyBlobs(BlobConfig.from_dict(cfg.get("blobs", {})))
        self._body_mouse = BodyMouse(int(settings.get("min_foreground_pixels", 1)))
        self._test_mouse = _TestMouse()
        self._painter_read_t = 0.0
        self._mouse = (0.0, 0.0, 0.0, 0.0)

    def handle_key(self, ev) -> None:
        """Forward a KEYDOWN / KEYUP to the Setup's keyboard texture."""
        code = js_keycode(ev.key)
        if code is None:
            return
        if ev.type == pygame.KEYDOWN:
            self.renderer.keyboard.key_down(code)
        else:
            self.renderer.keyboard.key_up(code)

    def frame(self, dt: float, fg) -> Exception | None:
        """Feed the newest foreground (or None), render, blit. Returns a render failure."""
        uses_blobs = self.renderer.setup is not None and self.renderer.setup.uses_blobs
        if fg is not None:
            body = pack_body(fg, self.roi, self.slabs)
            self.renderer.upload_body(body)
            self._mouse = self._body_mouse.update(body, *self.res)
            if uses_blobs:
                self.blobs.update(body[..., 0] > 0, body[..., 1] / 255.0)
        if self.test_input:
            self._mouse = self._test_mouse.update(self.win, self.res)
            if uses_blobs and time.monotonic() - self._painter_read_t >= PAINTER_TRACK_S:
                self._painter_read_t = time.monotonic()
                painted = self.renderer.read_body()
                self.blobs.update(painted[..., 0] > 0.5, painted[..., 1])
        if uses_blobs:
            self.renderer.upload_blobs(self.blobs.records())

        failure = None
        try:
            self.renderer.render(dt, self._mouse)
        except Exception as exc:
            failure = exc
        self._mouse = (*self._mouse[:3], -abs(self._mouse[3]))   # click flag lasts one frame
        self.ctx.screen.use()
        self.ctx.viewport = (0, 0, *self.win)
        self.renderer.output_tex.use(location=0)
        self._blit["src"].value = 0
        self._blit_vao.render(moderngl.TRIANGLE_STRIP)
        return failure

    def release(self) -> None:
        self._blit_vao.release()
        self._blit.release()
        self.renderer.release()


def main() -> None:
    ap = argparse.ArgumentParser(description="Shadertoy Setups driven by the depth camera")
    add_mode_args(ap)
    ap.add_argument("--setup", metavar="NAME", help="Pin one Setup (no cycling)")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    settings = load_settings()
    fps      = int(settings.get("shader_app", {}).get("fps", 30))
    if (args.camera or args.mock_camera) and not _CV_AVAILABLE:
        sys.exit("ERROR: CV libraries not available — pip install -r requirements.txt")

    ctx, win = open_display(args.windowed, "Shader player", args.test_input,
                            display_index(args, settings))
    stage    = ShaderStage(ctx, win, settings, args.test_input)
    rotation = Rotation(stage.renderer, [args.setup] if args.setup else _setup_names(),
                        on_load=stage.blobs.reset,
                        image_max=win, image_max_side=stage.max_texture_side)
    rotation.next()
    cam_q, stop = start_camera(args, settings)

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
                stage.handle_key(ev)
            elif ev.type == pygame.KEYUP:
                stage.handle_key(ev)

        rotation.tick()
        failure = stage.frame(dt, drain_camera(cam_q))
        if failure is not None:
            rotation.failed(failure)
        pygame.display.flip()

        fps_n += 1
        if time.monotonic() - fps_t >= 10.0:
            log.info("%.1f fps · %s", fps_n / (time.monotonic() - fps_t),
                     stage.renderer.setup.name if stage.renderer.setup else "-")
            fps_t, fps_n = time.monotonic(), 0

    stop.set()
    stage.release()
    pygame.quit()


if __name__ == "__main__":
    main()
