# ADR 0007 — OSC Fabric message schema

**Status:** Accepted

## Context

ADR-0001 established OSC/UDP as the cross-element communication protocol. As the senders (FlowerBeds, FundingCAPTCHA, Playing the Pipes) are now being implemented, the concrete addresses, value types, fire semantics, and network-addressing strategy need to be pinned down so all four elements and the dashboard can be built to a shared contract.

The TreeHouse OSC receive side had four addresses sketched in `osc_server.py`; this ADR makes that sketch canonical and extends it.

## Decision

### Address schema

| Address | Direction | Type | Semantics |
|---|---|---|---|
| `/flowerbeds/activity` | FlowerBeds → TreeHouse | float 0.0–1.0 | EMA(blob\_count / configured\_max), clamped 0–1 |
| `/captcha/game_started` | CAPTCHA → TreeHouse | (no args) | One-shot when a player sits down |
| `/captcha/intensity` | CAPTCHA → TreeHouse | float 0.0–1.0 | `level / total_levels`; 0.0 when idle; resets to 0.0 immediately after blowup |
| `/captcha/blowup` | CAPTCHA → TreeHouse | (no args) | One-shot when player loses at max intensity (reward event, not failure) |
| `/pipes/activity` | Pipes → TreeHouse | float 0.0–1.0 | Input activity normalised (expected to shift to smoothed output activity once music system is ready) |
| `/treehouse/mode` | Dashboard → TreeHouse | string | `"active"` \| `"dim"` \| `"inactive"` |
| `/flowerbeds/mode` | Dashboard → FlowerBeds | string | `"active"` \| `"dim"` \| `"inactive"` |
| `/captcha/mode` | Dashboard → CAPTCHA | string | `"active"` \| `"dim"` \| `"inactive"` |
| `/captcha/restart` | Any → CAPTCHA | (no args) | Hard-restart CV pipeline: close camera, reopen, redo background calibration |
| `/pipes/mode` | Dashboard → Pipes | string | `"active"` \| `"dim"` \| `"inactive"` |
| `/treehouse/brightness` | TouchOSC → TreeHouse | float 0.0–1.0 | Debug/operator override only; not part of the mode system |

### Fire semantics for continuous signals

Continuous float signals (`*/activity`, `/captcha/intensity`) are sent:
- **On change** — whenever the value changes meaningfully (sender-side epsilon filtering to avoid noise)
- **On heartbeat** — unconditionally every `heartbeat_interval_s` seconds even if unchanged

The heartbeat serves as a liveness signal. The global heartbeat interval lives in `network.json` (default: 5s).

One-shot events (`/captcha/game_started`, `/captcha/blowup`) are sent exactly once per occurrence with no heartbeat.

### Dead-sender policy

If the TreeHouse has not received a message from a sender in `2 × heartbeat_interval_s`, it treats that sender's contribution as 0.0. This prevents a crashed element from freezing the TreeHouse at a stale activity value.

### Mode vocabulary

All elements use the same three mode strings:

- `"active"` — fully operational
- `"dim"` — reduced/ambient (lights low, motion slowed or minimal, screen dimmed)
- `"inactive"` — completely stopped, appears unattended

Each element defines what `"dim"` means for its own outputs. The dashboard composes named scene presets by sending individual per-element mode messages.

**Breaking change:** TreeHouse `ShowMode` renames `"full"` → `"active"` and `"off"` → `"inactive"`.

### Network configuration — single source of truth

All network addressing (element IPs, OSC listen ports, HTTP ports, firmware IPs/MACs) lives in a single shared file: `ShowControl/network.json`. No element hardcodes an IP, port, or MAC address.

```json
{
  "heartbeat_interval_s": 5,
  "elements": {
    "treehouse":  { "ip": "192.168.1.10", "osc_port": 9001, "http_port": 8766 },
    "flowerbeds": { "ip": "192.168.1.11", "osc_port": 9002, "http_port": 8765 },
    "captcha":    { "ip": "192.168.1.12", "osc_port": 9003, "http_port": 8080 },
    "pipes":      { "ip": "192.168.1.13", "osc_port": 9004, "http_port": 8767 }
  },
  "firmware": {
    "flowerbeds_controller_1": { "ip": "192.168.1.50", "mac": "DE:AD:BE:EF:15:00", "osc_port": 9000 },
    "flowerbeds_controller_2": { "ip": "192.168.1.51", "mac": "DE:AD:BE:EF:15:01", "osc_port": 9000 },
    "treehouse_branch":        { "ip": null, "mac": null, "osc_port": null }
  }
}
```

Firmware targets read their config via a generated `config.h` produced by `scripts/hooks/firmware_config_gen.py` before flashing. The branch controller uses USB serial (ADR-0005) and has no IP/MAC.

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
