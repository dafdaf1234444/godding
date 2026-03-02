#!/bin/bash
# Universal swarm validation — call from any tool at session start/end.
# Replaces tool-specific hooks for non-Claude tools.
# Usage: bash tools/check.sh [--quick]
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

ARGS=()
if [ "${1:-}" = "--quick" ]; then
    ARGS+=(--quick)
fi

echo "=== SWARM CHECK ==="

# 0. Mass-deletion guard (FM-01, I9/MC-SAFE, L-346, L-350): abort if staged FILE deletions exceed threshold.
# Protects against WSL filesystem corruption staging mass file deletions via git add -A accidents.
# Counts DELETED FILES (D status), not line-level deletions — avoids false positives on large edits.
FILE_DELETION_THRESHOLD=20
FM09_NOTICE_THRESHOLD=5
STAGED_FILE_DELETIONS=$(git diff --cached --diff-filter=D --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "${STAGED_FILE_DELETIONS:-0}" -gt "$FILE_DELETION_THRESHOLD" ]; then
    echo "FAIL: Mass-deletion guard triggered — ${STAGED_FILE_DELETIONS} staged file deletions (threshold: ${FILE_DELETION_THRESHOLD})."
    echo "  This likely means WSL filesystem corruption caused 'git add' to stage file deletions."
    echo "  Run: git diff --cached --diff-filter=D --name-only | head -20 — to inspect."
    echo "  If intentional (compaction archive), set env ALLOW_MASS_DELETION=1 to bypass."
    if [ "${ALLOW_MASS_DELETION:-0}" != "1" ]; then
        exit 1
    fi
    echo "  ALLOW_MASS_DELETION=1 set — bypassing mass-deletion guard."
elif [ "${STAGED_FILE_DELETIONS:-0}" -gt "$FM09_NOTICE_THRESHOLD" ]; then
    # FM-09 cross-session notice (I9/MC-SAFE): staged deletions above notice threshold but below hard-fail.
    # May indicate concurrent session left foreign deletions in the index.
    echo "  FM-09 NOTICE: ${STAGED_FILE_DELETIONS} staged file deletions (>${FM09_NOTICE_THRESHOLD}) — verify these are yours"
    echo "    If foreign (from concurrent session): git restore --staged . — then re-stage your files"
    git diff --cached --diff-filter=D --name-only 2>/dev/null | head -5
fi
echo "  Mass-deletion guard: PASS (${STAGED_FILE_DELETIONS:-0} staged file deletions)"

# FM-01 layer 2: Mass-staging guard (L-903, S410). Catches 'git add -A' / 'git add .' even
# when no deletions are involved. Threshold: >100 staged files is almost certainly accidental.
MASS_STAGE_THRESHOLD=100
STAGED_FILE_COUNT=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "${STAGED_FILE_COUNT:-0}" -gt "$MASS_STAGE_THRESHOLD" ]; then
    echo "FAIL: Mass-staging guard triggered — ${STAGED_FILE_COUNT} staged files (threshold: ${MASS_STAGE_THRESHOLD})."
    echo "  This likely means 'git add -A' or 'git add .' was used. Stage files individually instead."
    echo "  If intentional, set env ALLOW_MASS_STAGING=1 to bypass."
    if [ "${ALLOW_MASS_STAGING:-0}" != "1" ]; then
        exit 1
    fi
    echo "  ALLOW_MASS_STAGING=1 set — bypassing mass-staging guard."
fi
echo "  Mass-staging guard: PASS (${STAGED_FILE_COUNT:-0} staged files)"

# FM-03: Ghost-lesson resurrection guard (I9/MC-SAFE, L-346).
# After 'git mv memory/lessons/L-NNN.md memory/lessons/archive/L-NNN.md', WSL may leave
# ghost copies in the source directory. If staged as new-file, they undo the archiving.
ARCHIVE_DIR="memory/lessons/archive"
if [ -d "$ARCHIVE_DIR" ]; then
    GHOST_FILES=""
    while IFS= read -r filepath; do
        lesson_name="$(basename "$filepath")"
        if [ -f "$ARCHIVE_DIR/$lesson_name" ]; then
            GHOST_FILES="$GHOST_FILES $filepath"
        fi
    done < <(git status --porcelain 2>/dev/null | { grep '^A ' || true; } | { grep 'memory/lessons/L-' || true; } | { grep -v '/archive/' || true; } | awk '{print $2}')
    if [ -n "$GHOST_FILES" ]; then
        echo "FAIL: Ghost-lesson resurrection detected —${GHOST_FILES}"
        echo "  These staged new-files already exist in archive/; staging would undo compaction."
        echo "  Fix: git restore --staged${GHOST_FILES}"
        if [ "${ALLOW_GHOST_LESSONS:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_GHOST_LESSONS=1 set — bypassing ghost-lesson guard."
    fi
    echo "  Ghost-lesson guard: PASS"
fi

# FM-18: Lesson number collision guard (L-903, S412).
# Detects concurrent sessions creating the same L-NNN.md — last-writer-wins silently drops work.
# Title-filename mismatch (title says L-NNN but file is L-MMM) is the primary collision signal.
if [ -f "tools/lesson_collision_check.py" ]; then
    COLLISION_EXIT=0
    COLLISION_OUT=$("${PYTHON_CMD[@]}" tools/lesson_collision_check.py --staged 2>&1) || COLLISION_EXIT=$?
    if [ "${COLLISION_EXIT}" -eq 1 ]; then
        echo "FAIL: Lesson number collision detected (FM-18, L-903)."
        echo "$COLLISION_OUT"
        echo "  Fix: rename conflicting lesson to next available L-NNN number."
        if [ "${ALLOW_LESSON_COLLISION:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_LESSON_COLLISION=1 set — bypassing collision guard."
    else
        echo "  FM-18 collision guard: PASS"
    fi
fi

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

# FM-11: Genesis bundle hash verification (I9/MC-SAFE, F-SEC1 Layer 1, S377).
# If a genesis hash file exists, verify current bundle matches. Mismatch = FAIL (was warning pre-S377).
LATEST_HASH_FILE=$(ls -t workspace/genesis-bundle-*.hash 2>/dev/null | head -1)
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
                # Auto-write updated hash so next run passes (L-S392 fix: race between working tree and hook)
                echo "$CURRENT_HASH" > "$LATEST_HASH_FILE"
                echo "  Genesis hash auto-updated in $(basename "$LATEST_HASH_FILE") (ALLOW_GENESIS_DRIFT=1)"
            else
                exit 1
            fi
        fi
    fi
fi

# FM-13: Colony belief drift check (I9/MC-SAFE, F-SEC1 Layer 3, S379).
# If any colony's belief drift exceeds 30%, require council review before commit.
if [ -f "tools/merge_back.py" ]; then
    DRIFT_OUT=$("${PYTHON_CMD[@]}" tools/merge_back.py --check 2>&1)
    DRIFT_EXIT=$?
    if [ "$DRIFT_EXIT" -ne 0 ]; then
        echo "FAIL: Colony belief drift exceeds 30% — council review required (F-SEC1 Layer 3)."
        echo "$DRIFT_OUT"
        if [ "${ALLOW_COLONY_DRIFT:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_COLONY_DRIFT=1 set — bypassing drift guard."
    else
        echo "  Colony drift check: PASS"
    fi
fi

# Near-duplicate lesson guard (G-CC2-4, F-QC1, L-356): bonding curve analog.
# Staged new lesson files are scanned against recent lesson titles for word-overlap >50%.
# Emits DUE warning (not hard FAIL) to enforce increasing cost for duplicate knowledge.
STAGED_NEW_LESSONS=$(git diff --cached --diff-filter=A --name-only 2>/dev/null | { grep 'memory/lessons/L-[0-9]' || true; } | { grep -v '/archive/' || true; })
if [ -n "$STAGED_NEW_LESSONS" ]; then
    "${PYTHON_CMD[@]}" - "$STAGED_NEW_LESSONS" << 'PYEOF'
import sys, os, re

new_lessons = sys.argv[1].split() if len(sys.argv) > 1 else []
lesson_dir = "memory/lessons"

# L-NNN citation check (L-457, F9-NK): new lessons should cite at least one other lesson
# to sustain K_avg > 1.5 threshold (F75). Emits NOTICE (not hard FAIL).
no_citation_lessons = []
for new_path in new_lessons:
    try:
        with open(new_path) as f:
            content = f.read()
        lid = os.path.basename(new_path).replace('.md', '')
        # find all L-NNN citations excluding self
        cites = [c for c in re.findall(r'L-(\d{3})', content) if 'L-' + c != lid]
        if not cites:
            no_citation_lessons.append(os.path.basename(new_path))
    except Exception:
        pass
if no_citation_lessons:
    for f in no_citation_lessons:
        print(f"  NOTICE: {f} has no L-NNN citations — add Related: L-NNN to sustain K_avg>1.5 (L-457)")
else:
    print("  L-NNN citation guard: PASS")

def get_title(path):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#"):
                    return re.sub(r"^#+\s*", "", line).lower()
    except Exception:
        pass
    return ""

def word_overlap(a, b):
    wa = set(re.findall(r'\w+', a)) - {"the","a","an","is","are","was","were","to","of","in","for","and","or","L","S"}
    wb = set(re.findall(r'\w+', b)) - {"the","a","an","is","are","was","were","to","of","in","for","and","or","L","S"}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))

# Get last 20 lesson titles (excluding staged files themselves)
existing = sorted([
    f for f in os.listdir(lesson_dir)
    if f.startswith("L-") and f.endswith(".md") and not f.startswith("L-0")
], reverse=True)[:40]

warned = False
for new_path in new_lessons:
    new_title = get_title(new_path)
    if not new_title:
        continue
    for existing_file in existing:
        existing_path = os.path.join(lesson_dir, existing_file)
        if os.path.abspath(existing_path) == os.path.abspath(new_path):
            continue
        existing_title = get_title(existing_path)
        ov = word_overlap(new_title, existing_title)
        if ov >= 0.5:
            print(f"  NEAR-DUP WARNING: {os.path.basename(new_path)} overlaps {existing_file} ({ov:.0%})")
            print(f"    New:      {new_title}")
            print(f"    Existing: {existing_title}")
            print("    Consider updating the existing lesson instead (F-QC1, G-CC2-4).")
            warned = True
            break

if warned:
    print("  Near-dup guard: WARN (see above) — DUE: update existing lessons before adding new ones")
else:
    print("  Near-dup guard: PASS")
PYEOF
fi

# FM-31: Lesson line-count guard (L-601, L-1053). Max 20 lines per lesson.
# Enforces at creation time — prevents post-hoc trim cycles (L-1053 structural fix).
if [ -n "$STAGED_NEW_LESSONS" ]; then
    LONG_LESSONS=""
    while IFS= read -r lesson_path; do
        if [ -f "$lesson_path" ]; then
            LINE_COUNT=$(wc -l < "$lesson_path" | tr -d ' ')
            if [ "$LINE_COUNT" -gt 20 ]; then
                LONG_LESSONS="${LONG_LESSONS} ${lesson_path}(${LINE_COUNT}L)"
            fi
        fi
    done <<< "$STAGED_NEW_LESSONS"
    if [ -n "$LONG_LESSONS" ]; then
        echo "  FM-31 FAIL: Lesson(s) exceed 20-line limit:${LONG_LESSONS}"
        echo "    Trim before committing. Bypass: ALLOW_LONG_LESSON=1 git commit ..."
        if [ "${ALLOW_LONG_LESSON:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_LONG_LESSON=1 set — bypassing lesson line-count guard."
    else
        echo "  FM-31 lesson line-count guard: PASS"
    fi
fi

# FM-19: Stale-write detector (L-525, L-601, F-CAT1).
# Detects when staged high-contention files were recently modified by another session.
# Content-loss detection for APPEND/MIXED files; warning for REPLACE files.
if [ -f "tools/stale_write_check.py" ]; then
    STALE_EXIT=0
    STALE_OUT=$("${PYTHON_CMD[@]}" tools/stale_write_check.py --staged 2>&1) || STALE_EXIT=$?
    if [ -n "$STALE_OUT" ]; then
        echo "$STALE_OUT"
    fi
    if [ "$STALE_EXIT" -eq 1 ]; then
        echo "  FM-19 stale-write: CONTENT LOSS RISK — re-read files and merge concurrent changes"
        echo "  Bypass: ALLOW_STALE_WRITE=1 git commit ..."
        if [ "${ALLOW_STALE_WRITE:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_STALE_WRITE=1 set — bypassing stale-write guard."
    elif [ "$STALE_EXIT" -eq 0 ]; then
        echo "  FM-19 stale-write guard: PASS"
    fi
fi

# Tool-size gate (L-469, L-476): warn when staged tool files exceed T4 ceiling.
# Prevents maintenance.py-style unbounded growth (28k tokens = 47% of all drift).
T4_TOKEN_CEILING=5000
STAGED_TOOLS=$(git diff --cached --name-only 2>/dev/null | { grep '^tools/.*\.py$' || true; })
if [ -n "$STAGED_TOOLS" ]; then
    OVERSIZED=0
    while IFS= read -r tool_path; do
        if [ -f "$tool_path" ]; then
            # Estimate tokens as chars/4 (standard approximation)
            CHARS=$(wc -c < "$tool_path" | tr -d ' ')
            EST_TOKENS=$((CHARS / 4))
            if [ "$EST_TOKENS" -gt "$T4_TOKEN_CEILING" ]; then
                echo "  NOTICE: ${tool_path} ~${EST_TOKENS}t exceeds T4 ceiling (${T4_TOKEN_CEILING}t) — consider splitting (L-469)"
                OVERSIZED=$((OVERSIZED + 1))
            fi
        fi
    done <<< "$STAGED_TOOLS"
    if [ "$OVERSIZED" -eq 0 ]; then
        echo "  Tool-size gate: PASS"
    else
        echo "  Tool-size gate: ${OVERSIZED} tool(s) over ceiling (NOTICE — not blocking)"
    fi
fi

# FM-24: Prescriptive-without-enforcement detector (L-601, F-CAT1).
# Voluntary protocols decay to structural floor (L-601). Detects new/modified lessons
# containing prescriptive rules (## Rule, should/must/always/never) but no tool/file reference.
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

# FM-30: Cross-layer cascade detector (L-1015, F-CAT1, S441).
# cascade_monitor.py detects simultaneous failure of adjacent swarm layers (K,T,Q,E,A).
# Non-blocking NOTICE — cascades require monitoring, not commit abort.
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

# EAD enforcement (Council S3, L-484): new session notes should have expect+actual fields.
# Stigmergy amplification requires prediction metadata on every trace.
if git diff --cached --name-only 2>/dev/null | grep -q 'tasks/NEXT.md'; then
    NEXT_DIFF=$(git diff --cached tasks/NEXT.md 2>/dev/null)
    # Check if adding a session note (## S<N> session note)
    if echo "$NEXT_DIFF" | grep -q '^+## S[0-9]'; then
        if ! echo "$NEXT_DIFF" | grep -q '^\+.*\*\*expect\*\*'; then
            echo "  EAD NOTICE: New session note in NEXT.md is missing **expect** field (P-182, L-484)"
            echo "    Add: - **expect**: <your prediction before acting>"
        fi
        if ! echo "$NEXT_DIFF" | grep -q '^\+.*\*\*actual\*\*'; then
            echo "  EAD NOTICE: New session note in NEXT.md is missing **actual** field (P-182, L-484)"
            echo "    Add: - **actual**: <what actually happened>"
        fi
    fi
fi

# FM-14: Git object health check (loose object corruption, L-720, L-658).
# Complements orient.py check_git_object_health() at session start.
# Only runs in full mode (not --quick) to avoid slowing pre-commit.
if [ "${#ARGS[@]}" -eq 0 ]; then
    GIT_FSCK_OUT=$(timeout 30 git fsck --no-dangling --connectivity-only 2>&1 || true)
    if echo "$GIT_FSCK_OUT" | grep -qiE "^(broken|missing|error)"; then
        echo "FAIL: Git object corruption detected (FM-14, L-720)."
        echo "$GIT_FSCK_OUT" | head -5
        echo "  Fix: git reflog expire --expire=now --all && git gc --prune=now"
        echo "  Or: fresh clone if gc fails."
        if [ "${ALLOW_GIT_CORRUPTION:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_GIT_CORRUPTION=1 set — bypassing git health guard."
    else
        echo "  Git object health: PASS"
    fi
fi

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

# 2. Maintenance (informational)
if ! "${PYTHON_CMD[@]}" tools/maintenance.py "${ARGS[@]}"; then
    echo "FAIL: maintenance check failed."
    exit 1
fi
echo ""

# 3. Bulletin regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_bulletin.py" ]; then
    run_suite "Bulletin regression" "tools/test_bulletin.py"
fi

# 4. Wiki swarm regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_wiki_swarm.py" ]; then
    run_suite "Wiki swarm regression" "tools/test_wiki_swarm.py"
fi

# 5. Swarm parse regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_swarm_parse.py" ]; then
    run_suite "Swarm parse regression" "tools/test_swarm_parse.py"
fi

# 6. Colony regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_colony.py" ]; then
    run_suite "Colony regression" "tools/test_colony.py"
fi

# 7. PR intake regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_swarm_pr.py" ]; then
    run_suite "Swarm PR regression" "tools/test_swarm_pr.py"
fi

# 8. Swarm lanes regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_swarm_lanes.py" ]; then
    run_suite "Swarm lanes regression" "tools/test_swarm_lanes.py"
fi

# 9. Mission constraints regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_mission_constraints.py" ]; then
    run_suite "Mission constraints regression" "tools/test_mission_constraints.py"
fi

# 10. Repair regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_repair.py" ]; then
    run_suite "Repair regression" "tools/test_repair.py"
fi

# 11. NK analyze regression suite (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/test_nk_analyze.py" ]; then
    run_suite "NK analyze regression" "tools/test_nk_analyze.py"
fi

# 12. Additional tool regressions auto-discovery (if not quick)
if [ "${#ARGS[@]}" -eq 0 ]; then
    CORE_TESTS=(
        "tools/test_bulletin.py"
        "tools/test_wiki_swarm.py"
        "tools/test_swarm_parse.py"
        "tools/test_colony.py"
        "tools/test_swarm_pr.py"
        "tools/test_swarm_lanes.py"
        "tools/test_mission_constraints.py"
        "tools/test_repair.py"
        "tools/test_nk_analyze.py"
    )
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
fi

# 13. Orient.py smoke test (if not quick)
if [ "${#ARGS[@]}" -eq 0 ] && [ -f "tools/orient.py" ]; then
    ORIENT_OUT=$("${PYTHON_CMD[@]}" tools/orient.py --brief 2>&1)
    if echo "$ORIENT_OUT" | grep -q "=== ORIENT"; then
        echo "  Orient smoke test: PASS"
    else
        echo "FAIL: orient.py produced unexpected output."
        echo "$ORIENT_OUT"
        exit 1
    fi
fi

# 14. Proxy K (if not quick)
if [ "${#ARGS[@]}" -eq 0 ]; then
    "${PYTHON_CMD[@]}" tools/proxy_k.py 2>/dev/null
fi

echo "=== CHECK COMPLETE ==="
