#!/usr/bin/env bash
set -Eeuo pipefail

REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-$(git branch --show-current 2>/dev/null || true)}"
SLEEP_SECONDS="${SLEEP_SECONDS:-20}"
MAX_PUSH_RETRIES="${MAX_PUSH_RETRIES:-3}"
STATUS_DIR="${STATUS_DIR:-runtime}"
LOG_FILE="${LOG_FILE:-$STATUS_DIR/swarm_auto.log}"
STATUS_FILE="${STATUS_FILE:-$STATUS_DIR/swarm_auto.status}"
SEEN_FILE="${SEEN_FILE:-$STATUS_DIR/swarm_auto.seen}"
STOP_FILE="${STOP_FILE:-tasks/KILL-SWITCH.md}"

mkdir -p "$STATUS_DIR"

ts() { date +"%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" | tee -a "$LOG_FILE"; }
status() { printf "%s\n" "$*" > "$STATUS_FILE"; }

die() {
  log "FATAL: $*"
  status "fatal: $*"
  exit 1
}

have() { command -v "$1" >/dev/null 2>&1; }

ensure_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not in git repo"
  [[ -n "${BRANCH}" ]] || die "could not determine branch"
}

stop_requested() {
  [[ "${SWARM_STOP:-0}" == "1" ]] && return 0
  [[ -f "$STOP_FILE" ]] && grep -Eqi '^\s*(STOP|1|TRUE|YES)\s*$' "$STOP_FILE" && return 0
  return 1
}

record_seen() {
  {
    echo "time=$(ts)"
    echo "branch=$BRANCH"
    echo "head=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
    echo "last_subject=$(git log -1 --pretty=%s 2>/dev/null || echo none)"
  } > "$SEEN_FILE"
}

dirty() {
  [[ -n "$(git status --porcelain)" ]]
}

staged_dirty() {
  [[ -n "$(git diff --cached --name-only)" ]]
}

ahead_of_remote() {
  local count
  count="$(git rev-list --count "${REMOTE}/${BRANCH}..HEAD" 2>/dev/null || echo 0)"
  [[ "${count}" != "0" ]]
}

safe_py() {
  local f="$1"
  if [[ -f "$f" ]]; then
    python3 "$f"
  else
    return 0
  fi
}

safe_sh() {
  local f="$1"
  shift || true
  if [[ -f "$f" ]]; then
    bash "$f" "$@"
  else
    return 0
  fi
}

safe_pwsh() {
  local f="$1"
  shift || true
  if have pwsh && [[ -f "$f" ]]; then
    pwsh -File "$f" "$@"
  else
    return 0
  fi
}

sync_first() {
  log "sync: fetch ${REMOTE}/${BRANCH}"
  git fetch "$REMOTE" "$BRANCH"

  log "sync: rebase onto ${REMOTE}/${BRANCH}"
  if ! git rebase "${REMOTE}/${BRANCH}"; then
    status "blocked: rebase conflict"
    log "REBASE CONFLICT"
    echo
    echo "Resolve manually, then run:"
    echo "  git add -A"
    echo "  git rebase --continue"
    echo "Then restart:"
    echo "  ./swarm_auto.sh"
    exit 2
  fi
}

run_health() {
  [[ -f tools/orient.py ]] && { log "run: tools/orient.py"; safe_py tools/orient.py || true; }
  if [[ -f tools/check.sh ]]; then
    log "run: tools/check.sh --quick"
    safe_sh tools/check.sh --quick || true
  elif [[ -f tools/check.ps1 ]]; then
    log "run: tools/check.ps1 -Quick"
    safe_pwsh tools/check.ps1 -Quick || true
  fi
  [[ -f tools/sync_state.py ]] && { log "run: tools/sync_state.py"; safe_py tools/sync_state.py || true; }
  [[ -f tools/validate_beliefs.py ]] && { log "run: tools/validate_beliefs.py"; safe_py tools/validate_beliefs.py || true; }
}

# Try to actually DO work using whatever exists in repo.
# Order is intentional: more swarm-native things first, generic fallback later.
run_action() {
  log "action: probing available worker entrypoints"

  if [[ -f tools/swarm.py ]]; then
    log "action: python3 tools/swarm.py"
    python3 tools/swarm.py && return 0 || return 1
  fi

  if [[ -f tools/swarm.sh ]]; then
    log "action: bash tools/swarm.sh"
    bash tools/swarm.sh && return 0 || return 1
  fi

  if [[ -f tools/worker.py ]]; then
    log "action: python3 tools/worker.py"
    python3 tools/worker.py && return 0 || return 1
  fi

  if [[ -f tools/worker.sh ]]; then
    log "action: bash tools/worker.sh"
    bash tools/worker.sh && return 0 || return 1
  fi

  if [[ -f tools/agent_do_next.py ]]; then
    log "action: python3 tools/agent_do_next.py"
    python3 tools/agent_do_next.py && return 0 || return 1
  fi

  if [[ -f tools/f_ops2_domain_priority.py ]]; then
    log "action: python3 tools/f_ops2_domain_priority.py"
    python3 tools/f_ops2_domain_priority.py && return 0 || return 1
  fi

  if [[ -f tools/do_next.py ]]; then
    log "action: python3 tools/do_next.py"
    python3 tools/do_next.py && return 0 || return 1
  fi

  if [[ -f tools/next.py ]]; then
    log "action: python3 tools/next.py"
    python3 tools/next.py && return 0 || return 1
  fi

  if [[ -f tools/act.sh ]]; then
    log "action: bash tools/act.sh"
    bash tools/act.sh && return 0 || return 1
  fi

  if [[ -f Makefile ]]; then
    if grep -qE '^[[:space:]]*swarm:' Makefile; then
      log "action: make swarm"
      make swarm && return 0 || return 1
    fi
    if grep -qE '^[[:space:]]*next:' Makefile; then
      log "action: make next"
      make next && return 0 || return 1
    fi
  fi

  # Last resort: leave a breadcrumb and keep system healthy.
  log "action: no known worker entrypoint found; health-only cycle"
  return 0
}

stage_commit() {
  git add -A

  if ! staged_dirty; then
    log "commit: nothing staged"
    return 0
  fi

  local summary changed hash
  changed="$(git diff --cached --name-only | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
  hash="$(printf "%s" "$changed" | sha1sum | awk '{print $1}' | cut -c1-10)"
  summary="swarm: ${hash} ${changed:0:180}"

  # Avoid immediate duplicate subject spam
  if [[ "$(git log -1 --pretty=%s 2>/dev/null || true)" == "$summary" ]]; then
    log "commit: duplicate summary avoided"
    return 0
  fi

  git commit -m "$summary"
  log "commit: $summary"
}

push_retry() {
  local i
  for i in $(seq 1 "$MAX_PUSH_RETRIES"); do
    log "push: attempt $i/$MAX_PUSH_RETRIES"
    if git push "$REMOTE" "$BRANCH"; then
      log "push: success"
      return 0
    fi
    log "push: failed, refetch/rebase/retry"
    git fetch "$REMOTE" "$BRANCH" || true
    if ! git rebase "${REMOTE}/${BRANCH}"; then
      status "blocked: rebase conflict during push retry"
      die "rebase conflict during push retry"
    fi
    sleep 2
  done
  return 1
}

cycle() {
  stop_requested && { log "stop requested"; status "stopped"; exit 0; }

  status "running"
  log "========== CYCLE START =========="
  ensure_repo
  record_seen

  sync_first
  run_health

  # pre-action fingerprint
  local before after
  before="$(git rev-parse HEAD 2>/dev/null || echo none)"

  if ! run_action; then
    log "action: returned non-zero"
  fi

  run_health

  if dirty; then
    stage_commit
  else
    log "tree: clean after action"
  fi

  # if health/check scripts created more changes after commit attempt
  if dirty; then
    stage_commit
  fi

  after="$(git rev-parse HEAD 2>/dev/null || echo none)"
  log "head: ${before} -> ${after}"

  if ahead_of_remote; then
    push_retry || die "push failed after retries"
  else
    log "push: nothing to push"
  fi

  record_seen
  status "ok"
  log "=========== CYCLE DONE =========="
}

main() {
  ensure_repo
  log "starting self-acting swarm loop on branch=${BRANCH} remote=${REMOTE} sleep=${SLEEP_SECONDS}s"
  while true; do
    cycle
    sleep "$SLEEP_SECONDS"
  done
}

main "$@"
