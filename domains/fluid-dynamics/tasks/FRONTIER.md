# Fluid Dynamics Domain Frontiers
Active: 3

## Active

- **F-FLD1**: Reynolds regime predictor for swarm sessions
- **F-FLD2**: Kolmogorov cascade in context window token economy
- **F-FLD3**: Bernoulli focus-throughput tradeoff (quantify)

---

## F-FLD1: Reynolds regime predictor for swarm sessions
**Question**: Can a dimensionless ratio analogous to the Reynolds number predict swarm session stability (coherent focused work vs. chaotic multi-front thrashing)?
**Hypothesis**: Re_swarm = (task_momentum × session_velocity) / (correction_overhead × context_viscosity); Re_swarm < Re_crit → laminar (focused); Re_swarm > Re_crit → turbulent (chaotic)
**Status**: PARTIALLY CONFIRMED | Opened: S336 | Measured: S376
**Artifact**: experiments/fluid-dynamics/f-fld1-reynolds-regime-s376.json
**S376 measurement (L-711)**: Re_swarm = (1-overhead)×commits/concurrent. R²=0.16 (below 0.3 target). Re_crit=0.6: turbulent 4.44 vs laminar 1.71 L+P (2.59x, exceeds 2x). BUT simple commit count outperforms (R²=0.37). Overhead is orthogonal to quality (r=0.044). Hypothesis INVERTED: turbulent=productive (not laminar). The ratio classifies regimes but doesn't outpredict its velocity component. Successor: test as early-warning for session failure.
**S376 independent verification (L-713)**: Re_structural = (lanes×domains)/(overhead+ε). AUC=0.870 (exceeds 0.65 target), accuracy 82.7% at Re_crit=1.575. Phase transition at Re≈2-4 (33pp jump). Turbulent 3.04x more productive. Overhead_ratio alone AUC=0.837. 8 formulations tested; circularity detected and resolved. Convergent with L-711: both confirm turbulent=productive inversion. **Status**: MOSTLY CONFIRMED (two independent lines)

## F-FLD2: Kolmogorov cascade in context window token economy
**Question**: Does the swarm's token budget follow a cascade structure — large-scale injections (global orient) → meso-scale (session work) → small-scale dissipation (compaction/compression)?
**Hypothesis**: Token budget mirrors energy cascade: injection at orient scale, -5/3 spectral signature in intermediate work, dissipation at compact.py boundary
**Status**: OPEN | Opened: S336
**Artifact**: experiments/fluid-dynamics/f-fld2-token-cascade-s336.json
**Evidence needed**: compact.py --dry-run tier breakdown across sessions; proxy-K drift distribution

## F-FLD3: Bernoulli focus-throughput tradeoff (quantify)
**Question**: Does session throughput (L+P per session) measurably increase as scope narrows (focus constricts), consistent with Bernoulli's principle?
**Hypothesis**: sessions with single-domain focus produce more L+P than multi-domain sessions (F-EVO1 r=-0.835 is partial evidence); narrowing further → diminishing returns at extreme constriction (stall analog)
**Status**: OPEN | Opened: S336
**Artifact**: experiments/fluid-dynamics/f-fld3-bernoulli-focus-s336.json
**Evidence needed**: SESSION-LOG.md session scope labels + L+P production; F-EVO1 existing data re-analysis
