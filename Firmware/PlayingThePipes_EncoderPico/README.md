# Playing the Pipes encoder Pico

MicroPython program for the two Raspberry Pi Picos that read the rotary encoders on the pipes (ADR-0014). Each Pico reads six.

- **Libraries:** none beyond MicroPython.
- **Wiring:** encoder `n` (0–5) has A on `GP(2n)` and B on `GP(2n+1)`, with internal pull-ups; encoder common to ground.
- **Protocol** (text lines over USB serial): `/enc BOARD ENC DELTA`, for example `/enc 0 3 -2` — board 0, encoder 3, two ticks counter-clockwise. Sent only when an encoder has moved.
- **Reader:** `ShowControl/PlayingThePipes/encoder_bridge.py` on the `pipes` host; its `/health` shows which boards it hears.

## Flashing

1. Set `BOARD_ID` at the top of `main.py`: `0` for the first Pico, `1` for the second. Two Picos with the same ID send indistinguishable events, so label each board.
2. Copy `main.py` to the Pico as `main.py` (Thonny, or `mpremote cp main.py :main.py`). It runs on power-up.
