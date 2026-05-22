# Operations Guide

Process supervision and deployment for CommunityGarden show-control software.

---

## Prerequisites

- Python 3.11+
- Git

Each show element has its own `requirements.txt`. Install them separately — they don't share a virtualenv.

---

## Services overview

Each show-control element runs as a systemd service with `Restart=always` and `RestartSec=5`, so it recovers automatically from crashes without operator intervention.

| Service | Element | Entry point | Default port | Host |
|---|---|---|---|---|
| `flowerbeds` | FlowerBeds | `ShowControl/FlowerBeds/main.py` | 8765 (viz) | 192.168.1.11 |
| `treehouse` | TreeHouse | `ShowControl/TreeHouse/main.py` | 8766 (viz) | 192.168.1.10 |
| `captcha` | FundingCAPTCHA | `ShowControl/FundingCAPTCHA/server.py` | 8080 | 192.168.1.12 |
| `captcha-kiosk` | FundingCAPTCHA kiosk | Chromium (kiosk mode) | — | 192.168.1.12 |
| `cg-dashboard` | Show Dashboard | `ShowControl/Dashboard/serve.py` | 9000 | 192.168.1.10 |

Playing the Pipes does not yet have a service file; one will be added once the element stub exists.

---

## Quick start (first deploy)

Run on each show computer **as root** after cloning the repo:

```bash
sudo bash scripts/install-services.sh
```

To install only specific elements:

```bash
sudo bash scripts/install-services.sh FlowerBeds TreeHouse
```

Each element's `deploy/install.sh` can also be run independently:

```bash
cd ShowControl/FlowerBeds/deploy
sudo bash install.sh
```

### What the install script does

1. Installs Python dependencies (`pip3 install -r requirements.txt`)
2. Copies the service file to `/etc/systemd/system/`, patching the working directory to match the actual repo location
3. Runs `systemctl enable` + `systemctl restart`

The service user defaults to the invoking user (`$SUDO_USER`) and falls back to `ii`.

---

## Manual startup (dev / local)

Run each element from its own terminal without systemd. All elements are independent; start only what you need.

### Dashboard
```bash
cd ShowControl/Dashboard
python serve.py
# → http://<your-ip>:9000
```

### TreeHouse
```bash
cd ShowControl/TreeHouse
pip install -r requirements.txt
python main.py
```

### FlowerBeds
```bash
cd ShowControl/FlowerBeds
pip install -r requirements.txt
python main.py --config settings.json
```

### FundingCAPTCHA
```bash
cd ShowControl/FundingCAPTCHA
python server.py
```

---

## Running without hardware

Every element has a dev mode — no camera, no LEDs, no servos required.

| Element | Dev flag(s) |
|---|---|
| TreeHouse | `--no-pico --no-branch --no-renderer` |
| FlowerBeds | `--mock-camera --no-osc` |
| FundingCAPTCHA | `--mock-camera` |

```bash
python3 main.py --no-pico --no-branch --no-renderer   # TreeHouse, no hardware or display
python3 main.py --mock-camera --no-osc                # FlowerBeds, no camera or servos
python3 server.py --mock-camera                       # FundingCAPTCHA, no depth camera
```

---

## Viewing logs

```bash
# Follow live logs for an element
journalctl -u flowerbeds -f
journalctl -u treehouse -f
journalctl -u captcha -f

# Show logs since last boot
journalctl -u flowerbeds -b

# Show logs from all CommunityGarden services together
journalctl -u flowerbeds -u treehouse -u captcha -u cg-dashboard -f
```

---

## Service management

```bash
# Status
sudo systemctl status flowerbeds
sudo systemctl status treehouse
sudo systemctl status captcha

# Restart an element (e.g. after a config change)
sudo systemctl restart flowerbeds

# Stop / start
sudo systemctl stop flowerbeds
sudo systemctl start flowerbeds

# Disable auto-start on boot
sudo systemctl disable flowerbeds
```

---

## Per-element notes

### FlowerBeds

- **Hardware:** Orbbec depth camera (USB), Arduino OSC controllers (network)
- **USB groups:** The service user must be in `video` and `plugdev` groups (added by `install.sh` via `SupplementaryGroups`)
- **Depth calibration:** On first start the camera captures `calibration_frames` (default 60) to build a background model. This takes several seconds; `Restart=always` handles spurious camera-open failures.
- **Flags:** Edit `/etc/systemd/system/flowerbeds.service` and add `--no-osc` (no Arduino), `--no-visualizer` (headless), or `--mock-camera` (software testing), then `sudo systemctl daemon-reload && sudo systemctl restart flowerbeds`
- **Visualizer:** `http://<host>:8765/` — live top-down blob view

#### Layout calibration (ArUco auto-layout)

The physical position and orientation of each flower module can be auto-detected from ArUco markers placed at each module's registration point, rather than measured and typed into `settings.json` by hand. Use this any time modules are repositioned.

**What you need**

- 12 printed ArUco markers, **DICT_4X4_50**, one per module, **40 cm square** (laminate if possible)
- Each module's `marker_id` in `settings.json` must match the printed tag ID (IDs 0–11 by default)
- The Orbbec camera must be mounted and powered (layout calibration uses the color sensor)

**Tag orientation convention**

Point the **top edge of the tag** (the edge opposite the printed ID number) toward the direction you want the module's flowers to face at rest. That direction becomes `yaw = 0°` for that module.

**Step-by-step workflow**

1. Place all tags flat on the floor at each module's registration point, oriented as above.
2. Run layout calibration (choose one):
   - **CLI:** `python main.py --config settings.json --layout-calibrate`
   - **Dashboard:** open `http://<show-ip>:8765/` and click **Layout Calibrate**
3. Wait ~3 seconds while the camera captures 30 frames (progress shown in the visualizer).
4. Remove all tags.
5. Restart (or continue) the show normally — `layout_calibrated.json` is loaded automatically.

The visualizer's **CAL:** badge turns green and shows `layout_calibrated` when done. Any module whose tag wasn't detected keeps its existing position from `settings.json`; a warning is logged.

**Files**

| File | Purpose |
|---|---|
| `settings.json` | Manual/default positions — versioned, never overwritten by calibration |
| `layout_calibrated.json` | Auto-detected overrides — gitignored, auto-loaded at startup |

Delete `layout_calibrated.json` to revert to the manual positions in `settings.json`.

**Recalibrating after a move**

Stop the service, re-place tags, run `--layout-calibrate` again, remove tags, restart. The new `layout_calibrated.json` replaces the old one.

```bash
sudo systemctl stop flowerbeds
python main.py --config settings.json --layout-calibrate
sudo systemctl start flowerbeds
```

Or trigger from the dashboard without stopping the service — the show pauses ~3 s and resumes automatically with the updated layout.

### TreeHouse

- **Hardware:** Raspberry Pi (Debian/Ubuntu), two Pi Picos (LED) + one branch controller over USB serial
- **USB groups:** The service user must be in `dialout` group (added by `install.sh`)
- **Flags:** Add `--no-pico` to skip serial connections (dev mode)
- **Visualizer:** `http://<host>:8766/` — live display state view

#### Looking Glass renderer

The renderer (`looking_glass/renderer.py`) runs as a **child process of the treehouse service** — not its own systemd unit. `main.py` spawns it on start, watches its exit code, and relaunches it with exponential back-off (1 s → 2 s → 4 s … cap 30 s) on crash. Renderer crashes do not crash the coordinator; OSC messages are simply dropped until the renderer is back.

**Restart the renderer** (without restarting the coordinator):

```bash
# Kill the renderer process — the coordinator will relaunch it automatically
sudo pkill -f looking_glass/renderer.py
```

**Restart everything** (coordinator + renderer):

```bash
sudo systemctl restart treehouse
```

**Run without a display** (dev machines, CI, WSL):

```bash
python3 main.py --no-pico --no-branch --no-renderer
```

**Run the renderer in isolation** (shader development):

```bash
cd ShowControl/TreeHouse
python3 -m looking_glass.renderer
# or
python3 looking_glass/renderer.py
```

The renderer opens fullscreen on whatever display is active. Send OSC to `127.0.0.1:9002` to control it:

| OSC address | Value | Effect |
|---|---|---|
| `/lookingglass/scene` | `bloom` / `fractal` / `mycelium` / `cosmos` | Switch shader |
| `/lookingglass/time` | float (seconds) | Show elapsed time |
| `/lookingglass/intensity` | float 0–1 | Drive brightness/activity |

Example with `oscsend` (from `liblo-tools`):

```bash
oscsend osc.udp://127.0.0.1:9002 /lookingglass/scene s cosmos
oscsend osc.udp://127.0.0.1:9002 /lookingglass/intensity f 0.8
```

**Renderer logs** appear in the treehouse journal (no separate unit):

```bash
journalctl -u treehouse -f | grep looking_glass
```

**Adding or editing shaders:**

1. Write a `.glsl` file in `ShowControl/TreeHouse/looking_glass/` using these uniforms:
   ```glsl
   #version 330
   uniform vec2  iResolution;   // viewport px
   uniform float iTime;         // show elapsed seconds
   uniform float iIntensity;    // 0–1 activity level
   out vec4 fragColor;
   ```
2. Name it `<scene>.glsl`. The renderer accepts the name via `/lookingglass/scene`.
3. Prototype on [shadertoy.com](https://www.shadertoy.com) using `mainImage()` + `fragCoord`, then port by replacing those with the uniforms above and `void main()`.
4. Hot-reload: send `/lookingglass/scene <name>` via OSC — no restart needed. If the shader fails to compile the renderer logs the error and stays on the previous scene.

**Wayland compositor (systemd context):**

The Pi runs Raspberry Pi OS Lite — no desktop session, no compositor. The renderer is wrapped in `cage`, a minimal Wayland kiosk compositor that runs a single app fullscreen and provides the Wayland socket itself:

```
ExecStart=/usr/bin/cage -- /usr/bin/python3 renderer.py
```

cage must be installed: `sudo apt install cage libgl1-mesa-dri`

The service user (`ii`) must be in the `video` and `render` groups for DRM access (handled by `SupplementaryGroups=video render` in the unit file).

**Multiple displays:** run a second cage instance targeting the other output. To target a specific output, add the `-d` flag:

```
ExecStart=/usr/bin/cage -d HDMI-A-2 -- /usr/bin/python3 renderer.py
```

List available outputs: `wlr-randr` (run from inside a cage session) or check kernel logs (`dmesg | grep -i hdmi`).

#### USB device naming (udev)

Three USB serial devices attach to the TreeHouse Pi. Linux enumerates `/dev/ttyACMx` in plug order — not stable across reboots. Udev rules map each device's USB serial number to a fixed symlink:

| Symlink | Device | Channels |
|---|---|---|
| `/dev/treehouse-pico-a` | Pico A (dioramas) | House Swarming, Club, Mycelium, F&F arc, F&F bloom |
| `/dev/treehouse-pico-b` | Pico B (structure) | Dormer, Porch Lights, Attic TV & Lamps |
| `/dev/treehouse-branches` | Branch controller | Dynamixel branch motors |

`settings.json` references these symlinks — never `/dev/ttyACMx` directly.

**First-time setup (run once per machine):**

```bash
# Find the USB serial numbers of each Pico/controller while plugged in one at a time:
udevadm info -a -n /dev/ttyACM0 | grep 'ATTRS{serial}'

# Then add to /etc/udev/rules.d/99-treehouse.rules:
SUBSYSTEM=="tty", ATTRS{serial}=="<pico-a-serial>", SYMLINK+="treehouse-pico-a"
SUBSYSTEM=="tty", ATTRS{serial}=="<pico-b-serial>", SYMLINK+="treehouse-pico-b"
SUBSYSTEM=="tty", ATTRS{serial}=="<branch-serial>", SYMLINK+="treehouse-branches"

sudo udevadm control --reload-rules && sudo udevadm trigger
```

Record the serial numbers in `ShowControl/network.json` under `"firmware"` so they are not lost.

### FundingCAPTCHA

- **Hardware:** Orbbec depth camera (USB, optional), Chromium kiosk browser
- **Services:** Two units — `captcha` (Python server) and `captcha-kiosk` (Chromium browser). The kiosk waits for the server to respond before opening.
- **Flags:** Edit `/etc/systemd/system/captcha.service` to change `--camera` → `--mock-camera` (no hardware) or remove it entirely (pointer-only mode)
- **Uploads:** Photos saved to `ShowControl/FundingCAPTCHA/uploads/`

### Show Dashboard

- **Runs on the TreeHouse machine** (192.168.1.10) — FastAPI server with static HTML pages and a mode-relay OSC endpoint
- Opens at `http://192.168.1.10:9000/` from any browser on the show network
- Reads `ShowControl/network.json` for element IPs and OSC ports — edit that file if addresses change
- `POST /api/mode` relays show mode (`active` / `dim` / `inactive`) to any element via OSC

---

## Updating the software

```bash
cd /home/ii/CommunityGarden   # or wherever the repo lives
git pull

# Restart affected services
sudo systemctl restart flowerbeds treehouse captcha cg-dashboard
```

If Python dependencies changed:

```bash
pip3 install --break-system-packages -r ShowControl/FlowerBeds/requirements.txt
pip3 install --break-system-packages -r ShowControl/TreeHouse/requirements.txt
pip3 install --break-system-packages -r ShowControl/FundingCAPTCHA/requirements.txt
sudo systemctl restart flowerbeds treehouse captcha
```

---

## Orbbec camera udev rules

The Orbbec SDK ships udev rules that grant USB access without root. If the camera doesn't open, install the rules (one-time, per machine):

```bash
# Locate the rules file in the pyorbbecsdk2 package:
python3 -c "import pyorbbecsdk2; import os; print(os.path.dirname(pyorbbecsdk2.__file__))"
# Then copy the .rules file to /etc/udev/rules.d/ and reload:
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## Open questions / future work

- **Playing the Pipes**: once the element stub exists, add `ShowControl/PlayingThePipes/deploy/pipes.service` following the same pattern and add it to `scripts/install-services.sh`.
- **Multi-machine deploy**: the install script currently runs locally. A simple Ansible playbook or `pdsh` wrapper would let a single operator re-deploy all machines simultaneously.
- **Health monitoring**: `Restart=always` handles crashes but doesn't alert operators. A lightweight watchdog that posts to a Slack/Discord webhook on repeated restarts would improve unattended operation.
- **Orbbec SDK version pinning**: `pyorbbecsdk2` must match the SDK `.so` installed on the host. Document the exact version pairing per machine if they diverge.
