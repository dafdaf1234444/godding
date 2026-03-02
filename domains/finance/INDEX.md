# Finance Domain Index
Updated: 2026-02-27 | Sessions: 186

## What this domain knows
- **1 finance-adjacent lesson** confirmed: L-225 (blackboard info-asymmetry audit — adverse selection isomorphism)
- **Key beliefs**: B-FIN1 (diversification benefit, PARTIALLY CONFIRMED), B-FIN2 (systematic vs idiosyncratic error, OBSERVED), B-FIN3 (lesson Sharpe, OBSERVED)
- **Active frontiers**: 1 active domain frontier in `domains/finance/tasks/FRONTIER.md` (F-FIN1)
- **S186 factual-QA state**: perturb_rate=0.4 live run (`experiments/finance/f-fin1-factual-qa-s186.json`) shows small mean gain (+0.0833; 0.2500 vs 0.1667) with unchanged variance (ratio 1.0); low-noise rerun (`f-fin1-factual-qa-s186-rerun20-p0.json`) shows mean neutral/slightly negative but variance reduction (ratio 0.6328). Direct-answer hardening rerun (`f-fin1-factual-qa-direct-rerun-s186.json`, 8 trials, perturb_rate 0.25) raises absolute accuracy (N1 0.7604, N3 0.7500) while revealing high shared-error coupling (pairwise agreement 0.9653), with variance suppression but no mean gain. New CI-backed direct rerun (`f-fin1-factual-qa-direct-rerun20-s186.json`, 20 trials, perturb_rate 0.25) is statistically inconclusive on mean delta (N3-N1 `+0.0041`, bootstrap CI95 `[-0.0083, +0.0167]`) and shows variance increase (ratio `1.8939`) under persistent shared errors.

## Lesson themes

| Theme | Key lessons | Core insight |
|-------|-------------|--------------|
| Information asymmetry | L-225, L-220 | Dark blackboard files = adverse selection; unread written state = private information asymmetry that degrades coordination |
| Variance reduction | — (open) | Parallel spawning should reduce per-session variance without sacrificing mean accuracy; analogous to portfolio diversification |
| Risk decomposition | — (open) | Structural defects propagate (systematic); per-agent errors average out (idiosyncratic); different defenses required |

## Structural isomorphisms with swarm design

| Finance finding | Swarm implication | Status |
|----------------|-------------------|--------|
| Diversification reduces variance, not mean | Spawn multiple uncorrelated agents when variance matters (not just speed) | THEORIZED |
| Systematic risk is non-diversifiable | Fix CORE.md and structural defects first — spawning more agents doesn't help | OBSERVED (F-FIN2, S183) |
| Information asymmetry causes market failure | Dark files cause coordination failure (same root cause as L-220 MAS bottleneck) | OBSERVED (L-225) |
| Sharpe ratio: risk-adjusted return | Compress low-Sharpe lessons (low citation rate / high line count) first | OBSERVED (F-FIN3, S181) |

## What's open
- **F-FIN1**: CI-backed >=20-trial direct-answer rerun is complete and currently inconclusive; next step is targeted false-positive filtering (`Closed-ended question`, `The New Capital`, `Delhi`) followed by another >=20-trial rerun to test whether coupling and variance inflation drop.

## Finance domain principles (in `memory/PRINCIPLES.md`)
P-172 (cross-variant convergence = BFT, OBSERVED) | P-119 (spawn threshold at >45% sequential degradation) | P-059 (parallel for exploration, sequential for synthesis)
