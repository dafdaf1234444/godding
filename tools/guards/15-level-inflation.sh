#!/bin/bash
# FM-37: Level inflation detector (L-1119, F-CAT1, S467).
# LLM self-tagging inflates L3+ levels — 45% misclassification rate.
# NOTICE only — advisory layer for awareness.
# Requires: PYTHON_CMD array and STAGED_LESSONS variable set by caller.
if [ -f "tools/level_inflation_check.py" ] && [ -n "$STAGED_LESSONS" ]; then
    INFLATION_OUT=$("${PYTHON_CMD[@]}" tools/level_inflation_check.py --staged 2>&1) || true
    if echo "$INFLATION_OUT" | grep -q "SUSPECT"; then
        echo "$INFLATION_OUT" | grep -E "(SUSPECT|NOTICE)" | head -5
    else
        echo "  FM-37 level inflation guard: PASS"
    fi
fi
