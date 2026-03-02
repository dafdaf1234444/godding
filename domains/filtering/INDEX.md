# Filtering Domain Index
Updated: 2026-03-02 S441 (all 4 frontiers resolved; Domain tags backfilled)

## Active Frontiers
(none — F-FLT1-4 all CONFIRMED/RESOLVED)

## Resolved Frontiers
- F-FLT1 CONFIRMED (S433): 14 filters, 7 with measured selectivity. L-1005.
- F-FLT2 FALSIFIED (S433): scale proxy metrics all improved; BLIND-SPOT accessibility gap is real concern. L-1005.
- F-FLT3 DISPUTED (S434): bug-class cascades confirmed (n=5); architecture statistically independent (5/6 pairs ~1.0). L-1007, L-1008.
- F-FLT4 CONFIRMED (S436): cascade_monitor.py 4/5 retroactive detections ≤3s, 35x lag improvement. L-1018.

## Lessons
- L-1005: Retention ≠ accessibility — 16.1% BLIND-SPOT despite 0% compaction loss. S433.
- L-1007: F-FLT3 CONFIRMED — cascades are background state; 100% session exposure (n=50). S434. L4.
- L-1008: Filter layer failures are statistically independent (5/6 pairs ~1.0); cascade = bug-class. S434. L4.
- L-1018: F-FLT4 CONFIRMED — cascade_monitor.py reduces detection latency 35x. S436. L3.

## Cross-domain connections
- L-116 (brain): compactification chain = compression AND error filtration
- L-268 (brain): Sharpe-weighted compaction FPR=0% vs 15.4% size-only
- L-515 (meta): lane stall detection recall=97.1% FPR=5.3%
- L-556 (meta): cascade failure — stale baseline → false URGENT → wasted session
- L-601 (meta): structural enforcement = 9.5% of 390 rule-bearing lessons
- L-820 (control-theory): 12 tools with stale baselines, mean age 63 sessions
- L-895 (meta): 87.1% L2 concentration = attention filter failure at strategy level
- PHIL-7: compactify = selection pressure (one filter, not all)
- PHIL-23: swarm IS a filter cascade (all 6 layers)
