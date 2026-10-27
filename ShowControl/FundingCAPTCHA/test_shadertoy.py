"""Tests for the Shadertoy-compatible renderer (shadertoy.py, ADR-0021).

GL tests need a headless context (EGL / llvmpipe) and skip without one.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from shadertoy import (BodyMouse, Keyboard, Renderer, ShaderError, js_keycode,
                       load_setup, pack_body)

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


# ── GL ────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ctx():
    moderngl = pytest.importorskip("moderngl")
    for kw in ({"backend": "egl"}, {}):
        try:
            c = moderngl.create_standalone_context(**kw)
            break
        except Exception:
            continue
    else:
        if os.environ.get("CI"):
            pytest.fail("no headless OpenGL context in CI — GL tests would silently skip")
        pytest.skip("no headless OpenGL context")
    yield c
    c.release()


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
    with pytest.raises(ShaderError, match=r"0:2"):
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
