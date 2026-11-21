# Showtime — install, start, debug, maintain

Day-to-day operations for The Community Garden. Hardware already provisioned per [bootstrap.md](bootstrap.md).

For element-specific detail, see: [FlowerBeds](FlowerBeds.md) · [TreeHouse](TreeHouse.md) · [FundingCAPTCHA](FundingCAPTCHA.md) · [PlayingThePipes](PlayingThePipes.md) · [Dashboard](Dashboard.md).

---

## Machine map

| Element | IP | URL |
|---|---|---|
| Dashboard | 192.168.1.10 | http://192.168.1.10:9000 |
| TreeHouse | 192.168.1.10 | http://192.168.1.10:8766 (visualizer) |
| FlowerBeds | 192.168.1.11 | http://192.168.1.11:8765 (visualizer) |
| FundingCAPTCHA | 192.168.1.12 | http://192.168.1.12:8080 (monitor) |
| Playing the Pipes | 192.168.1.13 | http://192.168.1.13:8767/health |

OpenRB-150 servo controllers: 192.168.1.50 / .51 (FlowerBeds firmware, Ethernet).

TreeHouse location controllers (ESP32-S3, WiFi `TCG-Show-5`): Swannatopia .60, Julia .61, Jess .62, Dormer .63, Garage .64.

---

## Services

Every host runs systemd units with `Restart=always RestartSec=5`.

| Service | Host | Entry | Hardware |
|---|---|---|---|
| `flowerbeds` | flowerbeds | `ShowControl/FlowerBeds/main.py` | Orbbec cam, OSC servos |
| `treehouse` | treehouse | `ShowControl/TreeHouse/main.py` | location controllers (WiFi), branch motor, 2× HDMI |
| `captcha` | captcha | `ShowControl/FundingCAPTCHA/app.py` | Orbbec cam, projector |
| `cg-dashboard` | treehouse | `ShowControl/Dashboard/serve.py` | none |
| `pipes-reuben` | pipes | `reuben play ShowControl/PlayingThePipes/reuben/pipes.json` (structure channel on the LAN, token-guarded) | audio interface (speakers + mic) |
| `pipes-bridge` | pipes | `ShowControl/PlayingThePipes/encoder_bridge.py` | 2× encoder Pico (USB) |

Power-on order is independent — services retry until hardware comes up.

---

## Venue setup (first day at each venue)

1. **Network.** Show switch on first. Connect all show computers + OpenRB-150 boards to switch via Ethernet **before powering them on** (OpenRB boards fail to init network if switch is absent at boot — [issue #56](https://github.com/Impractical-Instruments/CommunityGarden/issues/56)).
2. **Power on.** Any order. Services auto-start.
3. **Rebuild the FlowerBeds background.** FlowerBeds keeps its background depth model in `ShowControl/FlowerBeds/settings.calibration.npz` and reuses it on every start, so at a new venue it still holds the last venue's room. Get everyone out of the FlowerBeds camera's view (staff, animals, robots), then on the `flowerbeds` host:
   ```bash
   sudo systemctl stop flowerbeds
   rm ~/CommunityGarden/ShowControl/FlowerBeds/settings.calibration.npz
   sudo systemctl start flowerbeds
   journalctl -u flowerbeds -f     # stay hidden until "Calibration saved to …"
   ```
   It takes 60 frames, well under a minute. Do it again if the camera or anything large in its view moves. Funding CAPTCHA needs none of this: it learns its background continuously, with people in view (ADR-0023).
4. **Check the TreeHouse lights.** All five locations should be lit. A dark one: see [TreeHouse.md → Troubleshooting](TreeHouse.md#troubleshooting).
5. **Verify Dashboard.** Open http://192.168.1.10:9000. All elements should be green. Red → see [troubleshooting](#troubleshooting).
6. **Run FlowerBeds layout tool** on the operator laptop if modules moved since last venue. See [FlowerBeds.md](FlowerBeds.md#layout-tool).
7. Done.

---

## Daily startup

1. Power everything on (any order). Nobody needs to hide: FlowerBeds loads its saved background, and Funding CAPTCHA learns its own.
2. Wait about a minute for the services to come up.
3. Open Dashboard, verify green across the board.
4. If anything is red, see [troubleshooting](#troubleshooting).

Services restart automatically on crash. No babysitting needed.

---

## Service management

```bash
# Status
sudo systemctl status flowerbeds
sudo systemctl status treehouse
sudo systemctl status captcha
sudo systemctl status cg-dashboard
sudo systemctl status pipes-reuben pipes-bridge

# Restart
sudo systemctl restart flowerbeds

# Stop / start
sudo systemctl stop flowerbeds
sudo systemctl start flowerbeds

# Disable auto-start
sudo systemctl disable flowerbeds
```

---

## Logs

```bash
# Live
journalctl -u flowerbeds -f
journalctl -u treehouse -f
journalctl -u captcha -f
journalctl -u pipes-reuben -u pipes-bridge -f

# Since boot
journalctl -u flowerbeds -b

# Combined
journalctl -u flowerbeds -u treehouse -u captcha -u cg-dashboard -f
```

---

## Deploying code updates

Two flows. LAN push is the venue default.

### From the operator laptop on the show LAN (no internet)

`scripts/deploy.sh` pushes the laptop's current branch to a show machine and runs the element's `install.sh` (pip + restart). Prereqs covered in [bootstrap.md](bootstrap.md).

```bash
scripts/deploy.sh flowerbeds FlowerBeds
scripts/deploy.sh treehouse  TreeHouse
scripts/deploy.sh treehouse  Dashboard       # same host, different element
scripts/deploy.sh captcha    FundingCAPTCHA
scripts/deploy.sh pipes      PlayingThePipes
```

Behavior — `git push --force-with-lease` (matching branch), ssh checkout, `sudo bash install.sh`. If the show machine has a dirty working tree the checkout refuses; ssh in and `git stash` / `git checkout -- .` first.

**Playing the Pipes** also gets the reuben commit the branch pins, pushed into the box's `vendor/reuben`, and its installer rebuilds reuben before restarting. Three kinds of change need internet on the box once and cannot arrive by LAN deploy: a new Rust crate, a Rust toolchain change, and new or changed samples. The installer stops before restarting anything if one is missing. See [PlayingThePipes.md → Deploying code updates](PlayingThePipes.md#deploying-code-updates).

### From the show machine pulling GitHub (home / dev with internet)

```bash
cd /home/ii/CommunityGarden
git pull
sudo bash ShowControl/<Element>/deploy/install.sh
```

---

## Running without hardware (dev)

Every element has dev flags so you can run anywhere — no camera, no LEDs, no servos. Run each from the element's own directory. In a dev clone use `uv run python`; on a show machine, `python3`.

```bash
# TreeHouse, no hardware or displays
cd ShowControl/TreeHouse
uv run python main.py --no-locations --no-branch --no-renderer --no-club-screen

# FlowerBeds, no camera, no servo OSC
cd ShowControl/FlowerBeds
uv run python main.py --mock-camera --no-osc

# FundingCAPTCHA, synthetic depth frames
cd ShowControl/FundingCAPTCHA
uv run python app.py --mock-camera
# FundingCAPTCHA, mouse-paint depth (ADR-0016)
uv run python app.py --test-input
```

See each element doc for full flag reference.

---

## Troubleshooting

### Element offline in Dashboard

SSH to the element's host. Then:

```bash
sudo systemctl status <service>
journalctl -u <service> -f
sudo systemctl restart <service>
```

Service names: `flowerbeds` · `treehouse` · `captcha` · `cg-dashboard` · `pipes-reuben` · `pipes-bridge`

### FlowerBeds — flowers not moving

Most common cause: OpenRB-150 boards didn't initialize their network stack at boot ([firmware #56](https://github.com/Impractical-Instruments/CommunityGarden/issues/56)). Confirm switch was up before the boards powered on, then power-cycle the boards. The `flowerbeds` service reconnects automatically.

Boot-time diagnostics — `journalctl -u flowerbeds -b` shows a per-controller ping listing scanned servo IDs and any `Configured motor IDs not found on any controller: …` line. If a motor ID is on that list, no command reaches it.

Also see [FlowerBeds.md](FlowerBeds.md) for layout-tool aim mode and manual calibration sweeps.

### Camera not detected

Service auto-retries. If retries keep failing the udev rule probably isn't installed. See [bootstrap.md → FlowerBeds host](bootstrap.md#flowerbeds-host) or `FundingCAPTCHA/deploy/install.sh` (which writes the rule for captcha).

### FundingCAPTCHA — projector black or game stuck

```bash
sudo systemctl restart captcha
journalctl -u captcha -f
```

`captcha` is a single pygame process (ADR-0012) — no browser, no kiosk. State machine is `SCREENSAVER ↔ GAME` (`kiosk.py`). If the Dashboard shows `state=error` or `fg_pixels` never changes, the camera isn't producing frames.

### FundingCAPTCHA — getting a console on the kiosk

The kiosk is a systemd unit with `Restart=always` / `RestartSec=5`. Quitting the game with **Esc** or **Q** only makes `app.py` exit; systemd relaunches it five seconds later, forever. To get the machine back, stop the *unit*, not the process.

**Over ethernet (easiest).** Plug in a cable, `ssh ii@captcha`, then stop the service.

**On the Pi's own keyboard.** `SDL_VIDEODRIVER=kmsdrm` means pygame renders straight to DRM and holds the tty, so VT switching usually does nothing while the game is up. Use the restart gap:

1. Press **Esc** to quit the game.
2. Immediately press **Ctrl+Alt+F2** — a login prompt appears on tty2 during the ~5 s `RestartSec` window.
3. Log in as `ii` and run `sudo systemctl stop captcha`.

**If neither works — SD card.** Mount the boot partition on another machine and append `systemd.mask=captcha.service` to the single line in `cmdline.txt`. The Pi then boots to a clean console every time. Remove it when you're done.

Stop vs. disable:

```bash
sudo systemctl stop captcha            # down now, back up on next boot
sudo systemctl disable --now captcha   # down now, stays down across reboots
sudo systemctl enable  --now captcha   # back to show-ready — do this before load-in
```

Joining wifi from the console (to pull an update without the laptop):

```bash
sudo nmtui                                             # menu-driven, easiest at a console
sudo nmcli device wifi list
sudo nmcli device wifi connect "SSID" password "..."
ip addr show wlan0                                     # confirm an address
```

`sudo raspi-config` → System Options → Wireless LAN also works.

Updating the game from that console:

```bash
sudo systemctl stop captcha
cd ~/CommunityGarden && git pull && git lfs pull
sudo systemctl start captcha
journalctl -u captcha -f
```

If the install uses private show content, re-run its sync too: [FundingCAPTCHA.md → Private content sets](FundingCAPTCHA.md#private-content-sets).

### TreeHouse — displays off or wrong screen

Both displays are driven by a single `weston` compositor (ADR-0018). If only one shows up, check:

- `dmesg | grep -i hdmi` for connection state.
- `weston.ini` (in `ShowControl/TreeHouse/deploy/`) declares the two outputs at fixed resolutions; a screen at a different resolution falls back to index 0 with a warning in the journal.

The Looking Glass renderer + Club screen run as child processes of `treehouse`. To restart just the renderers without restarting the coordinator:

```bash
sudo pkill -f looking_glass/renderer.py
sudo pkill -f club_screen.py
# coordinator relaunches both with exponential backoff
```

### Pipes — no sound, or encoders dead

`http://192.168.1.13:8767/health` says which half is down: `reuben_alive` is the audio engine (`pipes-reuben`), `picos_connected` is the encoders (`pipes-bridge`). Then [PlayingThePipes.md → Troubleshooting](PlayingThePipes.md#troubleshooting).

---

## Open questions / future work

- **Health monitoring:** `Restart=always` handles crashes but doesn't alert. A watchdog → Slack/Discord webhook on repeated restarts would help unattended operation.
- **Multi-machine deploy:** `deploy.sh` is per-host. An Ansible playbook or `pdsh` wrapper could re-deploy all hosts at once.
- **Orbbec SDK pinning:** `pyorbbecsdk2` must match the host SDK `.so`. If versions diverge between hosts, document the pairing per machine.
