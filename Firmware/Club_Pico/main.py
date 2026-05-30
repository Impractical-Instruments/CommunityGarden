"""Club standalone Pico light controller (stopgap).

2x SK6812 RGBW strips, <=30 px each, + 1 transistor-driven superbright LED:
  GP0  backlights - magenta/cyan crossfade bands, slow scroll + pulse
  GP2  upper      - cool-white comet walking down strip
  GP6  superbright - transistor base, PWM ~70% constant

Flash this file as main.py. Runs forever on power-up.
"""

import time
import math
import array
import rp2
from machine import Pin, PWM


# --- SK6812 RGBW PIO driver (shared pattern from TreeHouse_PicoLEDs) ---
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=32)
def _sk6812():
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
        self.buf = [(0, 0, 0, 0)] * n
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
BACK_N = 30
UPPER_N = 30
FRAME_MS = 33                       # ~30 fps
TWO_PI = 2.0 * math.pi

back = Strip(0, BACK_N, master=1.0)
upper = Strip(2, UPPER_N, master=0.9)

# superbright LED via transistor, PWM ~70% constant
superbright = PWM(Pin(6))
superbright.freq(1000)
superbright.duty_u16(int(0.70 * 65535))

# backlight band params
BAND_WAVELENGTH = 10.0              # px per magenta->cyan->magenta cycle (~5px/color)
BACK_SCROLL = 0.15                  # px per frame (slow)
BACK_PULSE_PERIOD_S = 4.0           # slow brightness pulse

# upper comet params
HEAD_LEN = 3
TAIL_LEN = 4
COMET_SPEED = 0.4                   # px per frame


def step_backlights(scroll, pulse_phase):
    pulse = 0.7 + 0.3 * math.sin(pulse_phase)      # 0.4 .. 1.0
    for i in range(BACK_N):
        phase = (i + scroll) * (TWO_PI / BAND_WAVELENGTH)
        t = (math.sin(phase) + 1.0) * 0.5          # 0=magenta, 1=cyan
        # magenta (255,0,255) -> cyan (0,255,255)
        r = int(255 * (1.0 - t) * pulse)
        g = int(255 * t * pulse)
        b = int(255 * pulse)
        back.set(i, r, g, b, 0)
    back.show()


def step_upper(head_pos):
    for i in range(UPPER_N):
        d = (head_pos - i) % UPPER_N               # distance behind head (wraps)
        if d < HEAD_LEN:
            level = 1.0
        elif d < HEAD_LEN + TAIL_LEN:
            level = 1.0 - (d - HEAD_LEN) / TAIL_LEN
        else:
            level = 0.0
        w = int(255 * level)
        b = int(40 * level)                        # slight cool tint
        upper.set(i, 0, 0, b, w)
    upper.show()


def main():
    scroll = 0.0
    pulse_phase = 0.0
    head_pos = 0.0
    pulse_step = TWO_PI * (FRAME_MS / 1000.0) / BACK_PULSE_PERIOD_S
    while True:
        step_backlights(scroll, pulse_phase)
        step_upper(head_pos)
        scroll += BACK_SCROLL
        pulse_phase += pulse_step
        if pulse_phase > TWO_PI:
            pulse_phase -= TWO_PI
        head_pos = (head_pos + COMET_SPEED) % UPPER_N
        time.sleep_ms(FRAME_MS)


main()
