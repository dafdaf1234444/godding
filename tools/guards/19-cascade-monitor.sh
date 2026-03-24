#!/bin/bash
# FM-30: Cross-layer cascade detector (L-1015, F-CAT1, S441).
# Non-blocking NOTICE — cascades require monitoring, not commit abort.
# Requires: PYTHON_CMD array set by caller.
if [ -f "tools/cascade_monitor.py" ]; then
    CASCADE_OUT=$("${PYTHON_CMD[@]}" tools/cascade_monitor.py 2>&1) || true
    CASCADE_COUNT=$(echo "$CASCADE_OUT" | grep -c "ACTIVE CASCADES" || true)
    if echo "$CASCADE_OUT" | grep -q "ACTIVE CASCADES"; then
        SEVERITY=$(echo "$CASCADE_OUT" | grep -oE "severity=[0-9]+" | awk -F= 'BEGIN{m=0}{if($2>m)m=$2}END{print m}')
        echo "  FM-30 cascade guard: NOTICE — active cross-layer cascade (max severity=${SEVERITY}) — run cascade_monitor.py"
    else
        echo "  FM-30 cascade guard: PASS"
    fi
fi
