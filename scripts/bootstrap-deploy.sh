#!/usr/bin/env bash
# bootstrap-deploy.sh — one-time per-machine setup to accept LAN deploys
# from the dev laptop (see docs/showtime.md → "Deploying code updates").
#
# Run once on each Linux show machine, AFTER the initial git clone from
# GitHub during machine imaging. Run as the service user (ii) — not root;
# this script invokes sudo internally for the sudoers rule.
#
#   bash scripts/bootstrap-deploy.sh
#
# What it does:
#   1. Sets receive.denyCurrentBranch=updateInstead on the working repo so
#      `git push` from the laptop can land on the currently checked-out
#      branch without corrupting the working tree.
#   2. Installs /etc/sudoers.d/cg-deploy granting NOPASSWD on the per-element
#      install.sh scripts, so deploy.sh on the laptop can run them over ssh
#      without prompting for a password mid-script.
#
# Pipes (Windows) is bootstrapped manually — see docs/bootstrap.md.
set -e

if [ "$EUID" -eq 0 ]; then
    echo "Error: run as the service user (ii), not root. sudo is invoked internally." >&2
    echo "  bash scripts/bootstrap-deploy.sh" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_USER="$USER"

echo "=== bootstrap-deploy ==="
echo "Repo: $REPO_ROOT"
echo "User: $SERVICE_USER"
echo ""

echo "→ git config receive.denyCurrentBranch=updateInstead"
git -C "$REPO_ROOT" config receive.denyCurrentBranch updateInstead

echo "→ installing /etc/sudoers.d/cg-deploy"
SUDOERS_FILE=/etc/sudoers.d/cg-deploy
sudo tee "$SUDOERS_FILE" >/dev/null <<EOF
# Allow the deploy user to run per-element install scripts without password.
# Written by scripts/bootstrap-deploy.sh — re-run that script to update.
$SERVICE_USER ALL=(ALL) NOPASSWD: /bin/bash $REPO_ROOT/ShowControl/*/deploy/install.sh, /usr/bin/bash $REPO_ROOT/ShowControl/*/deploy/install.sh
EOF
sudo chmod 440 "$SUDOERS_FILE"
sudo visudo -cf "$SUDOERS_FILE"

echo ""
echo "=== Done ==="
echo "From your laptop on the show LAN:"
echo "  scripts/deploy.sh <target> <element>"
