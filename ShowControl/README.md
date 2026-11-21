# ShowControl

The show-control software: one directory per Element, plus what they share.

| Directory | What it is | Runs on | Docs |
|---|---|---|---|
| `FlowerBeds/` | Depth camera to servo flowers | `flowerbeds` Pi | `docs/FlowerBeds.md` |
| `TreeHouse/` | The Hub: collects Garden State, drives the Looking Glass, Branches and location controllers | `treehouse` Pi | `docs/TreeHouse.md` |
| `FundingCAPTCHA/` | The kiosk game | `captcha` Pi | `docs/FundingCAPTCHA.md` |
| `PlayingThePipes/` | The music engine: a reuben instrument and the encoder bridge that drives it | `pipes` mini PC | `docs/PlayingThePipes.md` |
| `Dashboard/` | Browser monitoring pages | `treehouse` Pi | `docs/Dashboard.md` |
| `ShowWeb/` | Shared package: `LiveServer`, the `/health`, `/ws` and `/logs` server behind the FlowerBeds and TreeHouse visualizers | FlowerBeds, TreeHouse | `ShowWeb/live.py` |
| `OSCFabric/` | Shared package: sends Element signals to the TreeHouse; reads `network.json` | every Element | its README |
| `network.json` | Every IP, MAC and port on the Show Network | | `docs/osc-fabric.md` |

- Each Element is a flat directory of scripts run from inside it (its systemd unit sets the working directory). `OSCFabric` and `ShowWeb` here and `IIVision` at the repo root are the only installed packages.
- Each Element's Python dependencies are an extra in the root `pyproject.toml`. A show machine's installer syncs only its own into `.venv` with uv (TreeHouse and FundingCAPTCHA still use system pip). On a dev machine, `uv run` has them all. See `docs/agents/running-and-testing.md`.
- Each Element with a `deploy/` directory installs with `sudo bash ShowControl/<Element>/deploy/install.sh`.
- Tests sit beside the code as `test_*.py`; `make test` runs them all.
