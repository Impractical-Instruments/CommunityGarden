# Signs of life

The smallest thing that proves an ESP32-S3 board is alive: it boots, its serial
output reaches the port you are watching, and 8 SK6812 RGBW pixels on **GPIO 4**
light up. No WiFi, no OSC, no generated headers, no `secrets.h`.

Flash this first whenever a board is behaving badly. If it does not run, nothing
in `../TreeHouse_Controllers/` will either.

## Running it in VSCode

PlatformIO only sees a project when the folder holding `platformio.ini` is the
workspace root, so **open this folder directly** — not the repo root:

```bash
code Firmware/ESP32S3_SignsOfLife
```

Then click the alien-head PlatformIO icon in the sidebar → **PROJECT TASKS** →
**uart** → **General → Upload**, then **Monitor**.

There is no need to install anything: the VSCode extension ships PlatformIO Core
at `~/.platformio/penv/bin/pio`. For a shell that already has `pio` on PATH, use
Command Palette → **PlatformIO: New Terminal**:

```bash
pio run -e uart -t upload
pio device monitor -b 115200
```

## Which USB socket?

The DevKitC-1 has two, and `ARDUINO_USB_CDC_ON_BOOT` decides which one `Serial`
comes out of. Silence on the wrong socket looks exactly like a dead board, so if
you see nothing, flash the other environment before suspecting the hardware:

| Environment | Serial appears on |
|---|---|
| `uart` (default) | the **UART** socket, via the onboard USB-serial bridge |
| `usb` | the **USB** socket, the S3's native USB |

## Three signs of life

In order of how little has to be working for each:

1. **The onboard RGB LED blinks green.** No wiring, no serial — if this blinks,
   the board boots. It is GPIO 48 on v1.1 boards and GPIO 38 on v1.0; if it
   stays dark, change `ONBOARD_PIN` to 38 and reflash before suspecting
   anything else.
2. **A serial heartbeat once a second**, with a millisecond timestamp.
3. **The strip cycles red → green → blue → white**, a second each. The white
   step lights the W element alone, so an RGB strip — or one with the W leg
   unwired — stays dark for it rather than faking a pass.

## Diagnosing a boot loop

Every boot prints `esp_reset_reason()`, which is what actually names the fault:

| Reason | What it means |
|---|---|
| `POWERON`, over and over | Not crashing — losing power. Suspect the supply or the cable. |
| `BROWNOUT` | LED current pulled the rail down. Most likely if the loop only starts once the strip is connected. |
| `PANIC` | The sketch crashed; the backtrace prints just above that line, decoded to file and line by `esp32_exception_decoder`. |

A boot loop with no reset reason at all — because it never reaches the sketch —
looks like this:

```
E (83) spi_flash: Detected size(4096k) smaller than the size in the binary image header(8192k). Probe failed.
assert failed: do_core_init startup.c:328 (flash_ret == ESP_OK)
```

That is a 4 MB module running an image built for 8 MB. PlatformIO's stock
`esp32-s3-devkitc-1` definition assumes 8 MB; both firmware projects here
override it back to 4 MB. If you meet a board that is neither, the three
`board_upload.flash_size` / `board_upload.maximum_size` /
`board_build.partitions` lines in `platformio.ini` are what to change.

Note that a board stuck in this loop re-enumerates its USB port every cycle, so
uploads fail with *"device reports readiness to read but returned no data"*.
Erasing (**PROJECT TASKS → Platform → Erase Flash**) leaves it with nothing to
run, which holds the port still long enough to flash it.

Brightness is capped at 40/255 — about 100 mA for 8 RGBW pixels, which USB alone
can supply. At full white those same 8 pixels want roughly 650 mA and will brown
out a USB port. For anything brighter, power the strip from its own 5 V supply
with its ground tied to the board's.

## Changing the strip

The three constants at the top of `src/main.cpp`:

```cpp
#define STRIP_PIN 4
#define STRIP_PIXELS 8
#define ONBOARD_PIN 48
```

GPIO 4 is a safe choice on the S3. If you need a different pin: 5, 6, 7, 15, 16,
17 and 18 are all fine. Avoid 0, 3, 45 and 46 (strapping), 19 and 20 (USB), 43
and 44 (UART0), and 26–37 (flash and PSRAM).
