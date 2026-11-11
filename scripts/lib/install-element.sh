# install-element.sh — the steps every ShowControl/<Element>/deploy/install.sh shares.
#
# Source it from an Element's deploy/install.sh, which runs under sudo:
#
#   . "$(dirname "$0")/../../../scripts/lib/install-element.sh"
#   ...Element-specific steps (apt packages, udev rules)...
#   install_element <extras> <service>
#   install_done <label> <port>
#
# Sourcing sets REPO_ROOT, ELEMENT, APP_DIR, DEPLOY_DIR, SERVICE_USER and
# SERVICE_UID, and prints the header. The Element is the directory holding
# deploy/, so nothing here depends on where the repo is cloned.

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$DEPLOY_DIR")"
ELEMENT="$(basename "$APP_DIR")"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_USER="${SUDO_USER:-ii}"
SERVICE_UID="$(id -u "$SERVICE_USER")"

echo "=== $ELEMENT install ==="
echo "App dir: $APP_DIR"
echo "User:    $SERVICE_USER"
echo ""

# render_unit <source.service>
# Print the unit with @REPO_ROOT@, @SERVICE_USER@ and @SERVICE_UID@ filled in.
render_unit() {
    local root user
    # Escape what sed treats specially in a replacement: \ & and the | delimiter.
    root="$(printf '%s' "$REPO_ROOT" | sed 's/[\\&|]/\\&/g')"
    user="$(printf '%s' "$SERVICE_USER" | sed 's/[\\&|]/\\&/g')"
    sed -e "s|@REPO_ROOT@|$root|g" \
        -e "s|@SERVICE_USER@|$user|g" \
        -e "s|@SERVICE_UID@|$SERVICE_UID|g" \
        "$1"
}

# install_element <extras> <service>
#   extras   pyproject.toml extras for this Element, e.g. "flowerbeds,camera"
#   service  systemd unit name without .service, e.g. "cg-dashboard"
# Installs the Python dependencies, writes the unit from the one *.service file
# in deploy/, then enables and restarts it.
install_element() {
    local extras="$1" service="$2"
    local units=("$DEPLOY_DIR"/*.service)
    if [ "${#units[@]}" -ne 1 ] || [ ! -f "${units[0]}" ]; then
        echo "Error: expected exactly one .service file in $DEPLOY_DIR" >&2
        return 1
    fi

    echo "→ Installing Python dependencies..."
    # --no-build-isolation: build with the system setuptools. An isolated build
    # downloads setuptools from PyPI, which fails on the show LAN (no internet).
    pip3 install --break-system-packages --no-build-isolation -e "$REPO_ROOT[$extras]"

    echo "→ Installing systemd unit..."
    # SYSTEMD_UNIT_DIR is overridden only by scripts/test_install_element.py.
    local dest="${SYSTEMD_UNIT_DIR:-/etc/systemd/system}/$service.service"
    render_unit "${units[0]}" > "$dest"
    echo "   written: $dest"

    systemctl daemon-reload
    systemctl enable "$service.service"
    systemctl restart "$service.service"
    INSTALLED_SERVICE="$service"
}

# install_done <label> <port>
# Print the trailer: how to check the service, and its URL on this host.
install_done() {
    echo ""
    echo "=== Done ==="
    echo "Status:  sudo systemctl status $INSTALLED_SERVICE"
    echo "Logs:    journalctl -u $INSTALLED_SERVICE -f"
    printf '%-8s http://%s:%s/\n' "$1:" "$(hostname -I | awk '{print $1}')" "$2"
}
