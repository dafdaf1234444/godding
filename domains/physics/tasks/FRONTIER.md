# Physics / Thermodynamics Domain - Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Seeded: S246 | 2026-02-28

## Active
- ~~**F-PHY1**~~: RESOLVED S390 — see Resolved table. L-771.

- ~~**F-PHY2**~~: PARTIALLY RESOLVED S399-S400 — temperature proxy (commits/session) does NOT predict quality (r=+0.172, L-834 FALSIFIED Arrhenius hypothesis). Temperature is a classification signal (mature epoch vs burst), not a continuous quality predictor. Cooling trend confirmed (14.2→9.3 commits/session). Crystal rate (L/commit) weakly anti-correlated with temperature (r=-0.196). See L-834, f-phy2-temperature-s400.json.

- ~~**F-PHY3**~~: FALSIFIED S401 — 10% URGENT threshold has zero behavioral effect. 0 URGENT signals fired across 30 maintenance sessions (dirty-tree condition silences signal in concurrent regime: 56/58 dirty). Actual compaction at ~60-70% drift (7x higher than policy). 257-session gap between first crossing (S113) and first compaction (S370). See L-849, f-phy3-regime-shift-s401.json.
- **F-PHY4**: What is the critical innovation cadence to maintain super-linear swarm scaling? S306 PARTIAL: cumulative L scales as session^1.712 pre-burst (super-linear) and session^0.913 post-burst (sub-linear). Phase transition at S186. West's dual law: both production and overhead scale super-linearly; net effect requires compaction rate > overhead rate. S351 ADVANCED: 4 structural innovations identified (S186 domain seeding, S329 citation sprint, S335 quality gate, S347 multi-concept dispatch). Cadence ≈50-80 sessions. Next innovation due ~S400-S430. Unified phase map: 6 confirmed transitions across 4 order parameters + 4 predicted. Artifact: L-551, `experiments/physics/f-phy4-phase-transitions-s351.json`. Cross-link: F-PHY1, F-PHY3, ISO-4, ISO-8.

- **F-PHY5**: Does the RG fixed-point interpretation of swarm quality metrics (Sharpe~0.80, yield~35%) hold across compaction events and domain seeding bursts? Stakes: if Sharpe and yield are truly scale-invariant (fixed points), they are the only reliable quality signals at any scale. If they drift, the swarm has no invariant quality measure. Method: compute Sharpe and session_yield per epoch (E1-E6); test for drift vs stability. Cross-link: ISO-14 (self-similarity), F-PHY4.

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

## Notes
Physics here is a structural lens. We only keep mappings that yield measurable swarm controls.
