#!/usr/bin/env bash
# install.sh — set up TreeHouse as an auto-starting systemd service.
# Run once after cloning the repo:
#   cd ShowControl/TreeHouse/deploy
#   sudo bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APP_DIR="$REPO_ROOT/ShowControl/TreeHouse"
SERVICE_USER="${SUDO_USER:-pi}"

echo "=== TreeHouse install ==="
echo "App dir: $APP_DIR"
echo "User:    $SERVICE_USER"
echo ""

# ── Python dependencies ────────────────────────────────────────────────────────
echo "→ Installing Python dependencies..."
pip3 install --break-system-packages -r "$APP_DIR/requirements.txt"

# ── Install service file ───────────────────────────────────────────────────────
echo "→ Installing systemd unit..."
DEST="/etc/systemd/system/treehouse.service"
sed "s|/home/pi/CommunityGarden/ShowControl/TreeHouse|$APP_DIR|g
     s|User=pi|User=$SERVICE_USER|g" \
    "$SCRIPT_DIR/treehouse.service" > "$DEST"
echo "   written: $DEST"

# ── Enable + start ─────────────────────────────────────────────────────────────
systemctl daemon-reload
systemctl enable treehouse.service
systemctl restart treehouse.service

echo ""
echo "=== Done ==="
echo "Status:  sudo systemctl status treehouse"
echo "Logs:    journalctl -u treehouse -f"
echo "Viz:     http://$(hostname -I | awk '{print $1}'):8766/"
