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
