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
