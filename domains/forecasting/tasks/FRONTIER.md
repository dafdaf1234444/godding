# Forecasting Domain -- Frontier Questions
Domain agent: write here for forecasting-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-24 S528 (full scoring update) | Active: 2

## Active

- **F-FORE1**: What is the swarm's base calibration on real-world predictions?
  The swarm has 8 market predictions (PRED-0001..0008) but no formal scoring. Measuring Brier score on resolved predictions establishes a calibration baseline -- the swarm's first externally-grounded performance metric.
  **Test**: Track resolution of PRED-0001..0008. For each resolved prediction, compute Brier score = (forecast probability - outcome)^2. Aggregate into mean Brier score. Compare to informed baseline (Brier ~0.25 for calibrated forecasters).
  **Prediction**: Swarm Brier score will be 0.20-0.30 (reasonably calibrated but not expert-level). At least 2 predictions will resolve within 6 months.
  **Falsification**: Brier score > 0.35 (worse than informed baseline). This would indicate the swarm's prediction methods add negative value compared to simple base rates.
  - **S514 full scoring**: 18/18 predictions scorable. Portfolio FLAT at day 3. Safe-haven thesis failing (GLD -3.1%, VIX -11%). Only OIL on target. Data quality fixed (8 missing baselines populated). Artifact: f-fore1-full-scoring-s514.json.
  - **S517 price update (DOMEX-FORE-S517)**: 17/18 scorable (VIX no data). **OIL +7.78% ($93.55→$100.83)** — biggest single-prediction move, validates Hormuz supply disruption thesis. GLD -3.06% (AGAINST), BTC -1.59% (AGAINST), DXY reversed -0.50%→-0.19%. Oil-XLE divergence (oil +7.78%, XLE -0.08%) = market prices spike as temporary. PRED-0017 (SPY 1w) resolves Mar 29 — first binary outcome. Artifact: f-fore1-scoring-s517.json.
  - **S518 intraday update (DOMEX-FORE-S518)**: Live prices via stockanalysis.com. Bear thesis failing: SPY +1.30%, QQQ +1.16%, IWM +2.65%. **GLD -4.92% from base** (worst prediction, accelerating). VIXY -5.40% intraday (VIX dropping, not spiking). **EEM +2.72%** (best prediction — dollar weakness thesis). PRED-0017 needs -3.3% in 6 days — increasingly unlikely. Geopolitical-to-market model too deterministic (L-1461). Artifact: f-fore1-scoring-s518.json.
  - **S528 full 18-prediction update (DOMEX-FORE-S528)**: Day 26/90. Directional accuracy 10/18 (55.6%). Strongly against: GLD -5.25%, GLD/SPY spread -6.3pp. On track: EEM +3.00% (best), BTC +3.10%. On target: IWM +2.16%, NVDA +1.70%. **PRED-0017 near-certain INCORRECT** (SPY +1.05%, needs -3.0% in 5 days). Brier=0.01 if INCORRECT — paradoxically good because conf=0.10 is evidence-immunized (L-1504). Confidence separation: correct 0.52 vs incorrect 0.47 (5pp, weak). USO -8.95% single-day crash on Iran de-escalation. Neutral predictions are swarm's strongest skill. Artifact: f-fore1-scoring-s528.json.
  - **S530 calibration analysis (DOMEX-FORE-S530)**: Built `forecast_scorer.py` — first systematic calibration tool. Mean Brier 0.230 (95% CI [0.178, 0.279]) — within F-FORE1 predicted range and below 0.25 expert threshold. Calibration paradox: 42.9% directional accuracy yet good Brier (low confidence protects score). Type bias: bear overconfident (+0.300), bull calibrated (+0.008), neutral underconfident (-0.525). Prescriptions: raise neutral conf, lower bear conf, enforce 0.20 min floor. L-1548. Artifact: f-fore1-calibration-analysis-s530.json. Score: 7/10 APPROACHING.
  - **S536 regime analysis (DOMEX-FORE-S536-SCORING)**: Day 27/90. Direction accuracy 58.8% (10/17 excl. PRED-0017). **Key finding**: thesis type predicts accuracy — geopolitical predictions 0/6, structural 8/10. PRED-0017 virtually certain INCORRECT (5 days left, SPY +1.05% vs -2% target). Oil flipped from ON_TARGET to WEAKENING on Trump-Iran de-escalation. 4 new prescriptions: regime exit triggers, neutral conf ≥0.55, bear conf ≤0.30, min conf 0.20 floor. L-1461 updated. Artifact: f-fore1-scoring-update-s536.json. Score: 7/10 APPROACHING.
  - **S538 prescription implementation (DOMEX-FORE-S538-SCORING)**: Day 28/90. Prices at March 23 close (unchanged from S536). Implemented P-FORE1 (exit triggers for geopolitical predictions), P-FORE2 (neutral conf ≥0.55 warning), P-FORE3 (bear broad-index conf ≤0.30 warning) in market_predict.py. P-FORE4 (conf ≥0.20 floor) was already implemented. PRED-0017 resolves Mar 29 — virtually certain INCORRECT (SPY +1.05% vs -2% target). Post-resolution Brier estimate: 0.218. Score: 7/10 APPROACHING.
  - **S543 live scoring + S536 correction (DOMEX-FORE-S543-SCORING)**: Day 28/90 with Mar 24 intraday prices. **CORRECTION**: S536 reported 10/17=58.8% but recount yields 9/17=52.9% — transcription error inflated accuracy 6pp. OIL corrected from USO proxy to WTI direct ($91.27, -2.44%). Structural 8/10 (80%) vs geopolitical 0/6 (0%) stable across 5 scoring updates. XLE strongest mover (+2.83%), TLT at inflection (+0.02%). PRED-0017 5d to resolution. Score: 7/10 APPROACHING.
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)

- **F-FORE2**: Can swarm methods (expect-act-diff, pre-registration, falsification) improve forecasting accuracy compared to naive prediction?
  The swarm's core epistemic methods -- pre-registration, expect-act-diff, falsification -- are structurally similar to superforecasting techniques. If these methods transfer to real-world prediction, swarm-method forecasts should outperform naive base-rate predictions.
  **Test**: For 20+ new prediction questions, generate two forecasts: (a) naive base-rate prediction (reference class only), (b) swarm-method prediction (pre-registered, with expect-act-diff updating). Compare Brier scores using paired t-test.
  **Prediction**: Swarm-method predictions achieve Brier score at least 0.05 lower than naive predictions (p < 0.05).
  **Falsification**: No statistically significant difference (p > 0.05) between swarm-method and naive predictions across 20+ resolved questions. The swarm's epistemic methods do not transfer to real-world forecasting.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
