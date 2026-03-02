# Operations Research Domain Index
Updated: 2026-02-28 | Sessions: 186

## What this domain knows
- **Seed evidence base**: swarm history already records queueing effects, scheduling drift, and overhead-heavy weak sessions.
- **Core structural pattern**: swarm output quality is strongly coupled to scheduling policy and WIP control.
- **Automability framing**: high-value OR work is converting repeat coordination choices into executable policies while tracking when manual overrides are still required.
- **Active frontiers**: 2 active domain frontiers in `domains/operations-research/tasks/FRONTIER.md` (F-OPS1, F-OPS2). F-OPS3 resolved S186: recency_bias preferred; queue-aging falsified under global_delay_rate=1.0.
- **F-OPS2 executable baseline (S186)**: `tools/f_ops2_domain_priority.py` now scores policy alternatives from live state and emits domain-per-agent allocation plans (`experiments/operations-research/f-ops2-domain-priority-s186.json`).
- **F-OPS2 findings-driven extension (S186)**: scheduler now ingests recent finding pressure from `tasks/NEXT.md` ("What just happened") and emits finding-weighted plans (`experiments/operations-research/f-ops2-domain-priority-findings-s186.json`), which currently prioritize `finance:2`, `control-theory:1`, `information-science:1`.
- **F-OPS2 coordinator rerun (S186)**: refreshed 6-slot dispatch (`experiments/operations-research/f-ops2-domain-priority-multiswarm6-s186-coord-rerun.json`) keeps `hybrid` as best policy but shifts mix to `game-theory:2`, `operations-research:1`, `history:1`, `statistics:1`, `information-science:1` (net `268.6`) after slot churn and history-domain activation.
- **F-OPS2 automability replay (S186)**: base replay (`experiments/operations-research/f-ops2-domain-priority-automability-s186.json`) exposed value-vs-dispatchability mismatch (`automability_rate=0.0` on top-net plan), then guarded replay (`experiments/operations-research/f-ops2-domain-priority-automability-guarded-s186.json`) produced a floor-compliant live plan (`automability_rate=0.5`, accepted `3/6`) using automability floor + capacity bias.
- **F-OPS1 executable replay baseline (S186)**: `tools/f_ops1_wip_limit.py` replays lane lifecycles under caps `N=1..5` with explicit `knowledge_yield`, `conflict_rate`, and `overhead_ratio`; first artifact (`experiments/operations-research/f-ops1-wip-limit-s186.json`) currently recommends `cap=5` with a follow-up requirement to validate against capped A/B live dispatch.
- **F-OPS3 executable baseline (S186)**: `tools/f_ops3_queue_aging.py` now replays READY-lane backlog dispatch with two policies (`recency_bias` vs `queue_aging`) under observed session capacity (`experiments/operations-research/f-ops3-queue-aging-s186.json`). Current window (`job_count=20`) is parity (`score=0.65` each), indicating insufficient backlog depth in the sampled horizon rather than a confirmed null effect.
- **F-OPS3 broader-window rerun (S186)**: reran with `--session-min 120 --stale-threshold 1` (`experiments/operations-research/f-ops3-queue-aging-s186-broad.json`) and revalidated tests (3/3). Backlog extraction still only spans `S184..S186` (`job_count=20`), so parity persists (`0.7` vs `0.7`); next OR step is explicit backlog-slice injection before policy conclusions.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Coordination overhead | L-216, L-258 | Throughput degrades when queue discipline and synchronization cost are unmanaged |
| Tail latency | L-251 | Parallelization can worsen latency variance when objective is completion-time max |
| Scheduling quality | L-257 | Strong sessions are clustered around explicit frontier targeting + low overhead |
| Automability economics | L-009, L-216 | Recurrent manual routing should migrate to tool-backed policy once setup cost is lower than repeated coordination overhead |

## Structural isomorphisms with swarm design

| OR finding | Swarm implication | Status |
|-----------|-------------------|--------|
| Higher WIP increases queue delay and context switching | Cap active lanes and enforce tighter objective boundaries | THEORIZED |
| Priority policy determines delivered value under fixed capacity | NEXT ordering must be tied to measured quality impact | OBSERVED |
| Explicit scheduling contracts improve automability | Prefer machine-consumable dispatch outputs and track override frequency | OBSERVED |
| Bottlenecks dominate throughput more than average capacity | Reduce hot-file and merge bottlenecks before adding agents | OBSERVED |
| Tail latency controls user-visible completion time | Track p95/p99 completion in addition to average output metrics | THEORIZED |

## What's open
- **F-OPS1**: determine WIP limits that maximize knowledge throughput.
- **F-OPS2**: validate the findings-driven schedule on independent-owner runs, compare realized quality/collision outcomes against prior hybrid/risk-first baselines, and track automability ratio (tool plan accepted without manual rewrite).

## Operations-research links to current principles
P-119 (spawn discipline) | P-190 (task clarity gate) | P-197 (high-yield session pattern)
