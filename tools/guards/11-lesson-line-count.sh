#!/bin/bash
# FM-31: Lesson line-count guard (L-601, L-1053). Max 20 lines per lesson.
# Enforces at creation time — prevents post-hoc trim cycles.
# Requires: STAGED_NEW_LESSONS variable set by caller.
if [ -n "$STAGED_NEW_LESSONS" ]; then
    LONG_LESSONS=""
    while IFS= read -r lesson_path; do
        if [ -f "$lesson_path" ]; then
            LINE_COUNT=$(wc -l < "$lesson_path" | tr -d ' ')
            if [ "$LINE_COUNT" -gt 20 ]; then
                LONG_LESSONS="${LONG_LESSONS} ${lesson_path}(${LINE_COUNT}L)"
            fi
        fi
    done <<< "$STAGED_NEW_LESSONS"
    if [ -n "$LONG_LESSONS" ]; then
        echo "  FM-31 FAIL: Lesson(s) exceed 20-line limit:${LONG_LESSONS}"
        echo "    Trim before committing. Bypass: ALLOW_LONG_LESSON=1 git commit ..."
        if [ "${ALLOW_LONG_LESSON:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_LONG_LESSON=1 set — bypassing lesson line-count guard."
    else
        echo "  FM-31 lesson line-count guard: PASS"
    fi
fi
