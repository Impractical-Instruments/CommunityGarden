#!/usr/bin/env bash
# install.sh — set up TreeHouse display stack (weston + both renderers).
# Run once after cloning the repo:
#   cd ShowControl/TreeHouse/looking_glass/deploy
#   sudo bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SERVICE_USER="${SUDO_USER:-ii}"

echo "=== TreeHouse display stack install ==="
echo "Repo:  $REPO_ROOT"
echo "User:  $SERVICE_USER"
echo ""

echo "→ Installing system dependencies..."
apt-get install -y weston libgl1-mesa-dri libegl1 libegl-mesa0 libgl1 seatd
systemctl enable --now seatd
usermod -aG _seat "$SERVICE_USER"
# moderngl requires unversioned .so symlinks; Pi OS ships only the versioned runtime libs
ln -sf /lib/aarch64-linux-gnu/libGL.so.1  /lib/aarch64-linux-gnu/libGL.so
ln -sf /lib/aarch64-linux-gnu/libEGL.so.1 /lib/aarch64-linux-gnu/libEGL.so
ldconfig

echo "→ Installing Python dependencies..."
pip3 install --break-system-packages moderngl pygame python-osc

echo ""
echo "=== Done ==="
echo "Renderers are managed by the treehouse service — no separate unit needed."
echo "Status:  sudo systemctl status treehouse"
echo "Logs:    journalctl -fu treehouse"
