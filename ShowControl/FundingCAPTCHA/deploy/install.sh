#!/usr/bin/env bash
# install.sh — set up FundingCAPTCHA as auto-starting systemd services on Pi.
# Run once after cloning the repo:
#   cd Prototypes/FundingCAPTCHA/deploy
#   sudo bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APP_DIR="$REPO_ROOT/ShowControl/FundingCAPTCHA"

SERVICE_USER="${SUDO_USER:-pi}"

echo "=== FundingCAPTCHA install ==="
echo "App dir:  $APP_DIR"
echo "User:     $SERVICE_USER"
echo ""

# ── Python dependencies ────────────────────────────────────────────────────────
echo "→ Installing Python dependencies..."
# numpy and scipy from apt are faster on Pi ARM
apt-get install -y python3-numpy python3-scipy 2>/dev/null || true
pip3 install --break-system-packages fastapi "uvicorn[standard]" websockets

# ── gpu_mem in /boot/config.txt (if not already set) ──────────────────────────
if ! grep -q "^gpu_mem=" /boot/config.txt 2>/dev/null && \
   ! grep -q "^gpu_mem=" /boot/firmware/config.txt 2>/dev/null; then
    echo "→ Adding gpu_mem=128 to boot config..."
    TARGET="/boot/firmware/config.txt"
    [ -f "$TARGET" ] || TARGET="/boot/config.txt"
    echo "gpu_mem=128" >> "$TARGET"
    echo "   (reboot required for GPU memory change to take effect)"
fi

# ── Disable Chromium password / restore prompts ────────────────────────────────
CHROME_PREFS="/home/pi/.config/chromium/Default/Preferences"
if [ -f "$CHROME_PREFS" ]; then
    python3 -c "
import json, sys
with open('$CHROME_PREFS') as f: p = json.load(f)
p.setdefault('profile', {})['exit_type'] = 'Normal'
p.setdefault('profile', {})['exited_cleanly'] = True
with open('$CHROME_PREFS', 'w') as f: json.dump(p, f)
" 2>/dev/null || true
fi

# ── Patch service files with actual app path ──────────────────────────────────
echo "→ Installing systemd units..."
for SVC in captcha.service captcha-kiosk.service; do
    DEST="/etc/systemd/system/$SVC"
    sed "s|/home/pi/CommunityGarden/ShowControl/FundingCAPTCHA|$APP_DIR|g
         s|User=pi|User=$SERVICE_USER|g" \
        "$SCRIPT_DIR/$SVC" > "$DEST"
    echo "   written: $DEST"
done

# ── Enable + start ─────────────────────────────────────────────────────────────
systemctl daemon-reload
systemctl enable captcha.service captcha-kiosk.service
systemctl start  captcha.service

echo ""
echo "=== Done ==="
echo "Server:  sudo systemctl start captcha"
echo "Kiosk:   sudo systemctl start captcha-kiosk"
echo "Logs:    journalctl -u captcha -f"
echo ""
echo "Games:   http://localhost:8080/"
echo "Upload:  http://$(hostname -I | awk '{print $1}'):8080/upload.html"
echo "Gallery: http://$(hostname -I | awk '{print $1}'):8080/gallery.html"
