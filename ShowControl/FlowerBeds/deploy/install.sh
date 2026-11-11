#!/usr/bin/env bash
# install.sh — set up FlowerBeds as an auto-starting systemd service.
# Run once after cloning the repo:
#   sudo bash ShowControl/FlowerBeds/deploy/install.sh
set -e
. "$(dirname "$0")/../../../scripts/lib/install-element.sh"

# numpy and scipy from apt are faster on Pi/ARM
apt-get install -y python3-numpy python3-scipy 2>/dev/null || true

install_element flowerbeds,camera flowerbeds
install_done Viz 8765
