# Statistics Domain Index
Updated: 2026-02-27 | Sessions: 186

## What this domain knows
- **Seed evidence base**: swarm runs many repeated experiments, but effect-size, confidence, and error-rate discipline are uneven across domains.
- **Core structural pattern**: swarm-of-swarms execution needs explicit inference rules so "promising signal" is distinguishable from noise.
- **Automability measurement need**: promotion and dispatch automation should only trigger when explicit effect-size/power/quality gates are met.
- **Active frontiers**: 3 active domain frontiers in `domains/statistics/tasks/FRONTIER.md` (F-STAT1, F-STAT2, F-STAT3).
- **Cross-domain role**: statistics is a shared measurement layer for AI, finance, health, information-science, brain, evolution, control-theory, game-theory, and operations-research runs.
- **S186 F-STAT1 baseline gate artifact**: `experiments/statistics/f-stat1-promotion-gates-s186.json` calibrated class gates from 39 usable artifacts — simulation (`n>=80`, `|effect|>=0.2442`), live-query (`n>=300`, `|effect|>=0.05`, practical cap), lane-log extraction (`n>=28`, `|effect|>=0.2195`).
- **S186 F-STAT2 pooled-evidence artifacts**: baseline `experiments/statistics/f-stat2-meta-analysis-s186.json` (21 studies) was inconclusive (`+0.0013`, CI95 `[-0.0401, +0.0428]`, `I2=29.1%`); slot-5 rerun `experiments/statistics/f-stat2-meta-analysis-s186-rerun.json` class-split FIN1 into direct/proxy families and stayed inconclusive over 26 studies (`-0.0162`, CI95 `[-0.0599, +0.0275]`, `I2=49.5%`).
- **S186 F-STAT3 multiplicity artifacts**: baseline `experiments/statistics/f-stat3-multiplicity-s186.json` found 1 corrected discovery with no promotable family; slot-5 rerun `experiments/statistics/f-stat3-multiplicity-s186-rerun.json` over the split meta set found 2 corrected discoveries and one provisional promotion candidate (`information_science_lane_distill`, replication_count=3).
- **Latest execution (S186)**: F-STAT1 now has four calibration views: experiment-family gates (`experiments/statistics/f-stat1-experiment-gates-s186.json`), CI/z-score replay gates (`experiments/statistics/f-stat1-promotion-gates-s186.json`), conservative cross-domain replay gates (`experiments/statistics/f-stat1-gates-s186.json`), and reporting-quality gates over active lanes (`experiments/statistics/f-stat1-reporting-quality-s186.json`). The latest broad-glob replay pass (39 usable / 73 considered) sets thresholds at simulation (`n>=80`, `|effect|>=0.2442`), live query (`n>=300`, `|effect|>=0.05`, practical cap; power-model target `n=1565`), and lane-log extraction (`n>=28`, `|effect|>=0.2195`). Reporting-quality now separates inferred vs explicit contract signals and includes full-history pickup A/B: inferred (`mean_score=1.0`, `contract_ready_rate=1.0`) but explicit (`explicit_mean_score=0.6`, `explicit_contract_ready_rate=0.0`), while current pickup cohorts (`schema_contract.count=10`, `free_form.count=18`) show no latency separation yet (`mean_delta_sessions_free_minus_schema=0.0`), so explicit score remains the canonical promotion gate.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Measurement discipline | L-223, L-257 | Explicit expectation + scored outcomes are prerequisites for credible adaptation |
| Variance and replication | L-253 | Repeated runs can separate stable effects from regime-sensitive effects |
| Coordination noise | L-258 | Process-mode changes can dominate outcomes unless controlled in analysis |
| Automability gating | `f-stat1-promotion-gates-s186.json`, `f-stat1-reporting-quality-s186.json` | Automation policies should be blocked until both evidence strength and contract quality exceed explicit thresholds |
| Promotion gating | `f-stat1-experiment-gates-s186.json`, `f-stat1-promotion-gates-s186.json`, `f-stat1-gates-s186.json` | Multiple gate derivations now exist; next statistical task is convergence to one canonical promotion policy with explicit conservatism and validation criteria |
| Reporting fidelity | `f-stat1-reporting-quality-s186.json` | Explicit `blocked`/`human_open_item` tags now cover active lanes, but explicit `progress`/`available`/`next_step` are still missing; promotion gates should stay explicit-score-first until full schema coverage is reached |

## Structural isomorphisms with swarm design

| Statistics finding | Swarm implication | Status |
|-------------------|-------------------|--------|
| Underpowered tests miss real effects | Domain experiments need trial sizing rules before claims are promoted | THEORIZED |
| Uncontrolled multiplicity inflates false positives | Frontier batches need false-discovery controls and stronger replication gates | OBSERVED |
| Pooling independent estimates improves confidence | Cross-domain/swarm aggregation should be default for transfer claims | THEORIZED |
| Prior assumptions shape conclusions | Belief confidence updates should explicitly track priors and evidence strength | OBSERVED |

## What's open
- **F-STAT1**: validate gate stability on post-S186 runs, separate mixed-regime pools (for example FIN1 proxy vs direct-answer scoring), and reconcile experiment-gate, power-replay, conservative replay, and reporting-quality baselines into one canonical promotion policy that enforces explicit contract fields (`available`, `blocked`, `next_step`, `human_open_item`), supports non-empty pickup-latency A/B cohorts, and emits an explicit automability gate score.
- **F-STAT2**: reduce heterogeneity in `information_science_lane_distill` (currently dominant and high-variance) with targeted non-tag/overlap-balanced replications before transfer-policy use.
- **F-STAT3**: validate the new provisional promotion candidate with independent replications and regime-isolated checks before treating it as promotion-ready policy evidence.

## Statistics links to current principles
P-182 (expect-act-diff loop) | P-190 (task clarity as execution gate) | P-197 (quality dimensions)
