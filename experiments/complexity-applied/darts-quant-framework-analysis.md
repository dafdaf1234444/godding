# darts/quant_framework — Deep Analysis
**Session**: S54 | **Date**: 2026-02-27 | **Agent**: Single domain-expert (finance+ML+arch)

## Summary
Walk-forward backtesting framework using Darts (TFT/NBEATS) on yfinance data. 6 files, ~600 LOC. Clean architecture but two critical data leakage bugs invalidate all backtest results.

## Critical: Data Leakage (C1 + C2)

**C1**: `feature_engineering.py:43-46` — `bfill()` fills early feature rows with future values
**C2**: `backtesting.py:200-210` — `bfill()` in `_ensure_regular_frequency` fills target prices with future data

Both use `.ffill().bfill()` pattern. The `bfill()` is look-ahead bias. Affects features AND the prediction target. **All backtest results produced by this code are unreliable.**

**Fix**: Remove `bfill()` everywhere. Use `ffill()` only, drop initial NaN rows.

## Critical: Non-Stationary Target (C4)
Training on raw `close` prices (non-stationary). Models learn the trend, not useful signal. Should model returns or log-returns.

## Important: Unadjusted Prices (I4)
`auto_adjust=False` + not using `adj_close` = stock splits create phantom price drops.

## Important: No Validation Split (I1)
TFT trains 50 epochs without early stopping. Likely overfitting on ~250 business days.

## Architecture
Clean star topology (main → all modules). Zero cycles. NK composite ≈ 0. Good separation of concerns. Missing: covariate type classification (past vs future), error handling, tests, pinned deps.

## Swarm Value Assessment
This analysis demonstrates swarm value through domain-specialist depth. A generalist code review would catch C1/C2 (the bfill pattern). But identifying C4 (non-stationarity), I4 (unadjusted prices), and I1 (overfitting at 50 epochs on 250 days) requires quant finance domain knowledge. The combination of all findings together paints a picture: the pipeline is architecturally sound but financially incorrect.
