#!/usr/bin/env bash
# Fail unless the commit vendor/reuben points at is on reuben's integration
# branch (dev), so main never pins a commit that can vanish when a reuben
# branch is deleted. While iterating, the submodule may point anywhere and be
# deployed from there; this only gates merging. See #177 and #236.
#
# Usage: check-reuben-pin.sh [sha]    (default: the gitlink in HEAD)
# Needs the gh CLI, authenticated (in CI: GH_TOKEN=${{ github.token }}).
set -euo pipefail

REPO="${REUBEN_REPO:-Impractical-Instruments/reuben}"
BRANCH="${REUBEN_BRANCH:-dev}"

sha="${1:-}"
if [ -z "$sha" ]; then
    # `160000 commit <sha>\tvendor/reuben` for a submodule; empty if there is none.
    sha="$(git ls-tree HEAD vendor/reuben | awk '$2 == "commit" { print $3 }')"
fi
if [ -z "$sha" ]; then
    echo "No vendor/reuben submodule in HEAD; nothing to check."
    exit 0
fi

err="$(mktemp)"
trap 'rm -f "$err"' EXIT

# compare/BRANCH...SHA: "identical" or "behind" means SHA is already on BRANCH.
if ! status="$(gh api "repos/$REPO/compare/$BRANCH...$sha" --jq .status 2>"$err")"; then
    echo "::error::Could not compare vendor/reuben $sha with $REPO $BRANCH (the gh error is below)."
    echo "::error::A 404 means $REPO does not have that commit: push it, merge it into $BRANCH, then update the submodule."
    sed 's/^/  /' "$err" >&2
    exit 1
fi

case "$status" in
    identical|behind)
        echo "vendor/reuben $sha is on $REPO $BRANCH."
        ;;
    *)
        echo "::error::vendor/reuben points at $sha, which is not on $REPO $BRANCH (compare status: $status)."
        echo "::error::Fine while iterating, but merge the reuben change into $BRANCH and re-point the submodule before this PR merges."
        exit 1
        ;;
esac
