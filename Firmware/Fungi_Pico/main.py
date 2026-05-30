"""Fungi room standalone Pico light controller (stopgap).

1x transistor-driven LED filament on PWM:
  GP0  filament - gamma-corrected sine breathing, 30%..80%, 12 s period

Flash this file as main.py. Runs forever on power-up.
"""

import time
import math
from machine import Pin, PWM


# --- config ---
PWM_PIN = 0
PWM_FREQ = 1000
FLOOR = 0.30                # perceived brightness floor
CEIL = 0.80                # perceived brightness ceiling
PERIOD_S = 16.0
FRAME_MS = 20              # ~50 fps for smooth fade
GAMMA = 2.2               # perceived brightness -> PWM duty
TWO_PI = 2.0 * math.pi

filament = PWM(Pin(PWM_PIN))
filament.freq(PWM_FREQ)


def main():
    phase = 0.0
    step = TWO_PI * (FRAME_MS / 1000.0) / PERIOD_S
    while True:
        s = (math.sin(phase) + 1.0) * 0.5          # 0 .. 1
        level = FLOOR + (CEIL - FLOOR) * s         # perceived 0.30 .. 0.80
        duty = int((level ** GAMMA) * 65535)       # gamma-correct to duty
        filament.duty_u16(duty)
        phase += step
        if phase > TWO_PI:
            phase -= TWO_PI
        time.sleep_ms(FRAME_MS)


main()
