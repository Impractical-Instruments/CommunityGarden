# Bootstrap — first-time hardware provisioning

One-time setup for fresh hardware. Run once per machine, ever. After this, see [showtime.md](showtime.md) for daily and venue ops.

For per-element detail (flags, settings, visualizers, architecture), see the element docs: [FlowerBeds](FlowerBeds.md) · [TreeHouse](TreeHouse.md) · [FundingCAPTCHA](FundingCAPTCHA.md) · [PlayingThePipes](PlayingThePipes.md) · [Dashboard](Dashboard.md).

---

## Hardware inventory

| Machine | Host | OS | Element(s) | Hardware attached |
|---|---|---|---|---|
| `treehouse` | 192.168.1.10 | Pi OS Lite (Pi 5) | TreeHouse + Dashboard | 1× branch controller (USB), 2× HDMI displays, 5× location controllers (WiFi, below) |
| `flowerbeds` | 192.168.1.11 | Pi OS Lite | FlowerBeds | Orbbec depth camera (USB) |
| `captcha` | 192.168.1.12 | Pi OS Lite | FundingCAPTCHA | Orbbec depth camera (USB), short-throw laser projector (HDMI) |
| `pipes` | 192.168.1.13 | Raspberry Pi 5, Raspberry Pi OS with desktop (Debian 13, arm64) | Playing the Pipes | 2× Pi Pico (USB serial), audio interface (speakers + mic) |

OpenRB-150 servo controllers (FlowerBeds firmware) sit on the show LAN at 192.168.1.50 / .51 — separate from the show computers.

TreeHouse location controllers: five ESP32-S3 boards that drive every LED in the TreeHouse. They join the show LAN over WiFi with static addresses. Provisioning: [TreeHouse location controllers](#treehouse-location-controllers).

| Controller | Address | PlatformIO environment |
|---|---|---|
| Swannatopia | 192.168.1.60 | `swannatopia` |
| Julia | 192.168.1.61 | `julia` |
| Jess | 192.168.1.62 | `jess` |
| Dormer | 192.168.1.63 | `dormer` |
| Garage | 192.168.1.64 | `garage` |

Every address here comes from `ShowControl/network.json`; if the two disagree, that file is right.

---

## Common Linux Pi setup

Repeat per Pi (FlowerBeds, FundingCAPTCHA, TreeHouse). The `pipes` Pi builds reuben from source, so it has its own section: [Playing the Pipes host provisioning](#playing-the-pipes-host-provisioning). Service user is `ii` by default.

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

This is the default path. The installers work from wherever the repo is cloned (they fill the path into each systemd unit). `scripts/deploy.sh` expects `~/CommunityGarden` on the show machine; for any other location, set `CG_REMOTE_REPO` when running it.

### 3. uv

As `ii` (not root), install [uv](https://docs.astral.sh/uv/). The installers use it to set up the Python and packages in `uv.lock`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 4. Install element service

Run the per-element installer once. Each `install.sh` handles apt packages, Python deps (uv; TreeHouse and FundingCAPTCHA still use system pip), systemd unit, enable + restart; the shared steps are in `scripts/lib/install-element.sh`. This first run needs internet for the apt packages, the Python download and the packages. Later runs (every `deploy.sh`) do not, unless a dependency was added.

```bash
sudo bash scripts/install-services.sh FlowerBeds
# or
sudo bash scripts/install-services.sh FundingCAPTCHA
# or (TreeHouse machine also runs Dashboard):
sudo bash scripts/install-services.sh TreeHouse Dashboard
```

Each Pi normally runs one element. TreeHouse host also runs `cg-dashboard`.

### 5. LAN deploy bootstrap

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
~/CommunityGarden/.venv/bin/python -c "import pyorbbecsdk2, os; print(os.path.dirname(pyorbbecsdk2.__file__))"
# Copy the .rules file from there to /etc/udev/rules.d/, reload.
```

Service user (`ii`) needs `video` + `plugdev` groups (granted via `SupplementaryGroups=` in the unit — no manual add needed).

### TreeHouse host

`install.sh` covers most provisioning automatically:

- apt: `weston seatd libgl1-mesa-dri libegl1 libegl-mesa0 libgl1 libx11-dev`
- `systemctl enable --now seatd` (weston needs seat management)
- EGL/GL symlinks (Pi OS ships only `.so.1`; moderngl dlopens `.so`)
- Display config: `ShowControl/TreeHouse/deploy/weston.ini` declares both HDMI outputs explicitly (1024×600 + 800×480)

What it does **not** do — the USB symlink rule for the branch controller. `/dev/ttyACMx` is plug-order; you need stable names referenced in `settings.json`.

**Branch USB symlink (one-time):**

| Symlink | Device | Drives |
|---|---|---|
| `/dev/treehouse-branches` | Branch controller | Dynamixel branch motors |

Plug it in alone and record its serial:

```bash
udevadm info -a -n /dev/ttyACM0 | grep 'ATTRS{serial}'
```

Then `/etc/udev/rules.d/99-treehouse.rules`:

```
SUBSYSTEM=="tty", ATTRS{serial}=="<branch-serial>", SYMLINK+="treehouse-branches"
```

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

That rule file is the only record of the serial, and it lives on the Pi, not in the repo. A replacement Pi or branch controller needs the steps above again.

`settings.json` references the symlink, never `/dev/ttyACMx` directly.

### TreeHouse location controllers

Five ESP32-S3 boards, flashed from a laptop, not from the Pi. Board, wiring, flashing and bench tests are in [`Firmware/TreeHouse_Controllers/README.md`](../Firmware/TreeHouse_Controllers/README.md); this is the part about getting them on the network.

**The network.** The controllers join the WiFi network `TCG-Show-5`. Each takes the static address in the [hardware inventory](#hardware-inventory), with the gateway and netmask from `lan` in `network.json`, so that WiFi network must be part of the show LAN (192.168.1.0/24): the TreeHouse Pi sends to the controllers by IP.

**Credentials.** They are compiled into the firmware from `include/secrets.h`, which is gitignored. Never put the password in a tracked file.

```bash
cd Firmware/TreeHouse_Controllers
cp include/secrets.h.example include/secrets.h     # the SSID is already TCG-Show-5; fill in the password
uv run python ../../scripts/hooks/firmware_config_gen.py   # refresh include/net_config.h from network.json
pio run -e jess -t upload                          # one environment per controller; see the table above
```

`pio` is PlatformIO's CLI. The VSCode PlatformIO extension provides it (see the firmware README); without it, `uvx --from platformio==6.2.0 pio` is the same tool, as the Makefile runs it.

A changed password or SSID means editing `secrets.h` and reflashing all five.

**Confirm a controller joined.** With the board on USB:

```bash
pio device monitor -b 115200
```

- `[net] connecting to "TCG-Show-5"`, then `[net] up as <hostname> on 192.168.1.6x:9000`: joined.
- The status line every 5 s starts `[<Location>] ok`. `no-wifi` there means it has not joined: check the password in `secrets.h` and that the access point is on.
- From the `treehouse` Pi, `ping 192.168.1.62` (Jess) answers.

The controllers light up whether or not they have joined: for now they animate on their own and ignore what the Pi sends (ADR-0021). A lit TreeHouse does not prove the WiFi works.

### FundingCAPTCHA host

`install.sh` covers everything:

- Orbbec udev rule (2bc5:0807 → `MODE="0666"`) auto-written
- pygame uses `SDL_VIDEODRIVER=kmsdrm` — direct DRM, no compositor (no weston, no X)
- `video plugdev render` groups granted via service unit

Plug projector via HDMI before first start; pygame picks up the active output automatically.

---

## Playing the Pipes host provisioning

`pipes` is a Raspberry Pi 5 running Raspberry Pi OS **with desktop** on Debian 13 (trixie), arm64. Unlike the other Pis it needs the desktop image: that is what brings PipeWire, which `pipes-reuben` plays through. It builds the reuben audio engine from source, so it needs Rust as well as Python.

> First run on the box: 2026-11-21 (#235). Beyond the steps as first written, it needed uv (step 3) and a device profile (step 4).

### 1. OS + first boot

1. Flash Raspberry Pi OS with desktop (64-bit, trixie) with Raspberry Pi Imager. In its settings, set the hostname, create the user `ii`, and enable SSH.
2. Set the static IP from the [hardware inventory](#hardware-inventory) on the wired interface (`nmcli`, or the desktop's network menu).
3. `sudo apt update && sudo apt upgrade`, then `sudo apt install git git-lfs curl`.
4. Make it behave like a show machine:
   - `sudo raspi-config` → Display Options → Screen Blanking: off.
   - `sudo apt remove modemmanager` if it is installed: it grabs the encoder Picos' serial ports.

### 2. Clone repo, with samples and reuben

```bash
cd /home/ii
git clone https://github.com/Impractical-Instruments/CommunityGarden.git
cd CommunityGarden
git lfs install && git lfs pull --include "ShowControl/PlayingThePipes/Lamplight2026/media/*"
git submodule update --init
```

### 3. Rust and uv

As `ii` (not root), install uv (for `pipes-bridge`) and rustup, then let rustup fetch the toolchain and crates reuben pins:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
. ~/.cargo/env
cd ~/CommunityGarden/vendor/reuben && cargo fetch
```

### 4. Device profile

Write the device profile for the box's audio interface and commit it as `ShowControl/PlayingThePipes/reuben/pipes.profile.json` ([PlayingThePipes.md → Device profile](PlayingThePipes.md#device-profile)). `pipes-reuben` restarts in a loop until it exists.

### 5. Install the services

```bash
sudo bash scripts/install-services.sh PlayingThePipes
```

This installs the build packages (`libasound2-dev`, `build-essential`, `pkg-config`), adds `ii` to the `audio` and `dialout` groups, enables lingering for `ii`, builds reuben, and installs and starts `pipes-reuben` and `pipes-bridge`. The first reuben build is the slow part.

Then run [LAN deploy bootstrap](#5-lan-deploy-bootstrap) as on the Pis.

### 6. Check

Reboot and **do not log in**. Audio should play, and `http://192.168.1.13:8767/health` should show `ok: true` with both Picos plugged in. If not: [PlayingThePipes.md → Troubleshooting](PlayingThePipes.md#troubleshooting).

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
    User ii
```

Copy laptop public key to each host's `~/.ssh/authorized_keys`:

```bash
ssh-copy-id flowerbeds
ssh-copy-id treehouse
ssh-copy-id captcha
ssh-copy-id pipes
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

The operator laptop also runs the FlowerBeds layout GUI (Windows, browser-based). See [FlowerBeds.md → Layout tool](FlowerBeds.md#layout-tool) for usage. Requirements: uv; run it with `uv run` as in the layout tool's docs.
