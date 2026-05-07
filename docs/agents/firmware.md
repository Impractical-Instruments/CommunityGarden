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

## TreeHouse Pico LEDs

`Firmware/TreeHouse_PicoLEDs/main.py` — MicroPython on Raspberry Pi Pico; drives SK6812 RGBW LED strips.
