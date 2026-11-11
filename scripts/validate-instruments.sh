#!/usr/bin/env bash
# Load-check reuben instruments with `reuben validate`, failing on warnings as
# well as errors: reuben only warns about a missing sample or voice file, and
# for a show instrument that is a broken instrument. Run via
# `make validate-instruments`.
#
# Usage: validate-instruments.sh <reuben binary> [instrument.json ...]
set -euo pipefail

reuben=$1
shift

if [ $# -eq 0 ]; then
    echo "No instruments in ShowControl/PlayingThePipes/reuben/ yet."
    exit 0
fi

fail=0
for f in "$@"; do
    rc=0
    report="$("$reuben" validate --json "$f" 2>&1)" || rc=$?
    if [ "$rc" -eq 0 ] && echo "$report" | jq -e '.ok and (.warnings | length == 0)' >/dev/null 2>&1; then
        echo "ok   $f"
        continue
    fi
    echo "FAIL $f"
    if echo "$report" | jq -e 'has("errors")' >/dev/null 2>&1; then
        echo "$report" | jq -r '(.errors[] | "  error   \(.node // "-"): \(.message)"), (.warnings[] | "  warning \(.node // "-"): \(.message)")'
    else
        # Not a report (reuben crashed or could not start): show what it printed.
        echo "$report" | sed 's/^/  /'
    fi
    fail=1
done
exit $fail
