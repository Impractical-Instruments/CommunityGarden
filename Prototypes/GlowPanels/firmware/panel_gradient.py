"""
GlowPanel firmware — Raspberry Pi Pico (MicroPython)
Controls SK6812 RGBW strips for mycelium glow panel prototypes.

Two gradient modes — change MODE below, then save as main.py on the Pico.

Wiring (see prototype READMEs for full diagrams):
  SK6812 DATA  →  [300 Ω resistor]  →  GP0  (pin 1)
  SK6812 5 V   →  VBUS (pin 40) or external 5 V PSU
  SK6812 GND   →  GND  (pin 38)
  470 µF cap across 5 V / GND at strip input

SK6812 byte order on wire is G-R-B-W.
set_pixel() accepts (r, g, b, w) and swaps internally.
"""

import time
import math
from machine import Pin
import neopixel

# ── Configuration ─────────────────────────────────────────────────────────────

NUM_LEDS  = 18      # 18 for side-lit single edge; 54 for back-lit 3-row box
DATA_PIN  = 0       # GPIO number (GP0 = physical pin 1)

# Global brightness multiplier 0.0–1.0.
# Keep at 0.4–0.6 during prototyping to avoid blinding yourself.
BRIGHTNESS = 0.5

# RGBW base colour — (R, G, B, W) each 0–255.
# COLOR_WARM: warm white-green tint, earthen/mycelium feel.
# COLOR_COOL: cooler cyan-white, more bioluminescent.
COLOR_WARM = (20,  60,  40, 180)
COLOR_COOL = (10,  80,  80, 120)

BASE_COLOR = COLOR_WARM

# Mode:
#   "A"  Static gradient — fixed brightness falloff from LED[0] to LED[N-1].
#        Calm, architectural. No animation loop needed.
#   "B"  Breathing gradient — per-LED sine wave with a phase offset between
#        neighbours. Organic, bioluminescent pulse.
MODE = "A"

# ── Mode A settings ───────────────────────────────────────────────────────────
# Gradient runs bright→dim from index 0 to NUM_LEDS-1.
GRADIENT_BRIGHT = 1.0    # scale at the bright end (index 0)
GRADIENT_DIM    = 0.05   # scale at the dim end  (last index)

# ── Mode B settings ───────────────────────────────────────────────────────────
BREATHE_SPEED      = 0.4    # full cycles per second (higher = faster pulse)
BREATHE_PHASE_STEP = 0.25   # radian phase shift between adjacent LEDs
#                             larger = more wave-like; 0 = whole strip in sync
BREATHE_MIN        = 0.02   # floor brightness during trough (prevents full-off)

# ─────────────────────────────────────────────────────────────────────────────

_pin = Pin(DATA_PIN, Pin.OUT)
# bpp=4 enables 4-byte (RGBW) mode. MicroPython writes bytes in the order
# stored in the buffer, so we store them in SK6812 wire order (GRBW) manually.
np = neopixel.NeoPixel(_pin, NUM_LEDS, bpp=4)


def set_pixel(i, r, g, b, w, scale=1.0):
    """Write one pixel with a per-call brightness scale applied on top of BRIGHTNESS."""
    s = min(max(scale * BRIGHTNESS, 0.0), 1.0)
    # SK6812 wire order is GRBW — swap r and g in the buffer.
    np[i] = (int(g * s), int(r * s), int(b * s), int(w * s))


def show_static_gradient():
    """Mode A: pre-compute a fixed gradient and write once."""
    r, g, b, w = BASE_COLOR
    for i in range(NUM_LEDS):
        t = i / max(NUM_LEDS - 1, 1)                          # 0.0 → 1.0
        scale = GRADIENT_BRIGHT - t * (GRADIENT_BRIGHT - GRADIENT_DIM)
        set_pixel(i, r, g, b, w, scale)
    np.write()


def show_breathing_gradient(t_sec):
    """Mode B: animate per-LED sine wave with phase offset between neighbours."""
    r, g, b, w = BASE_COLOR
    for i in range(NUM_LEDS):
        phase = t_sec * BREATHE_SPEED * 2.0 * math.pi + i * BREATHE_PHASE_STEP
        factor = (math.sin(phase) + 1.0) * 0.5               # 0.0 – 1.0
        scale = BREATHE_MIN + factor * (1.0 - BREATHE_MIN)
        set_pixel(i, r, g, b, w, scale)
    np.write()


def main():
    if MODE == "A":
        show_static_gradient()
        while True:
            time.sleep(1)

    elif MODE == "B":
        while True:
            t = time.ticks_ms() / 1000.0
            show_breathing_gradient(t)
            time.sleep_ms(30)           # ~33 fps is plenty for this effect

    else:
        raise ValueError(f"Unknown MODE {MODE!r} — set to 'A' or 'B'")


main()
