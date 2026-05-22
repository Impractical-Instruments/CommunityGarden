#!/usr/bin/env bash
# install.sh — set up Looking Glass renderer as an auto-starting systemd service.
# Run once after cloning the repo:
#   cd ShowControl/TreeHouse/looking_glass/deploy
#   sudo bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
APP_DIR="$REPO_ROOT/ShowControl/TreeHouse/looking_glass"
SERVICE_USER="${SUDO_USER:-ii}"

echo "=== Looking Glass install ==="
echo "App dir: $APP_DIR"
echo "User:    $SERVICE_USER"
echo ""

echo "→ Installing system dependencies..."
apt-get install -y cage libgl1-mesa-dri libegl1 libegl-mesa0 libgl1 seatd
systemctl enable --now seatd
usermod -aG _seat "$SERVICE_USER"

echo "→ Installing Python dependencies..."
pip3 install --break-system-packages moderngl pyglet numpy python-osc

echo "→ Installing systemd unit..."
DEST="/etc/systemd/system/looking_glass.service"
sed "s|User=ii|User=$SERVICE_USER|g" \
    "$SCRIPT_DIR/looking_glass.service" > "$DEST"
echo "   written: $DEST"

systemctl daemon-reload
systemctl enable looking_glass.service
systemctl restart looking_glass.service

echo ""
echo "=== Done ==="
echo "Status:  sudo systemctl status looking_glass"
echo "Logs:    journalctl -u looking_glass -f"
