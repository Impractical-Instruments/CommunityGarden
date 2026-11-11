# Firmware

One directory per microcontroller program. All four are live.

| Directory | Board | Toolchain | Drives | Talks to |
|---|---|---|---|---|
| `FlowerBeds_Follow_ServoController/` | OpenRB-150 (SAMD21) + Ethernet | Arduino | FlowerBeds Dynamixel servos | OSC over Ethernet from `ShowControl/FlowerBeds` |
| `TreeHouse_Controllers/` | ESP32-S3 DevKitC-1, one per location | PlatformIO | Every TreeHouse LED | Garden State over WiFi from `ShowControl/TreeHouse` |
| `TreeHouse_BranchController/` | OpenRB-150 (SAMD21) | Arduino | TreeHouse Branch servos | JSON lines over USB serial from `ShowControl/TreeHouse` |
| `PlayingThePipes_EncoderPico/` | Raspberry Pi Pico, two of them | MicroPython | Reads 6 rotary encoders each | Text lines over USB serial to Max |

- **Network addresses** are never written in firmware. `scripts/hooks/firmware_config_gen.py` generates `TreeHouse_Controllers/include/net_config.h` and `FlowerBeds_Follow_ServoController/config.h` from `ShowControl/network.json`; re-run it after editing that file.
- **Cross-layer contract:** the OSC address `/cg/ff/rot` is shared by the FlowerBeds firmware and `ShowControl/FlowerBeds`. Change both together.
- **Tests:** only `TreeHouse_Controllers` has them (`make test-firmware`); CI runs them and compiles that project.
- **Bringing up an ESP32-S3:** the `signsoflife-*` environments in `TreeHouse_Controllers`.

Each directory's README has the board, libraries, protocol and how to flash. Agent notes: `docs/agents/firmware.md`.
