# Playing the Pipes

The Element growing out of the base of the TreeHouse. Pipes and conduit with valves and switches; Visitors operate the controls to **steer** a music engine via **Tiller Control** (not direct note triggering).

**Host:** `pipes` · 192.168.1.13 (Ubuntu Desktop) · **Health:** http://192.168.1.13:8767/health · **Services:** `pipes-reuben`, `pipes-bridge` (systemd)

> **Not yet run on the box.** The install and deploy path below is built and tested on a dev machine (#239). How reuben reaches the audio interface at boot is still to be confirmed on the box (#235). If #235 changes it, this page and `deploy/pipes-reuben.service` change with it.

## Code

### Architecture summary

Two Pi Pico microcontrollers (ADR-0014) read rotary encoders mounted on the valves and switches and send encoder deltas as text lines over USB serial. Two services on the `pipes` host turn those into sound (ADR-0026):

| Service | What it runs | What it does |
|---|---|---|
| `pipes-bridge` | `encoder_bridge.py` | Finds the Picos by USB vendor ID on any port, turns their detents into knob and loop values (`pipes_control.py`, tuned by `settings.json`), and sends them to reuben as OSC every 10 ms. Serves `/health` |
| `pipes-reuben` | `reuben play reuben/pipes.json --io-map reuben/pipes.profile.json` | The audio engine: plays the instrument on the audio interface the device profile names |

[reuben](../vendor/reuben) is our audio engine, a git submodule at `vendor/reuben`, built from source on the box. The instrument is `ShowControl/PlayingThePipes/reuben/pipes.json`: 12 grain voices (one per encoder, dry), 13 stereo loops whose levels follow how busy the pipes are, the mic echo, and a limited master.

The bridge and reuben talk over OSC on the box itself. Those addresses are not part of the OSC Fabric; they are listed in [osc-fabric.md](osc-fabric.md#playing-the-pipes-the-encoder-bridge-to-reuben). The Element does not yet send `/pipes/activity` to the TreeHouse (see [Open items](#open-items)).

Key references:
- ADR-0026: Playing the Pipes runs on reuben, on Linux
- ADR-0014: the encoder Picos and their serial protocol
- `ShowControl/PlayingThePipes/README.md`: every file, the bridge-to-instrument contract, and where the instrument differs from the old Max patch
- `Firmware/PlayingThePipes_EncoderPico/`: Pico firmware

### Mic path

The instrument opens a stereo input (logical input channels 0 and 1) and echoes it back into the mix:

```
mic in (L, R) → gain → pre-delay (0.5 s left, 0.75 s right) → feedback echo → master
```

- **The pre-delay is what keeps the speakers out of the mic.** By the time the mic's sound leaves the speakers, the original has ended, so it cannot build into feedback howl. Do not shorten it without testing on the real speakers.
- **Which physical inputs are the mic** is set by the device profile's `input` block, not by the instrument.
- **reuben exits at startup if there is no input device.** `pipes-reuben` then restarts every 5 s until one appears. Silence plus a restart loop in `journalctl -u pipes-reuben` usually means the audio interface is unplugged or the profile names a device that isn't there.

Everything (grains, loops, mic echo) is summed into the master: the master volume (`/volume/in`, default 0.25, applied as the gains of the master `mix` nodes), a limiter (about 20:1, fast attack, −1 dB), then a hard clamp at ±1. The volume comes before the limiter so the limiter guards the real output at any volume.

### Device profile

`ShowControl/PlayingThePipes/reuben/pipes.profile.json` tells reuben which audio device to open and which of its channels are the speakers and the mic. It is specific to the box's audio interface and is committed next to the instrument. Format: `vendor/reuben/docs/device-profile.md`.

`pipes-reuben` cannot start without it. `make validate-instruments` skips files named `*.profile.json`.

### Health (`/health`)

`GET http://192.168.1.13:8767/health`, served by `pipes-bridge`. The Dashboard's Playing the Pipes page reads it.

| Field | Meaning |
|---|---|
| `ok` | Both Pico boards are connected **and** reuben is alive |
| `picos_connected` | How many Pico serial ports are open |
| `boards` | Which board IDs have been heard from (`[0, 1]` when both are up) |
| `last_event_age_s` | Seconds since a Pico last sent a turn; `null` if none yet |
| `reuben_alive` | reuben's structure channel accepts a connection |
| `last_virtual_age_s`, `last_source` | Turns from the Dashboard's virtual encoder surface, kept apart so they never make the Picos look connected |
| `fake_encoders` | The bridge was started with `--fake-encoders` (never on the box) |

It also carries the loop mix state. `GET /state` returns what the virtual encoder surface draws.

### Running it on a laptop

```bash
make pipes            # reuben + the bridge with fake encoders, on the default audio devices (mic included)
make pipes-surface    # reuben + the bridge + the Dashboard; turn the knobs yourself from the page it prints
```

`REUBEN_PLAY_ARGS="--io-map <profile>"` picks other devices. Both need Rust to build reuben (`make reuben`).

#### Virtual encoder surface

The Dashboard's Playing the Pipes page can turn the knobs without the Picos: it posts encoder lines to the bridge, which treats them like Pico turns, mixed with any real ones. Arm it on the page first; it disarms when the tab is hidden or loses focus, and after 5 min idle. It works against the box as well as a laptop.

### The Max patch

`ShowControl/PlayingThePipes/Lamplight2026/` is the Max 9 project the reuben instrument was ported from. Max does not run on the box, so it is **not a fallback**: it is the reference for the by-ear A/B, run on a laptop, until the reuben version is signed off (#177). After that it is deleted and the samples in `Lamplight2026/media/` move next to the instrument. Until then the instrument reads its samples from there.

To open it: Max 9, the Grainflow package from Max's Package Manager, and Max 9's ABL device objects. The patch's `fake_encoder` objects stand in for the Picos.

### Open items

- `/pipes/activity` is not implemented. The TreeHouse's `GardenState.pipes_activity` is always 0. The bridge already knows how busy the pipes are (it drives the loop mix from it), so it is the place to send it from.
- The launch method for `pipes-reuben` is unconfirmed on the box (#235).

## Operations

For whoever is running the Element at a show. A code change rarely needs it.

### Service management

```bash
sudo systemctl status pipes-reuben pipes-bridge
sudo systemctl restart pipes-reuben      # reloads the instrument and the device profile; takes a few seconds to load the samples
sudo systemctl restart pipes-bridge      # reloads settings.json
journalctl -u pipes-reuben -u pipes-bridge -f
```

Both units are `Restart=always`, `RestartSec=5`.

How `pipes-reuben` reaches the audio interface: on Ubuntu Desktop, PipeWire owns the interface and runs in the `ii` user's own systemd session. `install.sh` enables lingering for `ii` (`loginctl enable-linger`), so that session starts at boot with nobody logged in, and the unit points reuben at it through `XDG_RUNTIME_DIR`. `ii` is in the `audio` group (the interface) and `dialout` (the Picos' `/dev/ttyACM*`).

### Deploying code updates

From the operator laptop on the show LAN:

```bash
scripts/deploy.sh pipes PlayingThePipes
```

This pushes the current branch, pushes the reuben commit that branch pins into the box's `vendor/reuben` (the box never fetches reuben from GitHub), and runs `ShowControl/PlayingThePipes/deploy/install.sh`. The installer rebuilds reuben and restarts both services. If the build fails, nothing is restarted and the box keeps playing the old binary.

A deploy needs no internet on the box, except when it brings:

| Change | What the box needs, once, with internet |
|---|---|
| A reuben bump that adds a Rust crate | `cd ~/CommunityGarden/vendor/reuben && cargo fetch` |
| A reuben bump that changes `rust-toolchain.toml` | Any `cargo` command in `vendor/reuben`; rustup downloads the new toolchain |
| A new or changed sample in `Lamplight2026/media/` | `cd ~/CommunityGarden && git lfs pull` (samples are Git LFS files; a deploy push does not carry them) |

In each case the installer stops with an error before restarting anything. Do these at home before a show, not at the venue.

Tuning changes (`settings.json`, `reuben/pipes.json`) deploy the same way and need no internet.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard shows Pipes offline | `pipes-bridge` not running, or the box is off the network | `sudo systemctl status pipes-bridge`; `journalctl -u pipes-bridge -b` |
| `/health` has `reuben_alive: false`, no audio | `pipes-reuben` is in a restart loop | `journalctl -u pipes-reuben -b`. No input or output device: check the audio interface is plugged in and matches `pipes.profile.json`. Missing profile: commit it. Missing binary: run the installer |
| `/health` has `picos_connected` below 2 | A Pico is unplugged | Reseat its USB cable; the bridge reconnects by itself. `ls /dev/ttyACM*` should list two |
| A Pico is plugged in but never connects | Something else holds the port, usually ModemManager | `sudo apt remove modemmanager`, replug |
| Audio is fine, encoders do nothing | Bridge is not reaching reuben, or the knobs are asleep | Check `/health`; turn a knob and watch `last_event_age_s` reset; try the virtual encoder surface |
| Audio stops when someone logs in at the desktop | The login session took the audio interface | Record it on #235; restart `pipes-reuben` |
| Deploy stops at "still Git LFS pointers" | New samples did not arrive | `git lfs pull` on the box with internet (see [Deploying](#deploying-code-updates)) |
| Deploy stops in `cargo build` | A new crate or toolchain is not on the box | See [Deploying](#deploying-code-updates) |
