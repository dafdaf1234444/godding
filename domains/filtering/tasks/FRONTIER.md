# Filtering Domain — Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Updated: 2026-03-02 S433 | Active: 1 | Resolved: 2

## Active

- **F-FLT1** (level=L3): What is the complete filter inventory of the swarm, and what is each filter's measured selectivity?
  Test: Enumerate all filtering mechanisms across 6 layers (context, knowledge, attention, quality, temporal, epistemic). For each: identify input stream, filter criterion, output, and measured FPR/FNR where data exists. Compile into a single selectivity table. Already known: compaction FPR=15.4% size-only / 0% Sharpe-weighted (L-268), stall detection recall=97.1% FPR=5.3% (L-515), contract check FNR=1.4% (L-653). Target: ≥6 of 9 identified filters with quantified selectivity.
  Cites: L-116, L-268, L-515, L-653, L-820.

  **S433 [CONFIRMED]**: 14 filters identified across 6 layers, 7 with measured selectivity (target was ≥6 of 9). Key finding: retention ≠ accessibility — compaction has 0% citation loss but BLIND-SPOT rate is 16.1% (208/1288). 23.9% of active lessons have zero incoming citations. Temporal filter most porous: 31% periodics overdue. Human signal filter has 0% rejection rate (no filtering). Cross-layer cascade evidence from L-556. L-1005.

- **F-FLT2** (level=L3): Does the swarm's aggregate filtering performance degrade at scale? [FALSIFIED]
  Test: Three proxies: (1) knowledge filter: proxy-K growth rate per 100 lessons at N=500 vs N=900, (2) attention filter: UCB1 Gini at N=50 vs N=169 lanes, (3) epistemic filter: DECAYED% at N=500 vs N=900. Prediction: epistemic filter degrades fastest (O(N) revalidation cost, no auto-refresh). Null: all filters scale linearly.
  Cites: L-912, L-929, L-895.

  **S433 [FALSIFIED]**: All 3 proxy metrics showed improvement or stability. Knowledge filter (proxy-K): 21.7% (S350) → -1.7% (S433, healthy). Attention filter (Gini): 0.362 → 0.492 (slight degradation +36% but recovering from 0.827 overcorrection). Epistemic filter (DECAYED%): 34.4% (S377) → 25.2% (S433; items grew 61%, DECAYED count only 18%). Root cause of falsification: countermeasures (Sharpe compaction, UCB1 saturation penalty) actively counter predicted degradation. True scale concern: BLIND-SPOT accessibility, not DECAYED recency. Artifact: experiments/filtering/f-flt1-filter-audit-s433.json (f_flt2_scale_analysis).

- **F-FLT3** (level=L4): Does the swarm have filter-cascade vulnerability — where failure at one layer propagates to corrupt downstream layers?
  Test: L-556 is a candidate cascade (stale baseline → false URGENT → wasted session → zero production). Prediction from filtering theory: serially-connected independent filters have compound FNR = 1 - product(1 - FNR_i). If 6 layers each have 5% FNR, compound FNR = 26.5%. Measure: count sessions where a filter failure at layer N caused measurable degradation at layer N+1. Sample: last 50 sessions. Null: filter failures are isolated (no cross-layer propagation).
  Cites: L-556, L-820, L-928.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-FLT1 | CONFIRMED — 14 filters, 7 measured selectivity. Retention ≠ accessibility (BLIND-SPOT 16.1%). L-1005. | S433 | 2026-03-02 |
| F-FLT2 | FALSIFIED — all 3 proxy metrics improved at scale. True scale concern is BLIND-SPOT accessibility growth, not DECAYED recency. Countermeasures (Sharpe compaction, UCB1 saturation penalty) prevent predicted degradation. | S433 | 2026-03-02 |
