# F71 Agent B: investor/src Isolated Module Audit
Agent type: single-dimension (dead/isolated code only)
Files read: investor-src-nk.txt, analysis/market_regime.py, config.py, data/external_data.py, forecasting/advanced_anomaly_detection.py (first 40 lines), forecasting/anomaly_detection.py (first 40 lines), forecasting/big_data_models.py (first 40 lines), forecasting/ml_model_manager.py (first 40 lines), trading/anomaly_strategy.py (first 40 lines), utils/forecast_logger.py (first 40 lines), utils/unified_cache.py (first 40 lines)
Tool calls used: 13

## Isolated modules found

| module | K_in | K_out | LOC | verdict |
|--------|------|-------|-----|---------|
| analysis.market_regime | 0 | 0 | 322 | external-only (tests/analysis/test_market_regime.py imports it directly) |
| config | 0 | 0 | 137 | external-only (scripts/forecast_data.py imports ConfigManager) |
| data.external_data | 0 | 0 | 414 | dead (no imports found anywhere outside src; overlaps with data.macro_data which IS connected) |
| forecasting.advanced_anomaly_detection | 0 | 0 | 583 | external-only (scripts/forecast_data.py and tests/forecasting/test_advanced_anomaly_detection.py import it) |
| forecasting.anomaly_detection | 0 | 0 | 596 | external-only (scripts/forecast_data.py imports FinancialAnomalyDetector) |
| forecasting.big_data_models | 0 | 0 | 591 | dead (no external imports found; module self-references "external_data" but imports nothing local) |
| forecasting.ml_model_manager | 0 | 0 | 531 | external-only (scripts/forecast_data.py imports MLForecastingModelManager) |
| trading.anomaly_strategy | 0 | 0 | 717 | external-only (scripts/anomaly_investment_analysis.py and tests/trading/test_anomaly_strategy.py import it) |
| utils.forecast_logger | 0 | 0 | 207 | dead (no imports found anywhere in repo) |
| utils.unified_cache | 0 | 0 | 463 | dead (no imports found anywhere in repo; comment says "eliminate duplicate caching" but was never wired in) |

## Key finding

7 of the 10 structurally isolated modules (K_in=0, K_out=0) are reachable exclusively from outside `src/` — via scripts or tests — making them invisible to any graph analysis confined to the `src/` directory. The remaining 3 (`data.external_data`, `forecasting.big_data_models`, `utils.forecast_logger`, `utils.unified_cache`) are genuinely dead: written, never wired.

(Note: `utils.unified_cache` and `utils.forecast_logger` are fully dead — zero references anywhere in the entire repo. `data.external_data` and `forecasting.big_data_models` are also dead at the import level, though `big_data_models` contains internal method calls to a local `_merge_external_data` helper that mirrors what `data.external_data` provides — suggesting it was written in parallel with the data layer and then abandoned.)

## What I would have missed without isolation focus

A general complexity sweep (hub detection, cycle detection) would report 10 modules as K_in=0/K_out=0, but would not distinguish between modules that are live-but-entry-point-accessed (anomaly_strategy, ml_model_manager) versus modules that are completely dead and safe to delete (unified_cache, forecast_logger). Without isolation focus the "dead code" signal gets diluted by the "CLI entry point" pattern and the two categories merge into one undifferentiated noise bucket.

## Overlap risk

A general-purpose agent would likely find these modules by running the same NK grep queries the task prompt suggests, but would almost certainly misclassify most of them: the default interpretation of K_in=0/K_out=0 is "unused" when in reality 7 of 10 are actively used from scripts and tests. The isolation-focused agent adds the critical step of checking external consumers, which a general agent deprioritizes in favor of architecture or error-handling concerns. Overlap on detection: yes. Overlap on correct classification: no.
