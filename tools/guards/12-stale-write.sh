#!/bin/bash
# FM-19: Stale-write detector (L-525, L-601, F-CAT1).
# Detects when staged high-contention files were recently modified by another session.
# Content-loss detection for APPEND/MIXED files; warning for REPLACE files.
# Requires: PYTHON_CMD array set by caller.
if [ -f "tools/stale_write_check.py" ]; then
    STALE_EXIT=0
    STALE_ARGS=(--staged)
    # L-1175: pass session identity to avoid misidentification at N>=3 concurrency
    if [ -n "${SWARM_SESSION:-}" ]; then
        STALE_ARGS+=(--session "$SWARM_SESSION")
    fi
    STALE_OUT=$("${PYTHON_CMD[@]}" tools/stale_write_check.py "${STALE_ARGS[@]}" 2>&1) || STALE_EXIT=$?
    if [ -n "$STALE_OUT" ]; then
        echo "$STALE_OUT"
    fi
    if [ "$STALE_EXIT" -eq 1 ]; then
        echo "  FM-19 stale-write: CONTENT LOSS RISK — re-read files and merge concurrent changes"
        echo "  Bypass: ALLOW_STALE_WRITE=1 git commit ..."
        if [ "${ALLOW_STALE_WRITE:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_STALE_WRITE=1 set — bypassing stale-write guard."
    elif [ "$STALE_EXIT" -eq 0 ]; then
        echo "  FM-19 stale-write guard: PASS"
    fi
fi
