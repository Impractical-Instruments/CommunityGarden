#!/usr/bin/env bash
# Decide which test jobs a PR needs. Reads changed paths on stdin, one per line;
# prints `code=<bool>`, `gl=<bool>` and `firmware=<bool>` in $GITHUB_OUTPUT format.
#
#   code      run the fast job (everything except FundingCAPTCHA)
#   gl        run the fundingcaptcha job (headless-OpenGL shader tests, ~9 min)
#   firmware  run the firmware job (TreeHouse controller host tests and builds)
#
# These are deny-lists: a path this script does not recognise runs
# everything. Add a pattern here only for paths a job's tests cannot depend on.
set -euo pipefail

code=false
gl=false
firmware=false

while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
        # Generated header: the controller builds include it, and
        # scripts/test_firmware_config_gen.py (fast job) checks it is current.
        Firmware/TreeHouse_Controllers/include/net_config.h)
            code=true
            firmware=true
            ;;
        # The FlowerBeds sketch and its generated header. Only that Python test
        # reads them; there is no build for this board in CI.
        Firmware/FlowerBeds_Follow_ServoController/*)
            code=true
            ;;
        # No test reads these.
        docs/*|*.md|LICENSE|.gitignore|.gitattributes)
            ;;
        # The TreeHouse controllers: host tests and builds.
        Firmware/TreeHouse_Controllers/*)
            firmware=true
            ;;
        # Other firmware has no tests.
        Firmware/*)
            ;;
        # Elements FundingCAPTCHA does not import. Their own tests are in the fast job.
        ShowControl/FlowerBeds/*|ShowControl/TreeHouse/*|ShowControl/Dashboard/*|ShowControl/PlayingThePipes/*)
            code=true
            ;;
        # The rest of the Python: FundingCAPTCHA itself, the packages it imports
        # (IIVision, OSCFabric), network.json, scripts and packaging. The firmware
        # job compiles nothing from here.
        ShowControl/*|IIVision/*|scripts/*|pyproject.toml)
            code=true
            gl=true
            ;;
        # Everything else: CI config, the Makefile, and anything new.
        *)
            code=true
            gl=true
            firmware=true
            ;;
    esac
done

echo "code=$code"
echo "gl=$gl"
echo "firmware=$firmware"
