# TreeHouse branch controller

Arduino sketch for the OpenRB-150 (SAMD21) that drives the TreeHouse Branch servos. It is on USB serial, not the network, so it has no IP or MAC (ADR-0005).

- **Libraries:** `Dynamixel2Arduino`, `ArduinoJson` (6.x or later).
- **Boot:** scans the Dynamixel bus at each baud rate and remembers which servo IDs answered.
- **Protocol** (JSON lines over USB serial, 115200 baud):
  - In: `{"id": 1, "pos": 90.0}` — move servo `id` to `pos` degrees.
  - Out: `{"id": 1, "ok": true}` — acknowledges each command.
- **Host side:** `ShowControl/TreeHouse/branches.py` (`BranchDriver` is the serial driver, `BranchController` the Controllable). Motor IDs and positions belong in `ShowControl/TreeHouse/settings.json`, not here.

## Flashing

Build and upload from the Arduino IDE with the OpenRB-150 board selected. There is nothing to configure per board.
