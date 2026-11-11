#!/usr/bin/env bash
# install.sh — set up TreeHouse as an auto-starting systemd service.
# Run once after cloning the repo:
#   sudo bash ShowControl/TreeHouse/deploy/install.sh
set -e
. "$(dirname "$0")/../../../scripts/lib/install-element.sh"

# ── System dependencies ───────────────────────────────────────────────────────
echo "→ Installing system dependencies..."
apt-get install -y libx11-dev weston seatd libgl1-mesa-dri libegl1 libegl-mesa0 libgl1

# ── Seat management (weston drm-backend requires seatd or logind) ─────────────
echo "→ Enabling seatd..."
systemctl enable --now seatd
usermod -aG _seat "$SERVICE_USER"

# ── EGL symlinks (moderngl dlopen("libEGL.so") — Pi OS ships only versioned .so.1) ──
echo "→ Creating EGL/GL symlinks..."
ln -sf /lib/aarch64-linux-gnu/libEGL.so.1 /lib/aarch64-linux-gnu/libEGL.so
ln -sf /lib/aarch64-linux-gnu/libGL.so.1  /lib/aarch64-linux-gnu/libGL.so
ldconfig

install_element treehouse treehouse
install_done Viz 8766
