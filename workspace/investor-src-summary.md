# investor/src — NK Analysis Summary

**Analyzed**: 2026-02-27
**Source**: `<your-repos>/investor/src` (read-only, copy at `workspace/investor-src/`)
**NK output**: `workspace/investor-src-nk.txt`

---

## Top-Level Package Structure

```
workspace/investor-src/
└── investor/
    ├── __init__.py
    ├── config.py
    ├── data_loader.py
    ├── analysis/       (4 modules: holiday_effects, market_regime, options_analysis, regime_switching)
    ├── core/           (8 modules: analysis_manager, analysis_orchestrator, config, data_manager, error_handling, exceptions, output_manager, visualization_manager)
    ├── data/           (15 modules including base/ and providers/ sub-packages)
    ├── forecasting/    (11 modules: model_manager, ensemble, data_processor, anomaly_detection, scalable_plotting, …)
    ├── models/         (3 modules: factor_models, options_pricing)
    ├── trading/        (3 modules: anomaly_strategy, pairs_trading)
    ├── utils/          (8 modules: date_utils, logging, parallel_processing, performance, temporal_validation, …)
    └── visualization/  (3 modules: events_overlay, market_dashboard, options_charts)
```

---

## NK Metrics

| Metric             | Value                         |
|--------------------|-------------------------------|
| N (modules)        | 68                            |
| K_total (edges)    | 123                           |
| K_avg              | 1.81                          |
| K/N                | 0.027                         |
| K_max              | 13 (`core.data_manager`)      |
| Cycles             | 0                             |
| Composite (K_avg*N + Cycles) | 123.0               |
| Hub concentration  | 11%                           |
| Total LOC          | 25,685                        |
| LOC/N              | ~378 lines/module             |
| Architecture class | distributed                   |

**Benchmark position**: composite 123.0 places investor between `multiprocessing` (102) and `asyncio` (128) — a medium-complexity framework-scale package.

---

## Top 3 Highest-Complexity Modules

By outgoing coupling (K_out):

1. **`core.data_manager`** — K_out=13, 721 LOC
   Imports: config, error_handling, exceptions, data, crypto_data, currency_converter, earnings_data, earnings_processor, macro_data, sector_data, stock_data, storage, unified_data_manager.
   Acts as central data orchestration hub pulling from all data sub-modules.

2. **`core.analysis_manager`** — K_out=12, 422 LOC
   Imports: holiday_effects, options_analysis, core.config, error_handling, exceptions, data, data.events, forecasting, forecasting.data_processor, forecasting.ensemble, forecasting.investment_anomaly_detector, forecasting.model_manager.
   Orchestrates cross-domain analysis pipeline.

3. **`data.unified_data_manager`** — K_out=9, 261 LOC
   Imports from data.base (cache_manager, interfaces, provider_registry, providers sub-package, macro_data, sector_data).
   Provides unified access layer over all data providers.

Most-imported modules (K_in):

- `utils` (K_in=8) — shared utility hub
- `core.exceptions` (K_in=7) — error type hierarchy
- `data.base.interfaces` (K_in=7) — data provider contracts

---

## Top Architectural Patterns

**DAG (Directed Acyclic Graph) — clean**: 0 cycles detected across all 68 modules. The dependency graph is cycle-free, a strong signal of disciplined layering.

**Layered / tiered architecture**: Clear separation:
- Layer 0 (leaves): `utils.*`, `core.exceptions`, `core.config`, `data.base.interfaces`, `data.base.utils`
- Layer 1 (data access): `data.stock_data`, `data.storage`, `data.base.cache_manager`, provider implementations
- Layer 2 (aggregators): `core.data_manager`, `data.unified_data_manager`, `core.analysis_manager`
- Layer 3 (orchestration): `core.analysis_orchestrator`, `core.visualization_manager`

**Distributed / modular**: K_avg=1.81 and hub_pct=11% confirm no single dominant hub. Most modules are loosely coupled leaf nodes.

**Sparse domain modules**: `analysis/`, `forecasting/`, `trading/`, `models/` subpackages have many zero-import leaf modules (e.g., `forecasting.anomaly_detection`, `forecasting.big_data_models`, `trading.anomaly_strategy`) — self-contained computation units with no internal cross-imports.

---

## Open Questions

1. **Are the forecasting leaf modules actively used or abandoned?**
   `forecasting.advanced_anomaly_detection`, `forecasting.big_data_models`, `forecasting.ml_model_manager`, `trading.anomaly_strategy` have K_in=0 AND K_out=0 — they are completely isolated from the rest of the graph. Dead code? Draft features? Parallel experiments not yet wired in?

2. **Why does `core.data_manager` not use `data.base.*`?**
   The `data.base` sub-package provides `interfaces`, `cache_manager`, `provider_registry`, and `yfinance_provider` — an abstraction layer over data sources. Yet `core.data_manager` bypasses it, importing raw data modules directly. This suggests `data.base` was added later as a refactor effort that wasn't completed upward through the core layer.

3. **Is `data_loader.py` a legacy entry point?**
   The top-level `data_loader` module (K_in=0, only 106 LOC) imports from `data` and `data.storage` directly, with no connection to the newer `core.data_manager` or `data.unified_data_manager`. This looks like an earlier design that predates the core/ orchestration layer and may be redundant.
