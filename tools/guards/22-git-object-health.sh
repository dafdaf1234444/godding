#!/bin/bash
# FM-14: Git object health check (loose object corruption, L-720, L-658).
# Only runs in full mode (not --quick) to avoid slowing pre-commit.
# Requires: GUARD_MODE variable set by caller ("quick" or "full").
if [ "${GUARD_MODE:-quick}" = "full" ]; then
    GIT_FSCK_OUT=$(timeout 30 git fsck --no-dangling --connectivity-only 2>&1 || true)
    if echo "$GIT_FSCK_OUT" | grep -qiE "^(broken|missing|error)"; then
        echo "FAIL: Git object corruption detected (FM-14, L-720)."
        echo "$GIT_FSCK_OUT" | head -5
        echo "  Fix: git reflog expire --expire=now --all && git gc --prune=now"
        echo "  Or: fresh clone if gc fails."
        if [ "${ALLOW_GIT_CORRUPTION:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_GIT_CORRUPTION=1 set — bypassing git health guard."
    else
        echo "  Git object health: PASS"
    fi
fi
