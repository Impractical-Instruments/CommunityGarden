#!/usr/bin/env bash
# install.sh — set up the show Dashboard as an auto-starting systemd service.
# Run once after cloning the repo:
#   cd ShowControl/Dashboard/deploy
#   sudo bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APP_DIR="$REPO_ROOT/ShowControl/Dashboard"
SERVICE_USER="${SUDO_USER:-pi}"

echo "=== Dashboard install ==="
echo "App dir: $APP_DIR"
echo "User:    $SERVICE_USER"
echo ""

# ── Install service file ───────────────────────────────────────────────────────
echo "→ Installing systemd unit..."
DEST="/etc/systemd/system/cg-dashboard.service"
sed "s|/home/pi/CommunityGarden/ShowControl/Dashboard|$APP_DIR|g
     s|User=pi|User=$SERVICE_USER|g" \
    "$SCRIPT_DIR/dashboard.service" > "$DEST"
echo "   written: $DEST"

# ── Enable + start ─────────────────────────────────────────────────────────────
systemctl daemon-reload
systemctl enable cg-dashboard.service
systemctl restart cg-dashboard.service

echo ""
echo "=== Done ==="
echo "Status:  sudo systemctl status cg-dashboard"
echo "Logs:    journalctl -u cg-dashboard -f"
echo "URL:     http://$(hostname -I | awk '{print $1}'):9000/"
