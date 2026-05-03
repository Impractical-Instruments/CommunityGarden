#!/usr/bin/env bash
# install.sh — set up FlowerBeds as an auto-starting systemd service.
# Run once after cloning the repo:
#   cd ShowControl/FlowerBeds/deploy
#   sudo bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APP_DIR="$REPO_ROOT/ShowControl/FlowerBeds"
SERVICE_USER="${SUDO_USER:-pi}"

echo "=== FlowerBeds install ==="
echo "App dir: $APP_DIR"
echo "User:    $SERVICE_USER"
echo ""

# ── Python dependencies ────────────────────────────────────────────────────────
echo "→ Installing Python dependencies..."
# numpy and scipy from apt are faster on Pi/ARM
apt-get install -y python3-numpy python3-scipy 2>/dev/null || true
pip3 install --break-system-packages -r "$APP_DIR/requirements.txt"

# ── Install service file ───────────────────────────────────────────────────────
echo "→ Installing systemd unit..."
DEST="/etc/systemd/system/flowerbeds.service"
sed "s|/home/pi/CommunityGarden/ShowControl/FlowerBeds|$APP_DIR|g
     s|User=pi|User=$SERVICE_USER|g" \
    "$SCRIPT_DIR/flowerbeds.service" > "$DEST"
echo "   written: $DEST"

# ── Enable + start ─────────────────────────────────────────────────────────────
systemctl daemon-reload
systemctl enable flowerbeds.service
systemctl restart flowerbeds.service

echo ""
echo "=== Done ==="
echo "Status:  sudo systemctl status flowerbeds"
echo "Logs:    journalctl -u flowerbeds -f"
echo "Viz:     http://$(hostname -I | awk '{print $1}'):8765/"
