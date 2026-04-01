#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p tasks/lanes memory/logs runtime tools

touch .gitignore
grep -qxF 'runtime/*.lock' .gitignore || echo 'runtime/*.lock' >> .gitignore
grep -qxF 'runtime/*.pid' .gitignore || echo 'runtime/*.pid' >> .gitignore
grep -qxF 'runtime/*.tmp' .gitignore || echo 'runtime/*.tmp' >> .gitignore
grep -qxF 'runtime/*.local' .gitignore || echo 'runtime/*.local' >> .gitignore

cat > tasks/lanes/_TEMPLATE.md <<'TPL'
# LANE_ID

status=READY
owner=
created_at=
updated_at=
branch_hint=
focus=
allowed_paths=
blocked_by=
next_step=
human_open_item=
proof_of_novelty=
last_action=

## objective

## constraints

## notes

## handoff
TPL

cat > tools/swarm_claim.sh <<'CLAIM'
#!/usr/bin/env bash
set -Eeuo pipefail

LANE="${1:-}"
OWNER="${2:-$(hostname 2>/dev/null || echo worker)}"
[[ -n "$LANE" ]] || { echo "usage: tools/swarm_claim.sh <lane-file> [owner]"; exit 1; }
[[ -f "$LANE" ]] || { echo "missing lane: $LANE"; exit 1; }

STATUS="$(grep -E '^status=' "$LANE" | head -n1 | cut -d= -f2- || true)"
CUR_OWNER="$(grep -E '^owner=' "$LANE" | head -n1 | cut -d= -f2- || true)"

if [[ "$STATUS" == "ACTIVE" && -n "$CUR_OWNER" && "$CUR_OWNER" != "$OWNER" ]]; then
  echo "lane already active by $CUR_OWNER"
  exit 2
fi

NOW="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
TMP="$(mktemp)"
awk -v owner="$OWNER" -v now="$NOW" '
BEGIN{done_status=0;done_owner=0;done_updated=0}
{
  if ($0 ~ /^status=/)  { print "status=ACTIVE"; done_status=1; next }
  if ($0 ~ /^owner=/)   { print "owner=" owner; done_owner=1; next }
  if ($0 ~ /^updated_at=/) { print "updated_at=" now; done_updated=1; next }
  print
}
END{
  if(!done_status) print "status=ACTIVE"
  if(!done_owner) print "owner=" owner
  if(!done_updated) print "updated_at=" now
}
' "$LANE" > "$TMP"
mv "$TMP" "$LANE"

echo "claimed $LANE by $OWNER"
CLAIM
chmod +x tools/swarm_claim.sh

cat > tools/swarm_release.sh <<'RELEASE'
#!/usr/bin/env bash
set -Eeuo pipefail

LANE="${1:-}"
NEW_STATUS="${2:-MERGED}"
NOTE="${3:-}"
[[ -n "$LANE" ]] || { echo "usage: tools/swarm_release.sh <lane-file> [status] [note]"; exit 1; }
[[ -f "$LANE" ]] || { echo "missing lane: $LANE"; exit 1; }

NOW="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
TMP="$(mktemp)"
awk -v st="$NEW_STATUS" -v now="$NOW" -v note="$NOTE" '
BEGIN{done_status=0;done_owner=0;done_updated=0;done_last=0}
{
  if ($0 ~ /^status=/)  { print "status=" st; done_status=1; next }
  if ($0 ~ /^owner=/)   { print "owner="; done_owner=1; next }
  if ($0 ~ /^updated_at=/) { print "updated_at=" now; done_updated=1; next }
  if ($0 ~ /^last_action=/) { print "last_action=" note; done_last=1; next }
  print
}
END{
  if(!done_status) print "status=" st
  if(!done_owner) print "owner="
  if(!done_updated) print "updated_at=" now
  if(!done_last) print "last_action=" note
}
' "$LANE" > "$TMP"
mv "$TMP" "$LANE"

echo "released $LANE as $NEW_STATUS"
RELEASE
chmod +x tools/swarm_release.sh

cat > tools/swarm_pick_lane.sh <<'PICK'
#!/usr/bin/env bash
set -Eeuo pipefail
for f in tasks/lanes/*.md; do
  [[ "$(basename "$f")" == "_TEMPLATE.md" ]] && continue
  grep -q '^status=READY' "$f" || continue
  blocked="$(grep -E '^blocked_by=' "$f" | head -n1 | cut -d= -f2- || true)"
  if [[ -z "$blocked" ]]; then
    echo "$f"
    exit 0
  fi
done
exit 1
PICK
chmod +x tools/swarm_pick_lane.sh

cat > tools/swarm_worker.sh <<'WORKER'
#!/usr/bin/env bash
set -Eeuo pipefail

OWNER="${OWNER:-$(hostname 2>/dev/null || echo worker)}"
LANE="${1:-}"

if [[ -z "$LANE" ]]; then
  if ! LANE="$(tools/swarm_pick_lane.sh)"; then
    echo "no READY lane"
    exit 0
  fi
fi

tools/swarm_claim.sh "$LANE" "$OWNER"

LANE_ID="$(basename "$LANE" .md)"
STAMP="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
LOG="memory/logs/${LANE_ID}.log"

mkdir -p runtime memory/logs

echo "[$STAMP] owner=$OWNER lane=$LANE_ID start" >> "$LOG"

focus="$(grep -E '^focus=' "$LANE" | head -n1 | cut -d= -f2- || true)"
allowed="$(grep -E '^allowed_paths=' "$LANE" | head -n1 | cut -d= -f2- || true)"

echo "lane=$LANE_ID"
echo "focus=$focus"
echo "allowed_paths=$allowed"

[[ -f tools/orient.py ]] && python3 tools/orient.py || true
[[ -f tools/check.sh ]] && bash tools/check.sh --quick || true
[[ -f tools/check.ps1 ]] && command -v pwsh >/dev/null 2>&1 && pwsh -File tools/check.ps1 -Quick || true
[[ -f tools/sync_state.py ]] && python3 tools/sync_state.py || true
[[ -f tools/validate_beliefs.py ]] && python3 tools/validate_beliefs.py || true

python3 - "$LANE" "$OWNER" <<'PY'
import sys, datetime, pathlib
lane = pathlib.Path(sys.argv[1])
owner = sys.argv[2]
now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
text = lane.read_text(encoding="utf-8")
extra = f"\n- {now} owner={owner} heartbeat\n"
if "## notes\n" in text:
    text = text.replace("## notes\n", "## notes\n" + extra, 1)
else:
    text += "\n## notes\n" + extra
lane.write_text(text, encoding="utf-8")
PY

echo "[$STAMP] owner=$OWNER lane=$LANE_ID end" >> "$LOG"
WORKER
chmod +x tools/swarm_worker.sh

cat > swarm_safe_auto.sh <<'AUTO'
#!/usr/bin/env bash
set -Eeuo pipefail

REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-$(git branch --show-current)}"
SLEEP_SECONDS="${SLEEP_SECONDS:-20}"
OWNER="${OWNER:-$(hostname 2>/dev/null || echo worker)}"
MAX_PUSH_RETRIES="${MAX_PUSH_RETRIES:-3}"

mkdir -p runtime memory/logs tasks/lanes

ts() { date +"%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*"; }
dirty() { [[ -n "$(git status --porcelain)" ]]; }
ahead() { [[ "$(git rev-list --count ${REMOTE}/${BRANCH}..HEAD 2>/dev/null || echo 0)" != "0" ]]; }

sync_first() {
  git fetch "$REMOTE" "$BRANCH"
  git rebase "${REMOTE}/${BRANCH}" || {
    echo
    echo "REBASE CONFLICT"
    echo "run:"
    echo "  git status"
    echo "  git add -A"
    echo "  git rebase --continue"
    exit 2
  }
}

commit_once() {
  git add -A
  if [[ -z "$(git diff --cached --name-only)" ]]; then
    log "nothing staged"
    return 0
  fi
  changed="$(git diff --cached --name-only | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
  msg="swarm: ${changed:0:180}"
  last="$(git log -1 --pretty=%s 2>/dev/null || true)"
  [[ "$msg" == "$last" ]] && { log "duplicate commit avoided"; return 0; }
  git commit -m "$msg"
}

push_retry() {
  for i in $(seq 1 "$MAX_PUSH_RETRIES"); do
    if git push "$REMOTE" "$BRANCH"; then
      log "push ok"
      return 0
    fi
    log "push failed retry=$i"
    git fetch "$REMOTE" "$BRANCH" || true
    git rebase "${REMOTE}/${BRANCH}" || exit 2
    sleep 2
  done
  return 1
}

while true; do
  log "=== cycle start owner=$OWNER branch=$BRANCH ==="
  sync_first

  if tools/swarm_worker.sh; then
    log "worker ran"
  else
    log "worker returned non-zero"
  fi

  if dirty; then
    commit_once
    dirty && commit_once || true
  else
    log "tree clean"
  fi

  if ahead; then
    push_retry || exit 1
  else
    log "nothing to push"
  fi

  log "=== cycle done ==="
  sleep "$SLEEP_SECONDS"
done
AUTO
chmod +x swarm_safe_auto.sh

if ! find tasks/lanes -maxdepth 1 -name '*.md' ! -name '_TEMPLATE.md' | grep -q .; then
cat > tasks/lanes/lane-example.md <<'LANE'
# lane-example

status=READY
owner=
created_at=2026-04-17T00:00:00Z
updated_at=2026-04-17T00:00:00Z
branch_hint=
focus=Perform safe bounded swarm heartbeat without editing shared hotspot files
allowed_paths=tasks/lanes/,memory/logs/,runtime/
blocked_by=
next_step=Claim lane, run health checks, append heartbeat, commit, push
human_open_item=
proof_of_novelty=Avoid README.md and .gitignore churn
last_action=

## objective
Keep autonomous loop alive while minimizing merge conflicts.

## constraints
Do not edit shared root docs unless explicitly needed.

## notes

## handoff
LANE
fi

echo
echo "BOOTSTRAP DONE"
echo
echo "If you still have the old rebase conflict, run:"
echo "  git status"
echo "  git add -A"
echo "  git rebase --continue"
echo
echo "Then run:"
echo "  ./swarm_safe_auto.sh"
