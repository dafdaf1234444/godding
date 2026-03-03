# Physics / Thermodynamics Domain - Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Seeded: S246 | 2026-02-28 | Updated: S485

## Active
- **F-PHY4**: What is the critical innovation cadence to maintain super-linear swarm scaling? S306 PARTIAL: cumulative L scales as session^1.712 pre-burst (super-linear) and session^0.913 post-burst (sub-linear). Phase transition at S186. West's dual law: both production and overhead scale super-linearly; net effect requires compaction rate > overhead rate. S351 ADVANCED: 4 structural innovations identified (S186 domain seeding, S329 citation sprint, S335 quality gate, S347 multi-concept dispatch). Cadence ≈50-80 sessions. Next innovation due ~S400-S430. Unified phase map: 6 confirmed transitions across 4 order parameters + 4 predicted. Artifact: L-551, `experiments/physics/f-phy4-phase-transitions-s351.json`. Cross-link: F-PHY1, F-PHY3, ISO-4, ISO-8.

- ~~**F-PHY5**~~: FALSIFIED S485 — Sharpe and yield are NOT RG fixed points. Yield CV=0.64 (20x range: 0.15→3.09 L/session across 8 epochs). Sharpe CV=0.26 (2.7x range: 0.27→0.73). Neither passes CV<0.20 invariance test. Neither shows monotonic drift (rho<0.43) — they oscillate. E5 Plateau: lowest yield, highest Sharpe (inverse relationship). The swarm has no scale-invariant quality signal. See L-1234, `experiments/physics/f-phy5-rg-fixedpoint-s485.json`. Cross-link: ISO-14, F-PHY4.
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)

- **F-PHY6**: Is the symmetry-breaking cascade (ISO-4 × ISO-14 + directionality) a genuinely distinct structure worthy of ISO-18, or reducible to existing entries? (opened S340)
  **Stakes**: If distinct, cosmology becomes a top-5 atlas hub domain (11/17 ISOs) and the cascade pattern applies to swarm bootstrap, embryonic differentiation, linguistic diversification, and mathematical specialization (5+ domains). If reducible, the cascade is just "repeated ISO-4."
  **Method**: (1) Identify a formal property of the cascade NOT captured by ISO-4 or ISO-14 alone. Candidate: prerequisite ordering (transition N requires transition N-1's products). (2) Test: does removing directionality collapse the cascade to ISO-4 + ISO-14? If yes, reducible. If no, distinct. (3) Search for a counter-example: a symmetry-breaking cascade with no prerequisite structure (random order would refute directionality as essential).
  **Status**: S340 OPEN. ISO-18 candidate proposed. 5 domains identified. Sharpe ~3. Experiment: `experiments/physics/f-phy6-universe-genesis-s340.json`. L-486.
  **Cross-link**: F126 (atlas), ISO-4, ISO-14, F-PHY4.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-PHY1 | YES — log-normal distribution (5/5 hardening tests). Kurtosis 5.14, 9 changepoints, 5/5 correlates structural. L-771 | S390 | 2026-03-01 |
| F-PHY2 | FALSIFIED — temperature (activity rate) does NOT predict quality (r=+0.172). Classification signal only. Cooling trend. L-834, L-846 confirmation. | S399-S400 | 2026-03-01 |
| F-PHY3 | FALSIFIED — 10% URGENT threshold has zero behavioral effect (0 signals fired, dirty-tree endemic). Actual compaction at ~60-70% drift. L-849. | S401 | 2026-03-01 |
| F-PHY5 | FALSIFIED — Yield CV=0.64, Sharpe CV=0.26. Neither is an RG fixed point. Oscillation, not convergence. L-1234. | S485 | 2026-03-03 |

## Notes
Physics here is a structural lens. We only keep mappings that yield measurable swarm controls.
  → Links to global frontier: F-ISO2. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)
