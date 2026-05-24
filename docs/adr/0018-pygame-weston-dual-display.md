# ADR-0018 — pygame/SDL2 + weston for dual-display rendering

**Status:** Accepted  
**Supersedes:** ADR-0014 (compositor and renderer sections)

---

## Context

ADR-0014 established `cage` as the Wayland compositor for the Looking Glass renderer, with
`pyglet` as the windowing/OpenGL library. The Club diorama screen (ADR-0017) added a second
renderer subprocess using the same cage-launch pattern.

This failed at runtime: both HDMI outputs share a single DRM device (`card0` on the Pi 5).
`cage` requires exclusive DRM master, so two cage instances fight for the seat — one wins,
the other crashes in a restart loop.

Attempted workaround via `weston` + `Xwayland` (to satisfy pyglet's xlib-only backend) also
failed: `pyglet 2.1.x` on this Pi has no Wayland backend and always imports `xlib`, requiring
Xwayland to provide a `DISPLAY`. This worked but made output assignment non-deterministic
(kiosk-shell assigns outputs by connection order, and pyglet/Xwayland was slower to connect
than the SDL2 club screen, consistently landing on the wrong physical output).

---

## Decision

### Compositor

Run a single `weston` instance managing both HDMI outputs. `main.py` starts weston before
any renderer subprocess, waits for its Wayland socket, sets `WAYLAND_DISPLAY` in the process
environment, then launches both renderers. weston is supervised; if it exits, the whole
treehouse service crashes and systemd restarts it.

`weston.ini` (in `looking_glass/deploy/`) declares both outputs explicitly:

```ini
[core]
idle-time=0
shell=kiosk-shell.so

[output]
name=HDMI-A-1
mode=1024x600

[output]
name=HDMI-A-2
mode=800x480
```

### Renderer stack

Both renderers use **pygame + SDL2** with `SDL_VIDEODRIVER=wayland`. This is the same stack
already in use for the club screen (ADR-0017); the Looking Glass renderer is ported from
`pyglet + numpy` to `pygame + moderngl`.

`numpy` is removed from the renderer — the quad vertex buffer is written with `struct.pack`.

### Output assignment

Each renderer selects its target display by matching resolution against
`pygame.display.get_desktop_sizes()`:

- Looking Glass renderer: finds the 1024×600 output → HDMI-A-1
- Club screen: finds the 800×480 output → HDMI-A-2

SDL2 passes the resolved `wl_output` object to weston via
`xdg_toplevel.set_fullscreen(output)`. weston kiosk-shell honours this, making assignment
independent of subprocess startup order or connection timing.

### No Xwayland

Xwayland is not used. `DISPLAY` is explicitly unset in the treehouse process after weston
starts to prevent any SDL2 fallback to xlib.

### Process model (unchanged from ADR-0014)

Both renderers remain asyncio subprocesses of `main.py`, watched with exponential backoff.
`--no-renderer` and `--no-club-screen` flags skip the respective subprocess; both being
absent skips weston entirely.

---

## Consequences

- Single systemd unit (`treehouse`) manages both displays — `looking_glass.service` is
  obsolete and must not be installed.
- `install.sh` installs `weston` (not `cage`); pip deps are `moderngl pygame python-osc`
  (not `pyglet numpy`).
- GLSL shaders, OSC IPC, and uniform interface are unchanged.
- Output assignment is deterministic as long as both screens are connected and weston
  enumerates them at the declared resolutions. If a screen is absent, `_find_display()`
  falls back to index 0 with a warning.
- The `--no-renderer` / `--no-club-screen` dev flags still work; weston is only started
  when at least one renderer subprocess is enabled.
