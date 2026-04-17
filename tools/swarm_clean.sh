#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
LOCK_FILE="$ROOT/.swarm_clean.lock"
SEEN_FILE="$ROOT/.swarm_seen"
LOG_FILE="$ROOT/.swarm_clean.log"

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "already running"; exit 1; }

touch "$SEEN_FILE" "$LOG_FILE"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE"
}

DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | sed -n '/HEAD branch/s/.*: //p')"
[ -z "${DEFAULT_BRANCH:-}" ] && DEFAULT_BRANCH="$(git branch --show-current 2>/dev/null || echo master)"

pick_next() {
  python3 "$ROOT/tools/orient.py" 2>/dev/null \
    | grep -o 'L-[0-9]\+' \
    | grep -vxFf "$SEEN_FILE" \
    | head -n 1 || true
}

reset_seen_if_exhausted() {
  local nxt
  nxt="$(pick_next)"
  if [ -z "${nxt:-}" ]; then
    : > "$SEEN_FILE"
  fi
}

trap 'log "stopping"' EXIT INT TERM

log "starting"
log "root=$ROOT"
log "branch=$DEFAULT_BRANCH"

while true; do
  log "sync down"
  git fetch origin "$DEFAULT_BRANCH" || true
  git reset --hard "origin/$DEFAULT_BRANCH" || true

  reset_seen_if_exhausted
  ID="$(pick_next)"

  if [ -z "${ID:-}" ]; then
    log "no IDs from orient.py; sleeping"
    sleep 5
    continue
  fi

  echo "$ID" >> "$SEEN_FILE"
  log "selected $ID"

  if [ -x "$ROOT/tools/resolve_one.sh" ]; then
    bash "$ROOT/tools/resolve_one.sh" "$ID" || true
  else
    log "missing tools/resolve_one.sh"
  fi

  git add . || true
  git commit -m "auto: processed $ID" || git commit --allow-empty -m "auto: checkpoint $ID" || true
  git push origin HEAD:"$DEFAULT_BRANCH" || true

  log "done $ID"
  sleep 2
done
