# Running & Testing

## Tests

```bash
make test                 # all Python tests (pytest: IIVision, ShowControl, scripts)
make test-fast            # everything except FundingCAPTCHA; seconds
make test-fundingcaptcha  # FundingCAPTCHA only; minutes with a headless OpenGL context
python -m pytest          # the same as make test
```

CI runs `test-fast` and the FundingCAPTCHA tests as separate jobs and skips either when the PR cannot affect it. `.github/scripts/ci-changes.sh` holds the path rules; a path it does not recognise runs both.

Inside the FundingCAPTCHA job, [pytest-testmon](https://testmon.org/) runs only the tests whose Python dependencies changed, using data recorded by `.github/workflows/testmon-data.yml` on each push to `main`. testmon sees only the Python code a test executes, so it is blind to shaders, JSON and other data files. Any changed path listed in `.github/scripts/shader-force-run.txt` runs every test, and so does a run that finds no recorded data. When a test reads a new kind of non-Python file, add its path to that list. Locally, `make test` and `make test-fundingcaptcha` always run everything.

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
