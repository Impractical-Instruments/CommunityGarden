# TreeHouse location controllers

Firmware for the four ESP32-S3 controllers that light the TreeHouse — one per
location. See [ADR-0020](../../docs/adr/0020-treehouse-esp32s3-location-controllers.md)
for why it is built this way.

| Environment | Location | Channels | Static IP |
|---|---|---|---|
| `swannatopia` | Swannatopia | 3 × SK6812 RGBW (8 px each) | 192.168.1.60 |
| `julia` | Julia | 1 × PWM MOSFET (12 V filaments) | 192.168.1.61 |
| `jess` | Jess | 2 × SK6812 RGBW (20 px each) + 1 × PWM MOSFET flash | 192.168.1.62 |
| `dormer` | Dormer | 1 × PWM MOSFET (12 V) | 192.168.1.63 |

The Pi sends **Garden State**, not pixels. Each controller animates its own
channels, so a lost packet or a dropped access point costs nothing.

## First build

```bash
cp include/secrets.h.example include/secrets.h   # then fill in the WiFi credentials
python3 ../../scripts/hooks/firmware_config_gen.py   # refresh include/net_config.h
```

Then pick the environment in the PlatformIO toolbar in VSCode, or:

```bash
pio run -e jess              # build
pio run -e jess -t upload    # flash
pio device monitor -b 115200 # watch the heartbeat line
```

Debugging uses the S3's built-in USB JTAG (`debug_tool = esp-builtin`) — the
same cable you flash with. Start it from the VSCode **Run and Debug** panel with
the environment selected.

## Tests

```bash
pio test -e native
```

Runs on the host. Everything in `lib/` is free of Arduino headers for exactly
this reason; `src/` is the hardware binding and is not part of the test build.

## Wiring notes

- **Level shifting.** SK6812 data wants a 5 V logic level. The S3's 3.3 V output
  works on short runs but is marginal — put a level shifter (or a single
  74AHCT125 buffer) at the head of each strip. A 330 Ω series resistor on the
  data line and a 1000 µF cap across the strip's 5 V rail are the usual belt
  and braces.
- **MOSFET channels.** Use a logic-level N-channel MOSFET low-side switching the
  12 V return, with a gate resistor (~100 Ω) and a pulldown (~10 kΩ) so the
  fixture stays off while the S3 boots. Grounds must be common with the S3.
- **Pins.** Strips use GPIO 4/5/6, dimmers GPIO 7. These avoid the strapping
  pins (0, 3, 45, 46), the USB pair (19, 20) and the flash/PSRAM range. Change
  them in `src/targets/<location>.h` if the board layout demands it.
- **PWM is 20 kHz**, above the audible band, so the 12 V supply does not sing.

## Bench testing without the Pi

Any OSC sender works — the controller listens on the Fabric addresses directly:

```bash
oscsend osc.udp://192.168.1.62:9000 /flowerbeds/activity f 0.8
oscsend osc.udp://192.168.1.62:9000 /captcha/intensity f 0.5
oscsend osc.udp://192.168.1.62:9000 /captcha/blowup
oscsend osc.udp://192.168.1.62:9000 /treehouse/mode s dim
oscsend osc.udp://192.168.1.62:9000 /treehouse/brightness f 0.25
```

Stop sending for 10 seconds and the channels drop to the idle breathe — that is
the staleness fallback, not a fault.

## Retuning a location

Every look decision for a location is in one header, `src/targets/<location>.h`:
LED counts, colours, pattern choice, and the per-channel Signal Bag weights over
Garden State. Edit and reflash. There is no runtime configuration — see the
trade-off in ADR-0020.
