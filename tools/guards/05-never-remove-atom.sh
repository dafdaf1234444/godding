#!/bin/bash
# FM-10: NEVER-REMOVE atom guard (I9/MC-SAFE, F-SEC1 Layer 4, PROTOCOL.md).
# Core identity files must never be deleted — they are the epistemic backbone.
NEVER_REMOVE_FILES="beliefs/CORE.md tools/validate_beliefs.py"
ATOM_DELETED=0
for nrf in $NEVER_REMOVE_FILES; do
    if git diff --cached --diff-filter=D --name-only 2>/dev/null | grep -q "^${nrf}$"; then
        echo "FAIL: NEVER-REMOVE atom deletion detected — ${nrf}"
        echo "  This file is a load-bearing identity atom (F-SEC1 Layer 4, FM-10)."
        echo "  Deleting it would break epistemic gating. Restore with: git restore --staged ${nrf}"
        ATOM_DELETED=1
    fi
done
if [ "$ATOM_DELETED" -eq 1 ] && [ "${ALLOW_ATOM_DELETE:-0}" != "1" ]; then
    exit 1
fi
if [ "$ATOM_DELETED" -eq 0 ]; then
    echo "  NEVER-REMOVE atom guard: PASS"
fi
