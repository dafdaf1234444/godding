# F71 Agent A: investor/src EH Analysis
Agent type: single-dimension (EH only)
Files read: [investor/core/data_manager.py, investor/core/analysis_manager.py, investor/data/unified_data_manager.py, investor/core/error_handling.py, investor/data/currency_converter.py (lines 230-240, 480-495), investor/data/storage.py (lines 542-556), investor/data/factor_data.py (lines 148-156), investor/data/macro_data.py (lines 228-236)]
Tool calls used: 16

## Findings

### Bare `except:` blocks (silent swallows — no logging at all)

1. `investor/data/currency_converter.py:235` — `except: pass` inside `get_historical_rates()`. Cache read silently fails with no log, execution falls through to a live network fetch. Any `MemoryError`, `KeyboardInterrupt`, or permission problem is indistinguishable from a cache miss.

2. `investor/data/currency_converter.py:487` — `except: pass` inside `_cache_rate()`. Merging existing cached rate data fails silently; the bad state is then immediately written to disk on the next line (`self.storage.save_stock_data(...)`), so a corrupt cache is possible.

3. `investor/data/storage.py:548` — `except: pass` inside timestamp parsing for archive filenames. Benign but swallows `ValueError` and `OSError` without distinction; falls back to `stat().mtime` silently.

4. `investor/data/factor_data.py:154` — `except: continue` in Fama-French CSV row parser. Silently skips malformed rows. If the file format changes upstream, the entire dataset may be silently empty with no warning to the caller.

5. `investor/data/macro_data.py:234` — `except: return pd.DataFrame()` in rate regime classifier. Returns an empty DataFrame instead of raising; callers have no way to distinguish "no data" from "error computing regime".

6. `investor/data/events.py:203` — `except: pass` (bare). Not fully read but consistent with the pattern found via grep.

7. `investor/core/visualization_manager.py:313,374,390,404` — Four bare `except: pass` blocks in visualization code. Visualization errors are expected to be soft, but these could swallow resource exhaustion errors affecting the whole process.

### `except Exception:` blocks that log but swallow and return empty values (soft failures)

8. `investor/core/data_manager.py:403-408` — `load_sector_data()` has both a `@handle_data_errors` decorator AND an internal `except Exception as e: ... return {}`. The internal handler swallows the error before the decorator can see it. The decorator's `continue_on_error=False` contract is defeated: callers of `load_sector_data()` get `{}` and never know the sector load failed.

9. `investor/core/data_manager.py:415-420` — Same pattern in `get_available_symbols()`: `@handle_data_errors` decorator + internal `except` returning `[]`. The decorator is rendered inert.

10. `investor/core/data_manager.py:427-432` — Same pattern in `get_available_crypto_symbols()`: `@handle_data_errors` + internal `except` returning `[]`. Three functions with this contradictory decorator-plus-swallow pattern.

11. `investor/data/unified_data_manager.py:173-175` — `load_market_data()`: `except Exception as e: logger.error(...); return {}`. Uses `logger.error` (correct severity) but still returns `{}` to the caller. No `DataError` is raised; callers cannot detect the failure programmatically without inspecting the empty dict.

12. `investor/data/unified_data_manager.py:186-188` — `load_sector_data()`: identical pattern — `logger.error` then `return {}`. Same issue as finding 11.

13. `investor/core/analysis_manager.py:156-161` — Inner loop in `run_forecasting()`: per-symbol `except Exception as e` calls `ErrorHandler.log_error(..., level='warning')` then `# Continue with other symbols`. If ALL symbols fail, `predictions` stays `{}`, the outer try exits successfully, and the function returns an empty dict with no outer-level error raised. The callers (via `handle_data_errors` decorator on `run_forecasting`) therefore receive `{}` as a valid result.

14. `investor/core/analysis_manager.py:215-221` — `_get_relevant_events()`: `except Exception as e: ... return pd.DataFrame()`. Event data failures are silently converted to an empty DataFrame. The anomaly detector then runs with no event context and produces signals without knowing events were unavailable.

15. `investor/core/data_manager.py:602-603` — `_has_fresh_earnings_cache()`: bare `except Exception: return False`. No logging whatsoever. Any I/O error (disk full, permissions) is treated identically to "cache miss", causing a silent fallback to a live network fetch.

### Functions returning None/False/empty on error instead of raising

16. `investor/core/data_manager.py:278-283` — `_is_data_fresh()`: `except Exception as e: ... return False`. Returns `False` (stale) on error, which forces a re-download even when the underlying failure is unrelated to staleness (e.g., datetime parsing issue in an otherwise valid dataset).

17. `investor/core/error_handling.py:313-319` — `handle_analysis_errors` decorator is defined with `continue_on_error=True, default_return={}` as its baseline. Any function decorated with `@handle_analysis_errors` will silently return `{}` on any exception unless the caller explicitly checks for this. This is a systemic design choice that normalizes silent soft-failure across the entire analysis layer.

## What I would have missed without EH focus

A structural view would identify that `data_manager.py` has K_out=13 (high fan-out) and flag it as a change-risk hub, but would not notice that the decorator-plus-internal-catch anti-pattern (findings 8-10) specifically defeats the error contract the decorator was meant to enforce — so the module looks architecturally defended while actually silently degrading. Similarly, the systemic `handle_analysis_errors(continue_on_error=True)` default (finding 17) is invisible unless you trace what the decorator does with exceptions.

## Overlap risk

A general-purpose agent would likely catch the bare `except: pass` blocks (findings 1-7) because they are syntactically obvious. It would probably miss findings 8-10 (decorator-vs-internal-catch contradiction) and finding 17 (decorator default policy) because detecting those requires reading both the error_handling module and the call sites in context, cross-referencing decorator semantics — work a structural or dead-code focused agent would not do. Partial overlap: ~40% of findings would surface from a general scan; the deeper systemic issues (8-10, 17) and the "all symbols fail silently" scenario (13) are EH-specific discoveries.
