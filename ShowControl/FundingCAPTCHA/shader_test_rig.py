"""The scaffolding every shader Setup's tests share: a Rig that drives a Renderer, mask builders, GLSL constants, image helpers.

Tests read a Renderer only through its public methods (`read_buffer`, `snapshot`, `restore`,
`draw_deferred_image`). A Setup's own test file adds a Rig subclass for its buffer layout and nothing else.
"""
from __future__ import annotations

import ast
import copy
import json
import math
import operator
import re
from pathlib import Path

import numpy as np

from body_blobs import BlobConfig, BodyBlobs
from shadertoy import Renderer, load_setup, pack_body

BODY = (64, 40)                           # camera ROI (w, h) of the small test Body
SLABS = [{"near_mm": 1000, "far_mm": 4000}]
DT = 1 / 30
# The shipped defaults, except a smaller min_blob_pixels for the small test Body.
BLOBS = BlobConfig(min_blob_pixels=20)
PERSON_MM = 2000                          # the depth a mask's set pixels get


# ── GLSL constants ────────────────────────────────────────────────────────────

_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCTIONS = {"max": max, "min": min, "ceil": math.ceil, "float": float, "int": int,
              "vec2": lambda *a: tuple(float(x) for x in a), "vec3": lambda *a: tuple(float(x) for x in a)}


def _evaluate(node: ast.AST, known: dict):
    """The value of a GLSL constant expression: numbers, earlier constants, + - * /, and the calls in _FUNCTIONS."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in known:
        return known[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        return _BINARY[type(node.op)](_evaluate(node.left, known), _evaluate(node.right, known))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_evaluate(node.operand, known))
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS
            and not node.keywords):
        return _FUNCTIONS[node.func.id](*(_evaluate(a, known) for a in node.args))
    raise ValueError(f"not a GLSL constant expression: {ast.unparse(node)}")


class Consts(dict):
    """GLSL constants by name; asking for one that is not there says so."""

    def __getitem__(self, name):
        if name not in self:
            raise KeyError(f"{name} is not a numeric constant in common.glsl")
        return dict.__getitem__(self, name)


def glsl_consts(setup_dir: Path) -> Consts:
    """Every `const float|int|vec2|vec3 NAME = <expr>, ...;` in a Setup's common.glsl, evaluated.

    Simple arithmetic, earlier constants, max/min/ceil, float(...)/int(...); vec2/vec3 become tuples.
    Declarations that are not that (arrays, anything built from a constant skipped here) are left out.
    """
    src = re.sub(r"//[^\n]*", "", (Path(setup_dir) / "common.glsl").read_text())
    out = Consts()
    for m in re.finditer(r"\bconst\s+(?:float|int|vec2|vec3)\s+([^;]*);", src):
        depth, start, decls = 0, 0, []
        body = m.group(1)
        for i, ch in enumerate(body + ","):                 # split on top-level commas only
            depth += (ch == "(") - (ch == ")")
            if ch == "," and depth == 0:
                decls.append(body[start:i])
                start = i + 1
        for d in decls:
            name, expr = (x.strip() for x in d.split("=", 1))
            try:
                out[name] = _evaluate(ast.parse(expr, mode="eval").body, out)
            except (ValueError, SyntaxError):
                pass                                        # an array or a palette, not a number a test could read
    return out


# ── Masks ─────────────────────────────────────────────────────────────────────

def rect(x0, y0, x1, y1, body=BODY) -> np.ndarray:
    """bool mask (h, w) of a Body, row 0 = top, with the rectangle set; clipped to the Body's top and left edges."""
    m = np.zeros(body[::-1], dtype=bool)
    m[max(y0, 0):y1, max(x0, 0):x1] = True
    return m


EMPTY = rect(0, 0, 0, 0)


def standing(n, x=36):
    """n camera frames of a still person, left edge x."""
    return [rect(x, 8, x + 10, 36)] * n


def walking(n, step=1):
    """A person crossing the Body, `step` px per camera frame (~0.28 screen heights/s at step 1)."""
    return [rect(6 + (k * step) % 40, 8, 16 + (k * step) % 40, 36) for k in range(n)]


def flailing(n, x=30):
    """Arms out and in: the box width swings by 12 px at ~2 Hz."""
    return [rect(x - 6 * (k % 5 in (1, 2, 3)), 8, x + 10 + 6 * (k % 5 in (1, 2, 3)), 36) for k in range(n)]


def flickering(n, x=36, seed=0):
    """A still person whose 1-px border toggles randomly each camera frame."""
    rng = np.random.default_rng(seed)
    base = rect(x, 8, x + 10, 36)
    edge = rect(x - 1, 7, x + 11, 37) & ~rect(x + 1, 9, x + 9, 35)
    out = []
    for _ in range(n):
        m = base.copy()
        m[edge] = rng.random(edge.sum()) < 0.5
        out.append(m)
    return out


# ── Driving a Renderer ────────────────────────────────────────────────────────

def load_renderer(ctx, setup_dir: Path, size, image: np.ndarray | None = None) -> Renderer:
    """A camera-mode Renderer with the Setup loaded and the Image pass deferred until read_image()."""
    r = Renderer(ctx, size, body_mode="camera")
    r.load(load_setup(setup_dir), image=image)
    r.defer_image = True
    return r


def pack_frame(frame: np.ndarray) -> np.ndarray:
    """A camera frame as a packed Body, the frame being the whole ROI.

    frame: bool (h, w) mask, set pixels PERSON_MM away, or uint16 mm depth; row 0 = top.
    """
    fg = np.where(frame, PERSON_MM, 0).astype(np.uint16) if frame.dtype == bool else frame
    return pack_body(fg, {"x": 0, "y": 0, "w": fg.shape[1], "h": fg.shape[0]}, SLABS)


def read_image(r: Renderer) -> np.ndarray:
    """The Image as uint8 (h, w, 4), row 0 = bottom, drawn now if the Renderer deferred it."""
    r.draw_deferred_image()
    return np.frombuffer(r.output.read(components=4), np.uint8).reshape(r.size[1], r.size[0], 4)


class Rig:
    """A Renderer, plus the real BodyBlobs on a fake clock: camera at 10 Hz, render at `dt`.

    blobs: the tracker's config, or None to upload only the Body. record_slot: move the tracker's records
    there (owner = record_slot + 1). image: the Setup's "image" source, if it has one.
    """

    def __init__(self, ctx, setup_dir: Path, size, *, blobs: BlobConfig | None = BLOBS, dt: float = DT,
                 record_slot: int = 0, image: np.ndarray | None = None):
        self.size, self.dt, self.record_slot = size, dt, record_slot
        self.r = load_renderer(ctx, setup_dir, size, image=image)
        self.blobs = BodyBlobs(blobs) if blobs is not None else None
        self.t = 0.0

    def run(self, frames, frames_per_camera=3):
        """Upload each camera frame (see pack_frame), then render frames_per_camera frames of it."""
        for frame in frames:
            body = pack_frame(frame)
            self.r.upload_body(body)
            if self.blobs is not None:
                self.blobs.update(body[..., 0] > 0, body[..., 1] / 255.0, now=self.t)
            for _ in range(frames_per_camera):
                if self.blobs is not None:
                    self.r.upload_blobs(np.roll(self.blobs.records(now=self.t), self.record_slot, axis=1))
                self.r.render(self.dt, (0, 0, 0, 0))
                self.t += self.dt
                self.after_render()

    def hold(self, records: np.ndarray, seconds: float):
        """Render for `seconds` with these hand-written blob records, bypassing the tracker."""
        for _ in range(round(seconds / self.dt)):
            self.r.upload_blobs(records)
            self.r.render(self.dt, (0, 0, 0, 0))
            self.t += self.dt
            self.after_render()

    def after_render(self):
        """Called after every rendered frame; a subclass overrides it to watch the buffers."""

    def buf(self, name) -> np.ndarray:
        """A buffer as float32 (h, w, 4), row 0 = the GL bottom."""
        return self.r.read_buffer(name)

    def b(self) -> np.ndarray:
        """Buffer B."""
        return self.buf("buffer_b")

    def image(self) -> np.ndarray:
        """The Image as uint8 (h, w, 4), row 0 = bottom."""
        return read_image(self.r)

    def snapshot(self):
        """All state the next run() or read depends on, for restore()."""
        return self.r.snapshot(), self.t, copy.deepcopy(self.blobs)

    def restore(self, snap):
        state, self.t, blobs = snap
        self.r.restore(state)
        self.blobs = copy.deepcopy(blobs)

    def release(self):
        self.r.release()


# ── Setups written to disk ────────────────────────────────────────────────────

SOLID = "void mainImage(out vec4 o, in vec2 f) { o = vec4(1.0, 0.0, 0.0, 1.0); }"
SHOW_CH0 = ("void mainImage(out vec4 o, in vec2 f) {"
            " o = vec4(texture(iChannel0, f / iResolution.xy).rgb,"
            "          iChannelResolution[0].x > 0.0 ? 1.0 : 0.0); }")


def write_setup(tmp_path: Path, files: dict[str, str], cfg: dict | None = None) -> Path:
    """Setup "s" under tmp_path: the given tab files, and a setup.json if cfg is given."""
    d = tmp_path / "s"
    d.mkdir()
    for name, src in files.items():
        (d / name).write_text(src)
    if cfg is not None:
        (d / "setup.json").write_text(json.dumps(cfg))
    return d


def png(path: Path, size: tuple[int, int], colour: tuple, rows: list | None = None) -> Path:
    """Solid PNG, or one colour per row band (top first) when `rows` is given."""
    from PIL import Image
    im = Image.new("RGBA", size, colour)
    if rows:
        band = size[1] // len(rows)
        for i, c in enumerate(rows):
            for y in range(i * band, (i + 1) * band):
                for x in range(size[0]):
                    im.putpixel((x, y), c)
    im.save(path)
    return path


def image_setup(tmp_path: Path, images: dict[str, tuple | bytes] | None = None) -> Path:
    """Setup "s" under tmp_path showing its image; images: name → solid RGBA or raw bytes."""
    d = write_setup(tmp_path, {"image.glsl": SHOW_CH0}, {"channels": {"image": ["image"]}})
    if images is not None:
        (d / "images").mkdir()
        for name, v in images.items():
            if isinstance(v, bytes):
                (d / "images" / name).write_bytes(v)
            else:
                png(d / "images" / name, (4, 4), v)
    return d


def pixel(r: Renderer, x: int, y: int) -> tuple:
    """One RGBA texel of the Renderer's output as drawn, row 0 = bottom."""
    data = np.frombuffer(r.output.read(components=4), dtype=np.uint8)
    return tuple(data.reshape(r.size[1], r.size[0], 4)[y, x])


def rendered_colour(r: Renderer) -> tuple:
    """Render one frame and return its pixel at (1, 1)."""
    r.render(1 / 30, (0, 0, 0, 0))
    return pixel(r, 1, 1)
