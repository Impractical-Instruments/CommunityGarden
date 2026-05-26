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
git push --force-with-lease "$target":CommunityGarden "$branch":"$branch"

echo "→ checking out $branch and running install.sh on $target"
ssh -t "$target" "
  set -e
  cd /home/ii/CommunityGarden
  git checkout '$branch'
  sudo bash /home/ii/CommunityGarden/ShowControl/$element/deploy/install.sh
"
