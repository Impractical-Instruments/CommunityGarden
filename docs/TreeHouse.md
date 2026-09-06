# TreeHouse

The Hub Element. A 9.5-foot structure with dioramas, branch motors, and dual screens that reflect the aggregate **Garden State**.

**Host:** `treehouse` · 192.168.1.10 · **Visualizer:** http://192.168.1.10:8766 · **Service:** `treehouse`

---

## Architecture summary

`main.py` runs an asyncio loop that ticks every `Controllable` once per frame and forwards the resulting pixel buffers + branch commands over USB serial.

Hardware:
- 4× ESP32-S3 location controllers (WiFi/OSC) — Swannatopia, Julia, Jess, Dormer (ADR-0020). The Pi sends them Garden State, not pixels; they animate themselves.
- 2× Pi Pico (USB CDC) — superseded by the location controllers, still wired until the ESP32-S3 hardware is installed — drive SK6812 RGBW LED strips for the dioramas + structural lights (ADR-0010)
  - Pico A: House Swarming, Club, Mycelium, Forge & Flora (arc, bloom)
  - Pico B: Dormer, Porch Lights, Attic TV & Lamps
- 1× branch controller (USB serial) — Dynamixel servos via lead screws for the 4–6 motorised roof Branches (ADR-0005)
- 2× HDMI displays — Looking Glass renderer (1024×600) and Club diorama screen (800×480) (ADR-0017, ADR-0018)

The TreeHouse is the **Hub** of the OSC Fabric. It listens for `/captcha/intensity`, `/captcha/blowup`, `/flowerbeds/activity`, `/pipes/activity`, `/treehouse/mode`, `/treehouse/brightness` and folds them into `GardenState`, which is passed to every Controllable each frame (ADR-0006, ADR-0007, ADR-0008).

Display rendering — both screens run under a single `weston` compositor started by `main.py` (ADR-0018). Each screen is a child asyncio subprocess with exponential backoff. The renderers use `pygame + moderngl` against SDL2 with `SDL_VIDEODRIVER=wayland`. Output assignment is by resolution match against `pygame.display.get_desktop_sizes()`.

Key references:
- ADR-0005 — branch controller USB serial
- ADR-0006 — two-tier Controllable hierarchy
- ADR-0007 — OSC Fabric schema
- ADR-0008 — GardenState → display expression mapping
- ADR-0010 — TreeHouse LED + Pico architecture
- ADR-0017 — Club diorama rave screen
- ADR-0018 — pygame/weston dual-display
- ADR-0020 — ESP32-S3 location controllers (supersedes ADR-0010)
- `coordinator.py`, `displays/`, `looking_glass/`, `club_screen.py`, `pico_driver.py`, `location_sender.py`, `branch_controller.py`

---

## `main.py` flags

| Flag | Effect |
|---|---|
| `--config <path>` | Settings file (default `settings.json`) |
| `--no-pico` | Skip Pico LED USB connections (dev) |
| `--no-branch` | Skip branch controller USB connection (dev) |
| `--no-osc` | Skip OSC listener |
| `--no-locations` | Skip the ESP32-S3 location controllers (dev) |
| `--no-visualizer` | Disable WebSocket visualizer |
| `--visualizer-port N` | Default 8766 |
| `--no-renderer` | Skip Looking Glass renderer subprocess |
| `--no-club-screen` | Skip Club diorama screen subprocess |
| `--verbose` / `-v` | DEBUG logging |

If both `--no-renderer` and `--no-club-screen` are given, weston is not started.

---

## Service unit notes

`treehouse.service` sets:
- `XDG_RUNTIME_DIR=/run/user/1000` + `ExecStartPre` creates it (weston needs a runtime dir)
- `LIBSEAT_BACKEND=seatd` (weston needs seat management — `seatd.service` is enabled by `install.sh`)
- `MESA_GL_VERSION_OVERRIDE=3.3` + `MESA_GLSL_VERSION_OVERRIDE=330` (moderngl needs GL3.3 core)
- `SupplementaryGroups=dialout` (Pico + branch controller USB)

`After=network-online.target seatd.service systemd-logind.service`

---

## Compositor + weston.ini

Single `weston` instance, both HDMI outputs declared in `ShowControl/TreeHouse/deploy/weston.ini`:

```ini
[core]
idle-time=0
shell=desktop-shell.so

[shell]
panel-location=none
background-type=color
background-color=0xff000000
locking=false

[output]
name=HDMI-A-1
mode=1024x600

[output]
name=HDMI-A-2
mode=800x480
```

If only one screen is connected, weston still starts. The renderer that can't match its resolution falls back to index 0 with a warning in the journal.

List outputs from inside the weston session: `wlr-randr`. Or `dmesg | grep -i hdmi`.

---

## Looking Glass renderer

Lives at `looking_glass/renderer.py`. Runs as a child subprocess of `treehouse` (not its own systemd unit). Crashes are caught by an asyncio task that relaunches with exponential backoff (1 → 2 → 4 … cap 30 s).

Restart just the renderer (coordinator keeps running):

```bash
sudo pkill -f looking_glass/renderer.py
```

Restart in isolation (shader development, no coordinator running):

```bash
cd ShowControl/TreeHouse
python3 -m looking_glass.renderer
```

OSC control (renderer listens on `127.0.0.1:9002`):

| Address | Args | Effect |
|---|---|---|
| `/lookingglass/scene` | `s` (`bloom`/`fractal`/`mycelium`/`cosmos`) | Switch shader |
| `/lookingglass/time` | `f` (seconds) | Show elapsed time |
| `/lookingglass/intensity` | `f` (0–1) | Drive brightness/activity |

Example:
```bash
oscsend osc.udp://127.0.0.1:9002 /lookingglass/scene s cosmos
oscsend osc.udp://127.0.0.1:9002 /lookingglass/intensity f 0.8
```

### Adding shaders

Drop a `<scene>.glsl` in `looking_glass/`. Uniforms:

```glsl
#version 330
uniform vec2  iResolution;
uniform float iTime;
uniform float iIntensity;
out vec4 fragColor;
```

Hot reload: `/lookingglass/scene <name>`. Failed compile → renderer logs the error and stays on the previous scene.

Prototype on shadertoy.com using `mainImage()` + `fragCoord`, then port by replacing those with the uniforms above and `void main()`.

Logs land in the treehouse journal:
```bash
journalctl -u treehouse -f | grep looking_glass
```

---

## Club screen

`club_screen.py` — the second renderer subprocess, drives the Club diorama display (ADR-0017). Same supervision pattern as the Looking Glass renderer.

Restart only:
```bash
sudo pkill -f club_screen.py
```

---

## Pico LED + branch USB

USB devices appear as `/dev/ttyACMx` in plug order, so udev symlinks pin them by serial:

| Symlink | Device |
|---|---|
| `/dev/treehouse-pico-a` | Pico A — dioramas (House Swarming, Club, Mycelium, F&F) |
| `/dev/treehouse-pico-b` | Pico B — structure (Dormer, Porch Lights, Attic TV & Lamps) |
| `/dev/treehouse-branches` | Branch controller (Dynamixel) |

`settings.json` references these symlinks. First-time setup is in [bootstrap.md → TreeHouse host](bootstrap.md#treehouse-host).

---

## Controllable model

Every output is a `Controllable` (ADR-0006) with `update(dt, state: GardenState)` + `get_state()`. LED outputs are `LEDControllable` subclasses that also expose `get_pixels()` returning `ChannelFrame` objects (one per Pico GPIO pin). Each diorama / structural light is its own subclass with its own GardenState-reactive animation.

`GardenState` fields:
- `flowerbeds_activity` (0–1)
- `captcha_intensity` (0–1)
- `captcha_blowup` (bool, one-shot — drives the attic-spike Blow-Up Reaction)
- `pipes_activity` (0–1)
- `show_mode` (`active` / `dim` / `inactive`)
- `brightness` (0–1)

Each Controllable decides which fields it reads — see ADR-0008.

---

## Location controllers

Four ESP32-S3 controllers (ADR-0020) light Swannatopia, Julia, Jess and the Dormer. `location_sender.py` broadcasts Garden State to them each frame at `locations.send_hz`, following the ADR-0007 change/heartbeat rules: a value goes out when it moves past `change_epsilon`, and everything repeats at least once per `heartbeat_interval_s`. Blow-Ups are never rate-limited.

Addresses come from the `firmware` block of `network.json`; `settings.json` names the controllers but never their addresses.

| Location | Channels | IP |
|---|---|---|
| Swannatopia | 3× SK6812 RGBW | 192.168.1.60 |
| Julia | 1× PWM MOSFET (12 V filaments) | 192.168.1.61 |
| Jess | 2× SK6812 RGBW + 1× PWM MOSFET flash | 192.168.1.62 |
| Dormer | 1× PWM MOSFET (12 V) | 192.168.1.63 |

Firmware and bench-testing recipes: `Firmware/TreeHouse_Controllers/README.md`.

---

## OSC interface

Inbound (`/cg/...` are internal; rest are Fabric):

| Address | Args | Source |
|---|---|---|
| `/treehouse/mode` | `s` | Dashboard (mode relay) |
| `/treehouse/brightness` | `f` | operator override |
| `/captcha/intensity` | `f` | FundingCAPTCHA Arc |
| `/captcha/blowup` | — | FundingCAPTCHA Blow-Up event |
| `/flowerbeds/activity` | `f` | FlowerBeds |
| `/pipes/activity` | `f` | Playing the Pipes |
| `/lookingglass/*` | various | renderer OSC server (port 9002) |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Both screens off | weston didn't start or both HDMI unplugged | `journalctl -u treehouse -b` — look for `weston exited`; check cables; `dmesg | grep -i hdmi` |
| One screen blank | renderer crash-looping | `journalctl -u treehouse -f` and look for `Renderer crashed` lines; check shader compile errors |
| Wrong content on each screen | both screens at the same resolution (no resolution match) | Fix `weston.ini` modes, or change one display's resolution |
| LEDs dark | Pico not connected at expected symlink, or `--no-pico` left in unit | Check `/dev/treehouse-pico-a` and `-b` exist; remove `--no-pico` from service file |
| A location slowly breathing, ignoring the show | Controller has heard no Garden State for 10 s | That is the ADR-0020 fallback, not a fault. Check the Pi is running without `--no-locations`, then `ping` the controller's IP from `network.json` |
| A location dark, others fine | That controller is off, unflashed, or `show_mode` is `inactive` | Watch its serial heartbeat: `pio device monitor -b 115200` from `Firmware/TreeHouse_Controllers` |
| Branches not moving | branch controller serial port closed | Check `/dev/treehouse-branches`; restart service |
| OSC Fabric silent | network.json missing | Service falls back gracefully but logs `network.json — OSC disabled` |
| Renderer stuck on old scene | shader compile failure on last `/lookingglass/scene` | journal logs the GLSL error; fix shader, send the address again — hot reload re-tries |
