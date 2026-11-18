# ADR 0007 — OSC Fabric message schema

**Status:** Accepted. Amended 2026-11-11: five addresses that were never implemented are removed, and mode control is TreeHouse-only (see Amendment below).

## Context

ADR-0001 established OSC/UDP as the cross-element communication protocol. As the senders (FlowerBeds, FundingCAPTCHA, Playing the Pipes) are now being implemented, the concrete addresses, value types, fire semantics, and network-addressing strategy need to be pinned down so all four elements and the dashboard can be built to a shared contract.

The TreeHouse OSC receive side had four addresses sketched in `osc_server.py`; this ADR makes that sketch canonical and extends it.

## Decision

### Address schema, fire semantics and dead-sender policy

The address table and the send rules are kept current in [`docs/osc-fabric.md`](../osc-fabric.md). What this ADR decided:

- One address per signal, `/<element>/<signal>`, all sent to the TreeHouse.
- Continuous signals are sent on change (past a sender-side epsilon) and again on a heartbeat every `heartbeat_interval_s`, which doubles as a liveness signal. One-shot events are sent once, with no heartbeat.
- A sender silent for `2 × heartbeat_interval_s` has its contribution treated as 0.0, so a crashed Element cannot freeze the TreeHouse at a stale value.

### Mode vocabulary

All elements use the same three mode strings:

- `"active"` — fully operational
- `"dim"` — reduced/ambient (lights low, motion slowed or minimal, screen dimmed)
- `"inactive"` — completely stopped, appears unattended

Each element defines what `"dim"` means for its own outputs. The dashboard composes named scene presets by sending individual per-element mode messages.

**Breaking change:** TreeHouse `ShowMode` renames `"full"` → `"active"` and `"off"` → `"inactive"`.

### Network configuration — single source of truth

All network addressing (element IPs, OSC listen ports, HTTP ports, firmware IPs/MACs) lives in a single shared file: `ShowControl/network.json`. No element hardcodes an IP, port, or MAC address.

The keys are listed in [`docs/osc-fabric.md`](../osc-fabric.md#networkjson).

Firmware targets read their config via a generated header produced by `scripts/hooks/firmware_config_gen.py` before flashing. (It generates `Firmware/TreeHouse_Controllers/include/net_config.h` and `Firmware/FlowerBeds_Follow_ServoController/config.h`.) The branch controller uses USB serial (ADR-0005) and has no IP/MAC.

## Reasons

- A single address schema written before the senders are built prevents the TreeHouse receive side and the element send sides from drifting apart.
- On-change + heartbeat keeps network traffic near zero during quiet periods while giving the TreeHouse a reliable liveness signal.
- Per-element mode addresses let the dashboard compose arbitrary aggregate scene presets without a rigid global mode enum.
- A single `network.json` eliminates the "which settings.json has the real IP?" problem; ADR-0001's static-config-over-discovery principle applies at the whole-installation level, not just per element.
- Firmware codegen from `network.json` prevents copy-paste errors when flashing multiple controllers during festival load-in.

## Consequences

- Each element that sends fabric signals needs a fabric OSC client reading `network.json` for the TreeHouse address.
- Each element needs an OSC listener on its `osc_port` for inbound mode commands (new for FlowerBeds, CAPTCHA, and Pipes). CAPTCHA's listener (port 9003) is implemented in `app.py` (see ADR-0012); it handles `/captcha/restart` (hard-restart the CV pipeline / background calibration) in addition to any future mode commands.
- The dashboard `serve.py` must be upgraded from a static file server to a FastAPI app with a mode-relay endpoint that reads `network.json` and sends OSC.
- TreeHouse `ShowMode` enum values change: `"full"` → `"active"`, `"off"` → `"inactive"`. Any TouchOSC layouts sending `/treehouse/mode` need updating.
- `/captcha/intensity` is a discrete signal stepping in increments of `1/total_levels`; on-change sends will fire at level transitions, not continuously.

## Amendment (2026-11-11): unimplemented addresses removed

Five addresses in the original table never had both a sender and a receiver, and are removed from the schema rather than implemented:

- `/flowerbeds/mode`, `/captcha/mode`, `/pipes/mode`: only the TreeHouse runs an OSC server. FlowerBeds, FundingCAPTCHA and Playing the Pipes have no listener.
- `/captcha/restart`: FundingCAPTCHA restarts its camera over HTTP (`POST /api/restart` on its monitoring port), not OSC.
- `/captcha/game_started`: nothing sent it and the TreeHouse did not handle it.

Mode control is therefore TreeHouse-only. What this changes in the text above:

- "Mode vocabulary": the three mode strings are the TreeHouse's `ShowMode`. No other Element has a mode, and the Dashboard composes no per-element presets.
- "Consequences": FlowerBeds, FundingCAPTCHA and Pipes need no OSC listener. The Dashboard's mode-relay endpoint (`POST /api/mode`) is deleted; nothing called it. The Dashboard TreeHouse page sets the mode over HTTP, straight to the TreeHouse visualizer (`POST /control/show/mode`). `/treehouse/mode` stays as the OSC route to the same setting, for an operator's OSC tool.

