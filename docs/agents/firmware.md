# Firmware

## FlowerBeds servo controller

`Firmware/FlowerBeds_Follow_ServoController/FlowerBeds_Follow_ServoController.ino` — deploy to each OpenRB-150 (SAMD21) board.

- Listens on OSC address `/cg/ff/rot` with args `[int motor_id, float rotation_deg]`
- Calls `setRotDeg()` on the target Dynamixel servo
- IP and MAC come from a generated `config.h` — do not hardcode them; edit `ShowControl/network.json` and run `scripts/hooks/firmware_config_gen.py` before flashing
- Each board needs a unique IP and MAC when running multiple controllers

Required Arduino libraries: `Dynamixel2Arduino`, `Ethernet`, `OSCMessage` (CNMAT).

## TreeHouse branch controller

`Firmware/TreeHouse_BranchController/` — communicates over USB serial, not Ethernet (see ADR-0005).

## TreeHouse location controllers

`Firmware/TreeHouse_Controllers/` — PlatformIO / Arduino C++ on ESP32-S3, one controller per location (see [ADR-0020](../adr/0020-treehouse-esp32s3-location-controllers.md)).

- One project, five environments: `swannatopia`, `julia`, `jess`, `dormer`, `garage`. Everything specific to a location is in `src/targets/<location>.h`.
- **Controllers currently ignore Garden State** ([ADR-0021](../adr/0021-treehouse-controllers-standalone-and-garage-welder.md)): they animate from `cg::fullyActive()`, so every channel holds its `max_level`. `kFollowGardenState` in `src/main.cpp` switches the Pi back on.
- The Garage arc is a `ChannelKind::Trigger` (cap-discharge flash, pulsed not dimmed) driven by `lib/Weld`'s `Welder`; every tap `strike()`s the `Weld` glow strip.
- The Pi sends **Garden State**, not pixels — the Fabric addresses (`/flowerbeds/activity`, `/captcha/intensity`, `/captcha/blowup`, `/pipes/activity`, `/treehouse/mode`, `/treehouse/brightness`) over UDP. Each controller animates locally, so a dropped packet costs nothing.
- IPs come from `ShowControl/network.json` via a generated `include/net_config.h` — do not hardcode them. Run `scripts/hooks/firmware_config_gen.py` after editing network.json.
- WiFi credentials live in a gitignored `include/secrets.h`; copy `include/secrets.h.example`.
- Host tests: `pio test -e native`. Everything in `lib/` is Arduino-free so it can be tested without hardware; `src/` is the hardware binding.
- Sender side on the Pi: `ShowControl/TreeHouse/location_sender.py`, configured by the `locations` block in `settings.json`.

Full details in `Firmware/TreeHouse_Controllers/README.md`.

## TreeHouse Pico LEDs (superseded)

`Firmware/TreeHouse_PicoLEDs/main.py` — MicroPython on Raspberry Pi Pico; drives SK6812 RGBW LED strips. Superseded by the location controllers above (ADR-0020); still in the tree until the ESP32-S3 hardware is installed.
