#!/bin/bash
# Orient section re-export integrity (L-1213, F-META2).
# Every def section_* in orient_analysis.py and orient_monitors.py must be
# re-exported in orient_sections.py. Missing re-exports break orient.py for ALL sessions.
# Requires: PYTHON_CMD array set by caller.
if [ -f "tools/orient_sections.py" ] && [ -f "tools/orient_analysis.py" ] && [ -f "tools/orient_monitors.py" ]; then
    REEXPORT_EXIT=0
    REEXPORT_TMPF=$(mktemp)
    "${PYTHON_CMD[@]}" - << 'PYEOF' > "$REEXPORT_TMPF" 2>&1 || REEXPORT_EXIT=$?
import re
missing = []
hub = open("tools/orient_sections.py").read()
for sub in ["tools/orient_analysis.py", "tools/orient_monitors.py"]:
    for m in re.findall(r'^def (section_\w+)', open(sub).read(), re.MULTILINE):
        if m not in hub:
            missing.append(f"{sub}: {m}")
if missing:
    for m in missing:
        print(f"  MISSING re-export: {m}")
    raise SystemExit(1)
PYEOF
    REEXPORT_OUT=$(cat "$REEXPORT_TMPF")
    rm -f "$REEXPORT_TMPF"
    if [ "$REEXPORT_EXIT" -ne 0 ]; then
        echo "FAIL: Orient section re-export integrity broken (L-1213)."
        echo "$REEXPORT_OUT"
        echo "  Fix: add missing function(s) to orient_sections.py import statements."
        if [ "${ALLOW_MISSING_REEXPORT:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_MISSING_REEXPORT=1 set — bypassing re-export guard."
    else
        echo "  Orient re-export integrity: PASS"
    fi
fi
