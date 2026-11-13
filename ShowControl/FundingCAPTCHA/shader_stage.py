"""Shader stage — the shared kit for playing Shadertoy Setups on the kiosk screen (ADR-0021).

A library, not an entry point (playlist_app.py is the program). ShaderStage
takes the Orbbec silhouette in as Buffer A (the Body), renders the current
Setup and upscales it to the window; SetupImages feeds the "image" source
(ADR-0024); open_display, pick_display, display_index and add_mode_args are
the display and camera-mode helpers. Uses the camera feed (camera_feed.py,
with the self-learning background of ADR-0023) and settings (settings.py) as
app.py does, with an OpenGL loop where app.py has its game loop.

While the current Setup reads the "blobs" source (ADR-0022), blobs are tracked
in the Body at camera rate — in --test-input, in the painted Body read back
from the GPU — and their records uploaded every render frame.
"""
from __future__ import annotations

import argparse
import logging
import os
import time

os.environ.setdefault("MESA_GL_VERSION_OVERRIDE", "3.3")
os.environ.setdefault("MESA_GLSL_VERSION_OVERRIDE", "330")

import moderngl
import numpy as np
import pygame

from arc import ShuffleBag
from body_blobs import BlobConfig, BodyBlobs
from shadertoy import (BodyMouse, Renderer, ShaderError, VERT, decode_image, js_keycode,
                       pack_body)
from settings import DIR, with_defaults

log = logging.getLogger("shader_stage")

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

    Used by playlist_app.Playlist. Images keep enough pixels to
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


def pick_display(sizes: list[tuple[int, int]], index: int) -> tuple[int, tuple[int, int]]:
    """(display index, its desktop size). An index with no display falls back to the first."""
    if not 0 <= index < len(sizes):
        log.warning("No display %d (%d connected) — using display 0", index, len(sizes))
        index = 0
    return index, tuple(sizes[index])


# ── Display and camera-mode helpers ───────────────────────────────────────────

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
    return int(settings["shader_app"]["display"])


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


class ShaderStage:
    """Body in, current Setup rendered, upscaled to the screen."""

    def __init__(self, ctx, win: tuple[int, int], settings: dict, test_input: bool) -> None:
        settings = with_defaults(settings)
        cfg   = settings["shader_app"]
        scale = float(cfg["render_scale"])
        self.ctx, self.win = ctx, win
        self.max_texture_side = int(ctx.info["GL_MAX_TEXTURE_SIZE"])
        self.res   = (max(1, int(win[0] * scale)), max(1, int(win[1] * scale)))
        self.slabs = settings["depth_slabs"]
        self.roi   = settings["camera_roi"]
        self.test_input = test_input
        log.info("OpenGL %s · window %dx%d · render %dx%d", ctx.version_code, *win, *self.res)

        self.renderer = Renderer(ctx, self.res, body_mode="painter" if test_input else "camera")
        self._blit     = ctx.program(vertex_shader=VERT, fragment_shader=_BLIT_FRAG)
        self._blit_vao = ctx.vertex_array(self._blit, [(self.renderer.vbo, "2f", "in_vert")])
        self._blit["size"].value = (float(win[0]), float(win[1]))
        self.renderer.output_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # A load (or R reload) restarts the Setup's buffers, so the tracker restarts
        # with them: Setups that remember people by id must not meet ids from before.
        self.blobs       = BodyBlobs(BlobConfig.from_dict(cfg["blobs"]))
        self._body_mouse = BodyMouse(int(settings["min_foreground_pixels"]))
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
