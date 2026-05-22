#!/usr/bin/env bash
# install-services.sh — install all CommunityGarden show-control services.
#
# Run once after cloning the repo on each show computer:
#   sudo bash scripts/install-services.sh
#
# Optional: install a subset of elements:
#   sudo bash scripts/install-services.sh FlowerBeds TreeHouse
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ "$EUID" -ne 0 ]; then
    echo "Error: run as root — sudo bash $0"
    exit 1
fi

ALL_ELEMENTS=(FlowerBeds TreeHouse Dashboard FundingCAPTCHA)

if [ "$#" -eq 0 ]; then
    echo "Error: specify which element(s) to install. Each Pi runs one element."
    echo ""
    echo "Usage: sudo bash $0 <element> [element ...]"
    echo "Available: ${ALL_ELEMENTS[*]}"
    echo ""
    echo "To install all (unusual): sudo bash $0 ${ALL_ELEMENTS[*]}"
    exit 1
fi

ELEMENTS=("$@")

echo "=== CommunityGarden service install ==="
echo "Repo:     $REPO_ROOT"
echo "Elements: ${ELEMENTS[*]}"
echo ""

for element in "${ELEMENTS[@]}"; do
    deploy="$REPO_ROOT/ShowControl/$element/deploy/install.sh"
    if [ -f "$deploy" ]; then
        echo "━━━ $element ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        bash "$deploy"
        echo ""
    else
        echo "━━━ $element — no deploy/install.sh found, skipping ━━━━━━━━━"
        echo ""
    fi
done

echo "=== All done ==="
echo ""
echo "Service status:"
for svc in flowerbeds treehouse cg-dashboard captcha; do
    if systemctl list-unit-files "$svc.service" &>/dev/null; then
        state=$(systemctl is-active "$svc.service" 2>/dev/null || echo "inactive")
        printf "  %-20s %s\n" "$svc" "$state"
    fi
done
echo ""
echo "View logs:  journalctl -u <service> -f"
if systemctl is-active --quiet cg-dashboard.service 2>/dev/null; then
    echo "Dashboard:  http://$(hostname -I | awk '{print $1}'):9000/"
fi
