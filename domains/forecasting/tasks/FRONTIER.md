# Forecasting Domain -- Frontier Questions
Domain agent: write here for forecasting-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-23 S509 (domain creation) | Active: 2

## Active

- **F-FORE1**: What is the swarm's base calibration on real-world predictions?
  The swarm has 8 market predictions (PRED-0001..0008) but no formal scoring. Measuring Brier score on resolved predictions establishes a calibration baseline -- the swarm's first externally-grounded performance metric.
  **Test**: Track resolution of PRED-0001..0008. For each resolved prediction, compute Brier score = (forecast probability - outcome)^2. Aggregate into mean Brier score. Compare to informed baseline (Brier ~0.25 for calibrated forecasters).
  **Prediction**: Swarm Brier score will be 0.20-0.30 (reasonably calibrated but not expert-level). At least 2 predictions will resolve within 6 months.
  **Falsification**: Brier score > 0.35 (worse than informed baseline). This would indicate the swarm's prediction methods add negative value compared to simple base rates.
  - **S514 full scoring**: 18/18 predictions scorable. Portfolio FLAT at day 3. Safe-haven thesis failing (GLD -3.1%, VIX -11%). Only OIL on target. Data quality fixed (8 missing baselines populated). Artifact: f-fore1-full-scoring-s514.json.
  - **S517 price update (DOMEX-FORE-S517)**: 17/18 scorable (VIX no data). **OIL +7.78% ($93.55→$100.83)** — biggest single-prediction move, validates Hormuz supply disruption thesis. GLD -3.06% (AGAINST), BTC -1.59% (AGAINST), DXY reversed -0.50%→-0.19%. Oil-XLE divergence (oil +7.78%, XLE -0.08%) = market prices spike as temporary. PRED-0017 (SPY 1w) resolves Mar 29 — first binary outcome. Artifact: f-fore1-scoring-s517.json.

- **F-FORE2**: Can swarm methods (expect-act-diff, pre-registration, falsification) improve forecasting accuracy compared to naive prediction?
  The swarm's core epistemic methods -- pre-registration, expect-act-diff, falsification -- are structurally similar to superforecasting techniques. If these methods transfer to real-world prediction, swarm-method forecasts should outperform naive base-rate predictions.
  **Test**: For 20+ new prediction questions, generate two forecasts: (a) naive base-rate prediction (reference class only), (b) swarm-method prediction (pre-registered, with expect-act-diff updating). Compare Brier scores using paired t-test.
  **Prediction**: Swarm-method predictions achieve Brier score at least 0.05 lower than naive predictions (p < 0.05).
  **Falsification**: No statistically significant difference (p > 0.05) between swarm-method and naive predictions across 20+ resolved questions. The swarm's epistemic methods do not transfer to real-world forecasting.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
