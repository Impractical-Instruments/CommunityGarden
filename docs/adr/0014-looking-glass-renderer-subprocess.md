# ADR-0014 — Looking Glass: renderer as asyncio subprocess

**Status:** Accepted  
**Date:** 2026-05-22

---

## Context

The Looking Glass is a mirrored box (garage window) containing a 7" HDMI display (1024×600)
wired to the TreeHouse Pi 5. Infinite-regression reflections multiply every rendered frame into a
tunnel effect. The display runs generative GLSL fragment shaders driven by live show state.

The renderer requires its own OpenGL/Wayland event loop (pyglet), which is incompatible with the
asyncio frame loop in `main.py`. It must be a separate OS process.

---

## Decision

### Process model

`main.py` spawns `looking_glass/renderer.py` via `asyncio.create_subprocess_exec` immediately
before the frame loop starts. The subprocess is watched; on crash it is relaunched with
exponential back-off (cap 30 s). On clean shutdown the subprocess is terminated with SIGTERM,
then SIGKILL after 3 s.

A `--no-renderer` CLI flag mirrors the existing `--no-pico` / `--no-branch` pattern and skips
subprocess launch for dev environments without a display.

### IPC

Coordinator → renderer: OSC UDP on `127.0.0.1:9002` (already implemented in `renderer.py`).  
Messages: `/lookingglass/scene`, `/lookingglass/time`, `/lookingglass/intensity`.

### Shader scenes

Four `.glsl` files live in `looking_glass/`. Each uses `#version 330` with uniforms:

| uniform | type | description |
|---|---|---|
| `iResolution` | `vec2` | viewport size in pixels |
| `iTime` | `float` | elapsed show time (seconds) |
| `iIntensity` | `float` | 0–1 derived from garden activity |

All four scenes are **authored/adapted for Shadertoy first** (using `mainImage()` + `fragCoord`),
then trivially ported by wrapping in `void main()` with the custom uniform names. This lets the
author iterate visually on [shadertoy.com](https://www.shadertoy.com) and paste the final result.

| file | aesthetic |
|---|---|
| `bloom.glsl` | slow organic spiral growth (already exists) |
| `fractal.glsl` | recursive geometric fractal (IFS / folded-space) |
| `mycelium.glsl` | branching network propagation, organic tendrils |
| `cosmos.glsl` | stellar nebula drift, gas clouds, slow starfield |

### Wayland compositor

The Pi runs Raspberry Pi OS Lite — no desktop session, no Wayland compositor. Rather than
injecting socket variables and hoping a compositor exists, the renderer is wrapped in `cage`:

```
/usr/bin/cage -- /usr/bin/python3 renderer.py
```

`cage` is a minimal kiosk Wayland compositor (wlroots-based) that runs a single application
fullscreen and exits when it does. It sets `WAYLAND_DISPLAY` for the renderer child process automatically.
`XDG_RUNTIME_DIR` must still be set in the unit file — cage uses it to create the socket.

This also enables multiple independent displays: a second cage instance with `-d <output>`
runs a second renderer on a different physical screen, each managed by its own systemd unit.

`MESA_GL_VERSION_OVERRIDE=3.3` is set in the unit file (inherited by cage → renderer) and also
inside `renderer.py` as a belt-and-braces measure before any GL library loads.

---

## Consequences

- Renderer crash does not crash the coordinator; OSC messages continue to send and are simply
  dropped until the renderer is back.
- The `--no-renderer` flag is required when running on a dev machine without a display (e.g. CI,
  WSL). All existing `--no-*` flags already follow this pattern.
- `requirements.txt` already covers all renderer deps (`python-osc`, `moderngl`, `pyglet`,
  `numpy`). No new pip packages required.
- `install.sh` installs deps from `requirements.txt` and writes the service file — no changes
  needed beyond the env var additions to the service template.

---

## Implementation plan

1. **`looking_glass/fractal.glsl`** — folded-space IFS fractal, green/gold palette matching bloom.
2. **`looking_glass/mycelium.glsl`** — reaction-diffusion–style branching tendrils.
3. **`looking_glass/cosmos.glsl`** — layered fbm noise nebula + procedural starfield.
4. **`main.py`** — add `--no-renderer` flag; add `_renderer_subprocess` async task that spawns
   `renderer.py`, watches exit code, relaunches with back-off, terminates cleanly on shutdown.
5. **`deploy/treehouse.service`** — add four `Environment=` lines for Wayland + MESA vars.

No changes needed to:
- `requirements.txt` (deps already present)
- `coordinator.py` / `displays/video.py` (already wired)
- `settings.json` (looking_glass block already present)
