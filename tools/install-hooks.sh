#!/bin/bash
# Install swarm git hooks.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "FAIL: $HOOKS_DIR not found."
    exit 1
fi

cp "$REPO_ROOT/tools/pre-commit.hook" "$HOOKS_DIR/pre-commit"
cp "$REPO_ROOT/tools/commit-msg.hook" "$HOOKS_DIR/commit-msg"
chmod +x "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/commit-msg"

echo "Installed hooks: pre-commit, commit-msg."
