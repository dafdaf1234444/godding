#!/bin/bash
# F-GND1: External grounding check for staged lessons (L-1125, L-1192, S479).
# FAIL unless lesson has External: field or ALLOW_UNGROUNDED=1 is set.
# Requires: PYTHON_CMD array and STAGED_NEW_LESSONS variable set by caller.
if [ -n "$STAGED_NEW_LESSONS" ] && [ -f "tools/external_grounding_check.py" ]; then
    GND_EXIT=0
    GND_OUT=$("${PYTHON_CMD[@]}" tools/external_grounding_check.py --staged --enforce 2>&1) || GND_EXIT=$?
    if [ -n "$GND_OUT" ]; then
        echo "$GND_OUT"
    fi
    if [ "${GND_EXIT}" -eq 1 ]; then
        echo "FAIL: Lesson(s) without external grounding (F-GND1, L-1125, L-601)."
        echo "  Fix: add 'External: <url, paper, benchmark, or theory>' to lesson header."
        echo "  Or: add 'External: none — <reason>' to explicitly mark as internal-only."
        echo "  Override: ALLOW_UNGROUNDED=1 git commit ..."
        if [ "${ALLOW_UNGROUNDED:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_UNGROUNDED=1 set — bypassing grounding guard."
    fi
fi
