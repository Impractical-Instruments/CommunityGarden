# Firmware

One directory per microcontroller program under `Firmware/`. Each README has the board, libraries, protocol and how to flash. [`Firmware/README.md`](../../Firmware/README.md) compares them in one table.

- [`FlowerBeds_Follow_ServoController/`](../../Firmware/FlowerBeds_Follow_ServoController/README.md): the OpenRB-150 boards that aim the FlowerBeds servos, over OSC on Ethernet.
- [`TreeHouse_Controllers/`](../../Firmware/TreeHouse_Controllers/README.md): one ESP32-S3 per TreeHouse location, driving its LEDs. The only firmware with tests.
- [`TreeHouse_BranchController/`](../../Firmware/TreeHouse_BranchController/README.md): the OpenRB-150 that drives the Branch servos, over USB serial.
- [`PlayingThePipes_EncoderPico/`](../../Firmware/PlayingThePipes_EncoderPico/README.md): the two Picos that read the Playing the Pipes encoders.

Rules that hold for all of them:

- **No network address is written in firmware.** `scripts/hooks/firmware_config_gen.py` generates `TreeHouse_Controllers/include/net_config.h` and `FlowerBeds_Follow_ServoController/config.h` from `ShowControl/network.json`. Re-run it after editing that file; a test fails if a committed header is stale.
- **`/cg/ff/rot` is a cross-layer contract** between the FlowerBeds firmware and `ShowControl/FlowerBeds`. Change both together. Every OSC address is in [`docs/osc-fabric.md`](../osc-fabric.md).
- **Flashing a FlowerBeds board:** set `FLOWERBEDS_BOARD` first, and do not commit the number. Its README has the steps.
- **Tests and builds:** `make test-firmware` and `make build-firmware`; see [Running & testing](running-and-testing.md#tests).
