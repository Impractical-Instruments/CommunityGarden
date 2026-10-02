# ADR 0021 — TreeHouse controllers run standalone; a fifth controller welds in the Garage

**Status:** Accepted
**Amends:** [ADR-0020](0020-treehouse-esp32s3-location-controllers.md)

## Context

ADR-0020 put one ESP32-S3 at each TreeHouse location and had the Pi drive them with Garden
State: each channel's Signal Bag reduced the Fabric fields to a drive level, and patterns
animated from it.

For this round of the show, the looks matter more than the reactivity. Each location has a
specific, fixed look it should hold all the time, and Garden-State-driven brightness was
actively working against that: a quiet installation meant dim windows. Separately, a fifth
location was added: the Garage, with a welding effect.

## Decision

### Animate from a fully-active Garden State, ignore what arrives

Every controller animates from `cg::fullyActive()`: every Element at 1.0 and the show
Active. Every Signal Bag saturates there, so each channel sits permanently at its
`max_level`, which is the look it was tuned to have at full activity. The patterns still
move. Only the level they move around stops tracking the room.

The plumbing stays. Controllers still join the Show Network, parse every OSC packet into
the `GardenStateStore` and log it on the heartbeat (marked `(standalone)`), and the Pi's
`location_sender.py` keeps sending. A single constant, `kFollowGardenState` in
`src/main.cpp`, chooses which state the animators see. Turning reactivity back on is that
one line and a reflash.

Consequences of not following Garden State:

- Channels never go stale, so the idle breathe fallback never runs.
- No Blow-Up Reaction.
- `/treehouse/mode` and `/treehouse/brightness` no longer dim anything. The only way to
  darken a location is to cut its power.

The last point reverses ADR-0020's "inactive mode is the only path to darkness", knowingly.

### Per-location looks

| Location | Channel | Look |
|---|---|---|
| Dormer | dimmer | `Breathe`: a 12.5 s breath between 40% and 80%, never dark |
| Julia | dimmer | `Wander`: a drunk walk between 40% and 80%; a full sweep takes about a minute |
| Jess | 2 strips + flash | `Rave` on both strips: pink/violet/blue/cyan drifting a palette lap every ~3 min; the flash strobes 4 eighth-note pulses at 120 BPM, then waits 20 s |
| Swannatopia | 3 strips | `Fire` in the fireplace; warm `Incandescent` overhead; the chandelier the same look at half brightness and more amber |
| Garage | strip + arc | `Weld` (below) |

`Breathe` and `Wander` both span `min_level` up to the drive, so the floor of a look is
the channel's `min_level`, the same field that already meant "never darker than this".

### The Garage: a cap-discharge arc and 16 glow pixels

The arc light is a MOSFET dumping a charged capacitor through a very bright LED. The cap
sets how long the flash lasts, so the arc is not dimmed. One **tap** is a short high pulse
on the gate. This is a new channel kind, `ChannelKind::Trigger`, driven by a `Welder`
rather than by a pattern.

The `Welder` (`lib/Weld`) works on three nested, random timescales:

| Level | Gap | Count |
|---|---|---|
| Session | 8–25 s of quiet between sessions | 2–6 bursts |
| Burst | 1–5 s between bursts | 1–4 taps |
| Tap | 20–50 ms between taps (the cap's recharge window) | 15 ms gate pulse |

The ranges live in `ChannelSpec::weld` in `src/targets/garage.h`.

- **Timing granularity.** The `Welder` is polled every `loop()`, not every 16 ms frame,
  because frame jitter would smear a 20 ms stutter.
- **Recharge guarantee.** Each gap is measured from the moment a tap actually fires. A
  stalled loop therefore can never fire two taps closer together than the cap can
  recharge.
- **Seeding.** The `Welder` is seeded from `esp_random()` after the radio is up, so the
  rhythm differs on every boot.

Every tap also calls `strike()` on every animator. The strip channel runs the `Weld`
pattern, which is the only pattern that reads `strike()`:

- Each strike gives a crackling violet-white flash under the arc, which is gone in about
  0.1 s.
- Behind it, the heated metal cools through orange to dark over a few seconds.
- Each tap adds heat, so a four-tap burst glows longer than a single pop.

Between sessions the Garage is dark, which is what makes the next one surprising.

## Consequences

- `network.json` gains `treehouse_garage` (192.168.1.64), and `firmware_config_gen.py`
  generates `CG_IP_GARAGE`. The Pi's `locations.controllers` lists it too. It receives
  Garden State it ignores, so the sender stays uniform.
- `platformio.ini` gains `garage` and `garage-selftest`. Under self-test the arc taps once
  at the start of each colour phase, then fires a four-tap, 40 ms burst at the start of
  the white phase to prove the cap recharges in time.
- The Signal Bag weights in each target header are now inert. They are kept so that
  flipping `kFollowGardenState` restores the ADR-0020 behaviour without retuning.
- The Garage pins in `garage.h` are placeholders until the board is wired.
