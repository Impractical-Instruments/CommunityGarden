# install-element.sh — the steps every ShowControl/<Element>/deploy/install.sh shares.
#
# Source it from an Element's deploy/install.sh, which runs under sudo:
#
#   . "$(dirname "$0")/../../../scripts/lib/install-element.sh"
#   ...Element-specific steps (apt packages, udev rules)...
#   PYTHON_DEPS=pip    # only an Element that cannot use uv yet; say why beside it
#   install_element <extras> <service>...
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

# find_uv
# Print the service user's uv. CG_UV is set only by scripts/test_install_element.py.
find_uv() {
    local home candidate candidates
    if [ -n "${CG_UV:-}" ]; then
        candidates=("$CG_UV")
    else
        home="$(getent passwd "$SERVICE_USER" | cut -d: -f6)"
        candidates=("$home/.local/bin/uv" "$home/.cargo/bin/uv" "$(command -v uv || true)")
    fi
    for candidate in "${candidates[@]}"; do
        if [ -n "$candidate" ] && [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# uv_sync <extras>
# The repo's .venv, as the service user, from uv.lock: the Python in .python-version
# and exactly the locked packages, the same as CI. No dev group: only this Element's
# extras. --inexact so a second Element on the same machine keeps the first's packages.
# Offline first, from uv's cache, since show machines usually have no internet; online
# only when something new is not cached yet.
uv_sync() {
    local uv extra list args=(sync --locked --no-dev --inexact)
    if ! uv="$(find_uv)"; then
        echo "Error: no uv for $SERVICE_USER. Install it as $SERVICE_USER (needs internet):" >&2
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
        return 1
    fi
    IFS=, read -ra list <<< "$1"
    for extra in "${list[@]}"; do
        args+=(--extra "$extra")
    done
    if ! sudo -u "$SERVICE_USER" -H "$uv" --directory "$REPO_ROOT" "${args[@]}" --offline; then
        echo "   Not everything is in uv's cache; trying online..."
        sudo -u "$SERVICE_USER" -H "$uv" --directory "$REPO_ROOT" "${args[@]}"
    fi
}

# install_element <extras> <service>...
#   extras   pyproject.toml extras for this Element, e.g. "flowerbeds,camera"
#   service  systemd unit name without .service, e.g. "cg-dashboard"
# Installs the Python dependencies (uv_sync, or system pip when the Element set
# PYTHON_DEPS=pip), writes each unit from the *.service files in
# deploy/, then enables and restarts them in the order given.
#
# One service: deploy/ holds one *.service file, under any name. Several: each
# is rendered from deploy/<service>.service. A *.service file that no service
# claims is an error, so a unit cannot be left out by mistake.
install_element() {
    local extras="$1"
    shift
    local services=("$@") units=("$DEPLOY_DIR"/*.service) sources=() service
    if [ "${#services[@]}" -eq 1 ]; then
        if [ "${#units[@]}" -ne 1 ] || [ ! -f "${units[0]}" ]; then
            echo "Error: expected exactly one .service file in $DEPLOY_DIR" >&2
            return 1
        fi
        sources=("${units[0]}")
    else
        for service in "${services[@]}"; do
            if [ ! -f "$DEPLOY_DIR/$service.service" ]; then
                echo "Error: no $service.service in $DEPLOY_DIR" >&2
                return 1
            fi
            sources+=("$DEPLOY_DIR/$service.service")
        done
        if [ "${#units[@]}" -ne "${#services[@]}" ]; then
            echo "Error: $DEPLOY_DIR has a .service file that install.sh does not install" >&2
            return 1
        fi
    fi

    echo "→ Installing Python dependencies..."
    if [ "${PYTHON_DEPS:-uv}" = pip ]; then
        # --no-build-isolation: build with the system setuptools. An isolated build
        # downloads setuptools from PyPI, which fails on the show LAN (no internet).
        pip3 install --break-system-packages --no-build-isolation -e "$REPO_ROOT[$extras]"
    else
        uv_sync "$extras"
    fi

    echo "→ Installing systemd unit(s)..."
    # SYSTEMD_UNIT_DIR is overridden only by scripts/test_install_element.py.
    local i dest
    for i in "${!services[@]}"; do
        dest="${SYSTEMD_UNIT_DIR:-/etc/systemd/system}/${services[$i]}.service"
        render_unit "${sources[$i]}" > "$dest"
        echo "   written: $dest"
    done

    systemctl daemon-reload
    for service in "${services[@]}"; do
        systemctl enable "$service.service"
    done
    for service in "${services[@]}"; do
        systemctl restart "$service.service"
    done
    INSTALLED_SERVICES=("${services[@]}")
}

# install_done <label> <port>
# Print the trailer: how to check the service, and its URL on this host.
install_done() {
    echo ""
    echo "=== Done ==="
    echo "Status:  sudo systemctl status ${INSTALLED_SERVICES[*]}"
    echo "Logs:    journalctl -f$(printf ' -u %s' "${INSTALLED_SERVICES[@]}")"
    printf '%-8s http://%s:%s/\n' "$1:" "$(hostname -I | awk '{print $1}')" "$2"
}
