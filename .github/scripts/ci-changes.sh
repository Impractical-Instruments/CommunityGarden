#!/usr/bin/env bash
# Decide which test jobs a PR needs. Reads changed paths on stdin, one per line;
# prints `code=<bool>` and `gl=<bool>` in $GITHUB_OUTPUT format.
#
#   code  run the fast job (everything except FundingCAPTCHA)
#   gl    run the fundingcaptcha job (headless-OpenGL shader tests, ~9 min)
#
# Both lists are deny-lists: a path this script does not recognise runs
# everything. Add a pattern here only for paths no test can depend on.
set -euo pipefail

code=false
gl=false

while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
        # Firmware that scripts/test_firmware_config_gen.py reads: the two generated
        # headers and the FlowerBeds sketch. That test is in the fast job.
        Firmware/TreeHouse_Controllers/include/net_config.h|Firmware/FlowerBeds_Follow_ServoController/*)
            code=true
            ;;
        # No test reads these.
        docs/*|*.md|LICENSE|TouchOSC/*|Firmware/*|.gitignore|.gitattributes)
            ;;
        # Elements FundingCAPTCHA does not import. Their own tests are in the fast job.
        ShowControl/FlowerBeds/*|ShowControl/TreeHouse/*|ShowControl/Dashboard/*|ShowControl/PlayingThePipes/*)
            code=true
            ;;
        # Everything else: FundingCAPTCHA itself, the packages it imports (IIVision,
        # OSCFabric), network.json, test and CI config, and anything new.
        *)
            code=true
            gl=true
            ;;
    esac
done

echo "code=$code"
echo "gl=$gl"
