"""
Looking Glass video renderer — standalone subprocess (ADR-0018).

Renders a GLSL fragment shader fullscreen on the 7" HDMI display (1024×600).
Receives scene parameters from the TreeHouse coordinator via OSC on localhost:9002.

Uses pygame + moderngl (SDL2/Wayland + EGL). Targets the 1024×600 weston output
by resolution matching, making assignment independent of connection order.
"""
import os
import sys
import struct
import threading
import logging
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "wayland")
os.environ.setdefault("MESA_GL_VERSION_OVERRIDE", "3.3")
os.environ.setdefault("MESA_GLSL_VERSION_OVERRIDE", "330")

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


def _build_program(ctx: moderngl.Context, scene: str) -> tuple[moderngl.Program, moderngl.VertexArray]:
    try:
        frag = _load_frag(scene)
    except FileNotFoundError:
        log.warning("Shader %r missing, falling back to bloom", scene)
        scene = "bloom"
        frag = _load_frag("bloom")
    prog = ctx.program(vertex_shader=VERT, fragment_shader=frag)
    vbo = ctx.buffer(struct.pack("8f", -1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0))
    vao = ctx.vertex_array(prog, [(vbo, "2f", "in_vert")])
    return prog, vao


def _find_display(target: tuple[int, int]) -> int:
    sizes = pygame.display.get_desktop_sizes()
    for i, size in enumerate(sizes):
        if size == target:
            return i
    log.warning("Display %s not found, using 0. Available: %s", target, sizes)
    return 0


def main() -> None:
    threading.Thread(target=_osc_thread, daemon=True).start()

    pygame.init()
    display_index = _find_display((WIDTH, HEIGHT))
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.set_mode(
        (WIDTH, HEIGHT),
        pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN,
        display=display_index,
    )
    pygame.mouse.set_visible(False)

    ctx = moderngl.create_context()
    log.info("OpenGL %s on display %d", ctx.version_code, display_index)

    current_scene = _state["scene"]
    prog, vao = _build_program(ctx, current_scene)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

        if _state["scene"] != current_scene:
            try:
                vao.release()
                prog.release()
                prog, vao = _build_program(ctx, _state["scene"])
                current_scene = _state["scene"]
                log.info("Shader loaded: %s", current_scene)
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
