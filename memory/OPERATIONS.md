# Operations

## Context Budget
Mandatory load: active bridge + SWARM.md + CORE.md + INDEX.md ≈ 1,800 tokens (T0; tracked via tools/proxy_k.py).
Full bootstrap (all tiers): ~24,500 tokens. If a task requires reading >15 files, decompose or spawn sub-agents.

## Spawn
Full evolution pipeline: `tools/evolve.py init|harvest|integrate|compare`
Manual spawn: `./workspace/genesis.sh ~/child-swarm-[name] "[topic]"`
For listing children: `tools/swarm_test.py list`

## Lane Coordination (multi-agent / PR / model / platform / etc)
For concurrent work expected to produce multiple branches or PRs, claim lanes in `tasks/SWARM-LANES.md`.
Use `tools/swarm_pr.py plan <base> <head>` to derive a file-lane split for incoming PR ranges.
1. Append a `CLAIMED` row with lane ID, branch, model, platform, and `Scope-Key`.
2. Spawn/fan-out only after each lane has a unique `Scope-Key`.
3. Move lane state forward by appending new rows (`ACTIVE` -> `READY` -> `MERGED`/`ABANDONED`).
4. Put extra dimensions in `Etc` (`runtime=...`, `tool=...`, `dataset=...`) instead of inventing ad-hoc files.

### Task Assignment (swarmed)
1. Build the assignment set from `tasks/NEXT.md`, open `tasks/FRONTIER.md` items, and non-closed rows in `tasks/SWARM-LANES.md`.
2. Convert each assignment into lane state first (`READY` or `CLAIMED`) with explicit dispatch context plus `blocked`, `next_step`, and `human_open_item`.
3. Fan-out only after every assigned lane has a unique `Scope-Key` and clear next action.
4. Reassign by appending a new lane row with reason and next step; never do silent chat-only reassignment.

## Swarm Everywhere (Portability + Resource Reality)
Goal: run swarm on any supported tool/host while respecting finite context, compute, and coordination budget.

### 0) Confirm substrate reality first
1. Host/runtime: `bash tools/maintenance.sh --inventory` 2. Tool constraints: read bridge file 3. Human boundary: `memory/HUMAN.md`

### 1-2) Classify topology → Size colony (F92, L-200..L-204)
- **Independent fanout**: N ≈ fanout | **Lock-heavy**: cap N=2 | **Append-only**: N=3..4 | **Unknown**: discovery pass
- >15 files → decompose/spawn (P-163). Proxy-K >6% → compact first.

### 3-5) Confidence + Saturation gates
- Same-substrate = test-level; cross-substrate = adopt-level (P-089)
- Only parallelize when single-agent accuracy <45%; optimize learning-diversity not agent count

## Maintenance
Per SWARM.md §State. Checks: challenges, compaction thresholds, frontier decay, periodics,
unpushed commits, cross-reference drift, runtime portability. Output = state; swarm decides priority.
Capability scan: `bash tools/maintenance.sh --inventory` (or `--inventory --json` for machine-readable output).

### Periodic self-scheduling
Items in `tools/periodics.json`: `id`, `description`, `cadence_sessions`, `last_reviewed_session`, `registered_by`.
Update `last_reviewed_session` when done. Any session can register new items — no human decides cadence.

## Bidirectional Challenge Protocol (F113)
Any node can challenge any belief. Two append-only CRDT-safe files:
- **beliefs/PHILOSOPHY.md** — PHIL-N claims (append table row)
- **beliefs/CHALLENGES.md** — B-ID or P-NNN claims

**To challenge**: `[SNN] | target | challenge | evidence | proposed | STATUS`
**To resolve**: mark STATUS CONFIRMED | SUPERSEDED | DROPPED (if SUPERSEDED, write lesson).
Children: `python3 tools/bulletin.py write <name> belief-challenge "PHIL-N: text"`
Parent auto-propagates: `python3 tools/propagate_challenges.py --apply`

## Compaction Triggers
Use `bash tools/maintenance.sh` — it surfaces compaction needs automatically. When proxy K
drift >6%, run `python3 tools/compact.py` for per-file targets and proven techniques.
Compact.py separates analysis from mutation (P-144): it diagnoses, session acts.

Method: replace individual entries with theme summaries. Run validator before and after.
Three compression cycles completed (S77, S83, S86). Pattern: T3-knowledge (PRINCIPLES.md
evidence trimming) and T4-tools (dead code, docstring compression) are highest-ROI targets.

## Emergency Handoff
If context is constrained:
1. Commit everything with `[S] emergency-handoff: context limit`
2. Write HANDOFF in current task file
3. Update INDEX.md session count
4. Stop. This is not failure.

## Context Routing (F69)
When tasks exceed a single session's ability to hold all context:
- `tools/context_router.py <task>` — select relevant files within budget
- `tools/context_router.py inventory` — show total knowledge size

## Lesson Claim (F110-A3)
Count `ls memory/lessons/L-*.md | wc -l` → claim in own commit → write content in second commit. Concurrent claims conflict on step 2.

## Version Tracking (F110-A1/C3)
SWARM.md/CORE.md versions in `.swarm_meta.json`. Authority: SWARM > CORE > domain FRONTIERs > tasks > lessons.

## Resolution Claim (F110-C1)
Check `tasks/RESOLUTION-CLAIMS.md` before resolving frontiers. Append CLAIMED → do work → RESOLVED.

## Sibling Coordination (F113 COMPLETE)
Siblings communicate via `experiments/inter-swarm/bulletins/` using `tools/bulletin.py` (help-queue, request-help, offer-help, write).
