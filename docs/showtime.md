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

OpenRB-150 servo controllers: 192.168.1.50 / .51 (FlowerBeds firmware).

---

## Services

Linux hosts run systemd units with `Restart=always RestartSec=5`. Pipes (Windows) runs under NSSM.

| Service | Host | Entry | Hardware |
|---|---|---|---|
| `flowerbeds` | flowerbeds | `ShowControl/FlowerBeds/main.py` | Orbbec cam, OSC servos |
| `treehouse` | treehouse | `ShowControl/TreeHouse/main.py` | Picos, branch motor, 2× HDMI |
| `captcha` | captcha | `ShowControl/FundingCAPTCHA/app.py` | Orbbec cam, projector |
| `cg-dashboard` | treehouse | `ShowControl/Dashboard/serve.py` | none |
| `pipes-health` | pipes (NSSM) | `ShowControl/PlayingThePipes/health_server.py` | (Max runs separately) |

Power-on order is independent — services retry until hardware comes up.

---

## Venue setup (first day at each venue)

1. **Network.** Show switch on first. Connect all show computers + OpenRB-150 boards to switch via Ethernet **before powering them on** (OpenRB boards fail to init network if switch is absent at boot — [issue #56](https://github.com/Impractical-Instruments/CommunityGarden/issues/56)).
2. **Power on.** Any order. Services auto-start.
3. **Hide.** Get out of view of the Flower Beds and Funding CAPTCHA cameras. Tell other staff, animals, robots to hide as well.
4. **Wait ~60 s.** FlowerBeds and Funding CAPTCHA are slowest — they build a 60-frame background depth model before tracking.
5. **Verify Dashboard.** Open http://192.168.1.10:9000. All elements should be green. Red → see [troubleshooting](#troubleshooting).
6. **Run FlowerBeds layout tool** on the operator laptop if modules moved since last venue. See [FlowerBeds.md](FlowerBeds.md#layout-tool).
7. Done.

---

## Daily startup

1. Power everything on (any order).
3. Hide.
4. Wait ~60 s.
5. Open Dashboard, verify green across the board.
6. If anything is red, see [troubleshooting](#troubleshooting).

Services restart automatically on crash. No babysitting needed.

---

## Service management (Linux)

```bash
# Status
sudo systemctl status flowerbeds
sudo systemctl status treehouse
sudo systemctl status captcha
sudo systemctl status cg-dashboard

# Restart
sudo systemctl restart flowerbeds

# Stop / start
sudo systemctl stop flowerbeds
sudo systemctl start flowerbeds

# Disable auto-start
sudo systemctl disable flowerbeds
```

### Pipes (Windows / NSSM)

```powershell
nssm status pipes-health
nssm restart pipes-health
nssm stop pipes-health
```

---

## Logs

```bash
# Live
journalctl -u flowerbeds -f
journalctl -u treehouse -f
journalctl -u captcha -f

# Since boot
journalctl -u flowerbeds -b

# Combined
journalctl -u flowerbeds -u treehouse -u captcha -u cg-dashboard -f
```

Pipes:
```powershell
Get-Content C:\logs\pipes-health.log -Tail 50
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
```

Behavior — `git push --force-with-lease` (matching branch), ssh checkout, `sudo bash install.sh`. If the show machine has a dirty working tree the checkout refuses; ssh in and `git stash` / `git checkout -- .` first.

### Pipes (Windows) — manual

`deploy.sh` doesn't handle Pipes. Python changes are rare:

```bash
# From laptop:
git push --force-with-lease pipes:CommunityGarden $(git branch --show-current):$(git branch --show-current)
ssh pipes "cd C:/CommunityGarden && git checkout <branch> && nssm restart pipes-health"
```

Max patch: reload manually.

### From the show machine pulling GitHub (home / dev with internet)

```bash
cd /home/ii/CommunityGarden
git pull
sudo bash ShowControl/<Element>/deploy/install.sh
```

---

## Running without hardware (dev)

Every element has dev flags so you can run anywhere — no camera, no LEDs, no servos.

```bash
# TreeHouse, no hardware or displays
python3 main.py --no-pico --no-branch --no-renderer --no-club-screen

# FlowerBeds, no camera, no servo OSC
python3 main.py --mock-camera --no-osc

# FundingCAPTCHA, synthetic depth frames
python3 app.py --mock-camera
# FundingCAPTCHA, mouse-paint depth (ADR-0016)
python3 app.py --test-input
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

Service names: `flowerbeds` · `treehouse` · `captcha` · `cg-dashboard`

Pipes (Windows): `nssm status pipes-health` / `nssm restart pipes-health`.

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

`captcha` is a single pygame process (ADR-0012) — no browser, no kiosk. State machine is `BG_CAL → SCREENSAVER → GAME`. If stuck in BG_CAL the camera isn't producing frames.

### TreeHouse — displays off or wrong screen

Both displays are driven by a single `weston` compositor (ADR-0018). If only one shows up, check:

- `dmesg | grep -i hdmi` for connection state.
- `wlr-randr` from a shell in the weston session lists active outputs.
- `weston.ini` (in `ShowControl/TreeHouse/deploy/`) declares the two outputs at fixed resolutions; a screen at a different resolution falls back to index 0 with a warning in the journal.

The Looking Glass renderer + Club screen run as child processes of `treehouse`. To restart just the renderers without restarting the coordinator:

```bash
sudo pkill -f looking_glass/renderer.py
sudo pkill -f club_screen.py
# coordinator relaunches both with exponential backoff
```

### Pipes — Max patch silent

Open Max manually, check the `serial` objects connect to the expected COM ports (set in Device Manager — [bootstrap.md → COM port pinning](bootstrap.md#4-com-port-pinning)). Health endpoint can be up without Max running.

---

## Open questions / future work

- **Health monitoring:** `Restart=always` handles crashes but doesn't alert. A watchdog → Slack/Discord webhook on repeated restarts would help unattended operation.
- **Multi-machine deploy:** `deploy.sh` is per-host. An Ansible playbook or `pdsh` wrapper could re-deploy all hosts at once.
- **Orbbec SDK pinning:** `pyorbbecsdk2` must match the host SDK `.so`. If versions diverge between hosts, document the pairing per machine.
