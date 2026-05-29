#!/usr/bin/env bash
# start_pipes.sh — launch Playing the Pipes Max patch on the show Windows machine.
#
# Pre-requisites on Windows (one-time setup):
#   1. Open Settings → System → Optional features → Add "OpenSSH Server"
#   2. In PowerShell (admin): Start-Service sshd
#                              Set-Service sshd -StartupType Automatic
#   3. Note the Windows machine's IP on the Show Network (see ShowControl/network.json)
#
# Fill in the three FILL_IN values below, then run:
#   bash ShowControl/PlayingThePipes/deploy/start_pipes.sh
#
# Can also be triggered from any machine on the Show Network:
#   ssh <show-computer>@192.168.1.X bash /path/to/start_pipes.sh

set -e

# ── FILL IN BEFORE USE ────────────────────────────────────────────────────────
WINDOWS_USER="FILL_IN"              # Windows username, e.g. "charlie"
WINDOWS_IP="192.168.1.13"           # From ShowControl/network.json pipes.ip
WINDOWS_REPO_ROOT="FILL_IN"         # Full Windows path to repo root, e.g. C:/Users/charlie/projects/CommunityGarden
# ─────────────────────────────────────────────────────────────────────────────

PATCH_WIN="${WINDOWS_REPO_ROOT}/ShowControl/PlayingThePipes/PlayingThePipes.maxpat"

# Max 9 default install location — adjust if installed elsewhere
MAX_EXE="C:/Program Files/Cycling '74/Max 9/Max.exe"

if [ "$WINDOWS_USER" = "FILL_IN" ] || [ "$WINDOWS_REPO_ROOT" = "FILL_IN" ]; then
    echo "ERROR: Edit start_pipes.sh and fill in WINDOWS_USER and WINDOWS_REPO_ROOT first."
    exit 1
fi

echo "→ Launching Max patch on ${WINDOWS_USER}@${WINDOWS_IP} ..."

ssh "${WINDOWS_USER}@${WINDOWS_IP}" \
    "powershell -Command \"Start-Process -FilePath '${MAX_EXE}' -ArgumentList '${PATCH_WIN}' -WindowStyle Normal\""

echo "✓ Max patch launched on Windows machine."
echo "  If nothing opens, verify Max.exe path and patch path on the Windows machine."
