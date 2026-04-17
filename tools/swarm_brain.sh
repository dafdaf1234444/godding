#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
LOCK_FILE="$ROOT/.swarm_brain.lock"
SEEN_FILE="$ROOT/.swarm_brain.seen"
LOG_FILE="$ROOT/.swarm_brain.log"
CLAIM_DIR="$ROOT/.swarm_brain_claims"
MAX_BATCH="${MAX_BATCH:-3}"
SLEEP_SECS="${SLEEP_SECS:-4}"

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "already running"; exit 1; }

mkdir -p "$CLAIM_DIR" "$ROOT/tasks" "$ROOT/tools"
touch "$SEEN_FILE" "$LOG_FILE" "$ROOT/tasks/NEXT.md"

log() {
  printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG_FILE"
}

DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | sed -n '/HEAD branch/s/.*: //p')"
[ -z "${DEFAULT_BRANCH:-}" ] && DEFAULT_BRANCH="$(git branch --show-current 2>/dev/null || echo master)"

sync_down() {
  git fetch origin "$DEFAULT_BRANCH" || true
  git reset --hard "origin/$DEFAULT_BRANCH" || true
}

sync_up() {
  git add . || true
  git commit -m "brain: batch $(date +%H:%M:%S)" || true
  git push origin HEAD:"$DEFAULT_BRANCH" || true
}

claim() {
  local id="$1" f="$CLAIM_DIR/$1.claim"
  ( set -o noclobber; echo "$$" > "$f" ) 2>/dev/null
}

release() {
  rm -f "$CLAIM_DIR/$1.claim" 2>/dev/null || true
}

pick_batch() {
python3 - "$ROOT" "$SEEN_FILE" "$MAX_BATCH" << 'PY'
import re, sys, pathlib, subprocess

root = pathlib.Path(sys.argv[1])
seen_path = pathlib.Path(sys.argv[2])
max_batch = int(sys.argv[3])

seen = set()
if seen_path.exists():
    seen = {x.strip() for x in seen_path.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()}

next_md = (root / "tasks" / "NEXT.md")
lanes_md = (root / "tasks" / "SWARM-LANES.md")
session_log = (root / "memory" / "SESSION-LOG.md")

def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

text_next = read(next_md)
text_lanes = read(lanes_md)
text_log = read(session_log)

ids = {}
def add_score(id_, score, reason):
    if not re.fullmatch(r"L-\d+", id_):
        return
    entry = ids.setdefault(id_, {"score": 0, "reasons": []})
    entry["score"] += score
    entry["reasons"].append(reason)

# NEXT.md gets strong priority
for m in re.finditer(r"L-\d+", text_next):
    add_score(m.group(0), 80, "NEXT")

# SWARM-LANES.md priority logic
for line in text_lanes.splitlines():
    line_u = line.upper()
    line_l = line.lower()
    found = re.findall(r"L-\d+", line)
    if not found:
        continue
    base = 0
    if "ACTIVE" in line_u: base += 120
    if "READY" in line_u: base += 100
    if "BLOCKED" in line_u: base -= 90
    if "ABANDONED" in line_u or "MERGED" in line_u: base -= 120
    if "next_step=" in line_l: base += 10
    if "focus=" in line_l: base += 8
    if "available=" in line_l: base += 5
    if "human_open_item=" in line_l: base -= 25
    if "domain_sync=" in line_l: base += 4
    if "memory_target=" in line_l: base += 4
    for id_ in found:
        add_score(id_, base, "LANE")

# session log penalties/boosts
for line in text_log.lower().splitlines()[-400:]:
    ids_in_line = re.findall(r"l-\d+", line)
    for id_ in ids_in_line:
        id_ = id_.upper()
        if "duplicate" in line or "near-duplicate" in line:
            add_score(id_, -20, "dup")
        if "stale" in line or "obsolete" in line:
            add_score(id_, -15, "stale")
        if "resolved" in line or "done" in line or "working" in line:
            add_score(id_, 5, "good")

# orient fallback
try:
    out = subprocess.check_output(
        ["python3", str(root / "tools" / "orient.py")],
        stderr=subprocess.DEVNULL,
        text=True
    )
    for n, id_ in enumerate(re.findall(r"L-\d+", out)):
        add_score(id_, max(30 - n, 1), "ORIENT")
except Exception:
    pass

# filter seen / negative garbage
items = []
for id_, meta in ids.items():
    if id_ in seen:
        continue
    if meta["score"] < 0:
        continue
    items.append((meta["score"], id_))

items.sort(key=lambda x: (-x[0], x[1]))
for score, id_ in items[:max_batch]:
    print(id_)
PY
}

decide_action() {
python3 - "$ROOT" "$1" << 'PY'
import re, sys, pathlib
root = pathlib.Path(sys.argv[1])
id_ = sys.argv[2]
txt = ""
for p in [root/"tasks"/"NEXT.md", root/"tasks"/"SWARM-LANES.md", root/"memory"/"SESSION-LOG.md"]:
    try:
        txt += "\n" + p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass
scope = "\n".join([line.lower() for line in txt.splitlines() if id_.lower() in line.lower()]) or txt.lower()
if any(w in scope for w in ["blocked", "human_open_item", "unclear", "investigate", "question"]):
    print("s")
elif any(w in scope for w in ["duplicate", "near-duplicate", "stale", "obsolete", "abandoned"]):
    print("d")
else:
    print("k")
PY
}

process_one() {
  local id="$1"
  local action
  action="$(decide_action "$id")"
  log "WORK $id action=$action"

  if [ -x "$ROOT/tools/resolve_one.sh" ]; then
    AUTO_ACTION="$action" bash "$ROOT/tools/resolve_one.sh" "$id" || true
  else
    git commit --allow-empty -m "acknowledge $id" || true
  fi

  echo "$id" >> "$SEEN_FILE"
}

log "START branch=$DEFAULT_BRANCH batch=$MAX_BATCH"

while true; do
  sync_down

  mapfile -t BATCH < <(pick_batch)

  if [ "${#BATCH[@]}" -eq 0 ]; then
    log "NO REAL TASKS -> waiting"
    sleep "$SLEEP_SECS"
    continue
  fi

  log "BATCH ${BATCH[*]}"

  for id in "${BATCH[@]}"; do
    if claim "$id"; then
      process_one "$id"
      release "$id"
    else
      log "SKIP CLAIMED $id"
    fi
  done

  sync_up
  log "CYCLE DONE"
  sleep "$SLEEP_SECS"
done
