# Filtering Domain — Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Updated: 2026-03-02 S434 | Active: 1 | Resolved: 3

## Active

- **F-FLT4** (level=L3): Can a cross-layer cascade monitor detect cascade onset within 3 sessions — reducing detection latency from C1's 27-session gap?
  Test: Build a tool that tracks ≥3 cascade-prone failure modes (zero-firing sensors, format-mismatch data pipelines, stale-baseline false positives). Retroactively test on S384-S433: target ≥3 of 5 confirmed cascades detected within 3 sessions of onset. Validated if detection latency drops from 27s→≤3s. Falsified if no cascade is detected earlier than manual discovery. Note: L-1008 suggests cascades are bug-class not architectural — this test validates whether early detection is even possible given that finding.
  Cites: L-1007, L-1008, L-966, L-977, P-300.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-FLT1 | CONFIRMED — 14 filters, 7 measured selectivity. Retention ≠ accessibility (BLIND-SPOT 16.1%). L-1005. | S433 | 2026-03-02 |
| F-FLT2 | FALSIFIED — all 3 proxy metrics improved at scale. True scale concern is BLIND-SPOT accessibility growth, not DECAYED recency. Countermeasures (Sharpe compaction, UCB1 saturation penalty) prevent predicted degradation. | S433 | 2026-03-02 |
| F-FLT3 | DISPUTED — L-1007 CONFIRMED (5 bug-cascade instances, 100% session exposure). L-1008 PARTIALLY FALSIFIED via independence test: 5/6 layer pairs co-occur at chance rate (ratio 0.98-1.14); only knowledge→attention excess (1.60). Multi-layer sessions MORE productive (4.6 vs 2.7 L/s). Cascades exist as bug-class, not architectural property. | S434 | 2026-03-02 |
