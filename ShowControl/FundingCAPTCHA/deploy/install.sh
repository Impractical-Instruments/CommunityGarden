#!/usr/bin/env bash
# install.sh — set up FundingCAPTCHA as an auto-starting systemd service on Pi.
# Run once after cloning the repo:
#   cd ShowControl/FundingCAPTCHA/deploy
#   sudo bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APP_DIR="$REPO_ROOT/ShowControl/FundingCAPTCHA"

SERVICE_USER="${SUDO_USER:-ii}"

echo "=== FundingCAPTCHA install ==="
echo "App dir:  $APP_DIR"
echo "User:     $SERVICE_USER"
echo ""

# ── Orbbec USB permissions ─────────────────────────────────────────────────────
echo "→ Installing Orbbec udev rule..."
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2bc5", ATTR{idProduct}=="0807", MODE="0666"' \
    > /etc/udev/rules.d/99-orbbec.rules
udevadm control --reload-rules
udevadm trigger

# ── Git LFS ───────────────────────────────────────────────────────────────────
echo "→ Installing git-lfs and pulling LFS assets (background images)..."
apt-get install -y git-lfs 2>/dev/null || true
git -C "$REPO_ROOT" lfs install
git -C "$REPO_ROOT" lfs pull

# ── Python dependencies ────────────────────────────────────────────────────────
echo "→ Installing Python dependencies..."
apt-get install -y python3-numpy python3-scipy 2>/dev/null || true
pip3 install --break-system-packages -r "$APP_DIR/requirements.txt"

# ── Patch service file with actual app path ────────────────────────────────────
echo "→ Installing systemd unit..."
DEST="/etc/systemd/system/captcha.service"
sed "s|User=ii|User=$SERVICE_USER|g" \
    "$SCRIPT_DIR/captcha.service" > "$DEST"
echo "   written: $DEST"

# ── Enable + start ─────────────────────────────────────────────────────────────
systemctl daemon-reload
systemctl enable captcha.service
systemctl start  captcha.service

echo ""
echo "=== Done ==="
echo "Start:   sudo systemctl start captcha"
echo "Logs:    journalctl -u captcha -f"
echo "Monitor: http://$(hostname -I | awk '{print $1}'):8080/"
