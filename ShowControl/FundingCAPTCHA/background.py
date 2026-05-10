"""
Fullscreen background renderer.

Preferred: moderngl hybrid — GLSL shader behind pygame surface texture.
Fallback: solid-color fill if moderngl is unavailable.

Usage:
    from background import BackgroundRenderer, NEEDS_OPENGL
    # Pass NEEDS_OPENGL to pygame.display.set_mode flags
    bg = BackgroundRenderer(W, H)
    # Each frame:
    bg.render(dt, game_surf)   # game_surf is a pygame.Surface with SRCALPHA
"""
from __future__ import annotations

import numpy as np
import pygame

try:
    import moderngl as _mgl
    NEEDS_OPENGL = True
except ImportError:
    _mgl = None  # type: ignore
    NEEDS_OPENGL = False

# ── Shared vertex shader ───────────────────────────────────────────────────────

_VERT = """
#version 330
in vec2 in_vert;
out vec2 vUv;
void main() {
    vUv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

# ── Per-game background fragment shaders (ported from GLSL ES 1.0) ─────────────

_FRAG_LOBBY = """
#version 330
in vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
out vec4 fragColor;
void main() {
    float t = uTime * 0.25;
    vec3 col = vec3(0.03, 0.02, 0.08);
    col += vec3(0.05, 0.02, 0.13) * (sin(vUv.x * 3.14159 + t) * 0.5 + 0.5);
    col += vec3(0.03, 0.04, 0.10) * (cos(vUv.y * 2.0 + t * 0.73) * 0.5 + 0.5);
    col += vec3(0.18, 0.07, 0.35) * uEvent * 0.7;
    fragColor = vec4(col, 1.0);
}
"""

_FRAG_KEEPAWAY = """
#version 330
in vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
out vec4 fragColor;
void main() {
    float stripe = mod(floor(vUv.y * 7.0), 2.0);
    vec3 col = mix(vec3(0.07, 0.21, 0.06), vec3(0.06, 0.18, 0.05), stripe);
    float mark = smoothstep(0.025, 0.0, abs(fract(vUv.y * 7.0) - 0.5));
    col = mix(col, vec3(0.9, 0.9, 0.9), mark * 0.12);
    float dist = length(vUv - 0.5);
    float ring = smoothstep(0.018, 0.0, abs(dist - mod(uTime * 1.1, 0.75))) * uEvent;
    col += vec3(1.0, 0.82, 0.15) * ring * 0.9;
    col *= 0.52 + uIntensity * 0.18;
    fragColor = vec4(col, 1.0);
}
"""

_FRAG_RHYTHM = """
#version 330
in vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
out vec4 fragColor;
void main() {
    float colIdx = floor(vUv.x * 4.0);
    float colFrac = fract(vUv.x * 4.0);
    float phase = colIdx * 1.5708;
    float wave = sin(vUv.y * 22.0 - uTime * 5.0 + phase) * 0.5 + 0.5;
    wave *= 0.14;
    float sep = smoothstep(0.06, 0.0, min(colFrac, 1.0 - colFrac));
    vec3 col = vec3(0.02, 0.04, 0.13);
    col += vec3(0.0, 0.09, 0.28) * wave;
    col += vec3(0.06, 0.0, 0.12) * sep;
    col += col * uIntensity * 0.65;
    col += vec3(0.12, 0.42, 1.0) * uEvent * 0.45;
    fragColor = vec4(col, 1.0);
}
"""

_FRAG_UPSIDEDOWN = """
#version 330
in vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
out vec4 fragColor;
void main() {
    vec2 uv = vUv - 0.5;
    float angle  = atan(uv.y, uv.x);
    float radius = length(uv);
    float spiral = sin(angle * 4.0 - uTime * 1.6 - radius * 10.0) * 0.5 + 0.5;
    vec3 inner = vec3(0.04, 0.0, 0.10);
    vec3 outer = vec3(0.13, 0.03, 0.30);
    vec3 col = mix(inner, outer, radius * 1.8) * (0.48 + spiral * 0.52);
    col = mix(col, vec3(0.28, 0.0, 0.38), uIntensity * 0.55);
    col += vec3(0.45, 0.0, 0.65) * uEvent * 0.55;
    fragColor = vec4(col, 1.0);
}
"""

# Composite shader: blits pygame surface (as RGBA texture) over the background.
_FRAG_COMP = """
#version 330
in vec2 vUv;
uniform sampler2D tex;
out vec4 fragColor;
void main() {
    fragColor = texture(tex, vec2(vUv.x, 1.0 - vUv.y));
}
"""

_GAME_FRAGS: dict[str, str] = {
    "lobby":      _FRAG_LOBBY,
    "keepaway":   _FRAG_KEEPAWAY,
    "rhythm":     _FRAG_RHYTHM,
    "upsidedown": _FRAG_UPSIDEDOWN,
}

_FALLBACK_COLORS: dict[str, tuple[int, int, int]] = {
    "lobby":      (8,  5,  20),
    "keepaway":   (18, 54, 15),
    "rhythm":     (5,  10, 33),
    "upsidedown": (10, 0,  26),
}

# Fullscreen quad vertices for TRIANGLE_STRIP
_QUAD = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")


class BackgroundRenderer:
    """
    moderngl-backed renderer. Falls back to solid-color if moderngl unavailable.
    Instantiate after pygame.display.set_mode() has been called.
    """

    def __init__(self, W: int, H: int) -> None:
        self._W         = W
        self._H         = H
        self._game      = "lobby"
        self._u_time    = 0.0
        self._u_event   = 0.0
        self._intensity = 0.3
        self._dead      = not NEEDS_OPENGL

        if self._dead:
            return

        ctx = _mgl.create_context()
        self._ctx = ctx
        vbo = ctx.buffer(_QUAD.tobytes())

        self._bg_progs: dict = {}
        for name, frag in _GAME_FRAGS.items():
            try:
                prog = ctx.program(vertex_shader=_VERT, fragment_shader=frag)
                vao  = ctx.vertex_array(prog, [(vbo, "2f", "in_vert")])
                self._bg_progs[name] = (prog, vao)
            except Exception as exc:
                print(f"background: shader '{name}' compile failed: {exc}", flush=True)

        comp_prog       = ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG_COMP)
        self._comp_vao  = ctx.vertex_array(comp_prog, [(vbo, "2f", "in_vert")])
        if "tex" in comp_prog:
            comp_prog["tex"].value = 0

        self._tex = ctx.texture((W, H), 4)
        self._tex.filter = _mgl.LINEAR, _mgl.LINEAR

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_game(self, game: str | None) -> None:
        self._game = game or "lobby"

    def set_intensity(self, v: float) -> None:
        self._intensity = float(v)

    def on_event(self, kind: str) -> None:
        if kind == "win":
            self._u_event = 1.0
        elif kind == "lose":
            self._u_event = 0.8
        elif kind == "tap":
            self._u_event = min(1.0, self._u_event + 0.6)

    def render(self, dt: float, surf: pygame.Surface) -> None:
        """Advance time by dt seconds, then composite surf over the background."""
        self._u_time  += dt
        self._u_event  = max(0.0, self._u_event - dt * 2.2)

        if self._dead:
            disp = pygame.display.get_surface()
            if disp is not None:
                disp.fill(_FALLBACK_COLORS.get(self._game, (10, 10, 20)))
                disp.blit(surf, (0, 0))
            return

        ctx = self._ctx
        ctx.viewport = (0, 0, self._W, self._H)
        ctx.clear(0.0, 0.0, 0.0, 1.0)
        ctx.disable(_mgl.BLEND)

        key = self._game if self._game in self._bg_progs else "lobby"
        pair = self._bg_progs.get(key) or self._bg_progs.get("lobby")
        if pair:
            prog, vao = pair
            self._set_uniform(prog, "uTime",      self._u_time)
            self._set_uniform(prog, "uEvent",     self._u_event)
            self._set_uniform(prog, "uIntensity", self._intensity)
            vao.render(_mgl.TRIANGLE_STRIP)

        pixel_data = pygame.image.tostring(surf, "RGBA", True)
        self._tex.write(pixel_data)
        self._tex.use(0)
        ctx.enable(_mgl.BLEND)
        ctx.blend_func = _mgl.SRC_ALPHA, _mgl.ONE_MINUS_SRC_ALPHA
        self._comp_vao.render(_mgl.TRIANGLE_STRIP)
        ctx.disable(_mgl.BLEND)

    @staticmethod
    def _set_uniform(prog, name: str, value: float) -> None:
        try:
            if name in prog:
                prog[name].value = value
        except Exception:
            pass
