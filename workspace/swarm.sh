#!/usr/bin/env bash
# swarm — CLI for managing the swarm knowledge base
# Usage: ./workspace/swarm.sh <command>

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

choose_python() {
    if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
        PYTHON_CMD=(python3)
        return 0
    fi
    if command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
        PYTHON_CMD=(python)
        return 0
    fi
    # Git Bash / Windows launcher fallback when python aliases are missing.
    if command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
        PYTHON_CMD=(py -3)
        return 0
    fi
    return 1
}

declare -a PYTHON_CMD=()
choose_python || true

count_matches() {
    local pattern="$1"
    local file="$2"
    grep -c "$pattern" "$file" 2>/dev/null || true
}

lesson_count_total() {
    find "$REPO_ROOT/memory/lessons" -name "L-*.md" 2>/dev/null | wc -l | tr -d '[:space:]'
}

lesson_count_tracked() {
    if command -v git >/dev/null 2>&1 && git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        git -C "$REPO_ROOT" ls-files -- "memory/lessons/L-*.md" 2>/dev/null | wc -l | tr -d '[:space:]'
        return
    fi
    lesson_count_total
}

session_count_index() {
    local sessions
    sessions=$(awk '
        /Sessions:[[:space:]]*[0-9]+/ { sub(/.*Sessions:[[:space:]]*/, "", $0); print $0; found=1; exit }
        /Sessions completed:[[:space:]]*[0-9]+/ { sub(/.*Sessions completed:[[:space:]]*/, "", $0); print $0; found=1; exit }
        END { if (!found) print "0" }
    ' "$REPO_ROOT/memory/INDEX.md")
    sessions=$(printf '%s' "$sessions" | tr -d '[:space:]')
    if [[ "$sessions" =~ ^[0-9]+$ ]]; then
        echo "$sessions"
    else
        echo "0"
    fi
}

session_count_log() {
    local sessions
    sessions=$(grep -oE '^S[0-9]+' "$REPO_ROOT/memory/SESSION-LOG.md" 2>/dev/null | sed 's/^S//' | sort -n | tail -1)
    sessions=$(printf '%s' "${sessions:-0}" | tr -d '[:space:]')
    if [[ "$sessions" =~ ^[0-9]+$ ]]; then
        echo "$sessions"
    else
        echo "0"
    fi
}

session_count() {
    local index_sessions log_sessions
    index_sessions=$(session_count_index)
    log_sessions=$(session_count_log)
    if [ "$log_sessions" -gt "$index_sessions" ]; then
        echo "$log_sessions"
    else
        echo "$index_sessions"
    fi
}

cmd_status() {
    echo "=== Swarm Status ==="
    echo ""

    # Session count
    local sessions
    sessions=$(session_count)
    if [ "$sessions" -gt 0 ]; then
        echo "Sessions completed: $sessions"
    else
        echo "Sessions completed: ?"
    fi

    # Lesson count
    local lessons_total lessons_tracked lesson_drafts
    lessons_total=$(lesson_count_total)
    lessons_tracked=$(lesson_count_tracked)
    lesson_drafts=$((lessons_total - lessons_tracked))
    if [ "$lesson_drafts" -gt 0 ]; then
        echo "Lessons: $lessons_tracked tracked (+$lesson_drafts draft)"
    else
        echo "Lessons: $lessons_tracked"
    fi

    # Task count
    local done total
    done=$(grep -rl 'Status: DONE' "$REPO_ROOT/tasks/" 2>/dev/null | wc -l)
    total=$(find "$REPO_ROOT/tasks" -name "TASK-*.md" 2>/dev/null | wc -l)
    echo "Tasks: $done/$total done"

    # Belief count
    local beliefs
    beliefs=$(grep -c '^### B' "$REPO_ROOT/beliefs/DEPS.md" 2>/dev/null || echo "0")
    echo "Beliefs tracked: $beliefs"

    # Frontier
    local open resolved
    open=$(count_matches '^\- \*\*F' "$REPO_ROOT/tasks/FRONTIER.md")
    resolved=$(count_matches '^| F' "$REPO_ROOT/tasks/FRONTIER.md")
    echo "Frontier: $open open, $resolved resolved"
}

cmd_health() {
    echo "=== Health Check ==="
    echo ""

    # 1. Knowledge growth
    local lessons_total lessons_tracked lesson_drafts
    lessons_total=$(lesson_count_total)
    lessons_tracked=$(lesson_count_tracked)
    lesson_drafts=$((lessons_total - lessons_tracked))
    if [ "$lesson_drafts" -gt 0 ]; then
        echo "1. Knowledge: $lessons_tracked tracked lessons (+$lesson_drafts draft)"
    else
        echo "1. Knowledge: $lessons_tracked lessons"
    fi

    # 2. Confidence ratio
    local verified assumed
    verified=$(grep -r 'Confidence: Verified' "$REPO_ROOT/memory/lessons/" 2>/dev/null | wc -l)
    assumed=$(grep -r 'Confidence: Assumed' "$REPO_ROOT/memory/lessons/" 2>/dev/null | wc -l)
    local total_conf=$((verified + assumed))
    if [ "$total_conf" -gt 0 ]; then
        local pct=$((verified * 100 / total_conf))
        echo "2. Accuracy: ${pct}% verified ($verified/$total_conf)"
    else
        echo "2. Accuracy: no data"
    fi

    # 3. Compactness
    local long_lessons
    long_lessons=$(find "$REPO_ROOT/memory/lessons" -name "L-*.md" -exec sh -c 'wc -l < "$1"' _ {} \; 2>/dev/null | awk '$1 > 20' | wc -l)
    local index_lines
    index_lines=$(wc -l < "$REPO_ROOT/memory/INDEX.md" 2>/dev/null)
    echo "3. Compactness: $long_lessons lessons over 20 lines, INDEX is $index_lines lines"

    # 4. Belief evolution
    local belief_commits
    belief_commits=$(git -C "$REPO_ROOT" log --oneline beliefs/DEPS.md 2>/dev/null | wc -l)
    echo "4. Belief evolution: $belief_commits commits to DEPS.md"

    # 5. Task throughput
    local done total
    done=$(grep -rl 'Status: DONE' "$REPO_ROOT/tasks/" 2>/dev/null | wc -l)
    total=$(find "$REPO_ROOT/tasks" -name "TASK-*.md" 2>/dev/null | wc -l)
    if [ "$total" -gt 0 ]; then
        local pct=$((done * 100 / total))
        echo "5. Throughput: ${pct}% tasks done ($done/$total)"
    else
        echo "5. Throughput: no tasks"
    fi
}

cmd_frontier() {
    echo "=== Open Frontier Questions ==="
    echo ""
    grep '^\- \*\*F' "$REPO_ROOT/tasks/FRONTIER.md" 2>/dev/null | while read -r line; do
        echo "  $line"
    done
}

cmd_lessons() {
    echo "=== Lessons ==="
    echo ""
    grep '^\- \*\*L-' "$REPO_ROOT/memory/INDEX.md" 2>/dev/null | while read -r line; do
        echo "  $line"
    done
}

cmd_next() {
    echo "=== Suggested Next Session ==="
    echo ""

    # Check for in-progress tasks
    local in_progress
    in_progress=$(grep -rl 'Status: IN PROGRESS' "$REPO_ROOT/tasks/" 2>/dev/null | head -1 || true)
    if [ -n "$in_progress" ]; then
        echo "CONTINUE: $(basename "$in_progress") is still in progress"
        head -1 "$in_progress" | sed 's/^# /  /'
        return
    fi

    # Show critical frontier questions first
    echo "Critical open questions:"
    grep '^\- \*\*F' "$REPO_ROOT/tasks/FRONTIER.md" 2>/dev/null | head -3 | while read -r line; do
        echo "  $line"
    done
    echo ""

    # Health check suggestion
    local sessions
    sessions=$(session_count)
    if [ "$sessions" -gt 0 ] && [ $((sessions % 5)) -eq 0 ]; then
        echo "NOTE: Session $sessions — time for a health check (run: swarm.sh health)"
    fi
}

cmd_log() {
    echo "=== Recent Activity ==="
    echo ""
    git -C "$REPO_ROOT" log --oneline -10 2>/dev/null
}

cmd_check() {
    bash "$REPO_ROOT/tools/check.sh" "$@"
}

cmd_wiki() {
    if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
        echo "Usage: ./workspace/swarm.sh wiki [<topic>] [--depth N] [--fanout N] [--lang CODE]"
        echo "Examples:"
        echo "  ./workspace/swarm.sh wiki"
        echo "  ./workspace/swarm.sh wiki swarm --depth 1 --fanout 5"
        return 0
    fi

    local topic_parts=()
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --*) break ;;
            *) topic_parts+=("$1"); shift ;;
        esac
    done

    local topic slug stamp out_path
    if [ "${#topic_parts[@]}" -eq 0 ]; then
        topic="auto"
        slug="auto"
    else
        topic="${topic_parts[*]}"
        slug=$(printf '%s' "$topic" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//')
        [ -n "$slug" ] || slug="topic"
    fi
    stamp=$(date -u +%Y%m%d-%H%M%S)
    out_path="$REPO_ROOT/workspace/notes/wiki-swarm-${slug}-${stamp}.md"

    if [ "${#PYTHON_CMD[@]}" -eq 0 ]; then
        echo "FAIL: No runnable python interpreter found (python3/python/py -3)."
        return 1
    fi

    if [ "$topic" = "auto" ]; then
        "${PYTHON_CMD[@]}" "$REPO_ROOT/tools/wiki_swarm.py" --auto "$@" --out "$out_path"
    else
        "${PYTHON_CMD[@]}" "$REPO_ROOT/tools/wiki_swarm.py" "$topic" "$@" --out "$out_path"
    fi
    echo ""
    echo "Saved: $out_path"
}

cmd_colony() {
    if [ "${#PYTHON_CMD[@]}" -eq 0 ]; then
        echo "FAIL: No runnable python interpreter found (python3/python/py -3)."
        return 1
    fi

    local action="${1:-swarm-all}"
    shift || true
    "${PYTHON_CMD[@]}" "$REPO_ROOT/tools/colony.py" "$action" "$@"
}

cmd_help() {
    echo "swarm — CLI for the swarm knowledge base"
    echo ""
    echo "Commands:"
    echo "  status    Show system overview"
    echo "  health    Run health check"
    echo "  frontier  List open frontier questions"
    echo "  lessons   List all lessons"
    echo "  next      Suggest what to work on next"
    echo "  log       Show recent git activity"
    echo "  check     Run universal swarm validation (passes args to tools/check.sh)"
    echo "  wiki      Swarm a Wikipedia topic into workspace/notes/"
    echo "  colony    Manage colony experiments (default: swarm-all)"
    echo "  colonies  Alias for: colony swarm-all"
    echo "  help      Show this help"
}

case "${1:-help}" in
    status)   cmd_status ;;
    health)   cmd_health ;;
    frontier) cmd_frontier ;;
    lessons)  cmd_lessons ;;
    next)     cmd_next ;;
    log)      cmd_log ;;
    check)    shift; cmd_check "$@" ;;
    wiki)     shift; cmd_wiki "$@" ;;
    colony)   shift; cmd_colony "$@" ;;
    colonies) shift; cmd_colony swarm-all "$@" ;;
    help)     cmd_help ;;
    *)        echo "Unknown command: $1"; cmd_help; exit 1 ;;
esac
