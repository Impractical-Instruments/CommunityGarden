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

### 5. Run FlowerBeds layout calibration

Required any time flower modules have been repositioned. See [FlowerBeds setup](#flowerbeds) below.

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

**Layout calibration** — run every venue setup after placing flower modules.

**What you need:** 12 ArUco markers, `DICT_4X4_50`, one per module, printed **40 cm square** (laminate if possible). Each marker's ID must match its module's `marker_id` in `settings.json` (IDs 0–11 by default).

**Tag orientation:** Point the **top edge** (the edge opposite the printed ID number) toward the direction you want that module's flowers to face at rest.

**Steps:**

1. Place all markers flat on the floor at each module's registration point, oriented as above.
2. Trigger layout calibration — choose one:
   - **Dashboard:** http://192.168.1.11:8765 → click **Layout Calibrate**
   - **CLI (SSH to FlowerBeds machine):**
     ```bash
     sudo systemctl stop flowerbeds
     cd /home/pi/CommunityGarden/ShowControl/FlowerBeds
     python main.py --config settings.json --layout-calibrate
     sudo systemctl start flowerbeds
     ```
3. Wait ~3 seconds. The visualizer's **CAL:** badge turns green when done.
4. Remove all markers. Show resumes automatically with updated positions.

Any module whose tag wasn't detected keeps its existing position from `settings.json` — a warning is logged. Re-run calibration if you see unexpected positions.

See [Operations Guide — FlowerBeds](operations.md#flowerbeds) for more detail.

---

### TreeHouse

**Machine:** `192.168.1.10` | **Visualizer:** http://192.168.1.10:8766

Drives LEDs, branch motors, and video displays. Also runs the Dashboard on the same machine.

- Pi Pico connects via USB (`/dev/ttyACM0`). Verify the Pico LED is lit after startup.
- Check the visualizer to see live display state.

**First-time provisioning (once per machine):**

The Looking Glass renderer depends on `moderngl` → `glcontext`, which requires X11 development headers to compile. Install before running `pip3 install -r requirements.txt`:

```bash
sudo apt-get install -y libx11-dev
```

See [Operations Guide — TreeHouse](operations.md#treehouse) for more detail.

---

### FundingCAPTCHA

**Machine:** `192.168.1.12` | **URL:** http://192.168.1.12:8080

Browser kiosk showing proof-of-humanity games. Two services run:

| Service | Role |
|---|---|
| `captcha` | Python game server |
| `captcha-kiosk` | Chromium in kiosk mode (waits for server before opening) |

Verify the kiosk screen shows a screensaver or active game. If stuck on a loading screen, the `captcha` service may not have started — check:

```bash
journalctl -u captcha -f
```

See [Operations Guide — FundingCAPTCHA](operations.md#fundingcaptcha) for more detail.

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

### FundingCAPTCHA kiosk stuck on loading

```bash
sudo systemctl restart captcha
```

Chromium retries automatically once the server responds.

### Updating the software

See [Operations Guide — Updating the software](operations.md#updating-the-software).

---

*Full service management, log commands, and deployment detail: [Operations Guide](operations.md)*
