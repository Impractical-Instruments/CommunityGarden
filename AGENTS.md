# AGENTS.md — CommunityGarden

Python show-control monorepo for *The Community Garden* — a touring interactive installation where depth-camera blob detection drives servo-motor flowers, LED trees, and kiosk games in response to visitor presence.

## Test command

```
make test   # runs Node tests (FundingCAPTCHA) + Python pytest (IIVision, ShowControl)
```

## Critical constraints

These apply to every task in this repo:

1. **World coordinate system: X=right, Y=forward, Z=up, centimetres.** Orbbec camera-space is X=right, Y=down, Z=forward in metres. `IIVision.Blob3D.world_pos_cm()` converts between them. Never mix the two.
2. **OSC address `/cg/ff/rot` is a cross-layer contract.** `ShowControl/FlowerBeds/main.py` and `Firmware/FlowerBeds_Follow_ServoController/` must both be changed together if the address changes.
3. **All network addresses (IPs, MACs, ports) live in `ShowControl/network.json`.** Never hardcode them in source or firmware — firmware reads a generated `config.h`.
4. **All motor IDs, positions, and tuning parameters belong in each Element's `settings.json`.** Do not hardcode them.
5. **Test logic changes without hardware:** `python main.py --config settings.json --mock-camera --no-osc` from `ShowControl/FlowerBeds/`.
6. **Never commit anything under `ShowControl/FundingCAPTCHA/images/private/`, and never write a show/artist/album name into any file.** That directory is a clone of a private, unpublishable assets repo; `.gitignore` and a pre-commit hook (`bash scripts/install-git-hooks.sh`, per clone) both guard it, but neither is a substitute for not doing it.

## Docs

- [Architecture & pipeline](docs/agents/architecture.md)
- [Python conventions](docs/agents/python-conventions.md)
- [Configuration reference](docs/agents/configuration.md)
- [Running & testing](docs/agents/running-and-testing.md)
- [Firmware](docs/agents/firmware.md)
- [Git workflow](docs/agents/git-workflow.md)
- [Issue tracker](docs/agents/issue-tracker.md)
- [Triage labels](docs/agents/triage-labels.md)
- [Domain glossary & vocabulary](docs/agents/domain.md)
