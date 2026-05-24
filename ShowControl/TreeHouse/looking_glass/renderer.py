"""
Looking Glass video renderer — runs as a standalone process, receives scene
parameters from the TreeHouse coordinator via OSC on localhost:9002, renders
a GLSL fragment shader fullscreen on the 7" HDMI display (1024×600).

Uses pyglet for windowing (native Wayland+EGL on Pi 5).
Requires MESA_GL_VERSION_OVERRIDE=3.3 on Pi 5 (set below before moderngl import).
"""
import os
import threading
import logging
from pathlib import Path

os.environ.setdefault("MESA_GL_VERSION_OVERRIDE", "3.3")
os.environ.setdefault("MESA_GLSL_VERSION_OVERRIDE", "330")

import numpy as np
import pyglet
import moderngl
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("looking_glass")

OSC_PORT = 9002
WIDTH, HEIGHT = 1024, 600
FPS = 30
SHADER_DIR = Path(__file__).parent

_state = {"scene": "bloom", "time": 0.0, "intensity": 0.0}

VERT = """
#version 330
in vec2 in_vert;
void main() { gl_Position = vec4(in_vert, 0.0, 1.0); }
"""


def _osc_thread() -> None:
    def on_scene(addr, val):
        _state["scene"] = str(val)

    def on_time(addr, val):
        _state["time"] = float(val)

    def on_intensity(addr, val):
        _state["intensity"] = max(0.0, min(1.0, float(val)))

    d = Dispatcher()
    d.map("/lookingglass/scene", on_scene)
    d.map("/lookingglass/time", on_time)
    d.map("/lookingglass/intensity", on_intensity)
    log.info("OSC listening on 127.0.0.1:%d", OSC_PORT)
    ThreadingOSCUDPServer(("127.0.0.1", OSC_PORT), d).serve_forever()


def _load_frag(name: str) -> str:
    return (SHADER_DIR / f"{name}.glsl").read_text()


def _build_vao(ctx: moderngl.Context, prog: moderngl.Program):
    verts = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")
    vbo = ctx.buffer(verts.tobytes())
    return ctx.vertex_array(prog, [(vbo, "2f", "in_vert")])


class LookingGlassWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, caption="Looking Glass", fullscreen=True, vsync=True)
        self.set_mouse_visible(False)
        self.ctx = moderngl.create_context()
        log.info("OpenGL %s", self.ctx.version_code)
        self._current_scene = _state["scene"]
        self._load_scene(self._current_scene)

    def _load_scene(self, name: str) -> None:
        try:
            frag = _load_frag(name)
        except FileNotFoundError:
            log.warning("Shader %r missing, falling back to bloom", name)
            name = "bloom"
            frag = _load_frag("bloom")
        if hasattr(self, "vao"):
            self.vao.release()
            self.prog.release()
        self.prog = self.ctx.program(vertex_shader=VERT, fragment_shader=frag)
        self.vao = _build_vao(self.ctx, self.prog)
        self._current_scene = name
        log.info("Shader loaded: %s", name)

    def on_draw(self):
        if _state["scene"] != self._current_scene:
            try:
                self._load_scene(_state["scene"])
            except Exception as exc:
                log.error("Shader swap failed: %s", exc)
                _state["scene"] = self._current_scene

        self.ctx.clear()
        self.prog["iResolution"].value = (float(WIDTH), float(HEIGHT))
        self.prog["iTime"].value = _state["time"]
        self.prog["iIntensity"].value = _state["intensity"]
        self.vao.render(moderngl.TRIANGLE_STRIP)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()


def main() -> None:
    threading.Thread(target=_osc_thread, daemon=True).start()
    window = LookingGlassWindow()
    pyglet.clock.schedule_interval(lambda dt: window.dispatch_event("on_draw"), 1 / FPS)
    pyglet.app.run()


if __name__ == "__main__":
    main()
