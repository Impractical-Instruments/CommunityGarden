# FlowerBeds servo controller

Arduino sketch for the OpenRB-150 (SAMD21) boards that drive the FlowerBeds Dynamixel servos. One board per `flowerbeds_controller_<N>` entry in `ShowControl/network.json`.

- **Libraries:** `Dynamixel2Arduino`, `Ethernet`, `OSCMessage` (CNMAT).
- **Boot:** scans the Dynamixel bus at each baud rate and remembers which servo IDs answered.
- **Protocol** (OSC over UDP, on the board's `osc_port`):
  - `/cg/ff/rot [int motor_id, float degrees]` — aim one servo. A cross-layer contract with `ShowControl/FlowerBeds` (AGENTS.md constraint 2).
  - `/cg/ff/ping` — replies `/cg/ff/pong` with the scan result and packet counters. `ShowControl/FlowerBeds/diag.py` reads it.
  - `/cg/ff/hb` — the same status, broadcast once a second on port 9100.
- **Addresses:** `config.h` is generated from `network.json` by `scripts/hooks/firmware_config_gen.py`. Do not edit it or write addresses in the sketch.

## Flashing

1. Set `FLOWERBEDS_BOARD` near the top of the `.ino` to the board's number. It is committed as `0`, which does not compile, so two boards cannot end up with one MAC and IP. Do not commit the number.
2. Build and upload from the Arduino IDE with the OpenRB-150 board selected.
3. Check it: the layout tool (`ShowControl/FlowerBeds/layout_tool.py`) shows each controller's status, and its Aim mode moves one servo.
