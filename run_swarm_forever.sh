#!/data/data/com.termux/files/usr/bin/bash
set -u

cd "${1:-$HOME/swarm}" || {
  echo "Could not enter swarm repo"
  exit 1
}

mkdir -p runtime
LOG_FILE="runtime/swarm-forever.log"
PID_FILE="runtime/swarm-forever.pid"

# Keep runtime noise out of git without touching tracked .gitignore
mkdir -p .git/info
touch .git/info/exclude
grep -qxF 'runtime/' .git/info/exclude || echo 'runtime/' >> .git/info/exclude
grep -qxF '*.log' .git/info/exclude || echo '*.log' >> .git/info/exclude

echo $$ > "$PID_FILE"

cleanup() {
  echo
  echo "[swarm] stopping"
  rm -f "$PID_FILE"
  exit 0
}
trap cleanup INT TERM

run_step() {
  local label="$1"
  shift
  echo "[$(date '+%F %T')] run: $label" | tee -a "$LOG_FILE"
  "$@" >> "$LOG_FILE" 2>&1
  local rc=$?
  echo "[$(date '+%F %T')] done: $label rc=$rc" >> "$LOG_FILE"
  return $rc
}

echo "[$(date '+%F %T')] swarm forever start in $(pwd)" | tee -a "$LOG_FILE"

while true; do
  echo "[$(date '+%F %T')] tick" | tee -a "$LOG_FILE"

  [ -f tools/orient.py ] && run_step orient python3 tools/orient.py
  [ -f tools/check.sh ] && run_step check bash tools/check.sh --quick
  [ -f tools/sync_state.py ] && run_step sync_state python3 tools/sync_state.py
  [ -f tools/validate_beliefs.py ] && run_step validate_beliefs python3 tools/validate_beliefs.py

  # Auto-commit only real tracked changes; runtime/ is excluded
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git add -A
    if ! git diff --cached --quiet; then
      git commit -m "swarm: $(date '+%H:%M:%S')" >> "$LOG_FILE" 2>&1 || true
      git push >> "$LOG_FILE" 2>&1 || true
      echo "[$(date '+%F %T')] committed" | tee -a "$LOG_FILE"
    fi
  else
    echo "[$(date '+%F %T')] no changes" | tee -a "$LOG_FILE"
  fi

  sleep 15
done
