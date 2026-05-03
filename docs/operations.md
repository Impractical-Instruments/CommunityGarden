# Operations Guide

Process supervision and deployment for CommunityGarden show-control software.

---

## Services overview

Each show-control element runs as a systemd service with `Restart=always` and `RestartSec=5`, so it recovers automatically from crashes without operator intervention.

| Service | Element | Entry point | Default port | Host |
|---|---|---|---|---|
| `flowerbeds` | FlowerBeds | `ShowControl/FlowerBeds/main.py` | 8765 (viz) | 192.168.1.11 |
| `treehouse` | TreeHouse | `ShowControl/TreeHouse/main.py` | 8766 (viz) | 192.168.1.10 |
| `captcha` | FundingCAPTCHA | `ShowControl/FundingCAPTCHA/server.py` | 8080 | 192.168.1.12 |
| `captcha-kiosk` | FundingCAPTCHA kiosk | Chromium (kiosk mode) | — | 192.168.1.12 |
| `cg-dashboard` | Show Dashboard | `ShowControl/Dashboard/serve.py` | 9000 | any |

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

The service user defaults to the invoking user (`$SUDO_USER`) and falls back to `pi`.

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
- **Calibration:** On first start the camera captures `calibration_frames` (default 60) to build a background model. This takes several seconds; `Restart=always` handles spurious camera-open failures.
- **Flags:** Edit `/etc/systemd/system/flowerbeds.service` and add `--no-osc` (no Arduino), `--no-visualizer` (headless), or `--mock-camera` (software testing), then `sudo systemctl daemon-reload && sudo systemctl restart flowerbeds`
- **Visualizer:** `http://<host>:8765/` — live top-down blob view

### TreeHouse

- **Hardware:** Raspberry Pi (Debian/Ubuntu), Pi Pico over USB serial (`/dev/ttyACM0`)
- **USB groups:** The service user must be in `dialout` group (added by `install.sh`)
- **Flags:** Add `--no-pico` to skip serial connection (dev mode)
- **Visualizer:** `http://<host>:8766/` — live display state view

### FundingCAPTCHA

- **Hardware:** Orbbec depth camera (USB, optional), Chromium kiosk browser
- **Services:** Two units — `captcha` (Python server) and `captcha-kiosk` (Chromium browser). The kiosk waits for the server to respond before opening.
- **Flags:** Edit `/etc/systemd/system/captcha.service` to change `--camera` → `--mock-camera` (no hardware) or remove it entirely (pointer-only mode)
- **Uploads:** Photos saved to `ShowControl/FundingCAPTCHA/uploads/`

### Show Dashboard

- **No hardware dependencies** — pure static file server
- Opens at `http://<host>:9000/` — links to each element's visualizer

---

## Updating the software

```bash
cd /home/pi/CommunityGarden   # or wherever the repo lives
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
