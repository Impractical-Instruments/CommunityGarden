# Firmware

## FlowerBeds servo controller

`Firmware/FlowerBeds_Follow_ServoController/FlowerBeds_Follow_ServoController.ino` — deploy to each OpenRB-150 (SAMD21) board.

- Listens on OSC address `/cg/ff/rot` with args `[int motor_id, float rotation_deg]`
- Calls `setRotDeg()` on the target Dynamixel servo
- MAC, IP and port come from `config.h` beside the sketch, generated from `ShowControl/network.json` by `scripts/hooks/firmware_config_gen.py` — do not hardcode them. Re-run the script after editing `network.json`.
- **Before flashing, set `FLOWERBEDS_BOARD` near the top of the `.ino`** to the board's number: board `<N>` is `firmware.flowerbeds_controller_<N>` in `network.json`. It is committed as `0`, which does not compile, so a board cannot be flashed with another board's MAC and IP by leaving a default in place. Do not commit the number you set. With `arduino-cli`, pass it instead: `--build-property "compiler.cpp.extra_flags=-DFLOWERBEDS_BOARD=1"`.
- A new board is a new `flowerbeds_controller_<N>` entry in `network.json`; the generator picks it up.

Required Arduino libraries: `Dynamixel2Arduino`, `Ethernet`, `OSCMessage` (CNMAT).

## TreeHouse branch controller

`Firmware/TreeHouse_BranchController/` — communicates over USB serial, not Ethernet (see ADR-0005).

## TreeHouse location controllers

`Firmware/TreeHouse_Controllers/` — PlatformIO / Arduino C++ on ESP32-S3, one controller per location (see [ADR-0020](../adr/0020-treehouse-esp32s3-location-controllers.md)).

- One project, five location environments: `swannatopia`, `julia`, `jess`, `dormer`, `garage`. Everything specific to a location is in `src/targets/<location>.h`.
- **Controllers currently ignore Garden State** ([ADR-0021](../adr/0021-treehouse-controllers-standalone-and-garage-welder.md)): they animate from `cg::fullyActive()`, so every channel holds its `max_level`. `kFollowGardenState` in `src/main.cpp` switches the Pi back on.
- The Garage arc is a `ChannelKind::Trigger` (cap-discharge flash, pulsed not dimmed) driven by `lib/Weld`'s `Welder`; every tap `strike()`s the `Weld` glow strip.
- The Pi sends **Garden State**, not pixels — the Fabric addresses (`/flowerbeds/activity`, `/captcha/intensity`, `/captcha/blowup`, `/pipes/activity`, `/treehouse/mode`, `/treehouse/brightness`) over UDP. Each controller animates locally, so a dropped packet costs nothing.
- IPs come from `ShowControl/network.json` via a generated `include/net_config.h` — do not hardcode them. Run `scripts/hooks/firmware_config_gen.py` after editing network.json.
- WiFi credentials live in a gitignored `include/secrets.h`; copy `include/secrets.h.example`.
- Host tests: `pio test -e native` (or `make test-firmware` from the repo root). Everything in `lib/` is Arduino-free so it can be tested without hardware; `src/` is the hardware binding. CI runs them, and compiles one environment of each kind (`make build-firmware`), on any PR that touches this directory.
- Board misbehaving? Flash `signsoflife-uart` or `signsoflife-usb` first: one file (`src/signsoflife/main.cpp`), no networking, no config headers. See "Bring-up" in the README.
- Sender side on the Pi: `ShowControl/TreeHouse/location_sender.py`, configured by the `locations` block in `settings.json`.

Full details in `Firmware/TreeHouse_Controllers/README.md`.
