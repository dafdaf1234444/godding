# PDD-002: Compressed Research Cycle Validation

**Pre-registered Design Document**
**Filed**: 2026-04-02
**Status**: PRE-REGISTERED (no data collected yet)
**Falsification deadline**: 2026-06-02 (60 days)

---

## 1. Research question

Does a compressed research cycle (hours/days instead of months) produce results of comparable quality and credibility to a traditional cycle, when measured by prediction accuracy on out-of-sample data?

## 2. Prior work & motivation

- Traditional academic cycle: 12-24 months from question to publication.
- Swarm compressed cycle: orient -> hypothesize -> test -> publish in hours.
- Claim: most research time is ceremony, not thinking. Untested.
- Finance directive (S499): real market predictions as credibility test.
- Risk: speed without rigor = fast self-deception. This PDD tests whether the rigor holds.

## 3. Hypotheses (pre-registered)

| ID | Hypothesis | Metric | Falsified if |
|----|-----------|--------|-------------|
| H1 | Compressed-cycle predictions match traditional-cycle accuracy within 15% | RMSE ratio (compressed / traditional baseline) | Ratio > 1.15 |
| H2 | Pre-registration eliminates >80% of post-hoc rationalization | Fraction of results that match pre-registered analysis plan | < 80% adherence in compressed vs > 95% in traditional |
| H3 | Walk-forward validation catches >90% of overfitting that in-sample-only misses | False positive rate (strategies that pass in-sample but fail OOS) | Walk-forward false positive rate > 10% |
| H4 | Adversarial self-review (try to destroy own hypothesis) catches >60% of errors before publication | Error detection rate in adversarial vs non-adversarial review | Adversarial catches < 40% |
| H5 | 10 compressed cycles produce better cumulative accuracy than 1 traditional cycle of equal total time | Brier score over 10 predictions vs 1 prediction | Compressed Brier score worse (higher) |

## 4. Method

### 4.1 Test domain: financial time series prediction

Why finance:
- Ground truth is unambiguous (price went up or down)
- Data is free (Yahoo Finance)
- No domain gatekeeping (no IRB, no lab access needed)
- Prediction window creates natural out-of-sample test
- Hardest credibility test: market efficiency hypothesis says you can't beat random

### 4.2 Protocol: compressed cycle

Each cycle follows this exact sequence (timed):

```
T+0min   ORIENT    — pull latest data, check what's known
T+5min   QUESTION  — formulate specific, falsifiable prediction
T+10min  PREDICT   — state: direction, magnitude, confidence, timeframe
T+15min  METHOD    — walk-forward backtest on historical data
T+45min  TEST      — run backtest, record results
T+60min  DESTROY   — adversarial review: try to break own finding
T+75min  PUBLISH   — commit prediction with timestamp (git = notary)
T+Xdays  SCORE     — when prediction window closes, score it
```

Total per cycle: ~75 minutes active work.

### 4.3 Protocol: traditional baseline

Use published financial prediction papers (minimum 3) as baseline:
- Record their stated accuracy metrics
- Apply same walk-forward methodology to same time periods
- Compare compressed-cycle accuracy against their reported numbers

### 4.4 Experimental design

| Parameter | Value |
|-----------|-------|
| Number of compressed cycles | 10 |
| Prediction horizon | 5 trading days (1 week) |
| Assets | SPY, QQQ, GLD, TLT, VIX (5 liquid ETFs) |
| Walk-forward window | 252 days train / 63 days test / 21 day step |
| Backtest period | 2020-01-01 to 2026-03-31 |
| Out-of-sample period | 2026-04-07 to 2026-06-02 |

### 4.5 Metrics

- **Accuracy**: direction correct? (binary)
- **Calibration**: stated confidence vs actual hit rate
- **RMSE**: predicted return vs actual return
- **Brier score**: probability predictions vs outcomes
- **Sharpe ratio**: if predictions were traded (hypothetical)
- **Time-to-result**: minutes per cycle

### 4.6 Walk-forward specification

```
Anchored expanding window:
  Train: [start, start+252+i*21] for i in 0..N
  Test:  [train_end, train_end+63]
  Step:  21 trading days

Rolling fixed window:
  Train: [start+i*21, start+i*21+252]
  Test:  [train_end, train_end+63]
  Step:  21 trading days
```

Both variants run. Report which performs better and why.

## 5. Expected outcomes (point predictions)

- H1: RMSE ratio = **1.08** (compressed slightly worse but within 15%)
- H2: Pre-registration adherence = **92%** compressed, **97%** traditional
- H3: Walk-forward false positive rate = **4%** (catches 96% of overfitting)
- H4: Adversarial review catches = **65%** of errors
- H5: 10-cycle Brier score = **0.22**, single-cycle = **0.28** (compressed better due to learning)

## 6. Implementation

```
# Walk-forward template (Colab notebook)
swarm_walkforward.ipynb  — zero-setup, pip install in first cell

# Prediction logger
python3 tools/prediction_log.py --asset SPY --direction UP --confidence 0.65 --horizon 5d

# Scorer (run after prediction window closes)
python3 tools/prediction_score.py --check-all
```

## 7. Success criteria

- 3+ of 5 hypotheses confirmed = compressed cycle is viable for real research
- Cumulative Brier score < 0.25 = predictions are better than coin flip
- Calibration within 10% = stated confidence is meaningful
- If all hypotheses fail: compressed cycle needs more rigor, not more speed. Publish the failure.

## 8. Credibility checklist

- [x] Pre-registered before data collection
- [x] Falsification criteria explicit
- [x] Point predictions logged
- [x] Walk-forward methodology specified
- [x] Traditional baseline defined
- [x] Out-of-sample period future-dated (no peeking)
- [ ] Compressed cycles run (0/10)
- [ ] Predictions logged with git timestamps
- [ ] Out-of-sample scored
- [ ] Calibration report published
- [ ] Comparison with traditional baseline filed
