# Coupling Expert Report — S269 (lane L-S263-COUPLING-EXPERT)

**Date**: 2026-02-28
**Session**: S269
**Analyst**: Coupling Expert
**Lane**: `L-S263-COUPLING-EXPERT`

---

## Method

All measurements are reproducible from the git log. Commands are shown inline.

```bash
# Hotspot files (all-time)
git log --name-only --pretty=format: | grep -v '^$' | sort | uniq -c | sort -rn | head -15

# Co-change pairs (Python script — see below)
git log --name-only --pretty=format:COMMIT | python3 co_change_pairs.py

# Files with >5 commits in last 100 commits
git log --name-only --pretty=format: -n 100 | python3 frequency_filter.py
```

---

## 1. Top 10 Hotspot Files (all-time, 708 total commits)

| Rank | File | Commit appearances | % of all commits |
|------|------|-------------------|-----------------|
| 1 | `memory/INDEX.md` | 308 | 43.5% |
| 2 | `tasks/NEXT.md` | 295 | 41.7% |
| 3 | `tasks/FRONTIER.md` | 215 | 30.4% |
| 4 | `memory/PRINCIPLES.md` | 176 | 24.9% |
| 5 | `memory/SESSION-LOG.md` | 147 | 20.8% |
| 6 | `docs/PAPER.md` | 102 | 14.4% |
| 7 | `tasks/SWARM-LANES.md` | 63 | 8.9% |
| 8 | `README.md` | 58 | 8.2% |
| 9 | `tools/periodics.json` | 55 | 7.8% |
| 10 | `tools/maintenance.py` | 45 | 6.4% |

**Total unique files ever changed**: 1393
**Total commit-file appearances**: 4017
**Concentration**: the top 5 files alone account for 28.6% of all file appearances.

---

## 2. Co-Change Pairs (top 30, all-time)

The following pairs appear together in the same commit most frequently. Sorted descending.

| Count | File A | File B |
|-------|--------|--------|
| 183 | `memory/INDEX.md` | `tasks/NEXT.md` |
| 144 | `memory/INDEX.md` | `tasks/FRONTIER.md` |
| 133 | `memory/INDEX.md` | `memory/PRINCIPLES.md` |
| 101 | `memory/SESSION-LOG.md` | `tasks/NEXT.md` |
| 92 | `tasks/FRONTIER.md` | `tasks/NEXT.md` |
| 89 | `memory/INDEX.md` | `memory/SESSION-LOG.md` |
| 80 | `memory/PRINCIPLES.md` | `tasks/FRONTIER.md` |
| 79 | `memory/PRINCIPLES.md` | `tasks/NEXT.md` |
| 77 | `docs/PAPER.md` | `tasks/NEXT.md` |
| 75 | `docs/PAPER.md` | `memory/INDEX.md` |
| 49 | `memory/PRINCIPLES.md` | `memory/SESSION-LOG.md` |
| 45 | `memory/SESSION-LOG.md` | `tasks/FRONTIER.md` |
| 39 | `tasks/NEXT.md` | `tasks/SWARM-LANES.md` |
| 37 | `README.md` | `tasks/NEXT.md` |
| 34 | `tasks/NEXT.md` | `tools/periodics.json` |
| 28 | `memory/INDEX.md` | `tools/periodics.json` |
| 27 | `README.md` | `memory/INDEX.md` |
| 27 | `memory/SESSION-LOG.md` | `tools/periodics.json` |
| 26 | `memory/INDEX.md` | `tasks/SWARM-LANES.md` |
| 26 | `README.md` | `docs/PAPER.md` |
| 26 | `docs/PAPER.md` | `tasks/FRONTIER.md` |
| 24 | `docs/PAPER.md` | `memory/PRINCIPLES.md` |
| 24 | `memory/HUMAN-SIGNALS.md` | `tasks/NEXT.md` |
| 24 | `memory/INDEX.md` | `tools/maintenance.py` |
| 23 | `tasks/NEXT.md` | `tools/maintenance.py` |
| 22 | `tasks/FRONTIER.md` | `tools/periodics.json` |
| 22 | `experiments/proxy-k-log.json` | `tasks/NEXT.md` |
| 21 | `experiments/frontier-decay.json` | `memory/INDEX.md` |

---

## 3. Co-Change Cluster Summary

Four distinct clusters emerge from the pair data:

### Cluster A — State-sync core (highest density)
**Files**: `memory/INDEX.md`, `tasks/NEXT.md`, `tasks/FRONTIER.md`, `memory/PRINCIPLES.md`, `memory/SESSION-LOG.md`

These five files move together in nearly every session commit. The 183-count INDEX.md↔NEXT.md pair is the strongest coupling signal in the entire repo. This cluster represents the "key-state snapshot" that every session is expected to update. The co-movement is intentional by design (state-sync protocol), but the absence of any atomic update mechanism makes every multi-file update a potential race window.

Top recurring multi-file clusters (state files only, last 200 commits):
- `docs/PAPER.md + memory/INDEX.md + tasks/NEXT.md`: 17 commits
- `docs/PAPER.md + memory/INDEX.md + tasks/FRONTIER.md + tasks/NEXT.md`: 6 commits
- `memory/INDEX.md + tasks/FRONTIER.md + tasks/NEXT.md + tasks/SWARM-LANES.md`: 2 commits

### Cluster B — Coordination + lane files
**Files**: `tasks/SWARM-LANES.md`, `tasks/NEXT.md`

These move together in 39 commits. SWARM-LANES is written directly by both `lanes_compact.py` and `close_lane.py` — two separate tools operating on the same append-only format file.

### Cluster C — Scale counters (documentation sync)
**Files**: `docs/PAPER.md`, `README.md`, `memory/INDEX.md`

These hold redundant lesson/principle/frontier counts (L/P/F numbers). Any count change requires updating 2-3 of these simultaneously. This is a known duplication point (see L-332: compact.py idempotency issue).

### Cluster D — Experiment outputs
**Files**: `experiments/proxy-k-log.json`, `experiments/frontier-decay.json`, `tools/periodics.json`

These move with the state-sync cluster in ~34 commits. Experiments write JSON; tools read them. Lower concurrency risk since these are written by single-purpose tools, but `frontier-decay.json` is written by BOTH `frontier_decay.py` AND `maintenance.py` (see Section 4).

---

## 4. Shared Mutable State Risk Table

Files changed more than 5 times in the last 100 commits:

| File | Commits (last 100) | Tools that WRITE it | Lock mechanism |
|------|--------------------|---------------------|---------------|
| `tasks/NEXT.md` | 49 | agents (manual) | none |
| `memory/INDEX.md` | 31 | `sync_state.py`, `renew_identity.py`, agents (manual) | none |
| `tasks/SWARM-LANES.md` | 30 | `close_lane.py`, `lanes_compact.py`, agents (manual) | none |
| `docs/PAPER.md` | 27 | agents (manual) | none |
| `README.md` | 21 | agents (manual) | none |
| `tasks/FRONTIER.md` | 18 | `sync_state.py`, `frontier_decay.py`, agents (manual) | none |
| `memory/HUMAN-SIGNALS.md` | 10 | agents (manual) | none |
| `memory/SESSION-LOG.md` | 10 | agents (manual) | none |
| `tools/periodics.json` | 8 | agents (manual) | none |
| `experiments/proxy-k-log.json` | 6 | `compact.py` | none |
| `domains/dream/tasks/FRONTIER.md` | 6 | `evolve.py`, agents (manual) | none |

**Tool-to-shared-file write conflicts** (multiple tools writing the same file):

| File | Writers | Risk |
|------|---------|------|
| `tasks/FRONTIER.md` | `sync_state.py` + `frontier_decay.py` | HIGH — both do read-modify-write, no lock |
| `memory/INDEX.md` | `sync_state.py` + `renew_identity.py` | HIGH — both patch specific lines in-place |
| `tasks/SWARM-LANES.md` | `close_lane.py` (append) + `lanes_compact.py` (full rewrite) | HIGH — compact rewrites entire file; append is safe but compact is destructive |
| `experiments/frontier-decay.json` | `frontier_decay.py` + `maintenance.py` | MEDIUM — maintenance writes as side-effect of check; race with dedicated tool |

**Single exception**: `tools/bulletin.py` implements a `_append_with_lock()` function using `O_CREAT | O_EXCL` lock files — the only file in the toolchain with explicit cross-process mutual exclusion. This is the correct pattern but is absent from all other shared-state writers.

---

## 5. Tool-Data Coupling Matrix

```
sync_state.py       -> memory/INDEX.md, tasks/FRONTIER.md, memory/PRINCIPLES.md, tasks/NEXT.md
frontier_decay.py   -> tasks/FRONTIER.md, experiments/frontier-decay.json
maintenance.py      -> experiments/frontier-decay.json  (side-effect write during check)
renew_identity.py   -> memory/INDEX.md
lanes_compact.py    -> tasks/SWARM-LANES.md (full rewrite), tasks/SWARM-LANES-ARCHIVE.md
close_lane.py       -> tasks/SWARM-LANES.md (append)
compact.py          -> experiments/compact-citation-cache.json,
                       experiments/compact-lesson-cache.json,
                       experiments/proxy-k-log.json
bulletin.py         -> tasks/BULLETIN.md  [HAS LOCK — safe]
evolve.py           -> domains/*/tasks/FRONTIER.md
propagate_challenges.py -> beliefs/PHILOSOPHY.md
pulse.py            -> memory/PULSE.md
belief_evolve.py    -> beliefs/*.md
```

Tools reading SWARM-LANES (30 tools): agents get a stale snapshot if `lanes_compact.py` rewrites the file mid-read. The full list includes: `maintenance.py`, `f_ops1_wip_limit.py`, `f_ops2_domain_priority.py`, `f_ops3_queue_aging.py`, `info_flow_map.py`, `farming_expert.py`, and 25 additional experiment/analysis tools.

---

## 6. Concurrency Safety Verdict

**Verdict: UNSAFE (for the core coordination cluster)**

### Rationale

1. **No atomic multi-file update**: The state-sync pattern requires updating 3-5 files atomically (INDEX.md + NEXT.md + FRONTIER.md + PRINCIPLES.md + PAPER.md). There is no transaction mechanism. Concurrent sessions observe partial state between git commits. S186/S187 documented this: concurrent sessions completed the same tasks and produced drift in count fields.

2. **No file-level locks on shared mutable state**: `sync_state.py`, `frontier_decay.py`, `renew_identity.py`, and `lanes_compact.py` all perform read-modify-write on files that other tools and agents simultaneously write. The only lock implementation in the codebase (`bulletin.py` `_append_with_lock()`) is isolated to one tool.

3. **lanes_compact.py full-rewrite pattern**: When `lanes_compact.py` runs, it reads SWARM-LANES.md, computes kept/archived rows, and writes the entire file (`LANES_PATH.write_text(lanes_output)`). Any concurrent `close_lane.py` append happening within the same window will be silently lost.

4. **Count fields duplicated across 3+ files**: `README.md`, `docs/PAPER.md`, and `memory/INDEX.md` all carry lesson/principle/frontier count headers. These can diverge within a single session if one file is updated before a concurrent session reads and re-updates another. The swarm has accumulated at least one lesson about this (L-332 for compact.py idempotency; L-309/310 for count sync).

5. **Empirical evidence**: Multiple sessions document count drift as a recurring theme (S195 "fix PAPER frontier count: 29F→30F", S191 "proxy-K sync floor update", S192 "paper+readme+proxy-K: fix 2 count drifts"). The frequency of fix commits for the same files indicates this is an active failure mode, not theoretical risk.

### Safe subsystems
- `compact.py` cache files (single writer, no concurrent writer tool)
- `bulletin.py` BULLETIN.md (has proper lock)
- Domain FRONTIER.md files per-domain (single domain = single writer under normal operation)
- `experiments/` output JSON files (written once per tool run, not contention targets)

---

## 7. Top 3 Remediation Recommendations

### R1 — Consolidate count fields into single source of truth

**Problem**: Lesson/principle/frontier counts appear in README.md, docs/PAPER.md, and memory/INDEX.md. Every count change must update 3 files, creating race windows and drift.

**Recommendation**: Make `memory/INDEX.md` the canonical count store. Have README.md and docs/PAPER.md embed a reference tag (e.g., `<!-- COUNT:LESSONS -->`) that a single `sync_state.py` call resolves. Reduces co-change cluster A's mandatory footprint from 5 files to 2.

**Effort**: Low (sync_state.py already handles this pattern for NEXT.md counts).

---

### R2 — Add write-lock guard to lanes_compact.py (and all SWARM-LANES writers)

**Problem**: `lanes_compact.py` does a destructive full-rewrite of SWARM-LANES.md without any lock. `close_lane.py` appends to the same file. A simultaneous compact + close operation silently loses the close.

**Recommendation**: Port `bulletin.py`'s `_append_with_lock()` pattern to a shared `tools/filelock.py` utility. Require callers (`lanes_compact.py`, `close_lane.py`, any tool writing SWARM-LANES or FRONTIER.md) to acquire this lock before their read-modify-write cycle.

**Effort**: Medium — implement shared lock utility once, apply to 4 hotspot writers.

---

### R3 — Decouple maintenance.py's check-and-write pattern for frontier-decay.json

**Problem**: `maintenance.py` silently writes `experiments/frontier-decay.json` as a side-effect of running a check (not a write). `frontier_decay.py` also writes this file. The maintenance check is run by every session; the decay tool is run explicitly. Two writers, no coordination.

**Recommendation**: Remove the write side-effect from `maintenance.py`'s `check_frontier_decay()`. Make it read-only; let `frontier_decay.py` remain the sole writer. Add a DUE notice if `frontier-decay.json` is stale (>N sessions) rather than silently writing it.

**Effort**: Low — remove ~3 lines from maintenance.py, add a staleness check instead.

---

## 8. Expect / Actual / Diff

| Field | Value |
|-------|-------|
| **Expect** | 3-5 hotspot files concentrated in coordination layer; co-change pairs revealing intentional clusters; some unguarded shared writes |
| **Actual** | 5-file coordination cluster with very high coupling density (183-count top pair); 4 confirmed tool-vs-tool write conflicts on the same files without locking; only 1 tool (bulletin.py) has any lock; count duplication across 3 files is a confirmed active failure mode |
| **Diff** | Coupling concentration is higher than expected — top 5 files at 20-43% of all commits is extreme even for a coordination-heavy repo. The bulletin.py lock is a positive signal showing the pattern is known but under-applied. The `lanes_compact.py` full-rewrite pattern is the highest-severity point not previously flagged in lessons. |

---

*Produced by Coupling Expert, S269. Artifact: `experiments/architecture/coupling-expert-s263.md`*
