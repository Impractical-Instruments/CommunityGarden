# OSC Fabric

Every OSC address this repo sends or receives, the rule for when a signal is sent, and what is in `ShowControl/network.json`. Why the Fabric is shaped this way: [ADR-0007](adr/0007-osc-fabric-schema.md). All messages are OSC over UDP.

## Fabric signals: Elements to the TreeHouse

Received by `ShowControl/TreeHouse/osc_server.py` on `elements.treehouse.osc_port`. Only the TreeHouse listens; no other Element has an OSC server.

| Address | Args | Sender | Meaning |
|---|---|---|---|
| `/flowerbeds/activity` | float 0–1 | FlowerBeds `main.py`, through `FabricClient` | Tracked Visitors / `activity_max_blobs`, capped at 1 |
| `/captcha/intensity` | float 0–1 | FundingCAPTCHA `kiosk.py`, through `FabricClient` | Arc progress toward Blow-Up |
| `/captcha/blowup` | none | FundingCAPTCHA `kiosk.py`, through `FabricClient` | One-shot: a Blow-Up fired |
| `/pipes/activity` | float 0–1 | nothing yet | Music engagement. The TreeHouse handles it; Playing the Pipes does not send it |
| `/treehouse/mode` | string | an operator's OSC tool | `active`, `dim` or `inactive`. The Dashboard sets the same thing over HTTP |
| `/treehouse/brightness` | float 0–1 | an operator's OSC tool | Dim level override |
| `/lookingglass/scene` | string | an operator's OSC tool | `bloom`, `fractal`, `mycelium` or `cosmos` |

## Garden State: the TreeHouse to its location controllers

`ShowControl/TreeHouse/location_sender.py` sends the same six addresses, with the same arguments, to every `firmware.treehouse_<location>` entry: `/flowerbeds/activity`, `/captcha/intensity`, `/captcha/blowup`, `/pipes/activity`, `/treehouse/mode`, `/treehouse/brightness`. `Firmware/TreeHouse_Controllers/lib/GardenState/GardenState.cpp` receives them. Here `/treehouse/brightness` is the TreeHouse's current brightness, not an override.

## Looking Glass: the TreeHouse to its renderer, on localhost

`ShowControl/TreeHouse/controllables/video.py` sends all three every frame to `looking_glass/renderer.py` on `127.0.0.1`, port `looking_glass.renderer_port` in the TreeHouse `settings.json`.

| Address | Args | Meaning |
|---|---|---|
| `/lookingglass/scene` | string | Which shader to show |
| `/lookingglass/time` | float, seconds | Show time, scaled by the scene speed |
| `/lookingglass/intensity` | float 0–1 | Mean of the three Element signals, times brightness |

## FlowerBeds servo controllers

Between `ShowControl/FlowerBeds` and each `firmware.flowerbeds_controller_<N>` (`Firmware/FlowerBeds_Follow_ServoController/`). `/cg/ff/rot` is a cross-layer contract: change Python and firmware together.

| Address | Args | Direction | Meaning |
|---|---|---|---|
| `/cg/ff/rot` | int motor ID, float degrees | `controllers.py` to every controller | Aim one motor. Sent every frame; a controller ignores IDs it does not own. The sign is flipped on send (software is counter-clockwise positive) |
| `/cg/ff/ping` | none | `diag.py` to one controller | Ask for status |
| `/cg/ff/pong` | int controller ID, int baud, int servo count, string servo IDs, int packets received, int packets dropped, int last motor ID, float last degrees | controller to whoever pinged | Status reply |
| `/cg/ff/hb` | same as `/cg/ff/pong` | controller, broadcast once a second | Status heartbeat. Nothing in this repo listens for it |

## Playing the Pipes: the encoder bridge to reuben

`ShowControl/PlayingThePipes/encoder_bridge.py` sends to reuben on `elements.pipes.reuben_osc_port`. The addresses are built in `pipes_control.py` and must match the input pipes in `reuben/pipes.json`. This is not part of the Fabric.

| Address | Args | Meaning |
|---|---|---|
| `/pipes/knob<N>/<param>/in` | float | One knob's `position`, `grain_size`, `density`, `spray` or `level`; N from 0 |
| `/pipes/loop<N>/level/in` | float 0–1 | One loop's level; N from 1 |

## When a signal is sent

The rule is `SignalGate` in `ShowControl/OSCFabric/gate.py`. `FabricClient` and `location_sender.py` both use it. Send any OSC that crosses from one Element to another through `FabricClient` (`ShowControl/OSCFabric/`), which reads its addresses from `network.json`.

- **On change:** a float is sent when it moves by more than `change_epsilon`; a string when it differs.
- **Heartbeat:** every signal is sent again once `heartbeat_interval_s` has passed since it was last sent. A `FabricClient` only does this if its owner calls `tick(dt)`: FlowerBeds does; FundingCAPTCHA does not, so `/captcha/intensity` is sent on change only.
- **Events** (`/captcha/blowup`) are sent once, straight away, and never repeated.
- **Dead sender, TreeHouse:** an Element silent for more than 2 × `heartbeat_interval_s` has its signals set to 0 (`garden_state.py`). An Element that has never sent is not dead.
- **Dead sender, location controller:** after 10 s without a message, a controller falls back to an idle breathe (`GardenState.h`).

## `network.json`

Every IP, MAC and port on the Show Network. Nothing else may hold one (AGENTS.md constraint 3). Python reads it through `OSCFabric.load_network_config()`; `scripts/hooks/firmware_config_gen.py` writes the firmware headers from it and must be re-run after an edit.

- `lan.gateway`, `lan.netmask`: the Show Network, for the location controllers' static addresses.
- `heartbeat_interval_s`, `change_epsilon`: the send rule above.
- `elements.<name>` for `treehouse`, `flowerbeds`, `captcha`, `pipes`: `ip`, `osc_port`, `http_port` (the Element's monitoring server). Only the TreeHouse's `osc_port` has a listener. `pipes` also has `reuben_osc_port` and `reuben_structure_port`.
- `firmware.flowerbeds_controller_<N>`: `ip`, `mac`, `osc_port`. A new board is a new entry.
- `firmware.treehouse_<location>` for `swannatopia`, `julia`, `jess`, `dormer`, `garage`: `ip`, `osc_port`. `mac` is null and not read.
- `firmware.treehouse_branch`: all null. The Branch controller is on USB serial (ADR-0005).
