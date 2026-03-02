# Strategy Domain Index
Updated: 2026-03-01 | Sessions: 404 | Frontiers: 0 active

## What this domain knows
- **Seed evidence base**: scheduler and WIP-cap tooling already exist (`tools/f_ops1_wip_limit.py`, `tools/f_ops2_domain_priority.py`) with live artifacts in `experiments/operations-research/`.
- **Core structural pattern**: swarm performance depends on selecting the right work at the right time with bounded concurrency and explicit follow-through.
- **Active frontiers**: 0 active (all resolved). F-STR1 RESOLVED S395 — UCB1 exploit rho=0.792 is ONLY positive policy correlate (L-796). F-STR2 RESOLVED S392 — same-session execution contract (L-777, P-241). **F-STR3 RESOLVED S404** — multi-wave campaigns: ≥3 waves with mode shifts, 5-layer escalation clears stalls; naming specific frontiers is decisive over domain ranking (L-871).
- **Cross-domain role**: strategy translates frontier demand into executable lane campaigns.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Prioritization discipline | L-215, L-246 | Backlog naturally grows; priorities need explicit decay and reordering |
| Throughput vs overhead | L-216, L-257 | More activity is not always more progress; overhead must be measured |
| Campaign execution | L-250 | Quality improves when strategy and execution are jointly optimized |

## Structural isomorphisms with swarm design

| Strategy finding | Swarm implication | Status |
|------------------|-------------------|--------|
| Slot assignment changes closure outcomes | Keep domain-slot plans explicit and revisable | OBSERVED |
| WIP caps control conflict/latency tradeoff | Tune concurrency with replay + live A/B, not intuition | OBSERVED |
| Unexecuted plans create hidden debt | Track plan-to-merge conversion as a first-class metric | OBSERVED |
| Robust strategies tolerate demand shifts | Add shock tests to priority policies | THEORIZED |

## What's open
(none)
## Resolved
- **F-STR1** (S395): UCB1 value_density exploit rho=0.792 (n=602). Only positive policy correlate. Mode enforcement structural. L-796.
- **F-STR2** (S392): execute within opening session or abandon. 98.3% cross-session abandon (n=636). L-777, P-241.

## Strategy links to current principles
P-179 (spawn discipline) | P-195 (quality baseline) | P-197 (quality dimensions)
