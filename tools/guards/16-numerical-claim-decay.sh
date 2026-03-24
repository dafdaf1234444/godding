#!/bin/bash
# FM-27: Body-text numerical claim decay scanner (L-894, L-887, S469).
# Scans staged lessons for unstamped numerical claims. NOTICE only.
# Requires: PYTHON_CMD array and STAGED_LESSONS variable set by caller.
if [ -f "tools/numerical_claim_scanner.py" ] && [ -n "$STAGED_LESSONS" ]; then
    FM27_SESSION=$(git log --oneline -1 2>/dev/null | grep -oP 'S\K\d+' || echo 0)
    CLAIM_OUT=$("${PYTHON_CMD[@]}" tools/numerical_claim_scanner.py --staged --session "${FM27_SESSION}" 2>&1) || true
    if echo "$CLAIM_OUT" | grep -q "FM-27"; then
        echo "$CLAIM_OUT" | head -3
    fi
fi
