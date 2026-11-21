# Running & Testing

## One way to run Python

On a dev machine and in CI, every Python command runs through [uv](https://docs.astral.sh/uv/). It is the only thing to install; `make` prints the install command when it is missing. uv then sets up `.venv` with the Python in `.python-version` and the exact packages in `uv.lock`, the same on every machine. It installs the `dev` group from `pyproject.toml`: every Element's dependencies and the test tools.

- **`make …`** runs through uv already.
- **Any other Python command:** put `uv run` in front, from anywhere in the repo. Example: `uv run python main.py --mock-camera`. Where a doc says `python3 x.py`, run `uv run python x.py`.
- **Never** `pip install`, activate a venv, or call `.venv/bin/python` directly.
- **Changing dependencies:** edit `pyproject.toml`, then run `uv lock` and commit `uv.lock` with it. CI fails if the two disagree.

Show machines (the Pis and the Pipes PC) don't use this. They install an Element's extra with their system pip; see `docs/bootstrap.md`.

Python is 3.11 because that is what the show Pis run (Pi OS bookworm). A 3.12+ feature would pass on a laptop and fail at the show. Change `.python-version` when the Pis move to a newer Pi OS.

## Tests

The everyday targets (`make setup`, `test`, `test-fast`, `test-fundingcaptcha`, `test-firmware`, `validate-instruments`) are in [`AGENTS.md`](../../AGENTS.md#test-command). The rest:

```bash
uv run pytest IIVision    # any pytest arguments
make build-firmware       # compile the signs-of-life, location and self-test firmware
make reuben               # build the reuben CLI from vendor/reuben (needs Rust)
```

No test covers servos, LEDs or cameras. Each Element's doc (`docs/<Element>.md`) has its no-hardware command and how to check the hardware by hand.

CI runs `test-fast`, the FundingCAPTCHA tests, the two firmware targets and the two reuben targets as separate jobs and skips any the PR cannot affect. `.github/scripts/ci-changes.sh` holds the path rules; a path it does not recognise runs them all.

Inside the FundingCAPTCHA job, [pytest-testmon](https://testmon.org/) runs only the tests whose Python dependencies changed, using data recorded by `.github/workflows/testmon-data.yml` on each push to `dev`. testmon sees only the Python code a test executes, so it is blind to shaders, JSON and other data files. Any changed path listed in `.github/scripts/shader-force-run.txt` runs every test, and so does a run that finds no recorded data. When a test reads a new kind of non-Python file, add its path to that list. Locally, `make test` and `make test-fundingcaptcha` always run everything.

The FundingCAPTCHA job has a time budget: `.github/scripts/run-shader-tests.sh` fails a pytest run that takes longer than 8 minutes, even if every test passed. A full run takes 3 to 5. When it trips, make the slowest tests cheaper (the log lists them) or drop tests that do not check something a visitor sees; do not raise the budget to get a PR through.

A test that runs for 120 s has hung: pytest prints every thread's stack and ends the whole run with exit code 1 (`faulthandler_timeout` in `pyproject.toml`). The stack at the top of that dump names the test and the line it stopped on. The run stops there, so later tests do not run and there is no summary.

Shader tests run on software Mesa in CI, where fragment shading is the whole cost. `ShowControl/FundingCAPTCHA/shader_test_rig.py` holds the shared rig and sets `Renderer.defer_image = True`: frames skip the Image pass, and `read_image()` (or `Rig.image()`) calls `draw_deferred_image()` to draw the last frame's Image only when a test reads it. Build a Setup's tests on that rig, keep them in the Setup's folder (`shaders/<setup>/test_<setup>.py`), and read the Image only through it. To time the tests locally as CI does, force llvmpipe with `LIBGL_ALWAYS_SOFTWARE=1 __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json`; without these, EGL may pick a hardware GPU.

## reuben (Playing the Pipes audio engine)

[reuben](https://github.com/Impractical-Instruments/reuben) is a git submodule at `vendor/reuben`, built from source so it can be changed in place while working here (#177). `make setup` checks it out; after a pull that moves it, run `git submodule update --init --recursive`.

- **Prerequisites:** Rust via [rustup](https://rustup.rs), and on Linux the ALSA headers (`sudo apt-get install libasound2-dev`). `vendor/reuben/rust-toolchain.toml` pins the Rust version; rustup installs it on the first build.
- **`make reuben`** builds `vendor/reuben/target/release/reuben`.
- **`make validate-instruments`** runs `reuben validate` on every `ShowControl/PlayingThePipes/reuben/*.json` except device profiles (`*.profile.json`). A warning fails it as well as an error, because reuben only warns about a missing sample or voice file.
- **`make pipes`** plays the Playing the Pipes instrument on this machine, driven by the encoder bridge's fake encoders; see `ShowControl/PlayingThePipes/README.md`.
- **`make pipes-surface`** is the same with no fake encoders, plus the Dashboard: it prints the URL of the Dashboard's virtual encoder surface, where you turn the knobs yourself.
- **Editing an instrument** goes through reuben's MCP document verbs, never by hand: `.mcp.json` at the repo root starts reuben's MCP server (`vendor/reuben/scripts/reuben-mcp.sh`) in Claude Code sessions here. Read reuben's `docs/agents/authoring.md` first.
- **Changing reuben:** work in `vendor/reuben` on a branch there (its own `AGENTS.md` applies), push it to the reuben repo, and commit the new submodule commit here. You can deploy and test from any reuben commit, but CI's `reuben-pin` check blocks merging until that commit is on reuben's `dev` branch (its integration branch; `main` there is the release branch). `.github/scripts/check-reuben-pin.sh` runs the same check locally.
