#!/usr/bin/env bash
# install.sh — set up FlowerBeds as an auto-starting systemd service.
# Run once after cloning the repo:
#   sudo bash ShowControl/FlowerBeds/deploy/install.sh
set -e
. "$(dirname "$0")/../../../scripts/lib/install-element.sh"

install_element flowerbeds,camera flowerbeds
install_done Viz 8765
