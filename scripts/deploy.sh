#!/usr/bin/env bash
# deploy.sh — push the laptop's current branch to a show machine over the
# show LAN and run the per-element install.sh (pip install + service restart).
#
# Use this at the venue when show machines have no internet (the standard
# show workflow). See docs/showtime.md → "Deploying code updates".
#
#   scripts/deploy.sh <target> <element>
#
# Targets are ssh host aliases from ~/.ssh/config on the laptop:
#   flowerbeds   FlowerBeds   FundingCAPTCHA   TreeHouse   Dashboard
#
# Examples:
#   scripts/deploy.sh flowerbeds FlowerBeds
#   scripts/deploy.sh treehouse  TreeHouse
#   scripts/deploy.sh treehouse  Dashboard       # same machine, other element
#   scripts/deploy.sh captcha    FundingCAPTCHA
#
# Prerequisites:
#   - laptop ssh key in show machine's ~/.ssh/authorized_keys
#   - show machine bootstrapped: bash scripts/bootstrap-deploy.sh
set -e

target=$1
element=$2

if [ -z "$target" ] || [ -z "$element" ]; then
    cat >&2 <<USAGE
Usage: scripts/deploy.sh <target> <element>

  target   ssh host alias (flowerbeds | treehouse | captcha | pipes)
  element  repo dir name (FlowerBeds | TreeHouse | Dashboard | FundingCAPTCHA)

Examples:
  scripts/deploy.sh flowerbeds FlowerBeds
  scripts/deploy.sh treehouse  TreeHouse
  scripts/deploy.sh treehouse  Dashboard
  scripts/deploy.sh captcha    FundingCAPTCHA
USAGE
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "HEAD" ]; then
    echo "Error: detached HEAD — check out a branch first." >&2
    exit 1
fi

echo "→ pushing $branch to $target"

# We push to an ad-hoc ssh URL rather than a named remote, so there are no
# refs/remotes/<target>/* tracking refs. A bare --force-with-lease has nothing
# to compare against and git rejects the push with "(stale info)". Look the
# remote branch up ourselves and pass the expected sha explicitly.
url="$target":CommunityGarden
remote_sha=$(git ls-remote "$url" "refs/heads/$branch" | cut -f1)

if [ -z "$remote_sha" ]; then
    git push "$url" "$branch":"$branch"
elif ! git cat-file -e "$remote_sha^{commit}" 2>/dev/null; then
    echo "Error: $target has $remote_sha on $branch, a commit this laptop does not have." >&2
    echo "Someone committed on the show machine. Fetch it, or re-run with FORCE=1 to discard it." >&2
    [ "$FORCE" = 1 ] || exit 1
    git push --force "$url" "$branch":"$branch"
else
    git push --force-with-lease="$branch:$remote_sha" "$url" "$branch":"$branch"
fi

echo "→ checking out $branch and running install.sh on $target"
ssh -t "$target" "
  set -e
  cd /home/ii/CommunityGarden
  git checkout '$branch'
  sudo bash /home/ii/CommunityGarden/ShowControl/$element/deploy/install.sh
"
