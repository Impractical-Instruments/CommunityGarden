#!/bin/bash
# Double-click in Finder to launch the BodyCaptcha level editor (macOS).
# First launch creates .venv next to this file and installs pygame + Pillow.
# Needs Homebrew's python@3.13 (`brew install python@3.13`).

cd "$(dirname "$0")" || exit 1

fail() {
  echo
  echo "ERROR: $1"
  read -r -p "Press Return to close this window."
  exit 1
}

if [ ! -x .venv/bin/python ]; then
  PY=""
  for c in /opt/homebrew/opt/python@3.13/bin/python3.13 \
           /usr/local/opt/python@3.13/bin/python3.13 \
           python3.13; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
  done
  [ -n "$PY" ] || fail "Python 3.13 not found. Install it with: brew install python@3.13"

  echo "First launch: setting up the editor (takes a minute)..."
  "$PY" -m venv .venv || fail "could not create .venv"
  .venv/bin/python -m pip install --upgrade pip || fail "pip upgrade failed"
  .venv/bin/python -m pip install pygame pillow || fail "installing pygame/Pillow failed"
fi

.venv/bin/python bodycaptcha_editor.py "$@" || fail "the editor exited with an error (see above)"
