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

PlatformIO only sees a project when the folder holding `platformio.ini` is the
workspace root, so **open this folder directly** in VSCode — not the repo root:

```bash
code Firmware/TreeHouse_Controllers
```

Then:

```bash
cp include/secrets.h.example include/secrets.h   # then fill in the WiFi credentials
python3 ../../scripts/hooks/firmware_config_gen.py   # refresh include/net_config.h
```

To build and flash, click the alien-head PlatformIO icon in the sidebar →
**PROJECT TASKS** → the environment you want (`jess`, say) → **General →
Upload**, then **Monitor**. The environment switcher in the bottom status bar
sets which one the ✓ / → / plug icons act on.

The VSCode extension ships PlatformIO Core, so there is nothing extra to
install. For a shell that already has `pio` on PATH, use Command Palette →
**PlatformIO: New Terminal**:

```bash
pio run -e jess              # build
pio run -e jess -t upload    # flash
pio device monitor -b 115200 # watch the heartbeat line
```

Debugging uses the S3's built-in USB JTAG (`debug_tool = esp-builtin`) — the
same cable you flash with. Start it from the VSCode **Run and Debug** panel with
the environment selected.

If a board is misbehaving before any of this works, flash
[`../ESP32S3_SignsOfLife`](../ESP32S3_SignsOfLife) first. It has no networking
and no config headers, so it isolates the board from everything here.

## Self-test — proving the hardware without the show

Each location has a `-selftest` environment that walks every channel through a
fixed colour sequence with the network, Garden State and the whole animation
engine compiled out. If a fixture stays dark under self-test, there is nothing
left in the path but wiring, power, level shifting or the strip itself.

Pick `jess-selftest` under **PROJECT TASKS → General → Upload** in the
PlatformIO sidebar, or from the PlatformIO terminal:

```bash
pio run -e jess-selftest -t upload
pio device monitor -b 115200      # each phase is announced on serial
```

It needs no `secrets.h` — the self-test builds exclude `Net.cpp` entirely — so
this is the right thing to flash onto a bench before the Show Network exists.

The sequence loops:

| Phase | Duration | Strips | Dimmers |
|---|---|---|---|
| Red | 2 s | all pixels red | 25 % |
| Green | 2 s | all pixels green | 50 % |
| Blue | 2 s | all pixels blue | 75 % |
| White | 2 s | all pixels white, **W element only** | 100 % |
| Walk | 150 ms per pixel | one white pixel at a time, head to tail | blinking |
| Dark | 1 s | off | off |

Strips run at 35 %, and dimmers are still capped by that channel's `max_level`.
Proving a strip works should not require peak current from a bench supply, and
the Jess flash channel at full power is genuinely painful to look at.

### Reading the result

| What you see | What it means |
|---|---|
| Nothing at all, on every channel | Power or ground. Measure 5 V at the head **and** the tail of the run under load — voltage sag at the far end is the most common "dead strip" that isn't. |
| Red, green and blue fine, white phase dark | The W leg. Either the strip is RGB rather than RGBW, or the white element is not wired. This is exactly why the white phase uses W alone instead of faking white from R+G+B. |
| Colours wrong (red shows green, etc.) | Colour order. The firmware assumes GRBW (`NeoGrbwFeature` in `src/Outputs.cpp`). |
| First pixel dark, rest fine | Dead lead pixel. It will also corrupt everything behind it in normal operation — resolder DIN onto pixel 2 to confirm. |
| Walk stops partway along the run | Broken link at that pixel, or the strip is shorter than `kPixels` in `src/targets/<location>.h`. |
| Whole run flickers or shows garbage | Signal integrity: 3.3 V data over a long run. Try it with a short jumper at the strip head — if it behaves up close, you need a level shifter, not a code change. |
| Dimmer channel on at every step, no visible steps | MOSFET gate wired to a permanently-high pin, or the fixture is on the wrong side of the switch. |

### Why you cannot just put 5 V on the data pin

The SK6812's DIN is a clocked serial input, not a brightness control. Each chip
waits for a >80 µs low, consumes the next 32 bits and forwards the rest down the
line. Steady DC is neither a reset nor a valid bit, so the chip sits in whatever
state it powered up in — which is off. There is no voltage that produces a
colour, and applying 5 V to DIN while the strip's own V+ is *off* pushes current
through the chip's ESD diode and can kill the first pixel. Use the self-test.

## Tests

From the PlatformIO terminal (Command Palette → **PlatformIO: New Terminal**):

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
- **Power-up state.** SK6812 registers reset to zero, so a strip that is dark
  the instant power arrives is behaving correctly. A brief flash of random
  colour on some clones is also normal.
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
