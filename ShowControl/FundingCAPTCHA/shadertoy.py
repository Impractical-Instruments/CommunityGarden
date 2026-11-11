"""Shadertoy-compatible multipass GLSL renderer for the shader player (ADR-0021).

A Setup is a folder of Shadertoy tabs pasted verbatim:

  shaders/<name>/
    setup.json      {"duration_s": 120, "channels": {"image": ["A", "B"], ...}}
    common.glsl     optional — Shadertoy's Common tab, prepended to every pass
    buffer_b.glsl   optional — Buffer B..D tabs
    buffer_c.glsl
    buffer_d.glsl
    image.glsl      required — the Image tab

Buffer A is reserved for the Body: on the Pi it is the Orbbec silhouette,
in Shadertoy (and in --test-input) it is shaders/body_painter.glsl driven
by the mouse. Body texel: .r presence 0/1, .g nearness 0 (far) – 1 (near).

Source "blobs" is the tracker's blob records (ADR-0022): BLOB_SLOTS columns ×
BLOB_ROWS rows of RGBA32F, read with texelFetch(ch, ivec2(slot, row), 0):
  row 0  x0, y0, x1, y1         bounding box, Body UV (y up)
  row 1  cx, cy, vx, vy         centroid (UV) and velocity (UV/s)
  row 2  id, state, age_s, near stable id 1–999, BLOB_* state, seconds in
                                that state, mean Body nearness
A slot keeps its track for the track's whole life. In Shadertoy the source is
shaders/blob_painter.glsl in a spare buffer.

Source "image" is one image from <setup>/images/, chosen per load by
shader_app.SetupImages (ADR-0024); unbound (reads 0, resolution 0) without one.

Channel sources: "A" "B" "C" "D" "keyboard" "blobs" "image" or null. Buffers are linear-
filtered and clamped like Shadertoy's, but RGBA16F where Shadertoy's are
32-bit: the Pi's V3D can't linear-filter 32-bit float. Values above ~2048
lose integer precision.

Pure helpers (load_setup, wrap_source, pack_body, BodyMouse, Keyboard) need
no GL; Renderer needs a moderngl context.
"""
from __future__ import annotations

import json
import logging
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

log = logging.getLogger("shader_app")

BUFFERS  = ("buffer_b", "buffer_c", "buffer_d")      # render order, before image
SOURCES  = {"A", "B", "C", "D", "keyboard", "blobs", "image"}
IMAGE_EXTS = (".png", ".jpg", ".jpeg")                # <setup>/images/ files, any case
_BUF_KEY = {"buffer_b": "B", "buffer_c": "C", "buffer_d": "D"}

PAINTER_PATH = Path(__file__).parent / "shaders" / "body_painter.glsl"
BLOB_PAINTER_PATH = Path(__file__).parent / "shaders" / "blob_painter.glsl"

# Blob records contract (ADR-0022). Changing any of these breaks Setups.
BLOB_SLOTS = 8
BLOB_ROWS  = 3
BLOB_EMPTY, BLOB_TENTATIVE, BLOB_CONFIRMED, BLOB_COASTING, BLOB_LOST = range(5)
PAINTER_CHANNELS = ["A", "keyboard", None, None]

VERT = """
#version 330
in vec2 in_vert;
void main() { gl_Position = vec4(in_vert, 0.0, 1.0); }
"""

_HEADER = """#version 330
#extension GL_ARB_shading_language_packing : enable
#define HW_PERFORMANCE 0
uniform vec3  iResolution;
uniform float iTime;
uniform float iTimeDelta;
uniform float iFrameRate;
uniform int   iFrame;
uniform vec4  iMouse;
uniform vec4  iDate;
uniform float iSampleRate;
uniform vec3  iChannelResolution[4];
uniform float iChannelTime[4];
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
uniform sampler2D iChannel3;
out vec4 _fragColor;
"""

# Source-string numbers in compile errors: 0 = the pass file, 1 = common.glsl.
_FOOTER = """
void main() { vec4 c = vec4(0.0); mainImage(c, gl_FragCoord.xy); _fragColor = c; }
"""


class ShaderError(Exception):
    pass


# ── Setup loading ─────────────────────────────────────────────────────────────

@dataclass
class Setup:
    name:       str
    duration_s: float
    common:     str
    passes:     dict[str, str]                     # pass → source, render order
    channels:   dict[str, list[str | None]] = field(default_factory=dict)
    images:     list[Path] = field(default_factory=list)  # <setup>/images/, sorted

    @property
    def uses_blobs(self) -> bool:
        return any("blobs" in chans for chans in self.channels.values())

    @property
    def uses_image(self) -> bool:
        return any("image" in chans for chans in self.channels.values())


def load_setup(path: Path) -> Setup:
    path = Path(path)
    cfg_path = path / "setup.json"
    cfg  = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    if not (path / "image.glsl").exists():
        raise ShaderError(f"{path.name}: image.glsl missing")
    if (path / "buffer_a.glsl").exists():
        log.warning("%s: buffer_a.glsl ignored — Buffer A is the Body", path.name)

    passes = {p: (path / f"{p}.glsl").read_text()
              for p in BUFFERS if (path / f"{p}.glsl").exists()}
    passes["image"] = (path / "image.glsl").read_text()

    channels: dict[str, list[str | None]] = {}
    for p, chans in cfg.get("channels", {}).items():
        if p not in passes:
            raise ShaderError(f"{path.name}: channels for unknown pass {p!r}")
        if not isinstance(chans, list):
            raise ShaderError(f"{path.name}: channels for {p} must be a list")
        if len(chans) > 4:
            raise ShaderError(f"{path.name}: {p} binds more than 4 channels")
        bad = [c for c in chans if c is not None and c not in SOURCES]
        if bad:
            raise ShaderError(f"{path.name}: {p} binds unknown source(s) {bad}")
        missing = [c for c in chans if c in ("B", "C", "D")
                   and f"buffer_{c.lower()}" not in passes]
        if missing:
            raise ShaderError(f"{path.name}: {p} reads {missing} but no such buffer file")
        channels[p] = list(chans) + [None] * (4 - len(chans))

    img_dir = path / "images"
    images  = sorted((f for f in img_dir.iterdir()
                      if f.is_file() and f.suffix.lower() in IMAGE_EXTS),
                     key=lambda f: f.name.lower()) if img_dir.is_dir() else []

    common_path = path / "common.glsl"
    return Setup(
        name       = path.name,
        duration_s = float(cfg.get("duration_s", 120.0)),
        common     = common_path.read_text() if common_path.exists() else "",
        passes     = passes,
        channels   = channels,
        images     = images,
    )


def decode_image(path: Path, cover: tuple[int, int], max_side: int = 16384) -> np.ndarray:
    """An image file as uint8 RGBA (h, w, 4), row 0 = bottom (GL), upright per its EXIF.

    Downscaled (aspect kept, never upscaled) to the smallest size that still covers
    `cover`, since Setups cover-fit it to the screen; no side exceeds `max_side`.
    """
    from PIL import Image, ImageOps
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGBA")
            w, h = im.size
            scale = min(1.0, max(cover[0] / w, cover[1] / h), max_side / max(w, h))
            if scale < 1.0:
                im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                               Image.Resampling.LANCZOS)
            return np.ascontiguousarray(np.flipud(np.asarray(im, dtype=np.uint8)))
    except Exception as exc:
        raise ShaderError(f"{Path(path).name}: can't decode image: {exc}") from exc


def wrap_source(common: str, body: str) -> str:
    """Shadertoy tab → GLSL 330 fragment shader; error line numbers match the tab."""
    return f"{_HEADER}#line 1 1\n{common}\n#line 1 0\n{body}\n{_FOOTER}"


# ── Body packing ──────────────────────────────────────────────────────────────

def pack_body(foreground: np.ndarray, roi: dict, slabs: list[dict]) -> np.ndarray:
    """uint16 mm foreground (row 0 = top) → RGBA8 Body texels, row 0 = bottom.

    .r = 255 inside any Depth Slab (as render_silhouette), .g = nearness across
    the slabs' span (255 at the nearest near_mm, 0 at the farthest far_mm).
    """
    near_mm = min(s["near_mm"] for s in slabs)
    far_mm  = max(s["far_mm"] for s in slabs)
    crop  = foreground[roi["y"]:roi["y"] + roi["h"], roi["x"]:roi["x"] + roi["w"]]
    d     = crop.astype(np.float32)
    mask  = np.zeros(crop.shape, dtype=bool)
    for s in slabs:
        mask |= (d >= s["near_mm"]) & (d < s["far_mm"])
    near  = np.clip((far_mm - d) / (far_mm - near_mm), 0.0, 1.0)
    out   = np.zeros(crop.shape + (4,), dtype=np.uint8)
    out[..., 0] = mask * 255
    out[..., 1] = (near * mask * 255).astype(np.uint8)
    out[..., 3] = 255
    return np.ascontiguousarray(out[::-1])         # GL textures start at the bottom


class BodyMouse:
    """Synthesises Shadertoy's iMouse from the Body, so mouse ≡ person.

    xy = presence centroid in render pixels (held when nobody is there);
    zw = where presence began, positive while present; w positive only on
    the first frame — Shadertoy's click semantics. Fewer than min_pixels
    present texels counts as nobody (min_foreground_pixels, as app.py).
    The caller must negate w after one render; update() runs per camera frame.
    """

    def __init__(self, min_pixels: int = 1) -> None:
        self.min_pixels = max(1, min_pixels)
        self.xy      = (0.0, 0.0)
        self.start   = (0.0, 0.0)
        self.present = False

    def update(self, body: np.ndarray, w: int, h: int) -> tuple[float, float, float, float]:
        ys, xs = np.nonzero(body[..., 0])
        if xs.size < self.min_pixels:
            self.present = False
            return (*self.xy, -abs(self.start[0]), -abs(self.start[1]))
        bh, bw = body.shape[:2]
        self.xy = ((xs.mean() + 0.5) / bw * w, (ys.mean() + 0.5) / bh * h)
        onset   = not self.present
        if onset:
            self.start = self.xy
        self.present = True
        return (*self.xy, self.start[0], self.start[1] if onset else -self.start[1])


# ── Keyboard ──────────────────────────────────────────────────────────────────

def js_keycode(pg_key: int) -> int | None:
    """pygame key → browser keyCode, the column Shadertoy's keyboard texture uses."""
    import pygame
    if pygame.K_a <= pg_key <= pygame.K_z:
        return pg_key - pygame.K_a + 65
    if pygame.K_0 <= pg_key <= pygame.K_9:
        return pg_key - pygame.K_0 + 48
    return {
        pygame.K_SPACE: 32, pygame.K_RETURN: 13, pygame.K_ESCAPE: 27,
        pygame.K_TAB: 9, pygame.K_BACKSPACE: 8,
        pygame.K_LEFT: 37, pygame.K_UP: 38, pygame.K_RIGHT: 39, pygame.K_DOWN: 40,
        pygame.K_LSHIFT: 16, pygame.K_RSHIFT: 16,
        pygame.K_LCTRL: 17, pygame.K_RCTRL: 17,
        pygame.K_LALT: 18, pygame.K_RALT: 18,
    }.get(pg_key)


class Keyboard:
    """256×3 R8 texture: row 0 held, row 1 pressed this frame, row 2 toggled."""

    def __init__(self) -> None:
        self.data = np.zeros((3, 256), dtype=np.uint8)

    def key_down(self, code: int) -> None:
        if not self.data[0, code]:
            self.data[1, code] = 255
            self.data[2, code] ^= 255
        self.data[0, code] = 255

    def key_up(self, code: int) -> None:
        self.data[0, code] = 0

    def end_frame(self) -> None:
        self.data[1] = 0


# ── Renderer ──────────────────────────────────────────────────────────────────

class _PingPong:
    def __init__(self, ctx, size: tuple[int, int]) -> None:
        self.tex = [ctx.texture(size, 4, dtype="f2") for _ in range(2)]
        self.fbo = [ctx.framebuffer(color_attachments=[t]) for t in self.tex]
        for t in self.tex:
            t.repeat_x = t.repeat_y = False
        for f in self.fbo:
            f.clear()
        self.read = 0

    @property
    def read_tex(self):
        return self.tex[self.read]

    @property
    def write_fbo(self):
        return self.fbo[1 - self.read]

    def swap(self) -> None:
        self.read = 1 - self.read

    def release(self) -> None:
        for o in (*self.fbo, *self.tex):
            o.release()


class Renderer:
    """Runs one Setup per frame at `size`, leaving the Image in `self.output`.

    body_mode "camera": Buffer A is the texture given to upload_body().
    body_mode "painter": Buffer A runs body_painter.glsl (mouse-driven).
    """

    def __init__(self, ctx, size: tuple[int, int], body_mode: str = "camera") -> None:
        import moderngl
        self._mgl  = moderngl
        self.ctx   = ctx
        self.size  = size
        self.body_mode = body_mode
        # True: render() leaves `output` stale and draw_deferred_image() draws the last frame's Image on demand.
        # For tests that run many frames but read few Images; the Image pass feeds nothing back, so this is exact.
        self.defer_image = False
        self._deferred: tuple | None = None        # (chans, uniforms) of the last frame whose Image was skipped
        self._deferred_lost = False                # an input changed since then: that Image can't be drawn now
        self.vbo  = ctx.buffer(struct.pack("8f", -1, -1, 1, -1, -1, 1, 1, 1))
        self.keyboard = Keyboard()
        self._kb_tex  = ctx.texture((256, 3), 1, dtype="f1")   # normalised; "u1" is integer and samples as 0
        self._kb_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._blank  = ctx.texture((1, 1), 4, data=bytes(4))   # unbound channels read 0
        # Read with texelFetch; NEAREST keeps a 32-bit float texture complete on V3D.
        self._blobs_tex = ctx.texture((BLOB_SLOTS, BLOB_ROWS), 4, dtype="f4")
        self._blobs_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._blobs_tex.repeat_x = self._blobs_tex.repeat_y = False
        self.upload_blobs(np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32))

        self.output_tex = ctx.texture(size, 4)
        self.output   = ctx.framebuffer(color_attachments=[self.output_tex])

        self._body_tex = None
        self._painter  = None
        self._painter_buf = None
        if body_mode == "painter":
            self._painter = self._compile("", PAINTER_PATH.read_text(), "body_painter")
            self._painter_buf = _PingPong(ctx, size)

        self._image_tex = None                     # this load's "image" source (ADR-0024)
        self._passes:  dict[str, tuple] = {}       # pass → (prog, vao)
        self._buffers: dict[str, _PingPong] = {}
        self.setup: Setup | None = None
        self.reset_clock()

    # ── Setup lifecycle ───────────────────────────────────────────────────────

    def _compile(self, common: str, body: str, label: str) -> tuple:
        try:
            prog = self.ctx.program(vertex_shader=VERT,
                                    fragment_shader=wrap_source(common, body))
        except Exception as exc:
            raise ShaderError(f"{label}: {exc}") from exc
        vao = self.ctx.vertex_array(prog, [(self.vbo, "2f", "in_vert")])
        return prog, vao

    def load(self, setup: Setup, image: np.ndarray | None = None) -> None:
        """Compile every pass first so a broken Setup leaves the current one running.

        `image` (uint8 RGBA, row 0 = bottom, from decode_image) is bound to the
        "image" source; without one that source reads 0 with resolution 0.
        """
        compiled = {}
        try:
            for p, src in setup.passes.items():
                compiled[p] = self._compile(setup.common, src, f"{setup.name}/{p}.glsl")
        except ShaderError:
            for prog, vao in compiled.values():
                vao.release()
                prog.release()
            raise
        self._release_setup()
        self._passes  = compiled
        self._buffers = {p: _PingPong(self.ctx, self.size) for p in setup.passes if p in BUFFERS}
        if image is not None:
            h, w = image.shape[:2]
            self._image_tex = self.ctx.texture((w, h), 4, data=np.ascontiguousarray(image).tobytes())
            self._image_tex.filter = (self._mgl.LINEAR, self._mgl.LINEAR)
            self._image_tex.repeat_x = self._image_tex.repeat_y = False
        self.setup    = setup
        self.reset_clock()
        log.info("Setup loaded: %s (%s)", setup.name, ", ".join(setup.passes))

    def unload(self) -> None:
        self._release_setup()
        self.setup = None

    def _release_setup(self) -> None:
        for prog, vao in self._passes.values():
            vao.release()
            prog.release()
        for b in self._buffers.values():
            b.release()
        self._passes, self._buffers = {}, {}
        self._deferred, self._deferred_lost = None, False
        if self._image_tex is not None:
            self._image_tex.release()
            self._image_tex = None

    @property
    def image_size(self) -> tuple[int, int] | None:
        """(w, h) of the bound "image" source, or None."""
        return tuple(self._image_tex.size) if self._image_tex is not None else None

    def reset_clock(self) -> None:
        self.time  = 0.0
        self.frame = 0
        if self._painter_buf:
            for f in self._painter_buf.fbo:
                f.clear()

    # ── Inputs ────────────────────────────────────────────────────────────────

    def _inputs_changing(self) -> None:
        if self._deferred is not None:
            self._deferred, self._deferred_lost = None, True

    def upload_body(self, rgba: np.ndarray) -> None:
        self._inputs_changing()
        h, w = rgba.shape[:2]
        if self._body_tex is None or self._body_tex.size != (w, h):
            if self._body_tex is not None:
                self._body_tex.release()
            self._body_tex = self.ctx.texture((w, h), 4)
            self._body_tex.repeat_x = self._body_tex.repeat_y = False
        self._body_tex.write(rgba.tobytes())

    def upload_blobs(self, records: np.ndarray) -> None:
        """(BLOB_ROWS, BLOB_SLOTS, 4) float records; row 0 of the array is texel row 0."""
        if records.shape != (BLOB_ROWS, BLOB_SLOTS, 4):
            raise ValueError(f"blob records must be {(BLOB_ROWS, BLOB_SLOTS, 4)}, got {records.shape}")
        self._inputs_changing()
        self._blobs_tex.write(np.ascontiguousarray(records, dtype=np.float32).tobytes())

    def read_body(self) -> np.ndarray | None:
        """Painter mode: the painted Body as float (h, w, 4), row 0 = bottom. None otherwise."""
        if self._painter_buf is None:
            return None
        tex = self._painter_buf.read_tex
        data = np.frombuffer(tex.read(), dtype=np.float16)
        return data.reshape(tex.size[1], tex.size[0], 4).astype(np.float32)

    def _source_tex(self, src: str | None):
        if src is None:
            return None
        if src == "keyboard":
            return self._kb_tex
        if src == "blobs":
            return self._blobs_tex
        if src == "image":
            return self._image_tex
        if src == "A":
            return self._painter_buf.read_tex if self._painter_buf else self._body_tex
        return self._buffers[f"buffer_{src.lower()}"].read_tex

    # ── Frame ─────────────────────────────────────────────────────────────────

    def render(self, dt: float, mouse: tuple[float, float, float, float]) -> None:
        self._deferred, self._deferred_lost = None, False
        if self.setup is None:
            self.output.clear()
            return
        self._kb_tex.write(self.keyboard.data.tobytes())
        uniforms = {
            "iResolution": (float(self.size[0]), float(self.size[1]), 1.0),
            "iTime":       self.time,
            "iTimeDelta":  dt,
            "iFrameRate":  1.0 / dt if dt > 0 else 0.0,
            "iFrame":      self.frame,
            "iMouse":      tuple(float(v) for v in mouse),
            "iDate":       _idate(),
            "iSampleRate": 44100.0,
        }
        if self._painter:
            self._draw(self._painter, PAINTER_CHANNELS, uniforms, self._painter_buf.write_fbo)
            self._painter_buf.swap()
        for p, (prog, vao) in self._passes.items():
            chans = self.setup.channels.get(p, [None] * 4)
            if p == "image" and self.defer_image:
                self._deferred = chans, uniforms
            elif p == "image":
                self._draw((prog, vao), chans, uniforms, self.output)
            else:
                self._draw((prog, vao), chans, uniforms, self._buffers[p].write_fbo)
                self._buffers[p].swap()
        self.keyboard.end_frame()
        self.time  += dt
        self.frame += 1

    def draw_deferred_image(self) -> None:
        """With defer_image: draw the Image the last render() skipped, from that frame's inputs. Else a no-op.

        Exact: the Image is the last pass and feeds nothing back, and the buffers it reads were written by that frame.
        Raises if a Body or blob upload came in between, since that frame's inputs are gone.
        """
        if self._deferred_lost:
            raise RuntimeError("an input was uploaded after the last render(); render again before reading the Image")
        if self._deferred is not None:
            chans, uniforms = self._deferred
            self._draw(self._passes["image"], chans, uniforms, self.output)
            self._deferred = None

    def _draw(self, pv: tuple, chans: list, uniforms: dict, fbo) -> None:
        prog, vao = pv
        res = []
        for i, src in enumerate(chans):
            tex = self._source_tex(src)
            name = f"iChannel{i}"
            if tex is not None:
                tex.use(location=i)
                res.append((float(tex.size[0]), float(tex.size[1]), 1.0))
            else:
                self._blank.use(location=i)
                res.append((0.0, 0.0, 0.0))
            if name in prog:
                prog[name].value = i
        for k, v in uniforms.items():
            if k in prog:
                prog[k].value = v
        if "iChannelResolution" in prog:
            # The driver trims the array to the highest index the shader reads.
            n = prog["iChannelResolution"].array_length
            prog["iChannelResolution"].write(np.array(res[:n], dtype="f4").tobytes())
        fbo.use()
        vao.render(self._mgl.TRIANGLE_STRIP)

    def release(self) -> None:
        self._release_setup()
        for o in (self.output_tex, self.output, self._kb_tex, self._blank, self._blobs_tex,
                  self.vbo, self._body_tex):
            if o is not None:
                o.release()
        if self._painter:
            self._painter[1].release()
            self._painter[0].release()
            self._painter_buf.release()


def _idate() -> tuple[float, float, float, float]:
    t = time.localtime()
    secs = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec + (time.time() % 1.0)
    return (float(t.tm_year), float(t.tm_mon - 1), float(t.tm_mday), secs)
