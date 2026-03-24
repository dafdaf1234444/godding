#!/bin/bash
# FM-01 layer 2: Mass-staging guard (L-903, S410).
# Catches 'git add -A' / 'git add .' even when no deletions are involved.
# Threshold: >100 staged files is almost certainly accidental.
MASS_STAGE_THRESHOLD=100
STAGED_FILE_COUNT=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "${STAGED_FILE_COUNT:-0}" -gt "$MASS_STAGE_THRESHOLD" ]; then
    echo "FAIL: Mass-staging guard triggered — ${STAGED_FILE_COUNT} staged files (threshold: ${MASS_STAGE_THRESHOLD})."
    echo "  This likely means 'git add -A' or 'git add .' was used. Stage files individually instead."
    echo "  If intentional, set env ALLOW_MASS_STAGING=1 to bypass."
    if [ "${ALLOW_MASS_STAGING:-0}" != "1" ]; then
        exit 1
    fi
    echo "  ALLOW_MASS_STAGING=1 set — bypassing mass-staging guard."
fi
echo "  Mass-staging guard: PASS (${STAGED_FILE_COUNT:-0} staged files)"
