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
