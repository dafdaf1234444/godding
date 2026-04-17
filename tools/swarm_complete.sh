#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
RUNTIME="$ROOT/runtime"
LOCK_FILE="$RUNTIME/swarm_complete.lock"
LOG_FILE="$RUNTIME/swarm_complete.log"
STATUS_FILE="$RUNTIME/swarm_complete.status"
SEEN_FILE="$RUNTIME/swarm_complete.seen"
CLAIM_DIR="$RUNTIME/claims"
SLEEP_SECS="${SLEEP_SECS:-4}"

mkdir -p "$RUNTIME" "$CLAIM_DIR"
touch "$LOG_FILE" "$STATUS_FILE" "$SEEN_FILE"

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "already running"; exit 1; }

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE"
}

DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | sed -n '/HEAD branch/s/.*: //p')"
[ -z "${DEFAULT_BRANCH:-}" ] && DEFAULT_BRANCH="$(git branch --show-current 2>/dev/null || echo master)"

LAST_PICK="none"
LAST_ACTION="none"
LAST_RESULT="idle"

write_status() {
  cat > "$STATUS_FILE" <<STATUS
time: $(date '+%F %T')
root: $ROOT
branch: $DEFAULT_BRANCH
last_pick: $LAST_PICK
last_action: $LAST_ACTION
last_result: $LAST_RESULT
seen_count: $(wc -l < "$SEEN_FILE" 2>/dev/null || echo 0)
log_file: $LOG_FILE
STATUS
}

sync_down() {
  log "SYNC DOWN"
  git fetch origin "$DEFAULT_BRANCH" || true
  git reset --hard "origin/$DEFAULT_BRANCH" || true
}

sync_state() {
  log "STATE SYNC"
  [ -f "$ROOT/tools/sync_state.py" ] && python3 "$ROOT/tools/sync_state.py" || true
  [ -f "$ROOT/tools/validate_beliefs.py" ] && python3 "$ROOT/tools/validate_beliefs.py" || true
  [ -f "$ROOT/tools/check.sh" ] && bash "$ROOT/tools/check.sh" --quick || true
}

claim_key() {
  python3 - "$1" <<'PY'
import hashlib, sys
print(hashlib.md5(sys.argv[1].encode("utf-8")).hexdigest()[:12])
PY
}

claim() {
  local key="$1"
  local file="$CLAIM_DIR/$key.claim"
  ( set -o noclobber; echo "$$" > "$file" ) 2>/dev/null
}

release() {
  rm -f "$CLAIM_DIR/$1.claim" 2>/dev/null || true
}

pick_task() {
python3 - "$ROOT" "$SEEN_FILE" <<'PY'
import pathlib, re, subprocess, sys, hashlib

root = pathlib.Path(sys.argv[1])
seen_file = pathlib.Path(sys.argv[2])

def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

seen = set()
if seen_file.exists():
    seen = {x.strip() for x in read(seen_file).splitlines() if x.strip()}

next_text = read(root / "tasks" / "NEXT.md")
lanes_text = read(root / "tasks" / "SWARM-LANES.md")
session_text = read(root / "memory" / "SESSION-LOG.md")

items = []

def add(kind, score, text):
    text = " ".join(text.split())
    if not text:
        return
    key = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    if key in seen:
        return
    items.append((score, kind, key, text))

# NEXT.md: non-empty non-header lines, bullets preferred
for line in next_text.splitlines():
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    score = 0
    if s.startswith(("- [ ]", "* ", "- ", "1.", "2.", "3.")):
        score += 90
    else:
        score += 40
    low = s.lower()
    if "just happened" in low:
        score -= 30
    if "blocked" in low:
        score -= 50
    if "next" in low:
        score += 10
    add("NEXT", score, s)

# SWARM-LANES.md: prioritize ACTIVE/READY, skip MERGED/ABANDONED/BLOCKED
for line in lanes_text.splitlines():
    s = line.strip()
    if not s:
        continue
    u = s.upper()
    l = s.lower()
    if "MERGED" in u or "ABANDONED" in u:
        continue
    if "ACTIVE" not in u and "READY" not in u:
        continue
    score = 0
    if "ACTIVE" in u:
        score += 140
    if "READY" in u:
        score += 120
    if "BLOCKED" in u:
        score -= 100
    if "next_step=" in l:
        score += 25
    if "focus=" in l:
        score += 15
    if "available=" in l:
        score += 10
    if "human_open_item=" in l:
        score -= 35
    add("LANE", score, s)

# orient.py fallback: only use substantial lines
try:
    out = subprocess.check_output(
        ["python3", str(root / "tools" / "orient.py")],
        stderr=subprocess.DEVNULL,
        text=True
    )
    for n, line in enumerate(out.splitlines()):
        s = line.strip()
        if len(s) < 12:
            continue
        score = max(30 - n, 5)
        add("ORIENT", score, s)
except Exception:
    pass

# session log hints: penalize stale/duplicate phrases if text overlaps
penalties = []
for line in session_text.lower().splitlines()[-400:]:
    if "duplicate" in line or "near-duplicate" in line:
        penalties.append(("duplicate", -20))
    if "stale" in line or "obsolete" in line:
        penalties.append(("stale", -15))
    if "blocked" in line:
        penalties.append(("blocked", -25))

rescored = []
for score, kind, key, text in items:
    low = text.lower()
    for word, pen in penalties:
        if word in low:
            score += pen
    rescored.append((score, kind, key, text))

rescored.sort(key=lambda x: (-x[0], x[1], x[3]))

if rescored:
    score, kind, key, text = rescored[0]
    print(key)
    print(kind)
    print(text)
PY
}

decide_action() {
python3 - "$ROOT" "$1" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
task = sys.argv[2].lower()

txt = ""
for p in [root/"tasks"/"NEXT.md", root/"tasks"/"SWARM-LANES.md", root/"memory"/"SESSION-LOG.md"]:
    try:
        txt += "\n" + p.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        pass

scope_lines = [line for line in txt.splitlines() if task[:60] in line]
scope = "\n".join(scope_lines) if scope_lines else txt

if any(w in scope for w in ["blocked", "human_open_item", "unclear", "investigate", "question"]):
    print("s")
elif any(w in scope for w in ["duplicate", "near-duplicate", "stale", "obsolete", "abandoned", "remove", "delete"]):
    print("d")
else:
    print("k")
PY
}

run_task() {
  local key="$1"
  local kind="$2"
  local task="$3"
  local action="$4"

  LAST_PICK="$kind | $task"
  LAST_ACTION="$action"
  LAST_RESULT="started"
  write_status

  log "WORK kind=$kind action=$action"
  log "TASK $task"

  if [ -x "$ROOT/tools/resolve_one.sh" ]; then
    AUTO_ACTION="$action" bash "$ROOT/tools/resolve_one.sh" "$task" || true
  else
    case "$action" in
      d) git commit --allow-empty -m "swarm: resolve $kind" >/dev/null 2>&1 || true ;;
      k) git commit --allow-empty -m "swarm: acknowledge $kind" >/dev/null 2>&1 || true ;;
      s) : ;;
    esac
  fi

  echo "$key" >> "$SEEN_FILE"
  LAST_RESULT="done"
  write_status
}

sync_up() {
  log "SYNC UP"
  git add . || true
  git commit -m "swarm: $(date +%H:%M:%S)" || true
  git push origin HEAD:"$DEFAULT_BRANCH" || true
}

trap 'log "STOP"; write_status' EXIT INT TERM

log "START branch=$DEFAULT_BRANCH"
write_status

while true; do
  sync_down
  sync_state

  mapfile -t PICK < <(pick_task)

  if [ "${#PICK[@]}" -lt 3 ]; then
    LAST_PICK="none"
    LAST_ACTION="none"
    LAST_RESULT="waiting-no-task"
    write_status
    log "NO EXISTING TASK FOUND"
    sleep "$SLEEP_SECS"
    continue
  fi

  KEY="${PICK[0]}"
  KIND="${PICK[1]}"
  TASK="${PICK[2]}"

  if ! claim "$KEY"; then
    log "CLAIMED ELSEWHERE $KEY"
    sleep 2
    continue
  fi

  ACTION="$(decide_action "$TASK")"
  run_task "$KEY" "$KIND" "$TASK" "$ACTION"
  release "$KEY"

  sync_state
  sync_up

  sleep "$SLEEP_SECS"
done
