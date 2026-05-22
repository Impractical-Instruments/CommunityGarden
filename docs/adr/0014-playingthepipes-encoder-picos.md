# ADR 0014 — Playing the Pipes uses Pi Pico encoder boards, not direct Pi GPIO

**Status:** Accepted

## Context

Playing the Pipes has 12 rotary encoders distributed across the physical pipe structure. The original hardware path (resolved 2026-05-07, issue #49) assumed direct Pi GPIO reading via a Python bridge. Physical construction places encoders in two sections; running 24+ signal wires back to the Pi would be mechanically fragile and cable-intensive.

## Decision

Two Pi Pico microcontrollers (one per section, 6 encoders each) read quadrature rotary encoders and send encoder delta events over USB serial to the Windows mini PC. Max reads the two serial ports directly (as Windows COM ports, e.g. `COM3` / `COM4`) and routes events into the RNBO patch.

## Protocol

OSC-style newline-terminated text at USB CDC default baud:

```
/enc BOARD ENC DELTA\n
```

- `BOARD`: `0` or `1` — hardcoded per Pico
- `ENC`: `0`–`5` — encoder index on that board
- `DELTA`: signed integer tick count since last emission (only non-zero values are sent)

Example: `/enc 0 3 -2` = board 0, encoder 3, two ticks counter-clockwise.

In Max: `serial` object → `fromsymbol` → `route /enc` → `unpack i i i` → board, encoder, delta.

## Wiring (same layout on both boards)

| Encoder | A pin | B pin |
|---------|-------|-------|
| 0       | GP0   | GP1   |
| 1       | GP2   | GP3   |
| 2       | GP4   | GP5   |
| 3       | GP6   | GP7   |
| 4       | GP8   | GP9   |
| 5       | GP10  | GP11  |

All encoder pins use internal pull-ups. Encoder common to Pico GND.

## Reasons

- Picos sit physically near their encoders; only a USB cable runs back to the Windows mini PC
- Identical pin layout on both boards simplifies construction and maintenance
- MicroPython IRQ-based quadrature decoding is robust at human-speed turning rates
- Consistent with the USB serial pattern established for TreeHouse (ADR-0005, ADR-0010)

## Consequences

- Max must open two serial ports simultaneously and merge events by board/encoder address
- Board IDs must be flashed correctly; incorrect flashing produces silently wrong addresses — label each Pico physically
- Supersedes the "no microcontroller intermediary" note from the original 2026-05-07 hardware decision
