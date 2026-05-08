"""
Looking Glass video renderer — runs as a standalone process, receives scene
parameters from the TreeHouse coordinator via OSC on localhost:9002, renders
a GLSL fragment shader fullscreen on the 7" HDMI display (1024×600).

Requires MESA_GL_VERSION_OVERRIDE=3.3 on Pi 5 (set below before moderngl import).
"""
import os
import threading
import logging
from pathlib import Path

os.environ.setdefault("MESA_GL_VERSION_OVERRIDE", "3.3")
os.environ.setdefault("MESA_GLSL_VERSION_OVERRIDE", "330")

import numpy as np
import pygame
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


def main() -> None:
    threading.Thread(target=_osc_thread, daemon=True).start()

    pygame.init()
    pygame.mouse.set_visible(False)
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)

    ctx = moderngl.create_context()
    log.info("OpenGL %s", ctx.version_code)

    current_scene = _state["scene"]
    try:
        frag = _load_frag(current_scene)
    except FileNotFoundError:
        log.warning("Shader %r missing, falling back to bloom", current_scene)
        current_scene = "bloom"
        frag = _load_frag("bloom")

    prog = ctx.program(vertex_shader=VERT, fragment_shader=frag)
    vao = _build_vao(ctx, prog)
    log.info("Shader loaded: %s", current_scene)

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        # Hot-swap shader on scene change
        if _state["scene"] != current_scene:
            try:
                frag = _load_frag(_state["scene"])
                new_prog = ctx.program(vertex_shader=VERT, fragment_shader=frag)
                vao.release()
                prog.release()
                prog = new_prog
                vao = _build_vao(ctx, prog)
                current_scene = _state["scene"]
                log.info("Scene → %s", current_scene)
            except Exception as exc:
                log.error("Shader swap failed: %s", exc)
                _state["scene"] = current_scene

        ctx.clear()
        prog["iResolution"].value = (float(WIDTH), float(HEIGHT))
        prog["iTime"].value = _state["time"]
        prog["iIntensity"].value = _state["intensity"]
        vao.render(moderngl.TRIANGLE_STRIP)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
