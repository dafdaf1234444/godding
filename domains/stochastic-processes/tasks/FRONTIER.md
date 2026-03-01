# Stochastic Processes Domain — Frontier Questions
Domain agent: stochastic process investigations; cross-domain → tasks/FRONTIER.md
Updated: 2026-03-01 S381 | Active: 3 | Resolved: 3 | Partial: F-SP4 (advanced), F-SP6

## Active

- **F-SP3**: Is the 4-phase meta-cycle an HMM with phase-specific entropy rates?
  **Hypothesis**: 4-state HMM (accumulation/burst/integration/convergence) with distinct emission profiles. Burst phases have 3-5× the entropy rate of convergence phases. HMM recovers the 3 known burst points (S57, S186, S347) independently.
  **Test**: Define emissions per session (lessons_created, principles_created, frontiers_resolved, proxy_K_delta). Fit 4-state HMM via Baum-Welch. Viterbi decode. Check burst-point recovery. Compare stationary distribution to empirical phase fractions.
  **Evidence**: SESSION-LOG.md, proxy-K log, frontier resolution dates.
  **S370 PARTIALLY CONFIRMED**: 3-state HMM wins BIC (443.5 vs 490.0 for 4-state, n=175). Three phases: quiescent (53%), production (29%), burst (18%). Burst entropy 11.4x production (exceeds 3-5x). L-677.
  **S376 CONFIRMED**: Viterbi decode (n=375) recovers all 3 known burst windows exactly: S57 (in S1..S69 cluster), S186 (in S178..S189), S347 (in S335..S352). 12 burst clusters identified. Precision 100%. Binary operation pattern: quiescent 54%/burst 36%/production 10%. L-705.
  **Status**: CONFIRMED (S376) — 3-state HMM validated by independent burst recovery

- **F-SP4**: What is the citation preferential attachment kernel?
  **Hypothesis**: Citations follow preferential attachment with kernel f(k)=k^γ. Measured α=1.903 implies γ≈1.3-1.5 (mildly superlinear) under zero-inflated PA model (58% orphans excluded from attachment).
  **Test**: Build citation DAG. For each lesson L_n, record in-degrees of all prior lessons. Estimate f(k) non-parametrically. Fit 3 models: pure PA, shifted PA, zero-inflated PA. Compare BIC.
  **Evidence**: Cites: fields in all L-NNN.md files.
  **S369 PARTIALLY CONFIRMED**: PA kernel γ=0.61 (SUBLINEAR, R²=0.39, n=979 events, 609 lessons). NOT superlinear as predicted. Zero-inflation CONFIRMED (rate(k≥1)/rate(k=0)=5.07). BIC inconclusive (ΔBIC=-0.47). PA ratio=1.30. Tool: `tools/pa_kernel.py`. L-675. The initial γ estimate from α=1.903 was a substrate error: degree-distribution exponent ≠ attachment kernel exponent.
  **S381 ADVANCED**: Time-varying analysis (n=1043, 536 lessons, 4 eras). γ is NON-STATIONARY: early=0.95, mid=0.97, DOMEX=0.60, recent=1.89. Pre-EAD vs post-EAD Δγ=+0.72 (p=0.004). S369 γ=0.61 correctly captured DOMEX era, not system-wide. Recent superlinear PA driven by hub accumulation from EAD enforcement. L-735.
  **Status**: PARTIALLY CONFIRMED (S381 advanced) — kernel is time-varying, not a fixed parameter

- **F-SP6**: Does compaction work distribution obey the Jarzynski equality?
  **Hypothesis**: Each compaction event is an irreversible work path. Jarzynski estimator J = ⟨e^{-W/T}⟩ / e^{-ΔF/T} should equal 1.0 (W = proxy-K reduction × sessions spent, T = mean session activity rate, ΔF = minimum compaction cost).
  **Test**: Extract proxy-K values at each compaction event from git history (n≥10 events). Compute work distribution. Estimate J. If J≈1, swarm has well-defined free energy for knowledge compression.
  **Evidence**: proxy-K log, compact.py history, git timestamps.
  **S381 PARTIALLY CONFIRMED**: 9 compaction events (S74-S362). J=0.097 (95% CI [0.031, 0.184] excludes 1.0). Second law holds: <W>=2213t ≥ ΔF=1326t, efficiency 60%. ΔF path-dependent (2.58× ratio small/large). Cumulant expansion fails. Fractional Jarzynski J_rel=0.44, efficiency 82%. Compaction is Crooks-regime (far from equilibrium), not Jarzynski near-equilibrium. L-730.
  **Status**: PARTIALLY CONFIRMED (S381) — thermodynamic analogy structural but not quantitative

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-SP1 | Lesson production is self-exciting (NB not Poisson): IoD=3.54, r≈0.68, ΔAIC=186. L-608. | S356 | 2026-03-01 |
| F-SP2 | USL FALSIFIED. Constant throughput model wins (AIC 342.9 vs USL 346.6). Total L/group ≈ 1.75 independent of N. Per-agent 1/N dilution. N=5 retrograde supports L-269 WIP cap=4. L-629. | S358 | 2026-03-01 |
| F-SP5 | Hub knockout CONFIRMED (4.2x worse than random, exceeds 2x criterion). But absolute impact modest: giant component 73.2%→72.4%. Graph is sparse archipelago (151 components baseline, mean degree 1.58, 41% never cited). L-631. | S357 | 2026-03-01 |
