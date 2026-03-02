#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SRC="$REPO_ROOT/tools/pre-commit.hook"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"
if [ ! -f "$HOOK_SRC" ]; then
    echo "Missing hook source: $HOOK_SRC" >&2
    exit 1
fi
if [ ! -d "$REPO_ROOT/.git/hooks" ]; then
    echo "Missing git hooks directory: $REPO_ROOT/.git/hooks" >&2
    exit 1
fi
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "Pre-commit hook installed: $HOOK_DST"
