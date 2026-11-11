#!/usr/bin/env bash
# install.sh — set up the show Dashboard as an auto-starting systemd service.
# Run once after cloning the repo:
#   sudo bash ShowControl/Dashboard/deploy/install.sh
set -e
. "$(dirname "$0")/../../../scripts/lib/install-element.sh"

install_element dashboard cg-dashboard
install_done URL 9000
