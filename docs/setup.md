# The Community Garden — Site Setup Guide

For on-site crew. See [Operations Guide](operations.md) for full service management detail.

---

## Machine map

| Element | Machine IP | Key URLs |
|---|---|---|
| Dashboard | 192.168.1.10 | http://192.168.1.10:9000 |
| TreeHouse | 192.168.1.10 | http://192.168.1.10:8766 (visualizer) |
| FlowerBeds | 192.168.1.11 | http://192.168.1.11:8765 (visualizer) |
| FundingCAPTCHA | 192.168.1.12 | http://192.168.1.12:8080 |
| Playing the Pipes | 192.168.1.13 (Windows) | http://192.168.1.13:8767/health |

---

## First-time venue setup

Do once per venue after positioning all elements.

### 1. Network

1. Position and plug in the show switch.
2. Connect all show computers **and** OpenRB-150 controller boards to the switch via Ethernet.
3. **Important:** OpenRB-150 boards must be connected to the switch _before_ powering on — they fail to initialize their network stack if the switch isn't present at boot. ([Known firmware bug #56](https://github.com/Impractical-Instruments/CommunityGarden/issues/56))

### 2. Power on

Power on all hardware in any order — show computers, cameras, Pico, controller boards. Services start automatically and retry until hardware is ready.

### 3. Wait for services (~60 seconds)

FlowerBeds takes the longest — it captures 60 frames to build a background model before tracking begins. All other elements are faster.

### 4. Verify via Dashboard

Open **http://192.168.1.10:9000** from any laptop on the show network. All elements should appear online.

If any element shows offline, see [Troubleshooting](#troubleshooting).

### 5. Run FlowerBeds layout tool (operator laptop)

Required any time flower modules have been repositioned. The layout tool is a browser GUI run on the operator's Windows laptop — see [FlowerBeds setup](#flowerbeds) below.

### 6. Done

Services restart automatically on crash — no babysitting needed.

---

## Show morning (daily)

1. Power everything on — any order is fine.
2. Wait ~60 seconds.
3. Open **http://192.168.1.10:9000** — verify all elements online.
4. If anything is red, see [Troubleshooting](#troubleshooting).

---

## Element setup

### FlowerBeds

**Machine:** `192.168.1.11` | **Visualizer:** http://192.168.1.11:8765

Servo-motor flowers follow visitors using a depth camera.

**Layout tool** — run on the operator's Windows laptop every venue setup after placing flower modules (ADR-0015). The on-pi service does not need to be stopped to use it.

**Steps:**

1. Copy/clone the repo on the operator laptop (or use the prepared installation).
2. Plug the laptop into the show network.
3. From `ShowControl/FlowerBeds/`:
   ```powershell
   python layout_tool.py
   ```
   The tool opens at **http://localhost:8764** (drag modules on the top-down canvas; set yaw with the rotate handle; edit motor IDs per cluster).
4. Use **Test move** / **Hold at …°** per cluster to verify physical motors respond. The tool sends OSC directly to the controller IPs in `network.json`.
5. Click **Save** when done. The tool writes `coordinator.modules[]` into `settings.json` and backs up `settings.json.bak`.
6. Restart the FlowerBeds service so it picks up the new layout:
   ```bash
   sudo systemctl restart flowerbeds
   ```

See [Operations Guide — FlowerBeds](operations.md#flowerbeds) for more detail.

---

### TreeHouse

**Machine:** `192.168.1.10` | **Visualizer:** http://192.168.1.10:8766

Drives LEDs, branch motors, and video displays. Also runs the Dashboard on the same machine.

- Pi Pico connects via USB (`/dev/ttyACM0`). Verify the Pico LED is lit after startup.
- Check the visualizer to see live display state.

**First-time provisioning (once per machine):**

The Looking Glass + Club screen renderers use pygame/SDL2 against weston (ADR-0018). Install weston before running `pip3 install -r requirements.txt`:

```bash
sudo apt-get install -y weston libgl1-mesa-dri
```

See [Operations Guide — TreeHouse](operations.md#treehouse) for more detail.

---

### FundingCAPTCHA

**Machine:** `192.168.1.12` | **Monitoring:** http://192.168.1.12:8080

A single pygame app (`app.py`) owns the projector display, depth camera pipeline, and a lightweight monitoring HTTP/WebSocket server (ADR-0012). No browser, no kiosk service.

**First-time provisioning (once per machine):**

Runs Pi OS Lite — no desktop session. pygame uses `SDL_VIDEODRIVER=kmsdrm` (direct DRM access, no compositor). No extra packages needed beyond what `install.sh` handles; the `render` group is granted at runtime via `SupplementaryGroups` in the service unit.

```bash
cd ShowControl/FundingCAPTCHA/deploy
sudo bash install.sh
```

Verify the projector shows the screensaver or an active game. If the screen is black or stuck, check the `captcha` service logs:

```bash
journalctl -u captcha -f
```

See [Operations Guide — FundingCAPTCHA](operations.md#fundingcaptcha) for more detail.

---

### Playing the Pipes

**Machine:** `192.168.1.13` (Windows mini PC) | **Health:** http://192.168.1.13:8767/health

Max/RNBO patch runs the audio engine. Two Pi Picos connect via USB and appear as COM ports.

**First-time provisioning (once per machine):**

1. Assign fixed COM port numbers to each Pico in Device Manager → Ports (COM & LPT) → Properties → Port Settings → Advanced → COM Port Number. Record them in the [Operations Guide — Playing the Pipes](operations.md#playing-the-pipes) table.
2. Install Python deps: `pip install -r ShowControl\PlayingThePipes\requirements.txt`
3. Install NSSM and register the health server service (see Operations Guide).
4. Open `ShowControl\PlayingThePipes\PlayingThePipes.maxpat` in Max and confirm encoder events arrive.

**Startup (daily):**

Services start automatically via NSSM. Open Max manually if the patch is not set to auto-launch.

See [Operations Guide — Playing the Pipes](operations.md#playing-the-pipes) for service management detail.

---

### Dashboard

**URL:** http://192.168.1.10:9000 — runs on the TreeHouse machine.

Open from any browser on the show network. No login required. Use it to:
- Check which elements are online
- Switch show mode (`active` / `dim` / `inactive`) for any element

---

## Troubleshooting

### Element offline in Dashboard

SSH to the element's machine, then:

```bash
sudo systemctl status <service>   # quick status
journalctl -u <service> -f        # follow live logs
sudo systemctl restart <service>  # restart if needed
```

Service names: `flowerbeds` · `treehouse` · `captcha` · `cg-dashboard`

For **Playing the Pipes** (Windows): open a PowerShell window on the mini PC and run:

```powershell
nssm status pipes-health
nssm restart pipes-health
Get-Content C:\logs\pipes-health.log -Tail 50
```

### FlowerBeds flowers not moving

Most likely cause: **OpenRB-150 controller boards didn't initialize their network stack at boot** ([firmware bug #56](https://github.com/Impractical-Instruments/CommunityGarden/issues/56)).

Fix: confirm the switch was connected _before_ the boards powered on, then **power-cycle the controller boards**. The `flowerbeds` service will reconnect automatically.

If that doesn't help, check for OSC errors:

```bash
journalctl -u flowerbeds -f
```

### Camera not detected

The service will restart and retry automatically. If retries keep failing, udev rules may not be installed. Run once on the affected machine:

```bash
python3 -c "import pyorbbecsdk2, os; print(os.path.dirname(pyorbbecsdk2.__file__))"
# Copy the .rules file from that path to /etc/udev/rules.d/ then:
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### FundingCAPTCHA projector black or game stuck

`captcha` is a single pygame process (ADR-0012) — no browser involved. Restart the service:

```bash
sudo systemctl restart captcha
journalctl -u captcha -f
```

### Updating the software

See [Operations Guide — Updating the software](operations.md#updating-the-software).

---

*Full service management, log commands, and deployment detail: [Operations Guide](operations.md)*
