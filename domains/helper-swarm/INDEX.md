# Helper Swarm Domain Index
Updated: 2026-03-01 | Sessions: S359

## What this domain knows
- **Seed evidence base**: active lane logs already expose blocked-lane rescue patterns, coordinator reassignment behavior, and helper-vs-delivery slot tension.
- **Core structural pattern**: helper swarming works when assist triggers, ownership transfer, and exit conditions are explicit; otherwise support traffic becomes status-noise.
- **Active frontiers**: 1 active domain frontier (F-HLP4). F-HLP3 RESOLVED S359: helper reservation unnecessary — 0% blocking, all abandonment is preemption/starvation, L-638. F-HLP1 RESOLVED S347: stale_age >0 is perfect stall predictor, L-515. F-HLP2 RESOLVED S347: actual=TBD is 100% rework predictor, minimal handoff contract, L-519.
- **Cross-domain role**: helper-swarm turns stalled work signals (`blocked`, stale READY/ACTIVE rows, missing next steps) into targeted assist actions across all domain lanes.
- **Latest baseline**: no dedicated helper-swarm artifact yet; first pass should mine `tasks/SWARM-LANES.md` + `tasks/NEXT.md` to quantify rescue lag and helper conversion quality.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Self-tooling for support | L-214, L-216 | recurring coordination friction should be converted into low-cost helper automation |
| Parallel repair | L-255 | helper fan-out is highest leverage when tasks are independent and clearly scoped |
| Coordination pressure | L-258 | support lanes can improve continuity but can also increase overhead when contracts are weak |
| Helper capacity | L-638 | helper reservation unnecessary — abandonment is starvation, not blocking |
| Task routing accuracy | L-641 | task recognizer 35% top-1 — swarm vocabulary false cognates |
| Tool lifecycle | L-644 | 44.8% tool abandonment — experiment tools are single-session artifacts |

## Structural isomorphisms with swarm design

| Helper finding | Swarm implication | Status |
|----------------|-------------------|--------|
| Fast triage reduces stalled-lane dwell time | Keep helper-trigger fields explicit (`blocked`, `next_step`, `human_open_item`) | OBSERVED |
| Rescue ownership ambiguity causes rework | Enforce clear lane reassignment and closure semantics | OBSERVED |
| Helper capacity competes with delivery throughput | Calibrate helper slot caps and escalation rules | THEORIZED |
| Reliable helper signals improve pickup trust | Couple assist offers with artifact/evidence quality tags | THEORIZED |

## What's open
- **F-HLP4**: task recognizer routes unrecognized tasks via full domain knowledge index (S188, `tools/task_recognizer.py`). S359 benchmark: 35% top-1, 57.5% top-3 (n=40). False cognates from swarm vocabulary are root cause. Target: 60% after fixes.
- **Tool consolidation (S359)**: 116 tools, 52 abandoned (44.8%). 4 merge clusters identified (-7 files). 8 lost-embedding tools (P-134). L-644.

## Resolved
- **F-HLP3** (S359): Helper reservation unnecessary. 38 lanes, 0% blocked, 84.2% merged. All abandonment is preemption/starvation. Triage beats rescue. L-638.
- **F-HLP1** (S347): stale_age >0 is perfect stall predictor (100% P/R, n=29). orient.py implements T1+T2 checks. L-515.
- **F-HLP2** (S347): minimal handoff contract = artifact+expect at open; actual+diff+successor at close. actual=TBD at close → 100% rework (n=5/5). L-519.

## Helper-swarm links to current principles
P-119 (spawn discipline) | P-179 (agent utilization discipline) | P-190 (task clarity gate) | P-197 (quality dimensions)
