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
| `captcha` | FundingCAPTCHA | `ShowControl/FundingCAPTCHA/app.py` | 8080 (monitoring) | 192.168.1.12 |
| `cg-dashboard` | Show Dashboard | `ShowControl/Dashboard/serve.py` | 9000 | 192.168.1.10 |
| `pipes` | Playing the Pipes | `ShowControl/PlayingThePipes/` + Max/RNBO | 8767 (health) | 192.168.1.13 (Windows) |

Playing the Pipes runs on a **Windows mini PC** (not Linux). Service supervision uses NSSM or Task Scheduler instead of systemd — see [Playing the Pipes](#playing-the-pipes) below.

---

## Quick start (first deploy)

Run on each show computer **as root** after cloning the repo. Pass the element(s) installed on that machine — the script requires at least one:

```bash
sudo bash scripts/install-services.sh FlowerBeds
sudo bash scripts/install-services.sh FundingCAPTCHA
# Multiple at once (rare — each Pi normally runs one element):
sudo bash scripts/install-services.sh FlowerBeds TreeHouse
```

Each element's `deploy/install.sh` can also be run independently:

```bash
cd ShowControl/FlowerBeds/deploy
sudo bash install.sh
```

### What the install script does

1. Installs Python dependencies (`pip3 install --break-system-packages -r requirements.txt`; `python3-numpy` and `python3-scipy` first via apt where available)
2. Copies the service file to `/etc/systemd/system/`, patching `User=` to the invoking user
3. Runs `systemctl daemon-reload` + `systemctl enable` + `systemctl restart`

The service user defaults to the invoking user (`$SUDO_USER`) and falls back to `ii`. `WorkingDirectory=` in the unit is hard-coded to `/home/ii/CommunityGarden/...` — edit the service file if the repo lives elsewhere.

FundingCAPTCHA's `install.sh` additionally drops an Orbbec udev rule (`/etc/udev/rules.d/99-orbbec.rules`) and reloads udev. FlowerBeds' `install.sh` does not — see [Orbbec camera udev rules](#orbbec-camera-udev-rules) if the FlowerBeds camera fails to open.

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
python app.py
```

---

## Running without hardware

Every element has a dev mode — no camera, no LEDs, no servos required.

| Element | Dev flag(s) |
|---|---|
| TreeHouse | `--no-pico --no-branch --no-renderer` |
| FlowerBeds | `--mock-camera --no-osc` |
| FundingCAPTCHA | `--mock-camera` or `--test-input` (see ADR-0016) |

```bash
python3 main.py --no-pico --no-branch --no-renderer   # TreeHouse, no hardware or display
python3 main.py --mock-camera --no-osc                # FlowerBeds, no camera or servos
python3 app.py --mock-camera                          # FundingCAPTCHA, synthetic depth frames
python3 app.py --test-input                           # FundingCAPTCHA, mouse-paint depth frames
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

#### Layout tool (operator laptop)

Module positions are configured visually with a browser GUI run on the operator's Windows laptop (ADR-0015). The ArUco-marker auto-layout (ADR-0009) is superseded — no markers, no overhead RGB pass, no `layout_calibrated.json`.

`settings.json` is the single source of layout at runtime. The tool reads/writes only `coordinator.modules[]` and backs up `settings.json.bak` before each save.

**Run it:**

```powershell
cd ShowControl\FlowerBeds
python layout_tool.py
# opens http://localhost:8764
```

Key features:

- Drag-place modules on a top-down canvas; rotate handle or numeric input for yaw
- Per-cluster motor ID editing (defaults are sequential placeholders — always override)
- **Manual aim** mode: click on canvas → sends `/cg/ff/rot [motor_id, yaw_deg]` directly to the controller IP from `network.json`
- **Test move** per cluster: sends 30° → 0° to confirm the motor responds
- Controller status: TCP-ping the controllers' OSC port every 10 s

The laptop must be on the show network for manual aim and controller-status features. Save and offline editing work without network.

After saving, restart the show:

```bash
sudo systemctl restart flowerbeds
```

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

The Pi runs Raspberry Pi OS Lite — no desktop session. `main.py` starts a single `weston` compositor before launching the Looking Glass renderer and Club screen subprocesses (ADR-0018 — supersedes the previous `cage` setup). Both renderers run under `SDL_VIDEODRIVER=wayland`; each picks its target output by resolution match against `pygame.display.get_desktop_sizes()`.

Install:

```bash
sudo apt install weston libgl1-mesa-dri
```

The service user (`ii`) must be in the `video` and `render` groups for DRM access (handled by `SupplementaryGroups=video render` in the unit file). `weston.ini` lives in `looking_glass/deploy/` and declares both HDMI outputs explicitly. If only one screen is connected, weston still starts and the renderer that can't find its declared resolution falls back to index 0 with a warning.

List available outputs from a running weston session: `wlr-randr`. Or check kernel logs: `dmesg | grep -i hdmi`.

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

### Playing the Pipes

- **Machine:** Windows mini PC at `192.168.1.13` — **not Linux**; systemd commands do not apply
- **Audio engine:** Cycling '74 Max/RNBO (Max for Windows)
- **USB serial:** Two Pi Picos connect via USB and appear as Windows COM ports (e.g. `COM3` / `COM4`). Configure the port names in Max's `serial` object. COM port numbers are not stable by default — assign fixed numbers in Device Manager (Properties → Port Settings → Advanced → COM Port Number) and record them here once assigned.
- **Health endpoint:** A standalone Python http server (`ShowControl/PlayingThePipes/health_server.py`) serves `GET /health` on port 8767. This must be running for the Dashboard to show Pipes as online.
- **Service supervision:** No systemd. Use **NSSM** (Non-Sucking Service Manager) to run both the health server and Max as Windows services with auto-restart. Alternatively, Task Scheduler with `On startup` trigger.

**First-time service install (NSSM):**

Download NSSM from https://nssm.cc, place `nssm.exe` somewhere on `PATH`, then run once in an admin PowerShell:

```powershell
nssm install pipes-health python
nssm set pipes-health AppParameters "C:\CommunityGarden\ShowControl\PlayingThePipes\health_server.py"
nssm set pipes-health AppDirectory  "C:\CommunityGarden\ShowControl\PlayingThePipes"
nssm set pipes-health AppStdout     "C:\logs\pipes-health.log"
nssm set pipes-health AppStderr     "C:\logs\pipes-health.log"
nssm set pipes-health Start         SERVICE_AUTO_START
nssm start pipes-health
```

**Manual startup (dev):**

```powershell
cd ShowControl\PlayingThePipes
pip install -r requirements.txt
python health_server.py

# Max — open the patch manually or via CLI
"C:\Program Files\Cycling '74\Max 9\Max.exe" PlayingThePipes.maxpat
```

**Service management (NSSM):**

```powershell
# Status
nssm status pipes-health

# Restart
nssm restart pipes-health

# Logs
Get-Content C:\logs\pipes-health.log -Tail 50
```

**Updating the software:**

```powershell
cd C:\CommunityGarden
git pull
# Restart health server service
nssm restart pipes-health
# Reload Max patch manually
```

**COM port identification (first-time setup):**

```powershell
# List all COM ports
[System.IO.Ports.SerialPort]::GetPortNames()
# Or: Device Manager → Ports (COM & LPT)
```

Plug Picos in one at a time, note which COM port appears, label each Pico and record here:

| Pico | Board ID | COM port |
|------|----------|----------|
| Board 0 | 0 | TBD |
| Board 1 | 1 | TBD |

---

### FundingCAPTCHA

- **Hardware:** Orbbec depth camera (USB), short-throw laser projector
- **Service:** One unit — `captcha` runs `app.py`, a single pygame process that owns the projector display, camera pipeline, BG calibration, game rotation, and a lightweight monitoring HTTP/WebSocket server on port 8080 (ADR-0012). No browser, no kiosk service.
- **Flags:** Edit `/etc/systemd/system/captcha.service` to switch `--camera` → `--mock-camera` (synthetic depth frames) or `--test-input` (mouse-paint depth frames; ADR-0016).
- **Settings:** `captcha-settings.json` (main config — camera, depth slabs, ROI, screensaver list, OSC targets). `captcha-settings.local.json` overrides for per-machine tweaks.
- **Level assets:** Per-game JSON files alongside `app.py` — `bodycaptcha-levels.json`, `keepaway-body-levels.json`, plus `taunts.json` / `keepaway-body-taunts.json` and `screensavers.json`. Photos live in `ShowControl/FundingCAPTCHA/images/`. The standalone Windows BodyCaptcha editor for non-git teammates lives in `distribution/` (see `distribution/README.md`).

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

FundingCAPTCHA's `install.sh` writes `/etc/udev/rules.d/99-orbbec.rules` (vendor `2bc5`, product `0807`, `MODE="0666"`) automatically. FlowerBeds' `install.sh` does **not** — install the rule manually on the FlowerBeds Pi if the camera fails to open:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2bc5", ATTR{idProduct}=="0807", MODE="0666"' \
    | sudo tee /etc/udev/rules.d/99-orbbec.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

If your Orbbec device has a different product ID, the SDK ships its own rules file inside the `pyorbbecsdk2` package:

```bash
python3 -c "import pyorbbecsdk2, os; print(os.path.dirname(pyorbbecsdk2.__file__))"
# Copy the .rules file from that path to /etc/udev/rules.d/ and reload.
```

---

## Open questions / future work

- **Playing the Pipes**: runs on Windows — needs `ShowControl/PlayingThePipes/health_server.py` (Python/FastAPI, port 8767), NSSM service config, and Max patch wired to health state. `scripts/install-services.sh` does not cover this machine; a separate Windows setup script or NSSM config export is needed.
- **Multi-machine deploy**: the install script currently runs locally. A simple Ansible playbook or `pdsh` wrapper would let a single operator re-deploy all machines simultaneously.
- **Health monitoring**: `Restart=always` handles crashes but doesn't alert operators. A lightweight watchdog that posts to a Slack/Discord webhook on repeated restarts would improve unattended operation.
- **Orbbec SDK version pinning**: `pyorbbecsdk2` must match the SDK `.so` installed on the host. Document the exact version pairing per machine if they diverge.
