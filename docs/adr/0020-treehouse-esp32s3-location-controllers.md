# ADR 0020 — TreeHouse lighting: one ESP32-S3 per location, driven by Garden State

**Status:** Accepted
**Supersedes:** [ADR-0010](0010-treehouse-led-pico-architecture.md)

## Context

ADR-0010 put two MicroPython Picos in the garage as dumb pixel sinks: the Pi computed every
frame and pushed `{"pin", "pixels"}` JSON lines over USB serial at 30 fps. That decision
assumed all the microcontrollers live in the garage and copper runs radiate out to each
display.

Two things changed.

**The wire runs are the problem.** SK6812 data is a 800 kHz single-ended signal. Runs from
the garage to the Attic and the Dormer are long enough that the data line needs repeaters or
differential conversion to stay clean, and every one of those runs is a failure point that
only shows up under show conditions. The 12 V filament and high-power LED circuits added
since ADR-0010 also want their MOSFET drivers physically close to the load, not at the end of
a long run of high-current cable.

**Every frame depended on a cable.** A dumb pixel sink cannot ride out an interruption — a
disconnected USB cable or a stalled Pi means the lights freeze or go dark mid-show.

The locations have also been renamed and regrouped. The house is now organised as four
locations — **Swannatopia**, **Julia**, **Jess**, and **Dormer** — replacing the earlier
per-diorama naming.

## Decision

### One ESP32-S3 per location

Each location gets its own ESP32-S3, mounted at the location, driving only that location's
channels:

| Location | Channels |
|---|---|
| Swannatopia | 3 × SK6812 RGBW strips (8 px each) |
| Julia | 1 × PWM MOSFET dimming a 12 V LED filament string |
| Jess | 2 × SK6812 RGBW strips (20 px each) + 1 × PWM MOSFET flash channel |
| Dormer | 1 × PWM MOSFET dimming a 12 V LED circuit |

LED counts are provisional and live as single constants in each target header.

Fault isolation is now per-location: a dead controller darkens one location, not a functional
group.

### WiFi + OSC, carrying Garden State — not pixels

The Pi broadcasts **Garden State** to each controller over UDP/OSC. It does not send pixels.
The addresses are exactly the Fabric addresses the TreeHouse already consumes (ADR-0007), so
a controller can be bench-tested by pointing any Fabric sender at it:

| Address | Args | Meaning |
|---|---|---|
| `/flowerbeds/activity` | `f` | 0–1 |
| `/captcha/intensity` | `f` | 0–1 |
| `/captcha/blowup` | — | one-shot |
| `/pipes/activity` | `f` | 0–1 |
| `/treehouse/mode` | `s` | `active` / `dim` / `inactive` |
| `/treehouse/brightness` | `f` | 0–1 |

### Animation runs on the controller

Each channel owns a **Signal Bag** (per-channel weights over the Garden State fields, as
described in CONTEXT.md) that reduces to a single 0–1 drive value, and a pattern that
consumes it. This inverts ADR-0010's "Pi is the animation engine" — deliberately. Because
state, not pixels, crosses the network, a lost packet costs nothing: the controller keeps
animating from the last state it heard. Bandwidth drops from 30 fps × pixel arrays to a
handful of small packets per second.

The cost is that animation logic now lives in firmware and a change means a reflash. That is
an acceptable trade for lighting that does not stop when the network hiccups.

### Failure behaviour: never go dark

- No Garden State for `CG_STATE_TIMEOUT_MS` (10 s) → channels fall back to a slow idle
  breathe rather than freezing or blacking out. A TreeHouse with dark windows reads as broken
  to Visitors; a slowly breathing one does not.
- WiFi drop → non-blocking reconnect with backoff while animation continues.
- `show_mode == inactive` → all channels off. This is the *only* path to darkness, because it
  is the one a human asked for.

### One PlatformIO project, four environments

`Firmware/TreeHouse_Controllers/` builds all four controllers from one codebase.
`platformio.ini` declares `env:swannatopia`, `env:julia`, `env:jess`, `env:dormer`, each
selecting a header in `src/targets/` via a `-D CG_TARGET_*` flag. A fifth environment,
`env:native`, runs the unit tests on the host.

Pure logic (OSC parsing, state store, signal bags, pattern math, dimmer curves) lives in
`lib/` and includes no Arduino headers, so it compiles and is tested natively. Hardware
binding (WiFi, UDP, NeoPixelBus, LEDC) lives in `src/` and is never linked into the test
build.

### Addressing from network.json, credentials outside git

Static IPs and ports for the four controllers live in `ShowControl/network.json`
(AGENTS.md constraint #3). `scripts/hooks/firmware_config_gen.py` — previously a stub —
generates `include/net_config.h` from it. WiFi credentials live in a gitignored
`include/secrets.h`; `secrets.h.example` is committed.

## Consequences

- `Firmware/TreeHouse_PicoLEDs/` is superseded. It stays in the tree until the ESP32-S3
  hardware is physically installed, then is removed along with `pico_driver.py` and the
  `pico_*` blocks in `settings.json`.
- The Pi gains `location_sender.py`, which broadcasts Garden State to the four controllers at
  `locations.send_hz`. It is additive: the existing Pico pixel path is untouched, so both can
  run during the hardware transition.
- Retuning a location's look is a reflash, not a settings edit. Weights and pattern choices
  are grouped at the top of each target header to keep that edit small.
- `network.json` gains a `lan` block (gateway, netmask) that static-IP firmware needs.
