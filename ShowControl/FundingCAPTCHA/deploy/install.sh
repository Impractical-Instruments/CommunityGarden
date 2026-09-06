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

# ── Private show content (optional) ───────────────────────────────────────────
# Set PRIVATE_ASSETS_REPO to an SSH clone URL to pull unpublishable show content
# into images/private/. Skipped silently when unset or when no key is present, so
# a plain public clone still installs and runs the default level set. A
# configured-but-failing sync (unreadable key, network down, diverged history,
# etc.) warns loudly and falls back to the default level set rather than
# aborting the install — the systemd unit below must still get installed.
PRIVATE_DIR="$APP_DIR/images/private"
PRIVATE_KEY="${PRIVATE_ASSETS_KEY:-$(getent passwd "$SERVICE_USER" | cut -d: -f6)/.ssh/private_assets_ed25519}"

if [ -n "${PRIVATE_ASSETS_REPO:-}" ] && [ -f "$PRIVATE_KEY" ]; then
    if ! sudo -u "$SERVICE_USER" test -r "$PRIVATE_KEY"; then
        echo "→ WARNING: private assets key $PRIVATE_KEY is not readable by $SERVICE_USER"
        echo "   (likely owned by root, or its permissions are too restrictive) — skipping private content sync."
    else
        echo "→ Syncing private show content..."
        export GIT_SSH_COMMAND="ssh -i $PRIVATE_KEY -o IdentitiesOnly=yes"
        SYNC_OK=1
        if [ -d "$PRIVATE_DIR/.git" ]; then
            sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
                git -C "$PRIVATE_DIR" pull --ff-only \
                && sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
                    git -C "$PRIVATE_DIR" lfs pull \
                || SYNC_OK=0
        else
            sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
                git clone "$PRIVATE_ASSETS_REPO" "$PRIVATE_DIR" \
                && sudo -u "$SERVICE_USER" --preserve-env=GIT_SSH_COMMAND \
                    git -C "$PRIVATE_DIR" lfs pull \
                || SYNC_OK=0
        fi
        unset GIT_SSH_COMMAND
        if [ "$SYNC_OK" = 1 ]; then
            echo "   synced: $PRIVATE_DIR"
        else
            echo "→ WARNING: private show content sync FAILED — continuing without it."
            echo "   Check that $PRIVATE_ASSETS_REPO is reachable and $PRIVATE_KEY is a valid deploy key."
        fi
    fi
else
    echo "→ No private show content configured — skipping."
fi

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
