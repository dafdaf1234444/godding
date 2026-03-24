#!/bin/bash
# FM-13: Colony belief drift check (I9/MC-SAFE, F-SEC1 Layer 3, S379).
# If any colony's belief drift exceeds 30%, require council review before commit.
# Requires: PYTHON_CMD array set by caller.
if [ -f "tools/merge_back.py" ]; then
    DRIFT_OUT=$("${PYTHON_CMD[@]}" tools/merge_back.py --check 2>&1)
    DRIFT_EXIT=$?
    if [ "$DRIFT_EXIT" -ne 0 ]; then
        echo "FAIL: Colony belief drift exceeds 30% — council review required (F-SEC1 Layer 3)."
        echo "$DRIFT_OUT"
        if [ "${ALLOW_COLONY_DRIFT:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_COLONY_DRIFT=1 set — bypassing drift guard."
    else
        echo "  Colony drift check: PASS"
    fi
fi
