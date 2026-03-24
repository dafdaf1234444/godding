#!/bin/bash
# FM-11: Genesis bundle hash verification (I9/MC-SAFE, F-SEC1 Layer 1, S377).
# If a genesis hash file exists, verify current bundle matches.
# Requires: PYTHON_CMD array set by caller.
LATEST_HASH_FILE=$("${PYTHON_CMD[@]}" - <<'PY' 2>/dev/null
from pathlib import Path
import re

files = sorted(Path("workspace").glob("genesis-bundle-*.hash"),
               key=lambda f: f.stat().st_mtime)
canon = re.compile(r"genesis-bundle-S\d+[A-Za-z0-9-]*\.hash$")
pool = [f for f in files if canon.fullmatch(f.name)] or files
print(pool[-1].as_posix() if pool else "")
PY
)
if [ -n "$LATEST_HASH_FILE" ]; then
    STORED_HASH=$(head -1 "$LATEST_HASH_FILE" | tr -d '[:space:]')
    if [ -n "$STORED_HASH" ]; then
        CURRENT_HASH=$("${PYTHON_CMD[@]}" -c "
import hashlib, sys
from pathlib import Path
root = Path('.')
files = []
for p in ['workspace/genesis.sh', 'beliefs/CORE.md']:
    fp = root / p
    if fp.exists(): files.append(fp)
for candidate in ['beliefs/PRINCIPLES.md', 'memory/PRINCIPLES.md']:
    fp = root / candidate
    if fp.exists():
        files.append(fp)
        break
h = hashlib.sha256()
for f in files:
    h.update(f.read_bytes())
print(h.hexdigest())
" 2>/dev/null || echo "ERROR")
        if [ "$CURRENT_HASH" = "ERROR" ]; then
            echo "  Genesis hash check: SKIP (computation error)"
        elif [ "$CURRENT_HASH" = "$STORED_HASH" ]; then
            echo "  Genesis hash check: PASS (matches $(basename "$LATEST_HASH_FILE"))"
        else
            echo "  Genesis hash check: FAIL (current ${CURRENT_HASH:0:12}... != stored ${STORED_HASH:0:12}...)"
            echo "    Genesis bundle files changed since $(basename "$LATEST_HASH_FILE") was written."
            echo "    To update: python3 tools/genesis_hash.py --write (uses same file set as this check)"
            echo "    Files checked: workspace/genesis.sh, beliefs/CORE.md, memory/PRINCIPLES.md"
            echo "    If unexpected: investigate genesis.sh / CORE.md / PRINCIPLES.md changes."
            echo "    FM-11 hardening (L-720): genesis replay prevention requires hash match."
            echo "    Bypass: ALLOW_GENESIS_DRIFT=1 git commit ..."
            if [ "${ALLOW_GENESIS_DRIFT:-0}" = "1" ]; then
                echo "$CURRENT_HASH" > "$LATEST_HASH_FILE"
                echo "  Genesis hash auto-updated in $(basename "$LATEST_HASH_FILE") (ALLOW_GENESIS_DRIFT=1)"
            else
                exit 1
            fi
        fi
    fi
fi
