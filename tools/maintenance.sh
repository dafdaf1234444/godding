#!/bin/bash
# Portable maintenance wrapper for shells without a local python launcher.
# Usage:
#   bash tools/maintenance.sh
#   bash tools/maintenance.sh --inventory
#   bash tools/maintenance.sh --quick

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

choose_python() {
    if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
        PYTHON_CMD=(python3)
        return 0
    fi
    if command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
        PYTHON_CMD=(python)
        return 0
    fi
    # Windows launcher fallback for shells where python/python3 are not on PATH.
    if command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
        PYTHON_CMD=(py -3)
        return 0
    fi
    return 1
}

declare -a PYTHON_CMD=()
if ! choose_python; then
    echo "FAIL: No runnable python interpreter found (python3/python/py -3)."
    exit 1
fi

"${PYTHON_CMD[@]}" tools/maintenance.py "$@"
