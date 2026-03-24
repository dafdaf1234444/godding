#!/bin/bash
# Universal swarm validation — call from any tool at session start/end.
# Replaces tool-specific hooks for non-Claude tools.
# Usage: bash tools/check.sh [--quick]
#
# Guards are modular: each tools/guards/NN-name.sh is an independent check.
# Add new guards by dropping files into tools/guards/ — no check.sh edits needed.
# Guards receive: PYTHON_CMD, STAGED_NEW_LESSONS, STAGED_LESSONS, GUARD_MODE, REPO_ROOT.
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

ARGS=()
MINIMAL=0
GUARD_MODE="quick"
if [ "${1:-}" = "--quick" ]; then
    ARGS+=(--quick)
    GUARD_MODE="quick"
elif [ "${1:-}" = "--minimal" ]; then
    ARGS+=(--quick)
    MINIMAL=1
    GUARD_MODE="quick"
else
    GUARD_MODE="full"
fi

echo "=== SWARM CHECK ==="

# L-1319 guard: stderr suppression detection (FM-01 amplifier).
STDERR_TARGET=$(readlink /proc/self/fd/2 2>/dev/null || echo "unknown")
if [[ "$STDERR_TARGET" == "/dev/null" ]]; then
    echo "  L-1319 NOTICE: stderr → /dev/null. If retrying git commit, ensure exit codes are checked."
fi

# Export shared variables for guards.
export GUARD_MODE
STAGED_NEW_LESSONS=$(git diff --cached --diff-filter=A --name-only 2>/dev/null | { grep 'memory/lessons/L-[0-9]' || true; } | { grep -v '/archive/' || true; })
STAGED_LESSONS=$(git diff --cached --name-only 2>/dev/null | { grep '^memory/lessons/L-.*\.md$' || true; })

# --- Run all modular guards (tools/guards/*.sh) ---
GUARDS_DIR="$REPO_ROOT/tools/guards"
if [ -d "$GUARDS_DIR" ]; then
    for guard in "$GUARDS_DIR"/*.sh; do
        [ -f "$guard" ] || continue
        # Each guard runs in the current shell (source) so it can access
        # PYTHON_CMD, STAGED_NEW_LESSONS, STAGED_LESSONS, GUARD_MODE.
        # Guards that want to block exit with `exit 1`.
        source "$guard"
    done
fi

# --- Validation suites (post-guard) ---

run_suite() {
    local label="$1"
    local path="$2"
    if [ ! -f "$path" ]; then
        return 0
    fi
    if ! "${PYTHON_CMD[@]}" "$path" >/dev/null 2>&1; then
        echo "FAIL: ${label} failed."
        "${PYTHON_CMD[@]}" "$path"
        exit 1
    fi
    echo "  ${label}: PASS"
}

# 1. Belief integrity (critical)
if "${PYTHON_CMD[@]}" tools/validate_beliefs.py "${ARGS[@]}" 2>/dev/null | grep -q "RESULT: FAIL"; then
    echo "FAIL: Belief validation failed. Fix before committing."
    "${PYTHON_CMD[@]}" tools/validate_beliefs.py --quick
    exit 1
fi
echo "  Beliefs: PASS"

# 1b. Self-model contract (F-META8, L-597)
if "${PYTHON_CMD[@]}" tools/contract_check.py "${ARGS[@]}" 2>/dev/null | grep -q "FAIL"; then
    echo "FAIL: Self-model contract check failed. Fix before committing."
    "${PYTHON_CMD[@]}" tools/contract_check.py
    exit 1
fi
echo "  Self-model contract: PASS"

# 2. Maintenance (informational) — skipped in --minimal mode (L-1207)
if [ "$MINIMAL" -eq 0 ]; then
    if ! "${PYTHON_CMD[@]}" tools/maintenance.py "${ARGS[@]}"; then
        echo "FAIL: maintenance check failed."
        exit 1
    fi
    echo ""
else
    echo "=== MAINTENANCE ==="
    echo "  Skipped (--minimal mode, L-1207)"
    echo ""
fi

# 2b. Mission constraints regression suite (all modes)
if [ -f "tools/test_mission_constraints.py" ]; then
    run_suite "Mission constraints regression" "tools/test_mission_constraints.py"
fi

# --- Full-mode-only suites (not --quick) ---
if [ "$GUARD_MODE" = "full" ]; then
    # 3-8. Core regression suites
    CORE_TESTS=(
        "tools/test_bulletin.py"
        "tools/test_wiki_swarm.py"
        "tools/test_swarm_parse.py"
        "tools/test_colony.py"
        "tools/test_swarm_pr.py"
        "tools/test_swarm_lanes.py"
        "tools/test_nk_analyze.py"
    )
    for test_path in "${CORE_TESTS[@]}"; do
        test_name="$(basename "$test_path" .py | sed 's/^test_//')"
        run_suite "${test_name} regression" "$test_path"
    done

    # Auto-discover additional test suites
    EXTRA_COUNT=0
    while IFS= read -r test_path; do
        SKIP=0
        for core in "${CORE_TESTS[@]}"; do
            if [ "$test_path" = "$core" ]; then
                SKIP=1
                break
            fi
        done
        if [ "$SKIP" -eq 1 ]; then
            continue
        fi
        test_name="$(basename "$test_path" .py)"
        run_suite "Additional regression (${test_name})" "$test_path"
        EXTRA_COUNT=$((EXTRA_COUNT + 1))
    done < <(find tools -maxdepth 1 -type f -name 'test_*.py' | sort)
    if [ "$EXTRA_COUNT" -gt 0 ]; then
        echo "  Additional tool regressions: PASS (${EXTRA_COUNT} suites)"
    fi

    # L-1132: Correction propagation gap surfacing
    if [ -f "tools/correction_propagation.py" ]; then
        CP_OUT=$("${PYTHON_CMD[@]}" tools/correction_propagation.py --json 2>/dev/null) || true
        if [ -n "$CP_OUT" ]; then
            HIGH_COUNT=$(echo "$CP_OUT" | "${PYTHON_CMD[@]}" -c "
import json, sys
try:
    d = json.load(sys.stdin)
    q = d.get('correction_queue', [])
    high = [x for x in q if x.get('priority') == 'HIGH']
    print(len(high))
except: print(0)
" 2>/dev/null || echo 0)
            TOTAL_GAPS=$(echo "$CP_OUT" | "${PYTHON_CMD[@]}" -c "
import json, sys
try: d = json.load(sys.stdin); print(d.get('total_uncorrected_citations', 0))
except: print(0)
" 2>/dev/null || echo 0)
            CORRECTION_RATE=$(echo "$CP_OUT" | "${PYTHON_CMD[@]}" -c "
import json, sys
try: d = json.load(sys.stdin); print(f\"{d.get('avg_correction_rate', 0):.0%}\")
except: print('?')
" 2>/dev/null || echo "?")
            if [ "${HIGH_COUNT}" -gt 0 ]; then
                echo "  L-1132 correction gaps: ${TOTAL_GAPS} uncorrected citations (${HIGH_COUNT} HIGH), correction rate ${CORRECTION_RATE}"
                echo "    Run: python3 tools/correction_propagation.py — to see full queue"
            else
                echo "  L-1132 correction gaps: PASS (${TOTAL_GAPS} uncorrected, 0 HIGH, rate ${CORRECTION_RATE})"
            fi
        else
            echo "  L-1132 correction gaps: SKIP (tool error)"
        fi
    fi

    # Orient smoke test
    if [ -f "tools/orient.py" ]; then
        ORIENT_OUT=$("${PYTHON_CMD[@]}" tools/orient.py --brief 2>&1)
        if echo "$ORIENT_OUT" | grep -q "=== ORIENT"; then
            echo "  Orient smoke test: PASS"
        else
            echo "FAIL: orient.py produced unexpected output."
            echo "$ORIENT_OUT"
            exit 1
        fi
    fi

    # Proxy K
    "${PYTHON_CMD[@]}" tools/proxy_k.py 2>/dev/null
fi

echo "=== CHECK COMPLETE ==="
