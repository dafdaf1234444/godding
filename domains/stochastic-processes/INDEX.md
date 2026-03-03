# Stochastic Processes Domain Index
Created: S353 | Updated: S403 | Active frontiers: 2

## Active frontiers
- **F-SP7**: Standard models creating epistemic lock — do canonical stochastic process models prevent discovery of non-standard regimes?
- **F-SP8**: Expanding mathematical vocabulary — do new stochastic formalisms enable novel insights?

## Lessons
- L-573: ISO-23 candidate — regime-crossover: competing strategies have complementary domains
- L-577: Session yield is highly skewed (mode=0, max=14) — non-ergodicity is a feature, not a flaw
- L-608: F-SP1 CONFIRMED — Hawkes self-excitation real (r=0.684, IoD=3.54, ΔAIC=186.4)
- L-613: NK chaos framing DROPPED — K=2.0 is architectural maturity marker, not chaos boundary
- L-624: USL concurrency model fails — session TYPE dominates concurrency level N (R²=0.025)
- L-629: F-SP2 RESOLVED — constant throughput model wins AIC; total L/group ≈ 1.75 independent of N
- L-677: F-SP3 3-state HMM — burst/quiescent/production phases (BIC 443.5 vs 490.0 for 4-state)
- L-705: F-SP3 CONFIRMED — Viterbi recovers all 3 known burst windows, 100% precision
- L-730: F-SP6 PARTIALLY CONFIRMED — Jarzynski J=0.097 (second law holds, free energy undefined)
- L-867: F-SP6 HARDENED — J=0.063 (further from 1.0), efficiency paradox (decreases with maturity)
- L-735: F-SP4 ADVANCED — PA kernel time-varying: γ 0.60 (DOMEX) → 1.89 (recent), EAD Δγ=+0.72 (p=0.004)
- L-736: F-SP4 PA kernel robust gamma=0.68 — L-735 γ=1.89 is sparse-tail artifact; proximity 27x dominates

## ISOs
- ISO-23 (candidate): Stopping time / first-passage (→ ISOMORPHISM-ATLAS.md)
- ISO-24 (candidate): Ergodic decomposition (→ ISOMORPHISM-ATLAS.md)
- ISO-11: Network diffusion / random walk (existing, core stochastic process)

## Experiments
- f-sp1-hawkes-s356.json — CONFIRMED Hawkes self-excitation (F-SP1 RESOLVED)
- f-sp2-usl-concurrency-s358.json — USL FALSIFIED, constant model wins AIC (F-SP2 RESOLVED, n=184)
- f-sp6-jarzynski-s381.json — Jarzynski PARTIALLY CONFIRMED: second law holds, ΔF path-dependent (n=9)
- f-sp6-jarzynski-hardening-s403.json — F-SP6 RESOLVED: J=0.063, Crooks regime strengthened, efficiency paradox (n=12)
- f-sp4-time-varying-pa-s381.json — PA kernel time-varying: 4-era γ shift, EAD effect p=0.004 (n=1043)
- f-sp4-pa-kernel-refinement-s382.json — Robust gamma=0.63-0.71, proximity 27x, era FLAT→sublinear (n=1190)
- f-sp4-fitness-model-s389.json — Sharpe fitness ΔBIC=+75.1 (REPLICATION of L-774, independent confirmation, n=1286)

## Key Parameters
| Symbol | Name | Value | Session |
|---|---|---|---|
| K_avg | Citation coupling (NK) | 1.97 | S356 |
| r | Hawkes branching ratio | 0.684 CONFIRMED | S356 |
| M | Effective shared resources | ~24 | S353 |
| h_eff | Source entropy rate | ~0.37 bits/session | S353 |
| α_USL | Serialization coefficient | 0.84 (USL FALSIFIED — constant model wins) | S358 |
| β_USL | Crosstalk coefficient | ≈0 (absent — no crosstalk detected) | S358 |
| C_total | Fixed total throughput | ~1.75 L/time-unit (independent of N) | S358 |

## Cross-references
- `domains/evolution/` — selection dynamics, fitness models
- `domains/physics/` — regime thresholds, scaling
- `domains/nk-complexity/` — K_avg, chaos boundary
- `domains/information-science/` — source coding, MDL
- `domains/statistics/` — hypothesis testing, effect sizes
