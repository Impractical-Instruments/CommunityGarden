# Playing the Pipes

The show-control side of Playing the Pipes. It runs on the Windows `pipes` host. Operator docs: `docs/PlayingThePipes.md`.

The show is moving from a Max patch to [reuben](../../vendor/reuben) (#177). Both live here until reuben has run a live show; the box runs Max until #239 switches its services.

## reuben version

| Path | What it is |
|---|---|
| `encoder_bridge.py` | Reads the encoder Picos (found by USB vendor ID, any port), feeds their detents to `pipes_control`, and sends its values to reuben as OSC every 10 ms. Serves `GET /health` (Picos, reuben, loop state). `--fake-encoders` runs it without hardware |
| `pipes_control.py` | What the Max patch's `knobgrain`/`knobvelocity`/`wakemove`/`ComputeState` did: per-knob velocity, wake/sleep, grain parameters and level; the loop mix state and its preset crossfades |
| `settings.json` | All of `pipes_control`'s tuning, from the Max patch: velocity smoothing, timeouts, each grain voice's ranges, the 13 loop presets |
| `reuben/pipes.json` | The reuben instrument: 12 grain voices into a stereo reverb, 13 stereo loops, the mic echo, a limited master. Edit it only through reuben's MCP document verbs (`.mcp.json` at the repo root starts that server) |

**Run it on a laptop:** `make pipes` builds reuben, plays `reuben/pipes.json` on the default audio devices (the mic included), and drives it with fake encoders. `REUBEN_PLAY_ARGS="--io-map <profile>"` picks other devices.

**The OSC contract** between the bridge and the instrument (each a reuben input pipe, set at `/<pipe name>/in`):

| Address | Value |
|---|---|
| `/pipes/knobN/position/in` | 0..1, where in the grain buffer (N = board × 6 + encoder, 0–11) |
| `/pipes/knobN/grain_size/in` | ms (5–500) |
| `/pipes/knobN/density/in` | grains per second (1–200) |
| `/pipes/knobN/spray/in` | ms, random jitter of each grain's start |
| `/pipes/knobN/level/in` | 0..1 knob amplitude |
| `/pipes/loopN/level/in` | 0..1 loop amplitude, N = 1–13 |
| `/volume/in` | master volume, default 0.25 (−12 dB, as in Max) |

The two sides change together; `test_pipes_control.py` fails if the bridge sends an address the instrument has no pipe for.

**Where it differs from the Max patch, on purpose:**

- Fixed: a knob woken during its fade-out no longer stays silent; a wake no longer starts with a velocity spike; position holds through the fade-out; every knob counts as active for 20 s (e12 had 2 s).
- Grains are panned across the stereo field (board 0 left, board 1 right) into a true stereo reverb; in Max they summed to mono.
- The mic's spectral freeze is a feedback echo after the same pre-delay (0.5 s left, 0.75 s right), which keeps the speakers out of the mic.
- reuben's granulator ranges: density bottoms out at 1 grain/s (two voices rest at 0.625 in Max) and grain size tops out at 500 ms (one voice rests at 600). Max's `delayRandom` (grain onset jitter) maps to reuben's `spray` (start-position jitter).
- Values Max never saved, and so ran at defaults, are starting guesses to settle at the A/B: reverb room 0.85, damping 0.5, fully wet (the grains have no dry path); the limiter at −1 dB, 20:1, 0.1 ms attack.
- Everything starts at launch; Max waited for someone to click its toggle.

## Max version (the fallback until reuben has run a show)

| Path | What it is |
|---|---|
| `Lamplight2026/` | A Max 9 project. Open `Lamplight2026/patchers/Lamplight2026.maxpat` |
| `Lamplight2026/patchers/encoderin.maxpat` | Reads the two encoder Picos over serial; its two arguments are the Max serial port letters |
| `Lamplight2026/patchers/fake_encoder.maxpat` | On-screen stand-ins for the encoders, for running without hardware |
| `Lamplight2026/media/` | Samples (Git LFS); the reuben instrument reads them from here too |
| `EncoderTester.maxpat` | Checks one encoder Pico without the audio engine |
| `health_server.py` | `GET /health` on port 8767 so the Dashboard can see the host; runs under NSSM until #239 |

**Max externals the patch needs:** the Grainflow package (`grainflow~`, `grainflow.util.stereopan~`) and Max 9's ABL device objects (`abl.device.reverb~`, `abl.device.spectraltime~`). Everything else is stock Max.

**Encoder input:** `/enc BOARD ENC DELTA` lines from `Firmware/PlayingThePipes_EncoderPico/` (ADR-0014).

**Python:** `pip install -e ".[pipes]"` from the repo root covers `health_server.py`, `encoder_bridge.py` and `pipes_control.py`.
