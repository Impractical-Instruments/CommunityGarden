"""Tests for the Shadertoy-compatible renderer (shadertoy.py, ADR-0021).

GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shadertoy import (BLOB_CONFIRMED, BLOB_COASTING, BLOB_EMPTY, BLOB_LOST, BLOB_PAINTER_PATH,
                       BLOB_ROWS, BLOB_SLOTS, BLOB_TENTATIVE, BodyMouse, Keyboard, Renderer,
                       ShaderError, decode_image, js_keycode, load_setup, pack_body)

SHADER_DIR = Path(__file__).parent / "shaders"


def _write_setup(tmp_path: Path, files: dict[str, str], cfg: dict | None = None) -> Path:
    d = tmp_path / "s"
    d.mkdir()
    for name, src in files.items():
        (d / name).write_text(src)
    if cfg is not None:
        (d / "setup.json").write_text(json.dumps(cfg))
    return d


SOLID = "void mainImage(out vec4 o, in vec2 f) { o = vec4(1.0, 0.0, 0.0, 1.0); }"


# ── Setup loading ─────────────────────────────────────────────────────────────

def test_load_setup_pads_channels_and_orders_passes(tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": SOLID, "buffer_c.glsl": SOLID,
                                "buffer_b.glsl": SOLID, "common.glsl": "// c"},
                     {"duration_s": 30, "channels": {"image": ["A", "B"]}})
    s = load_setup(d)
    assert list(s.passes) == ["buffer_b", "buffer_c", "image"]
    assert s.channels["image"] == ["A", "B", None, None]
    assert s.duration_s == 30
    assert s.common == "// c"


def test_load_setup_rejects_missing_image(tmp_path):
    with pytest.raises(ShaderError, match="image.glsl"):
        load_setup(_write_setup(tmp_path, {"buffer_b.glsl": SOLID}))


def test_load_setup_rejects_reading_absent_buffer(tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": ["C"]}})
    with pytest.raises(ShaderError, match="no such buffer"):
        load_setup(d)


def test_load_setup_accepts_blobs_source(tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": ["A", "blobs"]}})
    s = load_setup(d)
    assert s.channels["image"][1] == "blobs" and s.uses_blobs
    (tmp_path / "x").mkdir()
    assert not load_setup(_write_setup(tmp_path / "x", {"image.glsl": SOLID}, {})).uses_blobs


def test_load_setup_rejects_unknown_source(tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": ["webcam"]}})
    with pytest.raises(ShaderError, match="unknown source"):
        load_setup(d)


def test_listed_setups_exist():
    for name in json.loads((SHADER_DIR / "setups.json").read_text()):
        load_setup(SHADER_DIR / name)


# ── Body packing ──────────────────────────────────────────────────────────────

def test_pack_body_flips_and_scales_nearness():
    fg = np.zeros((4, 4), dtype=np.uint16)
    fg[0, 0] = 1000        # top-left, at near_mm → nearness 255
    fg[3, 3] = 2500        # bottom-right, halfway
    fg[1, 1] = 5000        # beyond far_mm → absent
    body = pack_body(fg, {"x": 0, "y": 0, "w": 4, "h": 4}, [{"near_mm": 1000, "far_mm": 4000}])
    assert body.shape == (4, 4, 4)
    assert tuple(body[3, 0, :2]) == (255, 255)       # top row lands last (GL bottom-up)
    assert body[0, 3, 0] == 255 and body[0, 3, 1] == 127
    assert body[2, 1, 0] == 0
    assert (body[..., 3] == 255).all()


def test_pack_body_crops_roi():
    fg = np.full((10, 10), 1500, dtype=np.uint16)
    body = pack_body(fg, {"x": 2, "y": 3, "w": 5, "h": 4}, [{"near_mm": 1000, "far_mm": 4000}])
    assert body.shape == (4, 5, 4)


def test_pack_body_slab_gap_is_absent():
    fg = np.array([[1500, 2500, 3500]], dtype=np.uint16)
    slabs = [{"near_mm": 1000, "far_mm": 2000}, {"near_mm": 3000, "far_mm": 4000}]
    body = pack_body(fg, {"x": 0, "y": 0, "w": 3, "h": 1}, slabs)
    assert list(body[0, :, 0]) == [255, 0, 255]


def test_load_setup_rejects_non_list_channels(tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": None}})
    with pytest.raises(ShaderError, match="must be a list"):
        load_setup(d)


def test_body_mouse_click_semantics():
    bm   = BodyMouse()
    body = np.zeros((10, 10, 4), dtype=np.uint8)
    assert bm.update(body, 100, 100)[2] <= 0
    body[4:6, 4:6, 0] = 255
    x, y, z, w = bm.update(body, 100, 100)
    assert (x, y) == pytest.approx((50, 50))
    assert z > 0 and w > 0                           # click frame
    _, _, z, w = bm.update(body, 100, 100)
    assert z > 0 and w < 0                           # held
    body[:] = 0
    x, y, z, w = bm.update(body, 100, 100)
    assert (x, y) == pytest.approx((50, 50)) and z < 0


def test_body_mouse_ignores_speckle():
    bm   = BodyMouse(min_pixels=5)
    body = np.zeros((10, 10, 4), dtype=np.uint8)
    body[0, 0, 0] = 255
    assert bm.update(body, 100, 100)[2] <= 0
    body[4:6, 4:7, 0] = 255
    assert bm.update(body, 100, 100)[2] > 0


def test_keyboard_rows():
    kb = Keyboard()
    kb.key_down(67)
    assert kb.data[0, 67] == kb.data[1, 67] == kb.data[2, 67] == 255
    kb.end_frame()
    kb.key_down(67)                                  # key repeat: no new press
    assert kb.data[1, 67] == 0
    kb.key_up(67)
    kb.key_down(67)
    assert kb.data[1, 67] == 255 and kb.data[2, 67] == 0


def test_js_keycode():
    pygame = pytest.importorskip("pygame")
    assert js_keycode(pygame.K_c) == 67
    assert js_keycode(pygame.K_1) == 49
    assert js_keycode(pygame.K_LSHIFT) == 16
    assert js_keycode(pygame.K_F12) is None


def _png(path: Path, size: tuple[int, int], colour: tuple, rows: list | None = None) -> Path:
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


def test_load_setup_lists_images_sorted_ignoring_others(tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": ["image"]}})
    (d / "images").mkdir()
    for n in ("b.JPG", "a.png", "c.jpeg", "notes.md", ".DS_Store"):
        (d / "images" / n).write_bytes(b"x")
    s = load_setup(d)
    assert [p.name for p in s.images] == ["a.png", "b.JPG", "c.jpeg"]
    assert s.uses_image


def test_load_setup_without_images_folder_has_no_images(tmp_path):
    s = load_setup(_write_setup(tmp_path, {"image.glsl": SOLID}, {"channels": {"image": ["image"]}}))
    assert s.images == [] and s.uses_image


def test_setup_without_image_source_does_not_use_image(tmp_path):
    assert not load_setup(_write_setup(tmp_path, {"image.glsl": SOLID})).uses_image


def test_decode_image_puts_bottom_row_first(tmp_path):
    p = _png(tmp_path / "t.png", (1, 2), (0, 0, 0, 255), rows=[(255, 0, 0, 255), (0, 0, 255, 255)])
    a = decode_image(p, (64, 64))
    assert a.shape == (2, 1, 4) and a.dtype == np.uint8
    assert tuple(a[0, 0]) == (0, 0, 255, 255) and tuple(a[1, 0]) == (255, 0, 0, 255)


def test_decode_image_downscales_only_while_still_covering(tmp_path):
    p = _png(tmp_path / "w.png", (400, 200), (10, 20, 30, 255))
    assert decode_image(p, (100, 100)).shape == (100, 200, 4)     # covers 100×100, aspect kept
    assert decode_image(p, (1000, 1000)).shape == (200, 400, 4)   # never upscaled
    assert decode_image(p, (100, 100), max_side=150).shape == (75, 150, 4)


def test_decode_image_applies_exif_orientation(tmp_path):
    from PIL import Image
    im = Image.new("RGB", (40, 20), (200, 10, 10))
    exif = Image.Exif()
    exif[0x0112] = 6                                      # "rotate 90° CW to display"
    im.save(tmp_path / "phone.jpg", exif=exif)
    assert decode_image(tmp_path / "phone.jpg", (1000, 1000)).shape == (40, 20, 4)


def test_decode_image_corrupt_raises(tmp_path):
    (tmp_path / "bad.png").write_bytes(b"not a png")
    with pytest.raises(ShaderError):
        decode_image(tmp_path / "bad.png", (64, 64))


# ── GL ────────────────────────────────────────────────────────────────────────

def _pixel(r: Renderer, x: int, y: int) -> tuple:
    data = np.frombuffer(r.output.read(components=4), dtype=np.uint8)
    return tuple(data.reshape(r.size[1], r.size[0], 4)[y, x])


@pytest.mark.parametrize("name", json.loads((SHADER_DIR / "setups.json").read_text()))
def test_listed_setups_compile(ctx, name):
    r = Renderer(ctx, (64, 36), body_mode="painter")
    r.load(load_setup(SHADER_DIR / name))
    for _ in range(3):
        r.render(1 / 30, (32, 18, 32, 18))
    r.release()


def test_compile_error_reports_tab_line(ctx, tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": "void mainImage(out vec4 o, in vec2 f) {\n  o = nope;\n}"})
    r = Renderer(ctx, (8, 8))
    with pytest.raises(ShaderError, match=r"\b0(:2\b|\(2\))"):    # Mesa "0:2", NVIDIA "0(2)"
        r.load(load_setup(d))
    r.release()


def test_broken_setup_keeps_current_running(ctx, tmp_path):
    r = Renderer(ctx, (8, 8))
    r.load(load_setup(_write_setup(tmp_path, {"image.glsl": SOLID})))
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "image.glsl").write_text("garbage")
    with pytest.raises(ShaderError):
        r.load(load_setup(bad))
    r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 4, 4)[:3] == (255, 0, 0)
    r.release()


def test_buffer_feedback_and_same_frame_reads(ctx, tmp_path):
    # B counts frames by reading itself (previous frame); Image reads B (this frame).
    d = _write_setup(tmp_path, {
        "buffer_b.glsl": "void mainImage(out vec4 o, in vec2 f) {"
                         " o = texture(iChannel0, f / iResolution.xy) + vec4(0.1); }",
        "image.glsl":    "void mainImage(out vec4 o, in vec2 f) {"
                         " o = vec4(texture(iChannel0, f / iResolution.xy).r, 0.0, 0.0, 1.0); }",
    }, {"channels": {"buffer_b": ["B"], "image": ["B"]}})
    r = Renderer(ctx, (4, 4))
    r.load(load_setup(d))
    for _ in range(3):
        r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 1, 1)[0] == pytest.approx(round(0.3 * 255), abs=2)
    r.release()


def test_camera_body_reaches_image(ctx, tmp_path):
    d = _write_setup(tmp_path, {
        "image.glsl": "void mainImage(out vec4 o, in vec2 f) {"
                      " o = vec4(texture(iChannel0, f / iResolution.xy).rg, 0.0, 1.0); }",
    }, {"channels": {"image": ["A"]}})
    r = Renderer(ctx, (8, 8), body_mode="camera")
    r.load(load_setup(d))
    fg = np.zeros((8, 8), dtype=np.uint16)
    fg[0:4, :] = 1000                                # top half, nearest
    r.upload_body(pack_body(fg, {"x": 0, "y": 0, "w": 8, "h": 8}, [{"near_mm": 1000, "far_mm": 4000}]))
    r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 4, 6)[:2] == (255, 255)         # GL y=6 is the top half
    assert _pixel(r, 4, 1)[:2] == (0, 0)
    r.release()


def _feed(r: Renderer, k: int) -> None:
    """Frame k's inputs: a Body square and one confirmed blob, both moving."""
    fg = np.zeros((48, 64), dtype=np.uint16)
    fg[10:40, 8 + k:24 + k] = 2000
    r.upload_body(pack_body(fg, {"x": 0, "y": 0, "w": 64, "h": 48}, [{"near_mm": 1000, "far_mm": 4000}]))
    rec = np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32)
    rec[0, 0] = (1, BLOB_CONFIRMED, (16 + k) / 64, 0.5)
    rec[1, 0] = (0.25, 0.6, 0.2, 0.5)
    rec[2, 0] = (k * 0.1, 0, 0, 0)
    r.upload_blobs(rec)


@pytest.mark.parametrize("name", json.loads((SHADER_DIR / "setups.json").read_text()))
def test_deferred_image_matches_drawing_it_every_frame(ctx, name):
    # defer_image skips the Image pass; drawing it afterwards must give the bytes the frame would have drawn.
    rs = []
    for defer in (False, True):
        r = Renderer(ctx, (96, 54), body_mode="camera")
        r.load(load_setup(SHADER_DIR / name))
        r.defer_image = defer
        rs.append(r)
    try:
        for k in range(12):
            for r in rs:
                _feed(r, k)
                r.render(1 / 30, (0, 0, 0, 0))
            if k in (4, 11):                         # read mid-run too: drawing it late must not disturb the next frame
                rs[1].draw_deferred_image()
                assert rs[0].output.read() == rs[1].output.read(), k
    finally:
        for r in rs:
            r.release()


def test_deferred_image_refuses_after_an_upload(ctx, tmp_path):
    r = Renderer(ctx, (8, 8), body_mode="camera")
    r.load(load_setup(_write_setup(tmp_path, {"image.glsl": SOLID})))
    r.defer_image = True
    r.render(1 / 30, (0, 0, 0, 0))
    r.upload_blobs(np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32))   # that frame's inputs are gone
    with pytest.raises(RuntimeError, match="render again"):
        r.draw_deferred_image()
    r.render(1 / 30, (0, 0, 0, 0))
    r.draw_deferred_image()                          # a new frame clears it
    r.release()


def test_draw_deferred_image_is_a_no_op_when_nothing_was_skipped(ctx, tmp_path):
    r = Renderer(ctx, (8, 8))
    r.load(load_setup(_write_setup(tmp_path, {"image.glsl": SOLID})))
    r.render(1 / 30, (0, 0, 0, 0))
    before = r.output.read()
    r.output.clear()
    r.draw_deferred_image()                          # defer_image is off: the Image was drawn, nothing to redo
    assert r.output.read() != before
    r.release()


def test_painter_puts_body_under_mouse(ctx, tmp_path):
    d = _write_setup(tmp_path, {
        "image.glsl": "void mainImage(out vec4 o, in vec2 f) {"
                      " o = vec4(texture(iChannel0, f / iResolution.xy).r, 0.0, 0.0, 1.0); }",
    }, {"channels": {"image": ["A"]}})
    r = Renderer(ctx, (160, 90), body_mode="painter")
    r.load(load_setup(d))
    r.render(1 / 30, (40.0, 45.0, 40.0, 45.0))      # left button down at x=40
    assert _pixel(r, 40, 45)[0] == 255
    assert _pixel(r, 130, 45)[0] == 0
    r.render(1 / 30, (40.0, 45.0, -40.0, -45.0))    # released, nothing parked
    assert _pixel(r, 40, 45)[0] == 0
    r.release()


@pytest.mark.parametrize("src", [
    # The driver trims iChannelResolution to the highest index read.
    "o = vec4(iChannelResolution[0].x / 8.0, 0.0, 0.0, 1.0);",
    # GLSL ES 3.00 built-ins that desktop 330 only has by extension.
    "o = vec4(unpackHalf2x16(packHalf2x16(vec2(1.0))), 0.0, 1.0);",
    # Shadertoy predefines HW_PERFORMANCE.
    "o = vec4(float(HW_PERFORMANCE + 1));",
])
def test_shadertoy_idioms_render(ctx, tmp_path, src):
    d = _write_setup(tmp_path, {"image.glsl": f"void mainImage(out vec4 o, in vec2 f) {{ {src} }}"},
                     {"channels": {"image": ["keyboard"]}})
    r = Renderer(ctx, (8, 8))
    r.load(load_setup(d))
    r.render(1 / 30, (0, 0, 0, 0))
    r.release()


def test_keyboard_reaches_shaders(ctx, tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": "void mainImage(out vec4 o, in vec2 f) {"
                                " o = vec4(texelFetch(iChannel0, ivec2(32, 0), 0).x, 0.0, 0.0, 1.0); }"},
                     {"channels": {"image": ["keyboard"]}})
    r = Renderer(ctx, (4, 4))
    r.load(load_setup(d))
    r.keyboard.key_down(32)
    r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 1, 1)[0] == 255
    r.release()


def test_itime_starts_at_zero(ctx, tmp_path):
    d = _write_setup(tmp_path, {"image.glsl": "void mainImage(out vec4 o, in vec2 f) {"
                                              " o = vec4(iTime, 0.0, 0.0, 1.0); }"})
    r = Renderer(ctx, (4, 4))
    r.load(load_setup(d))
    r.render(0.5, (0, 0, 0, 0))
    assert _pixel(r, 1, 1)[0] == 0
    r.render(0.5, (0, 0, 0, 0))
    assert _pixel(r, 1, 1)[0] == pytest.approx(128, abs=1)
    r.release()


# ── Rotation (shader_app.py) ──────────────────────────────────────────────────

def _setups(root: Path, **images: str) -> Path:
    for name, src in images.items():
        (root / name).mkdir()
        (root / name / "image.glsl").write_text(src)
        (root / name / "setup.json").write_text(json.dumps({"duration_s": 10}))
    return root


def test_reload_with_broken_edit_keeps_current(ctx, tmp_path):
    from shader_app import Rotation
    root = _setups(tmp_path, a=SOLID, b=SOLID)
    r = Renderer(ctx, (4, 4))
    rot = Rotation(r, ["a", "b"], shader_dir=root)
    rot.next()
    current = r.setup.name
    (root / current / "image.glsl").write_text("garbage")
    rot.reload()
    assert r.setup.name == current
    r.release()


def test_single_setup_is_not_recompiled_on_expiry(ctx, tmp_path):
    from shader_app import Rotation
    now = [0.0]
    r = Renderer(ctx, (4, 4))
    rot = Rotation(r, ["a"], shader_dir=_setups(tmp_path, a=SOLID), clock=lambda: now[0])
    rot.next()
    first = r.setup
    now[0] = 11.0
    rot.tick()
    assert r.setup is first and rot.started == 11.0
    r.release()


def test_render_failure_drops_setup(ctx, tmp_path):
    from shader_app import Rotation
    r = Renderer(ctx, (4, 4))
    rot = Rotation(r, ["a", "b"], shader_dir=_setups(tmp_path, a=SOLID, b=SOLID))
    rot.next()
    bad = r.setup.name
    rot.failed(RuntimeError("boom"))
    assert rot.names == [n for n in ("a", "b") if n != bad]
    assert r.setup is not None and r.setup.name != bad
    r.release()


# ── Blob records (ADR-0022) ───────────────────────────────────────────────────

def _blob_setup(tmp_path, files, channels):
    return load_setup(_write_setup(tmp_path, files, {"channels": channels}))


def test_uploaded_blobs_reach_texelfetch(ctx, tmp_path):
    # Image paints slot 5 row 2's state into red, as 8-bit.
    r = Renderer(ctx, (8, 8))
    r.load(_blob_setup(tmp_path, {"image.glsl": "void mainImage(out vec4 o, in vec2 f) {"
                                  " o = vec4(texelFetch(iChannel0, ivec2(5, 2), 0).y / 4.0, 0.0, 0.0, 1.0); }"},
                       {"image": ["blobs"]}))
    rec = np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32)
    rec[2, 5] = (17, BLOB_COASTING, 0.5, 1.0)
    r.upload_blobs(rec)
    r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 3, 3)[0] == pytest.approx(round(BLOB_COASTING / 4 * 255), abs=1)
    with pytest.raises(ValueError):
        r.upload_blobs(np.zeros((BLOB_SLOTS, BLOB_ROWS, 4), dtype=np.float32))
    r.release()


def test_blobs_channel_resolution_is_slots_by_rows(ctx, tmp_path):
    r = Renderer(ctx, (8, 8))
    r.load(_blob_setup(tmp_path, {"image.glsl": "void mainImage(out vec4 o, in vec2 f) {"
                                  " o = vec4(iChannelResolution[0].xy / 32.0, 0.0, 1.0); }"},
                       {"image": ["blobs"]}))
    r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 1, 1)[:2] == (round(BLOB_SLOTS / 32 * 255), round(BLOB_ROWS / 32 * 255))   # no .5 ties: drivers round those either way
    r.release()


def test_read_body_returns_painted_body(ctx, tmp_path):
    r = Renderer(ctx, (160, 90), body_mode="painter")
    r.load(load_setup(_write_setup(tmp_path, {"image.glsl": SOLID})))
    r.render(1 / 30, (40.0, 45.0, 40.0, 45.0))
    body = r.read_body()
    assert body.shape == (90, 160, 4)
    assert body[45, 40, 0] == 1.0 and body[45, 130, 0] == 0.0
    assert Renderer(ctx, (8, 8)).read_body() is None


def _painter_records(r) -> np.ndarray:
    tex = r._buffers["buffer_d"].read_tex
    data = np.frombuffer(tex.read(), dtype=np.float16).reshape(tex.size[1], tex.size[0], 4)
    return data[:BLOB_ROWS, :BLOB_SLOTS].astype(np.float32)


def test_blob_painter_lifecycle(ctx, tmp_path):
    """The Shadertoy stand-in walks slot 0 through the same states as the Pi tracker."""
    r = Renderer(ctx, (160, 90), body_mode="painter")
    r.load(_blob_setup(tmp_path, {"buffer_d.glsl": BLOB_PAINTER_PATH.read_text(), "image.glsl": SOLID},
                       {"buffer_d": ["D", "keyboard"], "image": ["A", "D"]}))
    dt = 0.05
    r.render(dt, (40.0, 45.0, 40.0, 45.0))               # frame 0 clears
    r.render(dt, (40.0, 45.0, 40.0, 45.0))               # click: born
    rec = _painter_records(r)
    assert rec[2, 0, 1] == BLOB_TENTATIVE and rec[2, 0, 0] == 1
    x0, y0, x1, y1 = rec[0, 0]
    assert x0 < 40 / 160 < x1 and y0 < 45 / 90 < y1
    for _ in range(10):
        r.render(dt, (40.0, 45.0, 40.0, -45.0))          # held
    assert _painter_records(r)[2, 0, 1] == BLOB_CONFIRMED
    r.render(dt, (40.0, 45.0, -40.0, -45.0))             # released
    assert _painter_records(r)[2, 0, 1] == BLOB_COASTING
    for _ in range(18):
        r.render(dt, (40.0, 45.0, -40.0, -45.0))
    assert _painter_records(r)[2, 0, 1] == BLOB_LOST
    for _ in range(21):
        r.render(dt, (40.0, 45.0, -40.0, -45.0))
    assert _painter_records(r)[2, 0, 1] == BLOB_EMPTY
    r.render(dt, (40.0, 45.0, 40.0, 45.0))               # a new person gets a new id
    assert _painter_records(r)[2, 0, 0] == 2
    r.release()


def test_blob_painter_space_parks_into_next_slot(ctx, tmp_path):
    r = Renderer(ctx, (160, 90), body_mode="painter")
    r.load(_blob_setup(tmp_path, {"buffer_d.glsl": BLOB_PAINTER_PATH.read_text(), "image.glsl": SOLID},
                       {"buffer_d": ["D", "keyboard"]}))
    r.render(1 / 30, (40.0, 45.0, -40.0, -45.0))
    for x in (40.0, 120.0):
        r.keyboard.key_down(32)
        r.render(1 / 30, (x, 45.0, -40.0, -45.0))
        r.keyboard.key_up(32)
    rec = _painter_records(r)
    assert rec[2, 0, 1] == BLOB_EMPTY                     # nobody under a held mouse
    assert list(rec[2, 1:3, 1]) == [BLOB_TENTATIVE] * 2
    assert list(rec[2, 1:3, 0]) == [1, 2]
    r.keyboard.key_down(67)                               # C: everyone still tentative → gone
    r.render(1 / 30, (40.0, 45.0, -40.0, -45.0))
    assert not _painter_records(r)[2, :, 1].any()
    r.release()


def test_blob_debug_reference_setup_renders(ctx):
    r = Renderer(ctx, (64, 36), body_mode="painter")
    r.load(load_setup(SHADER_DIR / "blob_debug"))
    rec = np.zeros((BLOB_ROWS, BLOB_SLOTS, 4), dtype=np.float32)
    rec[0, 0] = (0.1, 0.1, 0.9, 0.9)
    rec[2, 0] = (1, BLOB_CONFIRMED, 0.0, 0.5)
    r.upload_blobs(rec)
    r.render(1 / 30, (32, 18, 32, 18))
    assert _pixel(r, int(0.1 * 64), 18)[:3] == (17, 17, 17)  # ink on the box's left edge
    r.release()


def test_rotation_calls_on_load_for_every_load(ctx, tmp_path):
    """Buffer state resets on every load, so the blob tracker must too (stamps match on id)."""
    from shader_app import Rotation
    root = _setups(tmp_path, a=SOLID, b=SOLID)
    r = Renderer(ctx, (4, 4))
    loads = []
    rot = Rotation(r, ["a", "b"], shader_dir=root, on_load=lambda: loads.append(r.setup.name))
    rot.next()
    rot.reload()
    assert loads == [r.setup.name] * 2
    (root / r.setup.name / "image.glsl").write_text("garbage")
    rot.reload()                                          # broken edit: nothing reloaded
    assert len(loads) == 2
    r.release()


# ── Image source (ADR-0024) ───────────────────────────────────────────────────

SHOW_CH0 = ("void mainImage(out vec4 o, in vec2 f) {"
            " o = vec4(texture(iChannel0, f / iResolution.xy).rgb,"
            "          iChannelResolution[0].x > 0.0 ? 1.0 : 0.0); }")


def _image_setup(tmp_path: Path, images: dict[str, tuple | bytes] | None = None) -> Path:
    """Setup "s" under tmp_path showing its image; images: name → solid RGBA or raw bytes."""
    d = _write_setup(tmp_path, {"image.glsl": SHOW_CH0}, {"channels": {"image": ["image"]}})
    if images is not None:
        (d / "images").mkdir()
        for name, v in images.items():
            if isinstance(v, bytes):
                (d / "images" / name).write_bytes(v)
            else:
                _png(d / "images" / name, (4, 4), v)
    return d


def test_image_channel_reaches_shader(ctx, tmp_path):
    img = np.zeros((2, 1, 4), dtype=np.uint8)
    img[0, 0] = (0, 0, 255, 255)                          # row 0 = bottom
    img[1, 0] = (255, 0, 0, 255)
    r = Renderer(ctx, (4, 4))
    r.load(load_setup(_image_setup(tmp_path)), image=img)
    r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 1, 3) == (255, 0, 0, 255)            # GL y=3 is the top
    assert _pixel(r, 1, 0) == (0, 0, 255, 255)
    r.release()


def test_unbound_image_reads_zero_resolution(ctx, tmp_path):
    r = Renderer(ctx, (4, 4))
    r.load(load_setup(_image_setup(tmp_path)))
    r.render(1 / 30, (0, 0, 0, 0))
    assert _pixel(r, 1, 1) == (0, 0, 0, 0)
    r.release()


def _rendered_colour(r: Renderer) -> tuple:
    r.render(1 / 30, (0, 0, 0, 0))
    return _pixel(r, 1, 1)


def test_rotation_shuffles_images_per_load(ctx, tmp_path):
    from shader_app import Rotation
    _image_setup(tmp_path, {"r.png": (255, 0, 0, 255), "g.png": (0, 255, 0, 255),
                            "b.png": (0, 0, 255, 255)})
    r = Renderer(ctx, (4, 4))
    rot = Rotation(r, ["s"], shader_dir=tmp_path)
    rot.next()
    seen = [_rendered_colour(r)]
    for _ in range(3):
        rot.reload()
        seen.append(_rendered_colour(r))
    assert len(set(seen[:3])) == 3                        # no repeat until all have shown
    assert seen[3] in seen[:3]
    r.release()


def test_rotation_skips_corrupt_image(ctx, tmp_path):
    from shader_app import Rotation
    _image_setup(tmp_path, {"bad.png": b"not a png", "good.png": (0, 255, 0, 255)})
    r = Renderer(ctx, (4, 4))
    rot = Rotation(r, ["s"], shader_dir=tmp_path)
    rot.next()
    colours = [_rendered_colour(r)]
    for _ in range(3):
        rot.reload()
        colours.append(_rendered_colour(r))
    assert colours == [(0, 255, 0, 255)] * 4
    r.release()


def test_rotation_with_only_corrupt_images_binds_nothing(ctx, tmp_path):
    from shader_app import Rotation
    _image_setup(tmp_path, {"bad.png": b"not a png"})
    r = Renderer(ctx, (4, 4))
    rot = Rotation(r, ["s"], shader_dir=tmp_path)
    rot.next()
    assert r.setup is not None and r.setup.name == "s"
    assert _rendered_colour(r)[3] == 0
    r.release()


def test_rotation_scales_images_to_cover_image_max(ctx, tmp_path):
    from shader_app import Rotation
    d = _image_setup(tmp_path, {})
    _png(d / "images" / "big.png", (40, 20), (9, 9, 9, 255))
    r = Renderer(ctx, (4, 4))
    rot = Rotation(r, ["s"], shader_dir=tmp_path, image_max=(10, 10))
    rot.next()
    assert r.image_size == (20, 10)                       # smallest size that still covers 10×10
    r.release()


# ── Display choice ────────────────────────────────────────────────────────────

def test_pick_display_uses_that_displays_own_size():
    from shader_app import pick_display
    sizes = [(3072, 1920), (1600, 1200)]
    assert pick_display(sizes, 1) == (1, (1600, 1200))
    assert pick_display(sizes, 0) == (0, (3072, 1920))


def test_pick_display_out_of_range_falls_back_to_first():
    from shader_app import pick_display
    assert pick_display([(1920, 1080)], 2) == (0, (1920, 1080))
    assert pick_display([(1920, 1080)], -1) == (0, (1920, 1080))


def test_display_index_flag_beats_settings():
    from argparse import Namespace
    from shader_app import display_index
    settings = {"shader_app": {"display": 1}}
    assert display_index(Namespace(display=None), settings) == 1
    assert display_index(Namespace(display=2), settings) == 2
    from settings import with_defaults
    assert display_index(Namespace(display=None), with_defaults({})) == 0
