#!/usr/bin/env bash
while true; do
  echo "===== $(date) ====="

  git pull --rebase --autostash 2>/dev/null

  python3 tools/orient.py 2>/dev/null
  bash tools/check.sh --quick 2>/dev/null

  python3 tools/sync_state.py 2>/dev/null
  python3 tools/validate_beliefs.py 2>/dev/null

  # try real runner if exists
  if [ -f tools/swarm.py ]; then python3 tools/swarm.py; fi
  if [ -f tools/dispatch.py ]; then python3 tools/dispatch.py; fi
  if [ -f tools/f_ops2_domain_priority.py ]; then python3 tools/f_ops2_domain_priority.py; fi

  git add -A
  git commit -m "swarm loop $(date)" 2>/dev/null
  git push 2>/dev/null

  sleep 20
done
