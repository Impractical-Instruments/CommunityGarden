# Running & Testing

## Tests

```bash
make test          # Node tests (FundingCAPTCHA) + Python pytest (IIVision, ShowControl)
python -m pytest   # Python only
```

## Run FlowerBeds show control

Install dependencies (first time):

```bash
cd ShowControl/FlowerBeds
pip install -r requirements.txt
```

Run without hardware (fastest way to test logic changes):

```bash
python main.py --config settings.json --mock-camera --no-osc
```

Run with real camera and Arduino:

```bash
python main.py --config settings.json
```

Run headless (no browser dashboard):

```bash
python main.py --config settings.json --no-visualizer
```

## CLI flags

| Flag | Description |
|---|---|
| `--config PATH` | Path to settings JSON (default: `settings.json`) |
| `--mock-camera` | Use mock camera — random blobs, no Orbbec hardware needed |
| `--no-osc` | Disable OSC output to Arduino |
| `--no-visualizer` | Disable WebSocket visualizer server |
| `--visualizer-port N` | Visualizer HTTP port (default: 8765) |
| `--calibrate-yaw DEG` | Hold all motors at DEG degrees (0=forward, 90=right); useful for physically aligning flowers to zero |
| `--verbose` / `-v` | Enable DEBUG logging |

## Run the layout tool (pre-show, Windows laptop)

The layout tool configures module positions visually. Run on your laptop before show; save
result to `settings.json` and deploy normally.

```bash
cd ShowControl/FlowerBeds
python layout_tool.py
# opens http://localhost:8764
```

Laptop must be on the show network to use manual aim and OSC test features. Controller
status check and saving work without network access.

## Verifying changes

There is no CI gate for hardware-in-the-loop behaviour. After any pipeline change:

1. Run `--mock-camera --no-osc` and confirm the log output is clean.
2. Open `http://localhost:8765` to verify blobs, clusters, and camera positions render correctly in the visualizer.
3. If touching OSC or servo logic, connect real hardware and validate with `TouchOSC/FlowerBedTester.tosc`.
