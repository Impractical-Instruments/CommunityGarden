# Playing the Pipes

The show-control side of Playing the Pipes. It runs on the Windows `pipes` host. Operator docs: `docs/PlayingThePipes.md`.

| Path | What it is |
|---|---|
| `Lamplight2026/` | The show: a Max 9 project. Open `Lamplight2026/patchers/Lamplight2026.maxpat` |
| `Lamplight2026/patchers/encoderin.maxpat` | Reads the two encoder Picos over serial; its two arguments are the Max serial port letters |
| `Lamplight2026/patchers/fake_encoder.maxpat` | On-screen stand-ins for the encoders, for running without hardware |
| `Lamplight2026/media/` | Samples (Git LFS) |
| `EncoderTester.maxpat` | Checks one encoder Pico without the audio engine |
| `health_server.py` | `GET /health` on port 8767 so the Dashboard can see the host; runs under NSSM |
| `encoder_bridge.py` | For the reuben port (#177): reads the encoder Picos (found by USB vendor ID) and sends `/pipes/knobN/in` OSC to reuben, and serves `/health` with Pico and reuben status. `--fake-encoders` runs it without hardware. Replaces `encoderin` and `health_server.py` once the box switches to reuben (#239) |

**Max externals the patch needs:** the Grainflow package (`grainflow~`, `grainflow.util.stereopan~`) and Max 9's ABL device objects (`abl.device.reverb~`, `abl.device.spectraltime~`). Everything else is stock Max.

**Encoder input:** `/enc BOARD ENC DELTA` lines from `Firmware/PlayingThePipes_EncoderPico/` (ADR-0014).

**Python:** `pip install -e ".[pipes]"` from the repo root covers `health_server.py` and `encoder_bridge.py`. On a dev machine: `uv run python ShowControl/PlayingThePipes/encoder_bridge.py --fake-encoders`.
