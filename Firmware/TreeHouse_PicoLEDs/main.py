import sys
import json
import rp2
import array
from machine import Pin


@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=32)
def _sk6812():
    # 10 MHz clock: T0H=300ns(3cy) T0L=900ns(9cy) T1H=600ns(6cy) T1L=600ns(6cy)
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


_SM_FREQ = 10_000_000
_strips: dict = {}
_next_sm = 0


def _get_sm(pin: int):
    global _next_sm
    if pin not in _strips:
        if _next_sm >= 8:
            return None
        sm = rp2.StateMachine(_next_sm, _sk6812, freq=_SM_FREQ, sideset_base=Pin(pin))
        sm.active(1)
        _strips[pin] = sm
        _next_sm += 1
    return _strips[pin]


def _write(sm, pixels: list) -> None:
    buf = array.array("I", [
        ((g & 0xFF) << 24) | ((r & 0xFF) << 16) | ((b & 0xFF) << 8) | (w & 0xFF)
        for r, g, b, w in pixels
    ])
    sm.put(buf, 0)


def main() -> None:
    while True:
        line = sys.stdin.readline()
        if not line:
            continue
        try:
            msg = json.loads(line)
            sm = _get_sm(msg["pin"])
            if sm is not None:
                _write(sm, msg["pixels"])
        except Exception:
            pass


main()
