#!/usr/bin/env bash
# install-git-hooks.sh — symlink this repo's tracked git hooks into .git/hooks.
#
# Symlinks rather than setting core.hooksPath: that setting makes git ignore
# .git/hooks entirely, which would disable the Git LFS hooks installed there
# (post-checkout, post-commit, post-merge, pre-push).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC="$REPO_ROOT/scripts/git-hooks"
DEST="$(git rev-parse --git-path hooks)"

for hook in "$SRC"/*; do
    name="$(basename "$hook")"
    ln -sf "$hook" "$DEST/$name"
    echo "installed: $DEST/$name -> $hook"
done

echo ""
echo "Done. Verify with: ls -l $DEST"
