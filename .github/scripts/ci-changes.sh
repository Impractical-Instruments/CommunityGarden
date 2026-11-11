#!/usr/bin/env bash
# Decide which test jobs a PR needs. Reads changed paths on stdin, one per line;
# prints `code=<bool>`, `gl=<bool>` and `force=<path>` in $GITHUB_OUTPUT format.
#
#   code   run the fast job (everything except FundingCAPTCHA)
#   gl     run the fundingcaptcha job (headless-OpenGL shader tests, minutes)
#   force  the first changed path on shader-force-run.txt, or empty. When set,
#          the fundingcaptcha job runs every test with testmon selection off.
#
# Both job lists are deny-lists: a path this script does not recognise runs
# everything. Add a pattern here only for paths no test can depend on.
set -euo pipefail

FORCE_LIST="$(dirname "${BASH_SOURCE[0]}")/shader-force-run.txt"
force_globs=()
while IFS= read -r line; do
    case "$line" in ''|'#'*) continue ;; esac
    force_globs+=("$line")
done < "$FORCE_LIST"

code=false
gl=false
force=

while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
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
echo "force=$force"
