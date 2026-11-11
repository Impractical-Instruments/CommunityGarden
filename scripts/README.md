# scripts

Deploy, install and repo tooling. Nothing here is imported by show code.

| File | Run where | What it does |
|---|---|---|
| `deploy.sh <target> <Element>` | operator laptop | Pushes the current branch to a show machine over the LAN and runs that Element's installer |
| `bootstrap-deploy.sh` | each show machine, once | Lets the machine accept `deploy.sh` pushes; adds the sudoers rule for the installers |
| `install-services.sh <Element>...` | each show machine | Runs `ShowControl/<Element>/deploy/install.sh` for each Element named |
| `lib/install-element.sh` | sourced by the installers | The shared install steps: pip, systemd unit, enable, restart |
| `install-git-hooks.sh` | each clone, once | Installs `git-hooks/pre-commit`, which blocks private show content |
| `hooks/firmware_config_gen.py` | after editing `network.json` | Regenerates the firmware network headers |

`test_*.py` cover these scripts and the CI path filter (`.github/scripts/ci-changes.sh`); they run under `make test`.

Operator instructions: `docs/bootstrap.md` (first install) and `docs/showtime.md` (deploying at a venue).
