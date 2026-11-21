#!/usr/bin/env bash
# deploy.sh — push the laptop's current branch to a show machine over the
# show LAN and run the per-element install.sh (Python deps + service restart).
#
# Use this at the venue when show machines have no internet (the standard
# show workflow). See docs/showtime.md → "Deploying code updates".
#
#   scripts/deploy.sh <target> <element>
#
# Targets are ssh host aliases from ~/.ssh/config on the laptop:
#   flowerbeds   treehouse   captcha   pipes
#
# Examples:
#   scripts/deploy.sh flowerbeds FlowerBeds
#   scripts/deploy.sh treehouse  TreeHouse
#   scripts/deploy.sh treehouse  Dashboard       # same machine, other element
#   scripts/deploy.sh captcha    FundingCAPTCHA
#   scripts/deploy.sh pipes      PlayingThePipes
#
# PlayingThePipes also carries the reuben submodule: its pinned commit is pushed
# to the box's vendor/reuben over ssh, so the box never fetches it from GitHub
# and a deploy can carry reuben commits that are not on GitHub yet.
#
# The repo on the show machine is ~/CommunityGarden. If it is cloned somewhere
# else, set CG_REMOTE_REPO to that path (absolute, or relative to the remote
# user's home):
#   CG_REMOTE_REPO=/opt/CommunityGarden scripts/deploy.sh treehouse TreeHouse
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
  element  repo dir name (FlowerBeds | TreeHouse | Dashboard | FundingCAPTCHA | PlayingThePipes)

Examples:
  scripts/deploy.sh flowerbeds FlowerBeds
  scripts/deploy.sh treehouse  TreeHouse
  scripts/deploy.sh treehouse  Dashboard
  scripts/deploy.sh captcha    FundingCAPTCHA
  scripts/deploy.sh pipes      PlayingThePipes
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
remote_repo="${CG_REMOTE_REPO:-CommunityGarden}"
url="$target:$remote_repo"
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

# Playing the Pipes builds reuben from the vendor/reuben submodule. Push the
# commit this branch pins into the box's submodule checkout, under a branch
# nothing has checked out, and let the box check it out without fetching.
submodule_step=""
if [ "$element" = "PlayingThePipes" ]; then
    pin=$(git rev-parse "HEAD:vendor/reuben")
    if ! git -C vendor/reuben cat-file -e "$pin^{commit}" 2>/dev/null; then
        echo "Error: vendor/reuben does not have the pinned commit $pin." >&2
        echo "Run: git submodule update --init" >&2
        exit 1
    fi
    if [ "$(git -C vendor/reuben rev-parse HEAD)" != "$pin" ]; then
        echo "Warning: vendor/reuben is not at the commit $branch pins. Deploying the pinned $pin;" >&2
        echo "commit the submodule change first if you meant to deploy what is checked out." >&2
    fi
    echo "→ pushing reuben $pin to $target"
    git -C vendor/reuben push --force "$url/vendor/reuben" "$pin:refs/heads/cg-deploy"
    submodule_step="git submodule update --no-fetch vendor/reuben"
fi

echo "→ checking out $branch and running install.sh on $target"
ssh -t "$target" "
  set -e
  cd '$remote_repo'
  git checkout '$branch'
  $submodule_step
  # Absolute path: the sudoers rule from bootstrap-deploy.sh matches on it.
  sudo bash \"\$(pwd)/ShowControl/$element/deploy/install.sh\"
"
