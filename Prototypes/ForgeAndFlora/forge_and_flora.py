"""
ForgeAndFlora tester firmware — Raspberry Pi Pico (MicroPython)

Forge channel (GP0, physical pin 1):
  LEDs 0–3  welding glow — warm amber flicker
  LEDs 4–5  arc flash    — bright blue-white burst

Flora channel (GP1, physical pin 2):
  LEDs 0–3  flora glow   — green/yellow breathing wave

Wiring:
  SK6812 DATA  →  [300 Ω resistor]  →  GP0 or GP1
  SK6812 5 V   →  VBUS (pin 40) or external 5 V PSU
  SK6812 GND   →  GND  (pin 38)
  470 µF cap across 5 V / GND at strip input

SK6812 byte order on wire is G-R-B-W.
set_pixel() accepts (r, g, b, w) and swaps internally.
"""

import time
import math
import random
from machine import Pin
import neopixel

# ── Configuration ─────────────────────────────────────────────────────────────

FORGE_PIN  = 0   # GP0, physical pin 1
FLORA_PIN  = 1   # GP1, physical pin 2

WELD_COUNT  = 4  # welding glow LEDs (indices 0–3 on forge strip)
ARC_COUNT   = 2  # arc flash LEDs    (indices 4–5 on forge strip)
FORGE_COUNT = WELD_COUNT + ARC_COUNT

FLORA_COUNT = 4  # flora LEDs on flora strip

BRIGHTNESS  = 0.8  # global multiplier 0.0–1.0

# Welding glow: warm amber
WELD_COLOR = (255, 100, 10, 60)   # R, G, B, W

# Arc flash: dim blue idle → bright blue-white burst
ARC_IDLE  = (20,  40, 120,  10)
ARC_FLASH = (200, 220, 255, 255)

ARC_FLASH_PROB   = 0.03  # probability per frame of triggering a flash (~30 fps)
ARC_FLASH_FRAMES = 3     # frames the flash stays bright

# Flora: alternating green/yellow per LED
FLORA_GREEN  = (0,   180, 10,  20)
FLORA_YELLOW = (200, 180, 0,   10)

FLORA_BREATHE_SPEED = 0.3           # cycles per second
FLORA_PHASE_STEP    = math.pi / 2   # quarter-wave offset between adjacent LEDs
FLORA_MIN           = 0.04          # trough floor (prevents full-off)

# ─────────────────────────────────────────────────────────────────────────────

forge_strip = neopixel.NeoPixel(Pin(FORGE_PIN, Pin.OUT), FORGE_COUNT, bpp=4)
flora_strip = neopixel.NeoPixel(Pin(FLORA_PIN, Pin.OUT), FLORA_COUNT, bpp=4)


def write_pixel(strip, i, r, g, b, w, scale=1.0):
    s = min(max(scale * BRIGHTNESS, 0.0), 1.0)
    # SK6812 wire order is G-R-B-W
    strip[i] = (int(g * s), int(r * s), int(b * s), int(w * s))


# ── Forge ─────────────────────────────────────────────────────────────────────

_arc_remaining = 0


def update_forge():
    global _arc_remaining

    # Welding glow: independent per-LED random flicker
    r, g, b, w = WELD_COLOR
    for i in range(WELD_COUNT):
        write_pixel(forge_strip, i, r, g, b, w, random.uniform(0.55, 1.0))

    # Arc flash: occasional bright burst
    if random.random() < ARC_FLASH_PROB:
        _arc_remaining = ARC_FLASH_FRAMES

    if _arc_remaining > 0:
        ar, ag, ab, aw = ARC_FLASH
        _arc_remaining -= 1
    else:
        ar, ag, ab, aw = ARC_IDLE

    for i in range(ARC_COUNT):
        write_pixel(forge_strip, WELD_COUNT + i, ar, ag, ab, aw)

    forge_strip.write()


# ── Flora ─────────────────────────────────────────────────────────────────────

def update_flora(t_sec):
    for i in range(FLORA_COUNT):
        phase = t_sec * FLORA_BREATHE_SPEED * 2.0 * math.pi + i * FLORA_PHASE_STEP
        factor = (math.sin(phase) + 1.0) * 0.5
        scale = FLORA_MIN + factor * (1.0 - FLORA_MIN)
        r, g, b, w = FLORA_GREEN if i % 2 == 0 else FLORA_YELLOW
        write_pixel(flora_strip, i, r, g, b, w, scale)
    flora_strip.write()


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    while True:
        t = time.ticks_ms() / 1000.0
        update_forge()
        update_flora(t)
        time.sleep_ms(33)  # ~30 fps


main()
