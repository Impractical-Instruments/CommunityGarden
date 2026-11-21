#!/usr/bin/env bash
# install.sh — set up Playing the Pipes as two auto-starting systemd services:
# pipes-reuben (the audio engine) and pipes-bridge (encoder Picos → reuben, /health).
# Run once after cloning the repo, then on every deploy:
#   sudo bash ShowControl/PlayingThePipes/deploy/install.sh
#
# Before the first run, on the box (docs/bootstrap.md): rustup for the service
# user, `git submodule update --init`, and git-lfs so the samples are real files.
#
# Later runs need no internet, with three exceptions. Each one stops the install
# before any service is restarted, so the box keeps playing what it had:
#   - a reuben bump that adds a crate: run `cargo fetch` in vendor/reuben once
#     with internet;
#   - a reuben bump that changes rust-toolchain.toml: rustup has to download the
#     new toolchain;
#   - a new or changed sample: samples are Git LFS files, and a deploy.sh push
#     does not carry LFS objects. Run `git lfs pull` on the box with internet.
set -e
. "$(dirname "$0")/../../../scripts/lib/install-element.sh"

REUBEN_DIR="$REPO_ROOT/vendor/reuben"
MEDIA_DIR="$APP_DIR/Lamplight2026/media"
PROFILE="$APP_DIR/reuben/pipes.profile.json"
USER_HOME="$(getent passwd "$SERVICE_USER" | cut -d: -f6)"

# Files in $MEDIA_DIR that are still Git LFS pointers, not audio.
lfs_pointers() {
    local f
    for f in "$MEDIA_DIR"/*; do
        [ -f "$f" ] || continue
        if head -c 64 "$f" | grep -qa '^version https://git-lfs'; then
            echo "$f"
        fi
    done
}

# ── System dependencies ───────────────────────────────────────────────────────
# libasound2-dev: reuben's audio layer (cpal) links ALSA.
echo "→ Installing system dependencies..."
apt-get install -y libasound2-dev build-essential pkg-config git-lfs

# ── Audio and serial access ───────────────────────────────────────────────────
# Lingering starts the service user's PipeWire at boot; without a login session
# it is the audio group that lets PipeWire open the interface.
echo "→ Enabling lingering and device groups for $SERVICE_USER..."
usermod -aG audio,dialout "$SERVICE_USER"
loginctl enable-linger "$SERVICE_USER"

# ── Samples ───────────────────────────────────────────────────────────────────
if [ -n "$(lfs_pointers)" ]; then
    echo "→ Some samples are Git LFS pointers; pulling them (needs internet)..."
    sudo -u "$SERVICE_USER" -H git -C "$REPO_ROOT" lfs pull --include "ShowControl/PlayingThePipes/Lamplight2026/media/*" || true
    missing="$(lfs_pointers)"
    if [ -n "$missing" ]; then
        echo "Error: these samples are still Git LFS pointers, so reuben cannot load them:" >&2
        echo "$missing" >&2
        echo "Connect the box to the internet and run: git lfs pull" >&2
        exit 1
    fi
fi

# ── Build reuben ──────────────────────────────────────────────────────────────
# As the service user, so target/ and ~/.cargo stay theirs. Before any restart:
# if the build fails, set -e stops here and the services keep the old binary.
if [ ! -f "$REUBEN_DIR/Cargo.toml" ]; then
    echo "Error: vendor/reuben is empty. Run: git submodule update --init" >&2
    exit 1
fi
CARGO="$USER_HOME/.cargo/bin/cargo"
if [ ! -x "$CARGO" ]; then
    echo "Error: no cargo at $CARGO. Install rustup as $SERVICE_USER (docs/bootstrap.md)." >&2
    exit 1
fi
echo "→ Building reuben (offline; see the header of this script if it fails)..."
# From inside vendor/reuben: rustup picks the pinned toolchain from the working directory.
(cd "$REUBEN_DIR" && sudo -u "$SERVICE_USER" -H "$CARGO" build --release --locked --offline -p reuben-native --bin reuben)

if [ ! -f "$PROFILE" ]; then
    echo "→ WARNING: $PROFILE is missing."
    echo "   pipes-reuben will restart in a loop until the box's device profile is committed there."
fi

# ── Structure channel token ───────────────────────────────────────────────────
# pipes-reuben listens for reuben-editor beyond loopback, which reuben allows only
# with a token. It is made once here and kept across deploys, so an editor's token
# stays good; delete the file and redeploy to rotate it. It never enters the repo.
# Readable by the service user, so `make pipes-editor` can fetch it over ssh.
# PIPES_REUBEN_ENV_FILE is overridden only by scripts/test_install_element.py.
ENV_FILE="${PIPES_REUBEN_ENV_FILE:-/etc/community-garden/pipes-reuben.env}"
STRUCTURE_PORT="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["elements"]["pipes"]["reuben_structure_port"])' "$REPO_ROOT/ShowControl/network.json")"
token=""
if [ -f "$ENV_FILE" ]; then
    token="$(sed -n 's/^REUBEN_STRUCTURE_TOKEN=//p' "$ENV_FILE")"
fi
if [ -z "$token" ]; then
    echo "→ Making the structure channel token..."
    token="$(od -An -tx1 -N16 /dev/urandom | tr -d ' \n')"
fi
mkdir -p "$(dirname "$ENV_FILE")"
(umask 027 && printf 'REUBEN_STRUCTURE_TOKEN=%s\nPIPES_STRUCTURE_ADDR=0.0.0.0:%s\n' "$token" "$STRUCTURE_PORT" > "$ENV_FILE.new")
chown "root:$SERVICE_USER" "$ENV_FILE.new"
mv "$ENV_FILE.new" "$ENV_FILE"
echo "   written: $ENV_FILE"

# ── Python dependencies, systemd units, enable + restart ──────────────────────
install_element pipes pipes-reuben pipes-bridge
install_done Health 8767
