#!/data/data/com.termux/files/usr/bin/bash
set -u

cd "${1:-$HOME/swarm}" || exit 1

mkdir -p runtime
LOG_FILE="runtime/swarm-forever.log"
PID_FILE="runtime/swarm-forever.pid"
LOCK_DIR="runtime/swarm-forever.lock"

mkdir -p .git/info
touch .git/info/exclude
grep -qxF 'runtime/' .git/info/exclude || echo 'runtime/' >> .git/info/exclude
grep -qxF '*.log' .git/info/exclude || echo '*.log' >> .git/info/exclude

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "another swarm loop is already running"
  exit 1
fi

echo $$ > "$PID_FILE"

cleanup() {
  rm -f "$PID_FILE"
  rmdir "$LOCK_DIR" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM EXIT

ts() { date '+%F %T'; }
log() { echo "[$(ts)] $*" | tee -a "$LOG_FILE"; }

run_step() {
  local label="$1"
  shift
  log "run: $label"
  "$@" >> "$LOG_FILE" 2>&1
  local rc=$?
  log "done: $label rc=$rc"
  return $rc
}

choose_focus() {
  if [ -f tasks/NEXT.md ]; then
    awk '
      /^[[:space:]]*[-*][[:space:]]/ {print; exit}
      /^[[:space:]]*[0-9]+\.[[:space:]]/ {print; exit}
    ' tasks/NEXT.md | sed 's/^[[:space:]]*[-*0-9.][[:space:]]*//'
  fi
}

smart_actions() {
  if grep -q "Missing hooks" "$LOG_FILE" && [ -f tools/install_hooks.sh ]; then
    log "[AUTO] installing hooks"
    bash tools/install_hooks.sh >> "$LOG_FILE" 2>&1 || true
  fi

  if [ -f tasks/KILL-SWITCH.md ] && grep -Eq 'SWARM_STOP=1|STOP|HALT' tasks/KILL-SWITCH.md; then
    log "[AUTO] kill switch detected, stopping"
    exit 0
  fi
}

commit_if_needed() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git add -A
    if ! git diff --cached --quiet; then
      git commit -m "swarm: $(date '+%H:%M:%S')" >> "$LOG_FILE" 2>&1 || true
      git push >> "$LOG_FILE" 2>&1 || true
      log "committed"
    else
      log "no staged changes after add"
    fi
  else
    log "no changes"
  fi
}

log "swarm forever start in $(pwd)"

while true; do
  log "tick"

  FOCUS="$(choose_focus)"
  if [ -n "${FOCUS:-}" ]; then
    log "focus: $FOCUS"
  else
    log "focus: none found in tasks/NEXT.md"
  fi

  [ -f tools/orient.py ] && run_step orient python3 tools/orient.py
  [ -f tools/check.sh ] && run_step check bash tools/check.sh --quick
  [ -f tools/sync_state.py ] && run_step sync_state python3 tools/sync_state.py
  [ -f tools/validate_beliefs.py ] && run_step validate_beliefs python3 tools/validate_beliefs.py

  smart_actions
  commit_if_needed

  sleep 15
done
