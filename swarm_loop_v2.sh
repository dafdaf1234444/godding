#!/usr/bin/env bash
set -u

BRANCH="$(git branch --show-current 2>/dev/null || echo main)"
REMOTE="${REMOTE:-origin}"
SLEEP_SECONDS="${SLEEP_SECONDS:-20}"

log() {
  printf '\n[%s] %s\n' "$(date '+%F %T')" "$*"
}

have_changes() {
  ! git diff --quiet || ! git diff --cached --quiet || [[ -n "$(git ls-files --others --exclude-standard)" ]]
}

checkpoint_commit() {
  git add -A
  if have_changes; then
    git commit -m "swarm: auto checkpoint $(date '+%F %T')" || true
  fi
}

clean_rebase_state() {
  if [[ -d .git/rebase-merge || -d .git/rebase-apply ]]; then
    log "rebase detected, trying continue"
    git add -A || true
    git rebase --continue || {
      log "rebase continue failed, aborting rebase"
      git rebase --abort || true
    }
  fi
}

sync_with_remote() {
  log "fetching $REMOTE"
  git fetch "$REMOTE" || return 1

  if have_changes; then
    log "local changes detected, checkpointing"
    checkpoint_commit
  fi

  log "rebasing onto $REMOTE/$BRANCH"
  git pull --rebase "$REMOTE" "$BRANCH" || {
    log "pull --rebase failed, trying recovery"
    git rebase --abort || true
    git stash push -u -m "swarm-auto-stash-$(date +%s)" || true
    git pull --rebase "$REMOTE" "$BRANCH" || return 1
    git stash pop || true
  }

  return 0
}

run_swarm_cycle() {
  log "cycle start on branch=$BRANCH"

  clean_rebase_state

  if [[ -f tools/orient.py ]]; then
    log "orient"
    python3 tools/orient.py || true
  fi

  if [[ -f tools/check.sh ]]; then
    log "quick check"
    bash tools/check.sh --quick || true
  fi

  if [[ -f tools/sync_state.py ]]; then
    log "sync state"
    python3 tools/sync_state.py || true
  fi

  if [[ -f tools/validate_beliefs.py ]]; then
    log "validate beliefs"
    python3 tools/validate_beliefs.py || true
  fi

  checkpoint_commit
  sync_with_remote || log "sync failed; continuing next cycle"

  log "push"
  git push "$REMOTE" "$BRANCH" || true

  log "cycle end"
}

while true; do
  if [[ "${SWARM_STOP:-0}" == "1" ]]; then
    log "SWARM_STOP=1, exiting"
    exit 0
  fi

  run_swarm_cycle
  log "sleeping ${SLEEP_SECONDS}s"
  sleep "$SLEEP_SECONDS"
done
