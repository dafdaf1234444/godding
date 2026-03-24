# Domain: Forecasting
Adjacent: finance, statistics, stochastic-processes, operations-research
Topic: Real-world prediction, calibration measurement, and external grounding through testable forecasts about markets, technology, and world events.
Beliefs: B1, B4 (forecasting-adjacent core beliefs)
Lessons: (none yet -- domain is newly created)
Frontiers: F-FORE1, F-FORE2
Experiments: experiments/strategy/
Load order: CLAUDE.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/FRONTIER.md

## Domain filter
Only forecasting work with externally verifiable outcomes qualifies. Qualification requires: a prediction with a concrete resolution date, a measurable outcome that does not depend on swarm internals, and a scoring method (Brier score, log score, or calibration curve).

## Core isomorphisms

| Forecasting concept | Swarm parallel | Isomorphism type | Status |
|---------------------|----------------|------------------|--------|
| Calibration | Expect-act-diff cycle accuracy | Prediction-outcome alignment | OBSERVED |
| Brier scoring | Pre-registered expectations vs outcomes | Probabilistic accuracy | THEORIZED |
| Base rate neglect | Swarm predictions without reference classes | Cognitive bias in forecasting | THEORIZED |
| Superforecasting | Iterative updating with evidence | Bayesian belief revision | THEORIZED |
| Prediction markets | Steerer cross-challenges as market mechanism | Information aggregation | THEORIZED |

## Isomorphism vocabulary
ISO-5 (feedback -- stabilizing): calibration feedback -- prediction errors feed back to update models; overconfidence and underconfidence self-correct with scoring
ISO-2 (selection -- attractor): prediction method selection -- accurate methods survive; inaccurate methods decay; Brier score as fitness function
ISO-7 (emergence): collective forecasting -- aggregated predictions outperform individual predictions; wisdom of crowds as emergence
ISO-13 (integral windup): prediction accumulation -- unresolved predictions accumulate without resolution; stale forecasts as unreleased windup

## Key assets
- PRED-0001..0008: 8 market predictions (existing, from finance-external directive)
- SIG-77: finance signal from human directive
- F-COMP1: external output frontier (swarm's first external-grounding domain)
- tools/human_impact.py: benefit ratio tracking (external evaluation mechanism)
