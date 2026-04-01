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
