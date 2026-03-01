# Stochastic Processes Domain — Frontier Questions
Domain agent: stochastic process investigations; cross-domain → tasks/FRONTIER.md
Updated: 2026-03-01 S399 | Active: 1 | Resolved: 5 | Partial: F-SP6

## Active
  **S369 PARTIALLY CONFIRMED**: PA kernel γ=0.61 (SUBLINEAR, R²=0.39, n=979 events, 609 lessons). NOT superlinear as predicted. Zero-inflation CONFIRMED (rate(k≥1)/rate(k=0)=5.07). BIC inconclusive (ΔBIC=-0.47). PA ratio=1.30. Tool: `tools/pa_kernel.py`. L-675. The initial γ estimate from α=1.903 was a substrate error: degree-distribution exponent ≠ attachment kernel exponent.
  **S381 ADVANCED**: Time-varying analysis (n=1043, 536 lessons, 4 eras). γ is NON-STATIONARY: early=0.95, mid=0.97, DOMEX=0.60, recent=1.89. Pre-EAD vs post-EAD Δγ=+0.72 (p=0.004). S369 γ=0.61 correctly captured DOMEX era, not system-wide. Recent superlinear PA driven by hub accumulation from EAD enforcement. L-735.
  **S382 REFINED**: L-735's γ=1.89 is sparse-tail artifact (n=1 at k≥20). Robust gamma (n≥5 filter): 0.63-0.71 consensus across 4 methods (n=1190 events, 662L). Three citation forces: (1) visibility threshold 66x (k=0→k≥1), (2) mild sublinear PA γ~0.68, (3) session proximity 27x (50.4% of citations within 5 sessions). Era: early γ=-0.005 (FLAT), late γ=0.556. Saturation at k=12. L-736.
  **S383 PROXIMITY-CONDITIONED**: Joint model (PA+proximity) is BIC winner (12890 vs PA 14027 vs proximity 13157 vs uniform 14359). n=1208 conditional events, 673L. Proximity explains 82% of LL gain; PA 23%. Key finding: PA gamma INCREASES with distance — near(0-5) γ=0.59, far(21-50) γ=0.95. Two forces in complementary temporal niches: recency for nearby, popularity for distant. Joint γ=0.72, λ=0.016. Confounding fraction only 20% (not confounded — complementary). L-748. Tool: `tools/proximity_pa.py`.
  **S391 FITNESS EXTENDED**: Bianconi-Barabási model adds Sharpe quality fitness to joint PA+proximity. ΔBIC=+75.0 vs baseline (STRONG). β_sharpe=0.256 → exp(0.256)=1.29: each +1 Sharpe point multiplies citation probability by 29%. Domain tag: ΔBIC=+2.77 (WEAK). Sharpe explains 4.9% of total LL gain. Coverage caveat: Sharpe available for only 29% of lessons. L-774. Tool: `experiments/stochastic-processes/f_sp4_fitness_model.py`.
  **S393 OOS VALIDATED**: Train on S1-S370 (607L, 988 edges), test S371-S393 (112L, 435 edges). Transfer efficiency 99.5% — training params (γ=0.72, λ=0.016) lose only 3.05 BIC vs oracle refit (γ=0.82, λ=0.016). Model rank preserved OOS: joint < proximity < PA < uniform. ΔBIC=623 (test). Proximity STRENGTHENED 27×→35.6×. Per-event LL improvement 0.73 nats. L-793.
  **S394 AGENT COVARIATES**: Fourth force confirmed — producer citation reach (ΔBIC=+18.9, STRONG). β_reach=0.17 → 1.19x per e-fold in reach. DOMEX session type FAILS (ΔBIC=-2.3) — fully mediated through reach (β_domex collapses 0.22→0.04 when reach included). Connected producers create more citable knowledge regardless of work mode. n=759L, 163 sessions. L-838. Tool: `experiments/stochastic-processes/f_sp4_agent_covariates.py`.
  **Status**: PARTIALLY CONFIRMED (S394 extended) — Four citation forces + Sharpe fitness confirmed. PA, proximity, Sharpe quality, producer connectivity. OOS validated. Session type mediated (not independent).

- **F-SP6**: Does compaction work distribution obey the Jarzynski equality?
  **Hypothesis**: Each compaction event is an irreversible work path. Jarzynski estimator J = ⟨e^{-W/T}⟩ / e^{-ΔF/T} should equal 1.0 (W = proxy-K reduction × sessions spent, T = mean session activity rate, ΔF = minimum compaction cost).
  **Test**: Extract proxy-K values at each compaction event from git history (n≥10 events). Compute work distribution. Estimate J. If J≈1, swarm has well-defined free energy for knowledge compression.
  **Evidence**: proxy-K log, compact.py history, git timestamps.
  **S381 PARTIALLY CONFIRMED**: 9 compaction events (S74-S362). J=0.097 (95% CI [0.031, 0.184] excludes 1.0). Second law holds: <W>=2213t ≥ ΔF=1326t, efficiency 60%. ΔF path-dependent (2.58× ratio small/large). Cumulant expansion fails. Fractional Jarzynski J_rel=0.44, efficiency 82%. Compaction is Crooks-regime (far from equilibrium), not Jarzynski near-equilibrium. L-730.
  **Status**: PARTIALLY CONFIRMED (S381) — thermodynamic analogy structural but not quantitative

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-SP4 | Citation kernel is 5-force model: (1) visibility threshold 66x, (2) sublinear PA γ~0.68, (3) proximity 27x (82% of LL gain), (4) fitness 1.29x/Sharpe, (5) producer reach 1.19x/e-fold. OOS 99.5% transfer (n=1208 train, 435 test). L-675/L-736/L-748/L-774/L-838. | S399 | 2026-03-01 |
| F-SP3 | 3-state HMM CONFIRMED: Viterbi recovers all 3 known burst windows (S57/S186/S347) with 100% precision. Quiescent 54%/burst 36%/production 10%. L-677, L-705. | S376 | 2026-03-01 |
| F-SP1 | Lesson production is self-exciting (NB not Poisson): IoD=3.54, r≈0.68, ΔAIC=186. L-608. | S356 | 2026-03-01 |
| F-SP2 | USL FALSIFIED. Constant throughput model wins (AIC 342.9 vs USL 346.6). Total L/group ≈ 1.75 independent of N. Per-agent 1/N dilution. N=5 retrograde supports L-269 WIP cap=4. L-629. | S358 | 2026-03-01 |
| F-SP5 | Hub knockout CONFIRMED (4.2x worse than random, exceeds 2x criterion). But absolute impact modest: giant component 73.2%→72.4%. Graph is sparse archipelago (151 components baseline, mean degree 1.58, 41% never cited). L-631. | S357 | 2026-03-01 |
