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
