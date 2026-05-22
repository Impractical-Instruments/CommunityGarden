import machine
import sys
import time
from machine import Pin

# --- CHANGE THIS PER BOARD ---
BOARD_ID = 0  # 0 for first Pico, 1 for second Pico
# ------------------------------

# Quadrature decode table: index = (prev_state << 2 | new_state), value = tick direction
_TABLE = [0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0]


class _Encoder:
    __slots__ = ("idx", "_a", "_b", "_state", "_count", "_reported")

    def __init__(self, idx, pin_a, pin_b):
        self.idx = idx
        self._state = 0
        self._count = 0
        self._reported = 0
        self._a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self._b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self._a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq)
        self._b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq)

    def _irq(self, _):
        self._state = (self._state << 2 | self._a.value() << 1 | self._b.value()) & 0xF
        self._count += _TABLE[self._state]

    def consume(self):
        s = machine.disable_irq()
        d = self._count - self._reported
        self._reported = self._count
        machine.enable_irq(s)
        return d


# Encoders 0-5: A on even pins, B on odd pins (GP0/1, GP2/3 ... GP10/11)
_encoders = [_Encoder(i, i * 2, i * 2 + 1) for i in range(6)]


def main():
    while True:
        for enc in _encoders:
            d = enc.consume()
            if d:
                print(f"/enc {BOARD_ID} {enc.idx} {d}")
        time.sleep_ms(2)


main()
