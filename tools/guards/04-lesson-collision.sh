#!/bin/bash
# FM-18: Lesson number collision guard (L-903, S412).
# Detects concurrent sessions creating the same L-NNN.md — last-writer-wins silently drops work.
# Title-filename mismatch (title says L-NNN but file is L-MMM) is the primary collision signal.
# Requires: PYTHON_CMD array set by caller.
if [ -f "tools/lesson_collision_check.py" ]; then
    COLLISION_EXIT=0
    COLLISION_OUT=$("${PYTHON_CMD[@]}" tools/lesson_collision_check.py --staged 2>&1) || COLLISION_EXIT=$?
    if [ "${COLLISION_EXIT}" -eq 1 ]; then
        echo "FAIL: Lesson number collision detected (FM-18, L-903)."
        echo "$COLLISION_OUT"
        echo "  Fix: rename conflicting lesson to next available L-NNN number."
        if [ "${ALLOW_LESSON_COLLISION:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_LESSON_COLLISION=1 set — bypassing collision guard."
    else
        echo "  FM-18 collision guard: PASS"
    fi
fi
