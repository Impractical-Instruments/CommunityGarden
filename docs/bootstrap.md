# Bootstrap — first-time hardware provisioning

One-time setup for fresh hardware. Run once per machine, ever. After this, see [showtime.md](showtime.md) for daily and venue ops.

For per-element detail (flags, settings, visualizers, architecture), see the element docs: [FlowerBeds](FlowerBeds.md) · [TreeHouse](TreeHouse.md) · [FundingCAPTCHA](FundingCAPTCHA.md) · [PlayingThePipes](PlayingThePipes.md) · [Dashboard](Dashboard.md).

---

## Hardware inventory

| Machine | Host | OS | Element(s) | Hardware attached |
|---|---|---|---|---|
| `treehouse` | 192.168.1.10 | Pi OS Lite (Pi 5) | TreeHouse + Dashboard | 2× Pi Pico (USB), 1× branch controller (USB), 2× HDMI displays |
| `flowerbeds` | 192.168.1.11 | Pi OS Lite | FlowerBeds | Orbbec depth camera (USB) |
| `captcha` | 192.168.1.12 | Pi OS Lite | FundingCAPTCHA | Orbbec depth camera (USB), short-throw laser projector (HDMI) |
| `pipes` | 192.168.1.13 | Windows 11 | Playing the Pipes | 2× Pi Pico (USB COM), Max/RNBO audio I/O |

OpenRB-150 servo controllers (FlowerBeds firmware) sit on the show LAN at 192.168.1.50 / .51 — separate from the show computers.

---

## Common Linux Pi setup

Repeat per Pi (FlowerBeds, FundingCAPTCHA, TreeHouse). Service user is `ii` by default.

### 1. Image + first boot

1. Flash Pi OS Lite (Bookworm, arm64) — desktop session not required, no element uses one.
2. Set hostname, enable SSH, set timezone via `raspi-config`.
3. Set static IP from [hardware inventory](#hardware-inventory) on the show LAN interface (Ethernet).
4. `sudo apt update && sudo apt upgrade`.

### 2. Clone repo

```bash
cd /home/ii
git clone https://github.com/Impractical-Instruments/CommunityGarden.git
```

The deploy scripts assume this exact path — `/home/ii/CommunityGarden`. If you put it elsewhere, edit each element's `deploy/*.service` `WorkingDirectory=` before installing.

### 3. Install element service

Run the per-element installer once. Each `install.sh` handles apt packages, pip deps, systemd unit, enable + restart.

```bash
sudo bash scripts/install-services.sh FlowerBeds
# or
sudo bash scripts/install-services.sh FundingCAPTCHA
# or (TreeHouse machine also runs Dashboard):
sudo bash scripts/install-services.sh TreeHouse Dashboard
```

Each Pi normally runs one element. TreeHouse host also runs `cg-dashboard`.

### 4. LAN deploy bootstrap

After the initial clone, allow `scripts/deploy.sh` (run from the operator laptop) to push code over the show LAN:

```bash
cd /home/ii/CommunityGarden
bash scripts/bootstrap-deploy.sh
```

This sets `receive.denyCurrentBranch=updateInstead` and writes `/etc/sudoers.d/cg-deploy` for NOPASSWD per-element `install.sh`. Run as `ii`, not root — script invokes sudo itself.

---

## Element-specific Pi provisioning

### FlowerBeds host

Orbbec udev rule — install.sh does **not** add one for FlowerBeds (it does for FundingCAPTCHA). Add manually if the camera fails to open:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2bc5", ATTR{idProduct}=="0807", MODE="0666"' \
    | sudo tee /etc/udev/rules.d/99-orbbec.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

If Orbbec has different idProduct, vendor rule ships in the SDK:

```bash
python3 -c "import pyorbbecsdk2, os; print(os.path.dirname(pyorbbecsdk2.__file__))"
# Copy the .rules file from there to /etc/udev/rules.d/, reload.
```

Service user (`ii`) needs `video` + `plugdev` groups (granted via `SupplementaryGroups=` in the unit — no manual add needed).

### TreeHouse host

`install.sh` covers most provisioning automatically:

- apt: `weston seatd libgl1-mesa-dri libegl1 libegl-mesa0 libgl1 libx11-dev`
- `systemctl enable --now seatd` (weston needs seat management)
- EGL/GL symlinks (Pi OS ships only `.so.1`; moderngl dlopens `.so`)
- Display config: `ShowControl/TreeHouse/deploy/weston.ini` declares both HDMI outputs explicitly (1024×600 + 800×480)

What it does **not** do — USB symlink rules for the Picos + branch controller. `/dev/ttyACMx` is plug-order; you need stable names referenced in `settings.json`.

**Pico/branch USB symlinks (one-time):**

| Symlink | Device | Channels |
|---|---|---|
| `/dev/treehouse-pico-a` | Pico A (dioramas) | House Swarming, Club, Mycelium, F&F arc/bloom |
| `/dev/treehouse-pico-b` | Pico B (structure) | Dormer, Porch Lights, Attic TV & Lamps |
| `/dev/treehouse-branches` | Branch controller | Dynamixel branch motors |

Plug each device in alone and record its serial:

```bash
udevadm info -a -n /dev/ttyACM0 | grep 'ATTRS{serial}'
```

Then `/etc/udev/rules.d/99-treehouse.rules`:

```
SUBSYSTEM=="tty", ATTRS{serial}=="<pico-a-serial>", SYMLINK+="treehouse-pico-a"
SUBSYSTEM=="tty", ATTRS{serial}=="<pico-b-serial>", SYMLINK+="treehouse-pico-b"
SUBSYSTEM=="tty", ATTRS{serial}=="<branch-serial>", SYMLINK+="treehouse-branches"
```

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Record the serials in `ShowControl/network.json` under `"firmware"` so they're not lost.

`settings.json` references the symlinks, never `/dev/ttyACMx` directly.

### FundingCAPTCHA host

`install.sh` covers everything:

- Orbbec udev rule (2bc5:0807 → `MODE="0666"`) auto-written
- pygame uses `SDL_VIDEODRIVER=kmsdrm` — direct DRM, no compositor (no weston, no X)
- `video plugdev render` groups granted via service unit

Plug projector via HDMI before first start; pygame picks up the active output automatically.

---

## Playing the Pipes (Windows) provisioning

Pipes runs on the Windows mini PC at 192.168.1.13. systemd commands do not apply.

### 1. Repo clone

```powershell
cd C:\
git clone https://github.com/Impractical-Instruments/CommunityGarden.git
cd C:\CommunityGarden
git config receive.denyCurrentBranch updateInstead
```

### 2. OpenSSH server

Settings → Apps → Optional Features → install **OpenSSH Server**. Start service. Add laptop public key to `C:\Users\<user>\.ssh\authorized_keys`.

### 3. Python deps

```powershell
cd C:\CommunityGarden\ShowControl\PlayingThePipes
pip install -r requirements.txt
```

### 4. COM port pinning

Both Picos enumerate as COM ports. Numbers are not stable by default — pin them in Device Manager:

1. Plug each Pico in alone. Note which COM appears.
2. Device Manager → Ports (COM & LPT) → right-click → Properties → Port Settings → Advanced → COM Port Number → assign fixed.
3. Record COM numbers in `PlayingThePipes.maxpat` `serial` objects (see [PlayingThePipes.md](PlayingThePipes.md)).

```powershell
# List COMs:
[System.IO.Ports.SerialPort]::GetPortNames()
```

### 5. Install NSSM + register health server service

Download NSSM from https://nssm.cc, put `nssm.exe` on PATH, run as admin:

```powershell
nssm install pipes-health python
nssm set pipes-health AppParameters "C:\CommunityGarden\ShowControl\PlayingThePipes\health_server.py"
nssm set pipes-health AppDirectory  "C:\CommunityGarden\ShowControl\PlayingThePipes"
nssm set pipes-health AppStdout     "C:\logs\pipes-health.log"
nssm set pipes-health AppStderr     "C:\logs\pipes-health.log"
nssm set pipes-health Start         SERVICE_AUTO_START
nssm start pipes-health
```

Health endpoint is `http://192.168.1.13:8767/health` — Dashboard pings this to show Pipes online.

### 6. Max/RNBO

Install Max 9. Open `ShowControl\PlayingThePipes\PlayingThePipes.maxpat` once, confirm encoder events arrive, save. Configure Max to auto-launch on login if you want hands-off boot.

---

## Operator laptop (one-time)

Used to push deploys over the show LAN with `scripts/deploy.sh`.

### SSH config

`~/.ssh/config`:

```
Host flowerbeds
    HostName 192.168.1.11
    User ii
Host treehouse
    HostName 192.168.1.10
    User ii
Host captcha
    HostName 192.168.1.12
    User ii
Host pipes
    HostName 192.168.1.13
    User charlie
```

Copy laptop public key to each host's `~/.ssh/authorized_keys`:

```bash
ssh-copy-id flowerbeds
ssh-copy-id treehouse
ssh-copy-id captcha
# pipes: paste pubkey manually into C:\Users\charlie\.ssh\authorized_keys
```

### Wired connection to the show LAN

The show LAN has **no DHCP server** — every host is statically addressed from the
[hardware inventory](#hardware-inventory). A laptop plugged into the show switch
must be given a static address too, or NetworkManager will sit in "configuring"
until DHCP times out (`Error: ... IP configuration could not be reserved`).

Two traps, both of which look identical from the operator's seat — the element
is up, has an IP, and is still unreachable.

**Trap 1 — the wired profile is left in shared mode.** If the adapter was last
used to feed a Pi directly (NM's "Share to other computers"), the profile keeps
`ipv4.method=shared` and the laptop hands out its own DHCP on `10.42.0.0/24`.
The giveaway is `ip -4 -br addr` showing `10.42.0.1/24` on the wired interface.

**Trap 2 — the show LAN collides with the venue wifi.** The show LAN is
`192.168.1.0/24`; so is many a house or venue network. Two interfaces on
overlapping subnets is a broken routing table — whichever route has the lower
metric wins, and if that's ethernet, the default route out the wifi gateway dies
with it.

Configure the wired profile like this. Wifi keeps the `/24` and the internet;
only explicitly-routed element addresses go out the wire:

```bash
nmcli con mod "Wired connection 1" \
  ipv4.method manual \
  ipv4.addresses 192.168.1.100/24 \
  ipv4.gateway "" \
  ipv4.never-default yes \
  ipv4.route-metric 700 \
  ipv4.ignore-auto-dns yes \
  +ipv4.routes "192.168.1.10/32" \
  +ipv4.routes "192.168.1.11/32" \
  +ipv4.routes "192.168.1.12/32" \
  +ipv4.routes "192.168.1.13/32"
nmcli con up "Wired connection 1"
```

`never-default` and the metric of 700 (above wifi's usual 600) keep the wifi
default route intact; the `/32` host routes beat the wifi `/24` by being more
specific, so element traffic still goes out the wire. Verify with
`ip route get 192.168.1.12` — it should name the wired interface.

Finding an element when you don't know what it has: `ping` bound to the wired
interface bypasses the routing-table ambiguity entirely.

```bash
for i in 10 11 12 13; do
  ping -c1 -W1 -I <wired-iface> 192.168.1.$i >/dev/null 2>&1 && echo "192.168.1.$i up"
done
ip neigh show dev <wired-iface>        # MAC addresses; Pi 5 OUI is 2c:cf:67
```

> The `/32` routes are a workaround for the subnet collision, not a fix — anything
> that broadcasts or scans across the show LAN still goes out wifi. If the show
> LAN is ever renumbered, move it to a subnet unlikely to collide with a venue
> network (`192.168.42.0/24`) and this whole section reduces to one static
> address.

**Taking the laptop elsewhere.** The profile is now hard-static, so the adapter
won't get an address on an ordinary DHCP network until you set it back:

```bash
nmcli con mod "Wired connection 1" ipv4.method auto
```

### Optional: hostname aliases

`C:\Windows\System32\drivers\etc\hosts` (admin, Windows laptop):

```
192.168.1.10  treehouse dashboard
192.168.1.11  flowerbeds
192.168.1.12  captcha
192.168.1.13  pipes
```

### FlowerBeds layout tool

The operator laptop also runs the FlowerBeds layout GUI (Windows, browser-based). See [FlowerBeds.md → Layout tool](FlowerBeds.md#layout-tool) for usage. Requirements: Python + `pip install -r ShowControl/FlowerBeds/requirements.txt`.
