# TreeHouse

The Hub Element. A 9.5-foot structure with dioramas, branch motors, and dual screens that reflect the aggregate **Garden State**.

**Host:** `treehouse` · 192.168.1.10 · **Visualizer:** http://192.168.1.10:8766 · **Service:** `treehouse`

---

## Architecture summary

`main.py` runs an asyncio loop that ticks every `Controllable` once per frame (the Looking Glass and the Branches, which send their motor commands over USB serial) and sends Garden State to the location controllers over WiFi. Each frame, `Coordinator.update()` takes `SignalIntake.snapshot()` (the OSC signals, with silent senders zeroed), adds show mode and brightness, and hands the resulting Garden State to every `Controllable` alike.

Hardware:
- 5× ESP32-S3 location controllers (WiFi/OSC) — Swannatopia, Julia, Jess, Dormer, Garage (ADR-0020, ADR-0021). They drive every LED in the TreeHouse. The Pi sends them Garden State, not pixels; they animate themselves, and for now ignore what the Pi sends (see [Location controllers](#location-controllers)).
- 1× branch controller (USB serial) — Dynamixel servos via lead screws for the 4–6 motorised roof Branches (ADR-0005)
- 2× HDMI displays — Looking Glass renderer (1024×600) and Club diorama screen (800×480) (ADR-0017, ADR-0018)

The TreeHouse is the **Hub** of the OSC Fabric: `osc_server.py` receives the Elements' signals and `SignalIntake` folds them into `GardenState`, which is passed to every Controllable each frame (ADR-0006, ADR-0007, ADR-0008). The addresses are under [OSC interface](#osc-interface).

Display rendering — both screens run under a single `weston` compositor started by `main.py` (ADR-0018). Each screen is a child asyncio subprocess with exponential backoff. The renderers use `pygame + moderngl` against SDL2 with `SDL_VIDEODRIVER=wayland`. Output assignment is by resolution match against `pygame.display.get_desktop_sizes()`.

Key references:
- ADR-0005 — branch controller USB serial
- ADR-0006 — two-tier Controllable hierarchy
- ADR-0007 — OSC Fabric schema
- ADR-0008 — GardenState → display expression mapping
- ADR-0017 — Club diorama rave screen
- ADR-0018 — pygame/weston dual-display
- ADR-0020 — ESP32-S3 location controllers (supersedes ADR-0010)

Files in `ShowControl/TreeHouse/`:

| File | What it holds |
|---|---|
| `main.py` | Flags, weston, the renderer subprocesses and the frame loop |
| `treehouse_config.py` | `settings.json` + `network.json` → `TreehouseConfig` |
| `osc_server.py` | The Fabric listener |
| `garden_state.py` | `SignalIntake`: the OSC signals, stale-sender expiry, `snapshot()` |
| `coordinator.py` | `Coordinator`: intake → `GardenState` → every `Controllable`; show mode and dim level |
| `controllables/base.py` | `GardenState`, `ShowMode`, `Controllable`, `ControllableState` |
| `controllables/video.py` | `LookingGlassControllable` |
| `branches.py` | `branch_positions()` maths, `BranchDriver` serial driver, `BranchController` (a `Controllable`) |
| `location_sender.py` | `LocationSender`: Garden State to the location controllers |
| `looking_glass/renderer.py`, `looking_glass/*.glsl` | The Looking Glass renderer subprocess and its scenes |
| `club_screen.py`, `club_messages.txt` | The Club screen subprocess and its messages |
| `visualizer.py` | State snapshot and the `/control/*` routes the Dashboard page posts to, on a `ShowWeb.LiveServer` |

---

## `main.py` flags

| Flag | Effect |
|---|---|
| `--config <path>` | Settings file (default `settings.json`) |
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
- `XDG_RUNTIME_DIR=/run/user/<uid of the service user>` + `ExecStartPre` creates it (weston needs a runtime dir); `install.sh` fills in the uid
- `LIBSEAT_BACKEND=seatd` (weston needs seat management — `seatd.service` is enabled by `install.sh`)
- `MESA_GL_VERSION_OVERRIDE=3.3` + `MESA_GLSL_VERSION_OVERRIDE=330` (moderngl needs GL3.3 core)
- `SupplementaryGroups=dialout` (branch controller USB)

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

To see which outputs the kernel found: `dmesg | grep -i hdmi`.

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

## Branch USB

USB devices appear as `/dev/ttyACMx` in plug order, so a udev symlink pins the branch controller by serial:

| Symlink | Device |
|---|---|
| `/dev/treehouse-branches` | Branch controller (Dynamixel) |

`settings.json` references this symlink. First-time setup is in [bootstrap.md → TreeHouse host](bootstrap.md#treehouse-host).

---

## Controllable model

Every output the Pi drives itself is a `Controllable` (ADR-0006) with `update(dt, state: GardenState)` + `get_state()`. `build_controllables()` in `coordinator.py` makes two: the Looking Glass (`LookingGlassControllable`) and the Branches (`BranchController`). The LEDs are not Controllables: each location's ESP32-S3 controller receives Garden State from `location_sender.py` and animates itself.

`GardenState` and its fields are defined in `controllables/base.py`. Each Controllable decides which fields it reads — see ADR-0008:

- **Looking Glass:** intensity is the mean of the three Element signals, times `brightness`.
- **Branches:** each motor blends the three signals by its `weights` between `min_pos` and `max_pos`; on a frame with `captcha_blowup` set it goes to `recoil_pos`.
- **Location controllers:** a Blow-Up adds a spike that decays on the controller. Not live while the controllers ignore Garden State (below).

---

## Location controllers

Five ESP32-S3 controllers (ADR-0020) light Swannatopia, Julia, Jess, the Dormer and the Garage. `location_sender.py` sends Garden State to all of them, `locations.send_hz` times a second, under the Fabric send rule ([`osc-fabric.md`](osc-fabric.md#when-a-signal-is-sent)). Blow-Ups are never rate-limited.

**The controllers currently ignore Garden State** (ADR-0021): `kFollowGardenState` in `Firmware/TreeHouse_Controllers/src/main.cpp` is `false`, so each animates as if every Element were at full, whatever the Pi sends, and the 10 s no-signal fallback is off. Setting it to `true` and reflashing puts the Pi back in charge.

Addresses come from the `firmware` block of `network.json`; `settings.json` names the controllers but never their addresses.

| Location | Channels | IP |
|---|---|---|
| Swannatopia | 3× SK6812 RGBW | 192.168.1.60 |
| Julia | 1× PWM MOSFET (12 V filaments) | 192.168.1.61 |
| Jess | 2× SK6812 RGBW + 1× PWM MOSFET flash | 192.168.1.62 |
| Dormer | 1× PWM MOSFET (12 V) | 192.168.1.63 |
| Garage | 1× cap-discharge arc trigger + 16× SK6812 RGBW | 192.168.1.64 |

Firmware, each location's look and bench-testing recipes: `Firmware/TreeHouse_Controllers/README.md`.

---

## OSC interface

The TreeHouse is the only Fabric listener (`osc_server.py`, on `elements.treehouse.osc_port`). It receives `/flowerbeds/activity`, `/captcha/intensity`, `/captcha/blowup`, `/pipes/activity`, `/treehouse/mode`, `/treehouse/brightness` and `/lookingglass/scene`, sends the first six on to the location controllers, and drives the Looking Glass renderer with `/lookingglass/*` (above). Arguments, senders and the send rule: [`osc-fabric.md`](osc-fabric.md).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Both screens off | weston didn't start or both HDMI unplugged | `journalctl -u treehouse -b` — look for `weston exited`; check cables; `dmesg | grep -i hdmi` |
| One screen blank | renderer crash-looping | `journalctl -u treehouse -f` and look for `Renderer crashed` lines; check shader compile errors |
| Wrong content on each screen | both screens at the same resolution (no resolution match) | Fix `weston.ini` modes, or change one display's resolution |
| A location ignoring show mode and activity | Expected for now: the controllers ignore Garden State (ADR-0021) | Nothing to fix. With `kFollowGardenState` on, a location that slowly breathes has heard nothing for 10 s: check the Pi is running without `--no-locations`, then `ping` the controller's IP from `network.json` |
| A location dark, others fine | That controller is off or unflashed | Watch its serial heartbeat: `pio device monitor -b 115200` from `Firmware/TreeHouse_Controllers` |
| Branches not moving | branch controller serial port closed | Check `/dev/treehouse-branches`; restart service |
| OSC Fabric silent | `network.json` missing | The service keeps running and logs `network.json not found at … — running without show-network addresses` |
| Renderer stuck on old scene | shader compile failure on the last scene change | The journal has `Shader swap failed` with the GLSL error; fix the shader and select the scene again |
