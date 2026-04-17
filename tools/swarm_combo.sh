#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
SEEN_FILE="$ROOT/.loop_seen"
LOG_FILE="$ROOT/.swarm.log"
LOCK_FILE="$ROOT/.swarm.lock"

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "already running"; exit 1; }

touch "$SEEN_FILE" "$LOG_FILE"

log() {
  printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG_FILE"
}

DEFAULT_BRANCH="$(git remote show origin | sed -n '/HEAD branch/s/.*: //p')"
[ -z "$DEFAULT_BRANCH" ] && DEFAULT_BRANCH=master

pick_next() {
  python3 "$ROOT/tools/orient.py" 2>/dev/null \
    | grep -o 'L-[0-9]\+' \
    | grep -vxFf "$SEEN_FILE" \
    | head -n 1 || true
}

while true; do
  log "SYNC"
  git fetch origin "$DEFAULT_BRANCH"
  git reset --hard FETCH_HEAD

  log "STATE"
  python3 "$ROOT/tools/sync_state.py" || true
  python3 "$ROOT/tools/validate_beliefs.py" || true
  bash "$ROOT/tools/check.sh" --quick || true

  ID="$(pick_next)"

  if [ -z "$ID" ]; then
    log "no work -> sleep"
    sleep 3
    continue
  fi

  echo "$ID" >> "$SEEN_FILE"
  log "WORK $ID"

  bash "$ROOT/tools/resolve_one.sh" "$ID" || true

  log "COMMIT"
  git add .
  git commit -m "auto:$ID" || true
  git push origin HEAD:"$DEFAULT_BRANCH" || true

  sleep 2
done
