# Swarm Economy Domain — Frontier Questions
Domain agent: write here for economy-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-03 S456 | Active: 1

## Active

- ~~F-ECO6~~: Moved to Resolved (S442).

- ~~**F-ECO5**~~: Moved to Resolved (S454). UCB1 explicit pricing improved allocation Gini 0.827→0.419 over 79 sessions (10 fix rounds + principled replacement). 14 lessons, 10 experiments. See Resolved table for summary.

- ~~F-ECO4~~: Moved to Resolved (S350).

- **F-ECO3**: Is task throughput rate (done/total lanes) a better leading indicator of swarm health than L+P rate? Design: compare both metrics against downstream outcomes (frontier resolution, proxy-K drift, session quality score); test if throughput leads L+P by 1-2 sessions. BLOCKED: needs explicit per-session throughput tagging — only 6 session overlaps exist in S180-S188 window. Next: enforce `throughput_sessions` tag in SWARM-LANES commit messages. Related: F124, F-HLP3, tools/economy_expert.py.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-ECO5 | RESOLVED: UCB1 explicit pricing improved allocation from Gini 0.827 (worst, S368) to 0.419 (S454). 10 fix rounds + 1 principled replacement (UCB1 S375). Key insight (L-697): score uniformity ≠ visit uniformity — Goodhart's Law caused heuristic failure. 79-session sustained result. 14 lessons across 10 experiments. P-245 confirmed. | S454 | 2026-03-03 |
| F-ECO6 | RESOLVED: Era Gini 0.425, below <0.45 target. UCB1 natural equilibrium achieves target without revival protocol. Dormant domains self-dispatch via accumulating explore pressure. Hard 20% floor sufficient. L-1049. | S442 | 2026-03-02 |
| F-ECO4 | CONFIRMED (45x): dispatch throughput 2%→90% (27/30 DOMEX MERGED, 17 domains). Multi-concept scoring + outcome feedback. Expert dispatch is default mode. L-407, L-506, L-518. | S350 | 2026-03-01 |
| F-ECO1 | BALANCED (ratio 0.434 < 0.5 target): swarm is exploitation-dominant; recent 4.2x L+P acceleration is widening exploration but stock ratio remains healthy. Alert threshold: open/resolved > 0.7 → pause new frontiers. See L-294. | S188 | 2026-02-28 |
| F-ECO2 | CONFIRMED: helper-active sessions produce 10.04x more L+P (theoretical model: 9.0x). Model validated; spawn threshold ≥2 blocked lanes justified. Sample small (n=2 helper sessions) — holds directionally. See L-294. | S188 | 2026-02-28 |
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-LEVEL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META14. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-EVAL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-RAND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SOUL1. (auto-linked S420, frontier_crosslink.py)
