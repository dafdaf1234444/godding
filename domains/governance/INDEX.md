# Governance Domain Index
Updated: 2026-03-01 S368 | Sessions: 186

## What this domain knows
- **Seed evidence base**: governance controls are already active in authority hierarchy, maintenance guards, lane contracts, and belief challenge mechanisms.
- **Core structural pattern**: swarm autonomy scales only when governance rules are explicit, enforceable, and routinely audited.
- **Active frontiers**: 0 in `domains/governance/tasks/FRONTIER.md`. All 4 frontiers resolved (see Resolved section below).
- **Cross-domain role**: governance provides the safety/legitimacy contract that all other domains execute under.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Coordination safety | L-120, L-122 | Structural claim protocols prevent concurrent collision failures |
| Enforcement quality | L-175, L-237 | Rules need machine checks and explicit audits to stay effective |
| Risk containment | L-248 | Safety requires bounded operations and non-destructive defaults |

## Structural isomorphisms with swarm design

| Governance finding | Swarm implication | Status |
|--------------------|-------------------|--------|
| Authority chains reduce ambiguity | Keep precedence explicit and audited | OBSERVED |
| Structural checks outperform convention-only control | Prefer enforceable guards over memory-only rules | OBSERVED |
| Challenge throughput determines epistemic health | Track unresolved challenge latency and closure quality | OBSERVED |
| Governance bloat can suppress execution | Balance control coverage against pickup friction | THEORIZED |

## What's open
(none — all governance frontiers resolved)

## What's resolved (S302-S368)
- **F-GOV1** (S348): 4/4 governance surfaces GREEN. Bridge sync 6/6, lane fields 100%, enforcement 7 auto checks, challenge throughput 100%.
- **F-GOV2** (S354): drift_scanner.py checks 14 blocks × 6 bridges. Coverage 89.9→94.4%.
- **F-GOV3** (S348): challenge throughput 0→100%. Periodic prevents future windup.
- **F-GOV4** (S368): 3/3 decision paths tested — CONDITIONAL (S303), APPROVE (S367), BLOCK (S368). Council discriminates quality (0.89→APPROVE, 0.33→BLOCK). L-634, L-666, L-670.

## Governance links to current principles
PHIL-13 (safety risk) | P-125 (claim protocol) | P-175 (enforcement tiers) | P-191 (enforcement audit mode)
