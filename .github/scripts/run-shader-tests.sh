#!/usr/bin/env bash
# Run the FundingCAPTCHA tests in the fundingcaptcha CI job, letting
# pytest-testmon select only the tests whose recorded Python dependencies
# changed when that is safe, and every test otherwise.
#
#   FORCE_PATH        the changed path that matched shader-force-run.txt, or empty
#   CACHE_KEY         key of the testmon cache restored from main, or empty
#   TESTMON_DATAFILE  where that cache was restored (testmon reads this variable)
#
# The testmon data is recorded on every push to main by testmon-data.yml.
# Locally, `make test-fundingcaptcha` runs everything; this script is for CI.
set -euo pipefail

TESTS=ShowControl/FundingCAPTCHA
# The slowest tests in every log, so a slow new test is seen when it lands (#203).
DURATIONS=--durations=25

# pytest exits 5 when it runs no tests; that is not a failure.
# $1 is what to log in that case (nothing if empty).
pytest_ok() {
    local why=$1 rc=0
    shift
    python3 -m pytest "$@" || rc=$?
    if [ "$rc" -eq 5 ]; then
        [ -z "$why" ] || echo "testmon: zero tests ran: $why"
        return 0
    fi
    return "$rc"
}

if [ -n "${FORCE_PATH:-}" ]; then
    echo "testmon: selection OFF, running every test: force-run path changed: $FORCE_PATH"
    pytest_ok "no tests were collected." "$TESTS" "$DURATIONS"
    exit
fi

if [ -z "${CACHE_KEY:-}" ] || [ ! -s "${TESTMON_DATAFILE:?}" ]; then
    echo "testmon: selection OFF, running every test: cache cold (no testmon data from main)."
    pytest_ok "no tests were collected." "$TESTS" "$DURATIONS"
    exit
fi

echo "testmon: selection ON: cache warm ($CACHE_KEY); no force-run path changed."

# testmon only records code that runs inside a test, so a module that runs
# only at import (OSCFabric, imported by app.py) never becomes a dependency,
# and an import-time error there would select nothing and pass. Collecting
# every test first, without testmon, surfaces such errors. It takes a second.
echo "Collecting every test without testmon, to catch import and collection errors:"
collected=$(mktemp)
if ! python3 -m pytest "$TESTS" --collect-only -q > "$collected" 2>&1; then
    cat "$collected"
    exit 1
fi
tail -n 1 "$collected"

# --testmon-nocollect: select from the restored data without recording new
# data. PR runs never save the cache, and recording slows every test.
# When testmon deselects everything pytest may exit 0 or 5, so count what ran
# from the JUnit report instead of relying on the exit code.
report=$(mktemp)
pytest_ok "" "$TESTS" "$DURATIONS" --testmon --testmon-nocollect --junit-xml="$report"
ran=$(python3 -c 'import sys, xml.etree.ElementTree as E
r = E.parse(sys.argv[1]).getroot()
print(sum(int(s.get("tests", 0)) for s in r.iter("testsuite")))' "$report")
total=$(tail -n 1 "$collected" | grep -oE '^[0-9]+' || echo "?")
echo "testmon: selected $ran of $total tests."
if [ "$ran" -eq 0 ]; then
    echo "testmon: zero tests selected: no Python code that a FundingCAPTCHA test executed on main has changed, and no force-run path changed."
fi
