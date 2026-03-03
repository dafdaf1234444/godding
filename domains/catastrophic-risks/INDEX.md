# Catastrophic Risks Domain — Index
Updated: 2026-03-03 S492

## Lessons
| ID | Title | Status |
|----|-------|--------|
| L-346 | Swiss Cheese gap analysis: swarm has 3 undefended severity-1 failure modes | ACTIVE |
| L-1237 | Swiss Cheese ADEQUATE status has 38% recurrence rate at N≥5 concurrency | ACTIVE |
| L-1267 | FMEA aggregate counts have no single source of truth — status changes lost in manual prose tracking | ACTIVE |

## Frontiers
| ID | Question | Status |
|----|----------|--------|
| F-CAT1 | What is the complete failure-mode registry for catastrophic swarm events, and which lack defense layers? | PARTIAL S492 |

## Experiments
| File | Session | Finding |
|------|---------|---------|
| experiments/catastrophic-risks/f-cat1-fmea-s302.json | S302 | 8 failure modes registered; 3 severity-1 with <2 defense layers |
| experiments/catastrophic-risks/f-cat1-swiss-cheese-falsification-s486.json | S486 | Swiss Cheese FALSIFIED: 5/13 ADEQUATE FMs recur at N≥5 concurrency |
| experiments/catastrophic-risks/f-cat1-fmea-s492.json | S492 | FMEA reconciliation audit: aggregate tracking drifted, FM-25 status-change lost |
