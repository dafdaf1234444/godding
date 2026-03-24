#!/bin/bash
# FM-24: Prescriptive-without-enforcement detector (L-601, F-CAT1).
# Detects new/modified lessons with prescriptive rules but no tool/file reference.
# NOTICE only — flags for awareness, does not block.
STAGED_LESSONS=$(git diff --cached --name-only 2>/dev/null | { grep '^memory/lessons/L-.*\.md$' || true; })
FM24_FLAGGED=0
if [ -n "$STAGED_LESSONS" ]; then
    while IFS= read -r lesson_path; do
        if [ -f "$lesson_path" ]; then
            if grep -qiE '^## Rule|^## Prescription' "$lesson_path" 2>/dev/null; then
                if ! grep -qE 'tools/|\.py\b|\.sh\b|check\.sh|maintenance\.py|orient\.py|open_lane\.py' "$lesson_path" 2>/dev/null; then
                    echo "  FM-24 NOTICE: ${lesson_path} has prescriptive rule but no enforcement path (L-601)"
                    FM24_FLAGGED=$((FM24_FLAGGED + 1))
                fi
            fi
        fi
    done <<< "$STAGED_LESSONS"
    if [ "$FM24_FLAGGED" -eq 0 ] && [ -n "$STAGED_LESSONS" ]; then
        echo "  FM-24 prescription guard: PASS"
    elif [ "$FM24_FLAGGED" -gt 0 ]; then
        echo "  FM-24 prescription guard: ${FM24_FLAGGED} lesson(s) without enforcement path (NOTICE — not blocking)"
    fi
fi
