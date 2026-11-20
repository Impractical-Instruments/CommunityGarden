# AGENTS.md — CommunityGarden

Python show-control monorepo for *The Community Garden* — a touring interactive installation where depth-camera blob detection drives servo-motor flowers, LED trees, and kiosk games in response to visitor presence.

## Test command

Every Python command runs through uv: `make` targets do it for you; otherwise run `uv run python …` or `uv run pytest …`. Never `pip install` or activate a venv. See [Running & testing](docs/agents/running-and-testing.md#one-way-to-run-python).

```
make setup                # first time in a clone: .venv from uv.lock, plus the pre-commit hook
make test                 # all Python tests (pytest: IIVision, ShowControl, scripts)
make test-fast            # everything except FundingCAPTCHA; seconds
make test-fundingcaptcha  # FundingCAPTCHA only; minutes, needs a headless OpenGL context
make test-firmware        # TreeHouse controller host tests; not part of `make test`
make validate-instruments # build reuben (vendor/reuben, needs Rust) and check the PtP instruments
```

## Critical constraints

These apply to every task in this repo:

1. **World coordinate system: X=right, Y=forward, Z=up, centimetres.** Orbbec camera space is X=right, Y=down, Z=forward, in metres. `IIVision.transforms.orbbec_to_world()` converts. Never mix the two.
2. **OSC address `/cg/ff/rot` is a cross-layer contract.** `OSC_ROT_ADDRESS` in `ShowControl/FlowerBeds/controllers.py` sends it and `Firmware/FlowerBeds_Follow_ServoController/` receives it. Change both together.
3. **All network addresses (IPs, MACs, ports) live in `ShowControl/network.json`.** Never hardcode them in source or firmware. `scripts/hooks/firmware_config_gen.py` generates the firmware headers from it; re-run it after editing `network.json`. A test fails if a committed header is stale.
4. **All motor IDs, positions, and tuning parameters belong in each Element's `settings.json`.** Do not hardcode them.
5. **Test logic changes without hardware:** `uv run python main.py --config settings.json --mock-camera --no-osc` from `ShowControl/FlowerBeds/`.
6. **Never commit anything under `ShowControl/FundingCAPTCHA/images/private/`, and never write a show/artist/album name into any file.** That directory is a clone of a private, unpublishable assets repo. `.gitignore` and a pre-commit hook (installed by `make setup`) guard it, but neither is a substitute for not doing it.

## Docs

- Directory indexes: [ShowControl](ShowControl/README.md), [Firmware](Firmware/README.md), [IIVision](IIVision/README.md), [scripts](scripts/README.md). Tests sit beside the code as `test_*.py`; there is no top-level `tests/`.
- [Glossary](CONTEXT.md): what a term means, and which words to avoid. Read it before naming anything.
- Element docs: [FlowerBeds](docs/FlowerBeds.md), [TreeHouse](docs/TreeHouse.md), [FundingCAPTCHA](docs/FundingCAPTCHA.md), [Playing the Pipes](docs/PlayingThePipes.md), [Dashboard](docs/Dashboard.md). Read the one you are changing: its files, flags, settings and how to check it.
- [OSC addresses](docs/osc-fabric.md): before sending, receiving or renaming any OSC message, or touching `network.json`.
- [Conventions](docs/agents/conventions.md): coordinates, rotation, logger names. Before writing Python.
- [Running & testing](docs/agents/running-and-testing.md): uv, the test targets, what CI runs, reuben.
- [Firmware](Firmware/README.md): before touching anything under `Firmware/`.
- [Git workflow and issues](docs/agents/git-workflow.md): before committing, opening a PR or filing an issue. PRs target `dev`, not `main`.
- [Decision records](docs/adr/README.md): why something is the way it is, and which decisions are still in force.
