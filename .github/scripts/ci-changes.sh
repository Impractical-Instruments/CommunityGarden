#!/usr/bin/env bash
# Decide which test jobs a PR needs. Reads changed paths on stdin, one per line;
# prints `code=<bool>`, `gl=<bool>`, `firmware=<bool>`, `reuben=<bool>` and
# `force=<path>` in $GITHUB_OUTPUT format.
#
#   code      run the fast job (everything except FundingCAPTCHA)
#   gl        run the fundingcaptcha job (headless-OpenGL shader tests, minutes)
#   firmware  run the firmware job (TreeHouse controller host tests and builds)
#   reuben    run the reuben job (build vendor/reuben, validate the PtP instruments)
#   force     the first changed path on shader-force-run.txt, or empty. When set,
#             the fundingcaptcha job runs every test with testmon selection off.
#
# The job lists are deny-lists: a path this script does not recognise runs
# everything. Add a pattern here only for paths a job's tests cannot depend on.
set -euo pipefail

FORCE_LIST="$(dirname "${BASH_SOURCE[0]}")/shader-force-run.txt"
force_globs=()
while IFS= read -r line; do
    case "$line" in ''|'#'*) continue ;; esac
    force_globs+=("$line")
done < "$FORCE_LIST"

code=false
gl=false
firmware=false
reuben=false
force=

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
        # The reuben submodule (a gitlink: the one path vendor/reuben). The fast
        # job's encoder-bridge test checks network.json against reuben's ports.
        vendor/*)
            code=true
            reuben=true
            ;;
        # The Playing the Pipes instruments: the reuben job validates them, and the fast
        # job's contract test checks the bridge's OSC addresses against their pipes.
        ShowControl/PlayingThePipes/reuben/*)
            code=true
            reuben=true
            ;;
        # Elements FundingCAPTCHA does not import. Their own tests are in the fast job.
        ShowControl/FlowerBeds/*|ShowControl/TreeHouse/*|ShowControl/Dashboard/*|ShowControl/PlayingThePipes/*)
            code=true
            ;;
        # The rest of the Python: FundingCAPTCHA itself, the packages it imports
        # (IIVision, OSCFabric), network.json, scripts and packaging. The firmware
        # job compiles nothing from here.
        ShowControl/*|IIVision/*|scripts/*|pyproject.toml|uv.lock|.python-version)
            code=true
            gl=true
            ;;
        # Everything else: CI config, the Makefile, and anything new.
        *)
            code=true
            gl=true
            firmware=true
            reuben=true
            ;;
    esac
    if [ -z "$force" ]; then
        for glob in "${force_globs[@]}"; do
            # Unquoted on the right: a pattern, in which * also matches /.
            # shellcheck disable=SC2053
            if [[ $path == $glob ]]; then
                force=$path
                break
            fi
        done
    fi
done

echo "code=$code"
echo "gl=$gl"
echo "firmware=$firmware"
echo "reuben=$reuben"
echo "force=$force"
