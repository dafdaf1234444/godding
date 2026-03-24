#!/bin/bash
# FM-01 layer 1: Mass-deletion guard (I9/MC-SAFE, L-346, L-350).
# Protects against WSL filesystem corruption staging mass file deletions via git add -A accidents.
# Counts DELETED FILES (D status), not line-level deletions — avoids false positives on large edits.
FILE_DELETION_THRESHOLD=20
FM09_NOTICE_THRESHOLD=5
STAGED_FILE_DELETIONS=$(git diff --cached --diff-filter=D --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "${STAGED_FILE_DELETIONS:-0}" -gt "$FILE_DELETION_THRESHOLD" ]; then
    echo "FAIL: Mass-deletion guard triggered — ${STAGED_FILE_DELETIONS} staged file deletions (threshold: ${FILE_DELETION_THRESHOLD})."
    echo "  This likely means WSL filesystem corruption caused 'git add' to stage file deletions."
    echo "  Run: git diff --cached --diff-filter=D --name-only | head -20 — to inspect."
    echo "  If intentional (compaction archive), set env ALLOW_MASS_DELETION=1 to bypass."
    if [ "${ALLOW_MASS_DELETION:-0}" != "1" ]; then
        exit 1
    fi
    echo "  ALLOW_MASS_DELETION=1 set — bypassing mass-deletion guard."
elif [ "${STAGED_FILE_DELETIONS:-0}" -gt "$FM09_NOTICE_THRESHOLD" ]; then
    # FM-09 cross-session notice (I9/MC-SAFE): staged deletions above notice threshold but below hard-fail.
    echo "  FM-09 NOTICE: ${STAGED_FILE_DELETIONS} staged file deletions (>${FM09_NOTICE_THRESHOLD}) — verify these are yours"
    echo "    If foreign (from concurrent session): git restore --staged . — then re-stage your files"
    git diff --cached --diff-filter=D --name-only 2>/dev/null | head -5
fi
echo "  Mass-deletion guard: PASS (${STAGED_FILE_DELETIONS:-0} staged file deletions)"
