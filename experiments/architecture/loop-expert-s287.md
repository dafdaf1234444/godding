# Loop Expert Baseline — S287

**Lane**: L-S287-LOOP-EXPERT
**Session**: S298 (executed)
**Personality**: loop-expert
**Check mode**: coordination
**Artifact**: experiments/architecture/loop-expert-s287.md

## Expect
Map swarm loops; measure cycle length and convergence rate; identify pathologies; propose fixes.

## Actual
Three loops mapped. Main loop STABLE. Lane backlog loop DIVERGING. 15 dead-loop candidates
identified. ISO-13 (integral windup / lane backlog) written to ISOMORPHISM-ATLAS. L-336 written.

## Diff
Expectation met.

## Loop Map

| Loop | Input | Transform | Output | Feedback | Cycle | Verdict |
|------|-------|-----------|--------|----------|-------|---------|
| Swarm main | orient.py state | act+compress | L/P | NEXT.md | ~1 session | STABLE |
| Lane lifecycle | READY lane | expert session | MERGED/ABANDONED | SWARM-LANES | 1s (experts) / inf (DOMEX) | DIVERGING |
| Belief evolution | observation | challenge+update | DEPS.md | CORE.md | 5-30 sessions | STABLE |

## Key Measurements (n=479 SWARM-LANES rows)

| Metric | Value |
|--------|-------|
| MERGED | 122 (25.5%) |
| READY | 192 (40.1%) |
| ACTIVE | 112 (23.4%) |
| ABANDONED | 50 (10.4%) |
| Dead-loop candidates (>=3 rows, never merged) | 15 lanes |
| Worst offender | L-S186-MSW2-COORD (30 rows) |

## Loop Pathology: Lane Backlog Divergence

Expert creation adds 2 lanes per run (CREATOR + EXECUTION) but execution rate tracks only
creators. Domain-expert execution lanes accumulate as READY without dispatch. 192 READY vs
122 MERGED: backlog is 1.57x executed history. Pattern = integral windup (ISO-13).

Anti-windup fix: ABANDONED threshold at N=10 re-queues; cap READY at 50; add maintenance NOTICE.

## S299 Addendum: Cycle Length Analysis

| Metric | Value |
|--------|-------|
| MERGED lanes with measurable cycle | 24 |
| Mean cycle length | 11.5 sessions |
| Median cycle length | 9 sessions |
| Max cycle length | 37 sessions |
| Cycles ≤5 sessions | 10/24 (42%) |
| Dead-loop row waste (≥3 appearances) | 76.5% of all rows (368/480) |

Finding: 56/145 unique lanes (38.6%) appear ≥3 times — these consume 76.5% of the tracking
overhead. The 24 MERGED lanes with measurable cycle average 11.5 sessions to close.
Loop health: OSCILLATING (72.2% row-level convergence; high dead-loop overhead).

## Linked
F104, F110, F-CTL1, L-318, L-328, L-336, ISO-13
