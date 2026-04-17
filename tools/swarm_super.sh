#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
LOCK_FILE="$ROOT/.swarm_super.lock"
SEEN_FILE="$ROOT/.swarm_super.seen"
LOG_FILE="$ROOT/.swarm_super.log"
CLAIM_DIR="$ROOT/.swarm_claims"
MAX_PARALLEL="${MAX_PARALLEL:-3}"
SLEEP_SECS="${SLEEP_SECS:-3}"

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "already running"; exit 1; }

mkdir -p "$CLAIM_DIR" tasks
touch "$SEEN_FILE" "$LOG_FILE" tasks/NEXT.md

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG_FILE"; }

DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | sed -n '/HEAD branch/s/.*: //p')"
[ -z "$DEFAULT_BRANCH" ] && DEFAULT_BRANCH="$(git branch --show-current 2>/dev/null || echo master)"

# ---------- TASK SOURCE (TRUE SCHEDULER) ----------
pick_tasks() {
  # priority: NEXT.md → LANES → orient → fallback generate
  (
    grep -o 'L-[0-9]\+' "$ROOT/tasks/NEXT.md" 2>/dev/null || true

    [ -f "$ROOT/tasks/SWARM-LANES.md" ] && \
    awk '/ACTIVE|READY/ && !/BLOCKED|ABANDONED|MERGED/' "$ROOT/tasks/SWARM-LANES.md" \
    | grep -o 'L-[0-9]\+' || true

    python3 "$ROOT/tools/orient.py" 2>/dev/null | grep -o 'L-[0-9]\+' || true
  ) | awk '!seen[$0]++'
}

pick_batch() {
  pick_tasks | grep -vxFf "$SEEN_FILE" | head -n "$MAX_PARALLEL"
}

# ---------- CLAIM ----------
claim() {
  local id="$1"
  local f="$CLAIM_DIR/$id"
  ( set -o noclobber; echo "$$" > "$f" ) 2>/dev/null
}

release() { rm -f "$CLAIM_DIR/$1" 2>/dev/null || true; }

# ---------- AUTO DECISION ----------
decide() {
  local id="$1"
  local txt
  txt="$(grep -i "$id" "$ROOT/tasks/"* 2>/dev/null || true | tr '[:upper:]' '[:lower:]')"

  [[ "$txt" == *"blocked"* ]] && { echo s; return; }
  [[ "$txt" == *"duplicate"* || "$txt" == *"stale"* ]] && { echo d; return; }

  echo k
}

# ---------- WORKER ----------
work() {
  local id="$1"
  local act
  act="$(decide "$id")"
  log "WORK $id ($act)"

  if [ -x "$ROOT/tools/resolve_one.sh" ]; then
    AUTO_ACTION="$act" bash "$ROOT/tools/resolve_one.sh" "$id" || true
  fi

  echo "$id" >> "$SEEN_FILE"
}

# ---------- SYNC ----------
sync_down() {
  git fetch origin "$DEFAULT_BRANCH" || true
  git reset --hard FETCH_HEAD || true
}

sync_up() {
  git add . || true
  git commit -m "auto swarm $(date +%H:%M:%S)" || true
  git push origin HEAD:"$DEFAULT_BRANCH" || true
}

# ---------- LOOP ----------
log "START branch=$DEFAULT_BRANCH parallel=$MAX_PARALLEL"

while true; do
  sync_down

  mapfile -t BATCH < <(pick_batch)

  # fallback: generate task if empty
  if [ "${#BATCH[@]}" -eq 0 ]; then
    NEW="L-$(date +%s)"
    echo "$NEW" >> "$ROOT/tasks/NEXT.md"
    log "GENERATED $NEW"
    sleep "$SLEEP_SECS"
    continue
  fi

  log "BATCH ${BATCH[*]}"

  pids=()
  active=()

  for id in "${BATCH[@]}"; do
    if claim "$id"; then
      active+=("$id")
      ( work "$id" ) &
      pids+=("$!")
    fi
  done

  for p in "${pids[@]}"; do wait "$p" || true; done
  for id in "${active[@]}"; do release "$id"; done

  sync_up
  log "CYCLE DONE"

  sleep "$SLEEP_SECS"
done
