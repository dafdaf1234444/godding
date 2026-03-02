#!/bin/sh
# portable_check.sh — Shell-only swarm integrity check for foreign repo deployment.
# Works without Python. Compatible with POSIX sh, bash, zsh.
# Usage: sh tools/portable_check.sh [REPO_ROOT]
# Implements F120: cross-substrate portable integrity checker.
# No Python required — safe for any OS with a POSIX shell.

REPO="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
PASS=0; FAIL=0; WARN=0

chk() {
    name="$1"; status="$2"; level="${3:-FAIL}"
    if [ "$status" = "ok" ]; then
        printf "  PASS  %s\n" "$name"; PASS=$((PASS+1))
    elif [ "$level" = "WARN" ]; then
        printf "  WARN  %s\n" "$name"; WARN=$((WARN+1))
    else
        printf "  FAIL  %s\n" "$name"; FAIL=$((FAIL+1))
    fi
}

echo "=== PORTABLE CHECK | $(basename "$REPO") ==="

# 1. Core entry file
[ -f "$REPO/SWARM.md" ] \
    && chk "SWARM.md present" "ok" \
    || chk "SWARM.md present" "fail"

# 2. Belief and state files
[ -f "$REPO/beliefs/CORE.md" ] \
    && chk "beliefs/CORE.md" "ok" \
    || chk "beliefs/CORE.md" "fail"
[ -f "$REPO/memory/INDEX.md" ] \
    && chk "memory/INDEX.md" "ok" \
    || chk "memory/INDEX.md" "fail"
[ -f "$REPO/tasks/FRONTIER.md" ] \
    && chk "tasks/FRONTIER.md" "ok" \
    || chk "tasks/FRONTIER.md" "fail"

# 3. Lessons exist and are growing
L_COUNT=$(ls "$REPO/memory/lessons/L-"*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "${L_COUNT:-0}" -ge 1 ]; then
    chk "lessons present ($L_COUNT)" "ok"
else
    chk "lessons present (0 found)" "fail"
fi

# 4. Recent git activity (at least one commit)
if command -v git >/dev/null 2>&1; then
    RECENT=$(git -C "$REPO" log --oneline -1 2>/dev/null)
    [ -n "$RECENT" ] \
        && chk "git history: $RECENT" "ok" \
        || chk "git history (no commits)" "fail"
else
    chk "git unavailable (skip)" "ok" "WARN"
fi

# 5. At least one bridge entry file present
BRIDGES=0
for f in CLAUDE.md AGENTS.md .cursorrules GEMINI.md .windsurfrules \
         .github/copilot-instructions.md; do
    [ -f "$REPO/$f" ] && BRIDGES=$((BRIDGES+1))
done
if [ "$BRIDGES" -ge 1 ]; then
    chk "bridge files ($BRIDGES found)" "ok"
else
    chk "bridge files (none — at least one required)" "ok" "WARN"
fi

# 6. Lesson line-limit compliance (latest 10 lessons)
OVERLONG=0
for f in $(ls -t "$REPO/memory/lessons/L-"*.md 2>/dev/null | head -10); do
    LINES=$(wc -l < "$f" | tr -d ' ')
    [ "${LINES:-0}" -gt 20 ] && OVERLONG=$((OVERLONG+1))
done
if [ "$OVERLONG" -eq 0 ]; then
    chk "lesson line-limit ok (latest 10)" "ok"
else
    chk "lesson line-limit: $OVERLONG of latest 10 over 20 lines" "fail"
fi

# 7. NEXT.md exists (handoff surface)
[ -f "$REPO/tasks/NEXT.md" ] \
    && chk "tasks/NEXT.md present" "ok" \
    || chk "tasks/NEXT.md present" "ok" "WARN"

echo ""
printf "Result: PASS=%s  WARN=%s  FAIL=%s\n" "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then
    echo "STATUS: OK"
else
    echo "STATUS: NEEDS REPAIR"
fi
exit "$FAIL"
