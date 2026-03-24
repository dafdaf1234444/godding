#!/bin/bash
# FM-38: Instrument validity check for staged experiment JSONs (L-1165, S472).
# NOTICE only — advisory layer.
# Requires: PYTHON_CMD array set by caller.
STAGED_EXPERIMENTS=$(git diff --cached --name-only 2>/dev/null | { grep '^experiments/.*\.json$' || true; })
if [ -n "$STAGED_EXPERIMENTS" ] && [ -f "tools/false_instrument_check.py" ]; then
    FM38_OUT=$("${PYTHON_CMD[@]}" tools/false_instrument_check.py --staged 2>&1) || true
    if [ -n "$FM38_OUT" ]; then
        echo "$FM38_OUT" | head -5
        echo "  FM-38 instrument validity: NOTICE — flagged experiment(s) (L-1165)"
    else
        echo "  FM-38 instrument validity: PASS"
    fi
fi
