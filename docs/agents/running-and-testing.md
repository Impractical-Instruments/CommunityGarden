# Running & Testing

## One way to run Python

On a dev machine and in CI, every Python command runs through [uv](https://docs.astral.sh/uv/). It is the only thing to install: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`). uv then sets up `.venv` with the Python in `.python-version` and the exact packages in `uv.lock`, the same on every machine. It installs the `dev` group from `pyproject.toml`: every Element's dependencies and the test tools.

- **`make …`** runs through uv already.
- **Any other Python command:** put `uv run` in front, from anywhere in the repo. Example: `uv run python main.py --mock-camera`. Where a doc says `python3 x.py`, run `uv run python x.py`.
- **Never** `pip install`, activate a venv, or call `.venv/bin/python` directly.
- **Changing dependencies:** edit `pyproject.toml`, then run `uv lock` and commit `uv.lock` with it. CI fails if the two disagree.

Show machines (the Pis and the Pipes PC) don't use this. They install an Element's extra with their system pip; see `docs/bootstrap.md`.

Python is 3.11 because that is what the show Pis run (Pi OS bookworm). A 3.12+ feature would pass on a laptop and fail at the show. Change `.python-version` when the Pis move to a newer Pi OS.

## Tests

```bash
make setup                # first time in a clone: .venv, plus the pre-commit hook
make test                 # all Python tests (pytest: IIVision, ShowControl, scripts)
make test-fast            # everything except FundingCAPTCHA; seconds
make test-fundingcaptcha  # FundingCAPTCHA only; minutes with a headless OpenGL context
uv run pytest IIVision    # any pytest arguments
make test-firmware        # TreeHouse controller host tests (PlatformIO, run by uv)
make build-firmware       # compile the signs-of-life, location and self-test firmware
make reuben               # build the reuben CLI from vendor/reuben (needs Rust)
make validate-instruments # load-check the Playing the Pipes instruments with that build
```

CI runs `test-fast`, the FundingCAPTCHA tests, the two firmware targets and the two reuben targets as separate jobs and skips any the PR cannot affect. `.github/scripts/ci-changes.sh` holds the path rules; a path it does not recognise runs them all.

Inside the FundingCAPTCHA job, [pytest-testmon](https://testmon.org/) runs only the tests whose Python dependencies changed, using data recorded by `.github/workflows/testmon-data.yml` on each push to `main`. testmon sees only the Python code a test executes, so it is blind to shaders, JSON and other data files. Any changed path listed in `.github/scripts/shader-force-run.txt` runs every test, and so does a run that finds no recorded data. When a test reads a new kind of non-Python file, add its path to that list. Locally, `make test` and `make test-fundingcaptcha` always run everything.

Shader tests run on software Mesa in CI, where fragment shading is the whole cost. The test rigs set `Renderer.defer_image = True`: frames skip the Image pass, and the file's image helper calls `draw_deferred_image()` to draw the last frame's Image only when a test reads it. A new rig should do the same and read `output` only through such a helper. To time the tests locally as CI does, force llvmpipe with `LIBGL_ALWAYS_SOFTWARE=1 __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json`; without these, EGL may pick a hardware GPU.

## reuben (Playing the Pipes audio engine)

[reuben](https://github.com/Impractical-Instruments/reuben) is a git submodule at `vendor/reuben`, built from source so it can be changed in place while working here (#177). `make setup` checks it out; after a pull that moves it, run `git submodule update --init --recursive`.

- **Prerequisites:** Rust via [rustup](https://rustup.rs), and on Linux the ALSA headers (`sudo apt-get install libasound2-dev`). `vendor/reuben/rust-toolchain.toml` pins the Rust version; rustup installs it on the first build.
- **`make reuben`** builds `vendor/reuben/target/release/reuben`.
- **`make validate-instruments`** runs `reuben validate` on every `ShowControl/PlayingThePipes/reuben/*.json` except device profiles (`*.profile.json`). A warning fails it as well as an error, because reuben only warns about a missing sample or voice file.
- **`make pipes`** plays the Playing the Pipes instrument on this machine, driven by the encoder bridge's fake encoders; see `ShowControl/PlayingThePipes/README.md`.
- **Editing an instrument** goes through reuben's MCP document verbs, never by hand: `.mcp.json` at the repo root starts reuben's MCP server (`vendor/reuben/scripts/reuben-mcp.sh`) in Claude Code sessions here. Read reuben's `docs/agents/authoring.md` first.
- **Changing reuben:** work in `vendor/reuben` on a branch there (its own `AGENTS.md` applies), push it to the reuben repo, and commit the new submodule commit here. You can deploy and test from any reuben commit, but CI's `reuben-pin` check blocks merging until that commit is on reuben's `dev` branch (its integration branch; `main` there is the release branch). `.github/scripts/check-reuben-pin.sh` runs the same check locally.

## Run FlowerBeds show control

Run without hardware (fastest way to test logic changes):

```bash
cd ShowControl/FlowerBeds
uv run python main.py --config settings.json --mock-camera --no-osc
```

Run with real camera and Arduino. The Orbbec SDK is the `camera` extra, outside the `dev` group:

```bash
uv run --extra camera python main.py --config settings.json
```

Run headless (no browser dashboard):

```bash
uv run python main.py --config settings.json --no-visualizer
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
uv run python layout_tool.py
# opens http://localhost:8764
```

Laptop must be on the show network to use manual aim and OSC test features. Controller
status check and saving work without network access.

## Verifying changes

There is no CI gate for hardware-in-the-loop behaviour. After any pipeline change:

1. Run `--mock-camera --no-osc` and confirm the log output is clean.
2. Open `http://localhost:8765` to verify blobs, clusters, and camera positions render correctly in the visualizer.
3. If touching OSC or servo logic, connect real hardware and validate with the layout tool's Aim mode (one servo at a time) or `uv run python main.py --calibrate-yaw-sweep` (every servo through its limits).
