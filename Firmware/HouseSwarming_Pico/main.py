"""HouseSwarming standalone Pico light controller (stopgap).

3x SK6812 RGBW strips, <=8 px each, no host:
  GP0  fireplace  - flame flicker
  GP2  overhead1  - static warm white (~2700K)
  GP4  overhead2  - static warm white (~2700K)

Flash this file as main.py. Runs forever on power-up.
"""

import time
import array
import random
import rp2
from machine import Pin


# --- SK6812 RGBW PIO driver (shared pattern from TreeHouse_PicoLEDs) ---
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=32)
def _sk6812():
    # 10 MHz: T0H=300ns T0L=900ns T1H=600ns T1L=600ns
    T1 = 3
    T2 = 3
    T3 = 6
    wrap_target()
    label("bitloop")
    out(x, 1)              .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")  .side(1)    [T1 - 1]
    jmp("bitloop")         .side(1)    [T2 - 1]
    label("do_zero")
    nop()                  .side(0)    [T2 - 1]
    wrap()


_next_sm = 0


class Strip:
    def __init__(self, pin, n, master=1.0):
        global _next_sm
        self.n = n
        self.master = master
        self.buf = [(0, 0, 0, 0)] * n          # r, g, b, w
        self._out = array.array("I", [0] * n)
        self.sm = rp2.StateMachine(_next_sm, _sk6812, freq=10_000_000,
                                   sideset_base=Pin(pin))
        self.sm.active(1)
        _next_sm += 1

    def set(self, i, r, g, b, w):
        self.buf[i] = (r, g, b, w)

    def show(self):
        m = self.master
        for i in range(self.n):
            r, g, b, w = self.buf[i]
            r = int(r * m); g = int(g * m); b = int(b * m); w = int(w * m)
            self._out[i] = (((g & 0xFF) << 24) | ((r & 0xFF) << 16) |
                            ((b & 0xFF) << 8) | (w & 0xFF))
        self.sm.put(self._out, 0)


# --- config ---
FIRE_N = 8
OVERHEAD_N = 8
FRAME_MS = 50

fire = Strip(0, FIRE_N, master=0.8)
over1 = Strip(2, OVERHEAD_N, master=0.6)
over2 = Strip(4, OVERHEAD_N, master=0.6)


def set_overhead(strip):
    # warm white ~2700K: W high, small R, tiny G, no B
    for i in range(strip.n):
        strip.set(i, 80, 30, 0, 255)
    strip.show()


def step_fireplace():
    # px 0 = bottom (hottest). per-pixel flicker, occasional pop, ember glow.
    for i in range(FIRE_N):
        grad = 1.0 - 0.5 * (i / (FIRE_N - 1))      # bottom brighter
        flick = random.uniform(0.45, 1.0)
        if random.random() < 0.08:
            flick = 1.0                            # pop
        level = grad * flick
        r = int(255 * level)
        g = int((70 + random.randint(-15, 25)) * level)
        if g < 0:
            g = 0
        w = int(15 * level)                        # ember glow
        fire.set(i, r, g, 0, w)
    fire.show()


def main():
    set_overhead(over1)
    set_overhead(over2)
    while True:
        step_fireplace()
        time.sleep_ms(FRAME_MS)


main()
