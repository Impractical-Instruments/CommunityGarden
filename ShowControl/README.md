# ShowControl

The show-control software: one directory per Element, plus what they share.

| Directory | What it is | Runs on | Docs |
|---|---|---|---|
| `FlowerBeds/` | Depth camera to servo flowers | `flowerbeds` Pi | `docs/FlowerBeds.md` |
| `TreeHouse/` | The Hub: collects Garden State, drives the Looking Glass, Branches and location controllers | `treehouse` Pi | `docs/TreeHouse.md` |
| `FundingCAPTCHA/` | The kiosk game | `captcha` Pi | `docs/FundingCAPTCHA.md` |
| `PlayingThePipes/` | The Max music engine and its health server | `pipes` Windows PC | `docs/PlayingThePipes.md` |
| `Dashboard/` | Browser monitoring pages | `treehouse` Pi | `docs/Dashboard.md` |
| `OSCFabric/` | Shared package: sends Element signals to the TreeHouse; reads `network.json` | every Element | its README |
| `network.json` | Every IP, MAC and port on the Show Network | | `docs/agents/configuration.md` |

- Each Element is a flat directory of scripts run from inside it (its systemd unit sets the working directory). `OSCFabric` here and `IIVision` at the repo root are the only installed packages.
- Each Element's Python dependencies are an extra in the root `pyproject.toml`. A show machine installs its own with pip (`pip install -e ".[flowerbeds]"`, done by its installer). On a dev machine, `uv run` has them all; see `docs/agents/running-and-testing.md`.
- Each Element with a `deploy/` directory installs with `sudo bash ShowControl/<Element>/deploy/install.sh`.
- Tests sit beside the code as `test_*.py`; `make test` runs them all.
