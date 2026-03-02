# NK Complexity Analysis: Python `unittest` (stdlib)

**Date**: 2026-02-26
**Python version**: 3.12
**Source**: `/usr/lib/python3.12/unittest/`

## Module Inventory (N = 13)

| # | Module | Role |
|---|--------|------|
| 1 | `__init__` | Package facade, re-exports public API |
| 2 | `__main__` | CLI entry (`python -m unittest`) |
| 3 | `_log` | Logging assertion context managers |
| 4 | `async_case` | `IsolatedAsyncioTestCase` |
| 5 | `case` | Core `TestCase`, all assertions, decorators |
| 6 | `loader` | `TestLoader`, test discovery |
| 7 | `main` | `TestProgram`, CLI arg parsing |
| 8 | `mock` | `Mock`, `MagicMock`, `patch`, `AsyncMock` |
| 9 | `result` | `TestResult` base class |
| 10 | `runner` | `TextTestRunner`, `TextTestResult` |
| 11 | `signals` | SIGINT handling for graceful Ctrl-C |
| 12 | `suite` | `TestSuite`, `BaseTestSuite` |
| 13 | `util` | Pure utilities (`safe_repr`, `strclass`, diff helpers) |

## Dependency Map (K per module)

Internal imports only (imports of other modules within the `unittest` package).

| Module | Imports from (internal) | K |
|--------|------------------------|--:|
| `__init__` | result, case, suite, loader, main, runner, signals, async_case (lazy) | 8 |
| `__main__` | main | 1 |
| `_log` | case | 1 |
| `async_case` | case | 1 |
| `case` | result, util, _log (lazy via `from ._log import _AssertLogsContext`) | 3 |
| `loader` | case, suite, util | 3 |
| `main` | loader, runner, signals | 3 |
| `mock` | util (absolute: `from unittest.util import safe_repr`) | 1 |
| `result` | util | 1 |
| `runner` | result, case, signals | 3 |
| `signals` | (none) | 0 |
| `suite` | case, util | 2 |
| `util` | (none) | 0 |

**Total edges (K_total)**: 27

## Key Metrics

```
Package: unittest
N (modules): 13
K_avg: 2.077 (27 / 13)
K_max: 8 (__init__); 3 among core modules (case, loader, main, runner)
K/N: 2.077 (same as K_avg since K/N = total_edges / N)
Density: 0.173 (27 / (13 * 12) = 27/156)
Cycles: 1 (case <-> _log, managed via lazy import)
Architecture pattern: hub-spoke with pipeline spine
Comparison: see below
Key insight: unittest's coupling density (0.173) is 3-4x higher than json/email,
  but the graph is almost acyclic and the hub (case) is domain-appropriate;
  mock's isolation (44% of code, K=1) is the standout structural achievement.
```

## Cycle Analysis

**1 cycle found:**

```
case --> _log --> case
```

- `case.py` line 835/844: `from ._log import _AssertLogsContext` (inside method bodies, lazy)
- `_log.py` line 4: `from .case import _BaseTestCaseContext` (top-level)

This is a **managed cycle**. The lazy import in `case.py` means at import time the dependency is unidirectional (`_log -> case`). The cycle only materializes at call time, when `assertLogs()` or `assertNoLogs()` is invoked. Python handles this without error because `case` is fully loaded before any test code calls those methods.

**No other cycles exist.** The remaining graph is a clean DAG.

## In-degree Analysis (who is depended upon)

| Module | In-degree | Role |
|--------|----------:|------|
| `case` | 6 | Primary hub (gravitational center) |
| `util` | 5 | Utility foundation (pure functions) |
| `result` | 3 | Mid-tier |
| `signals` | 3 | Mid-tier |
| `suite` | 2 | Standard |
| `loader` | 2 | Standard |
| `main` | 2 | Standard |
| `runner` | 2 | Standard |
| `_log` | 1 | Appendage of case |
| `async_case` | 1 | Extension leaf |
| `__init__` | 0 | Root |
| `__main__` | 0 | Root |
| `mock` | 0 | Isolated satellite |

## Comparison with Benchmarks

| Package | N | K_total | K_avg | K_max | Density | Cycles | Architecture |
|---------|--:|--------:|------:|------:|--------:|-------:|-------------|
| `json` | 5 | ~4 | ~0.8 | 2 | 0.040 | 0 | facade + engine |
| `http.client` | 24 | ~38 | ~1.6 | 10 | 0.003 | 0 | god-class risk |
| `email` | 28 | ~48 | ~1.7 | 5 | 0.002 | 9 (lazy) | tangled web |
| **`unittest`** | **13** | **27** | **2.077** | **8 (3 core)** | **0.173** | **1 (lazy)** | **hub-spoke + pipeline** |

### Analysis

1. **vs json (N=5, density 0.040)**: unittest is 4x denser. But json is tiny (5 modules) with a simple facade+engine split. unittest's 13 modules span a full framework (discovery, execution, assertion, reporting), so higher coupling is expected.

2. **vs http.client (N=24, density 0.003, K_max=10)**: http.client has lower density but a worse K_max problem -- one module with 10 dependencies (god-class). unittest's K_max of 3 (core) is much healthier. unittest trades higher average coupling for better max-coupling discipline.

3. **vs email (N=28, density 0.002, 9 cycles)**: email has the lowest density but **9 lazy-import cycles**, making its graph topology much more tangled. unittest has only 1 cycle. email's low density is misleading -- the cycles create hidden coupling that the raw numbers do not capture.

**Verdict**: unittest has the highest density of the four, but the best cycle discipline (only 1, managed) and the best K_max (core) control. Its coupling is high but structurally sound.

## Architecture Pattern: Hub-Spoke with Pipeline Spine

```
                    loader --> suite --> case --> result
                      |                   |        ^
                      v                   v        |
                     main ------------> runner ----+
                                          |
                                          v
                                       signals

  [isolated satellite]     [appendage]      [extension]
       mock                  _log            async_case
       (K=1)              (cycle w/ case)    (K=1)
```

The core forms a **pipeline**: discover (loader) -> group (suite) -> run (case) -> collect (result) -> display (runner). This pipeline is overlaid on a **hub-spoke** where `case` and `util` are the two hubs.

Two foundation modules (`util`, `signals`) sit at the bottom with zero outgoing dependencies -- a clean, stable base.

`mock` (3,022 lines, 44.7% of the package) is a **satellite**: massive in size but minimally coupled (K=1). It could be extracted to an independent package with near-zero cost (and historically was -- `mock` was a separate PyPI package before Python 3.3).

## Work Shown

Import extraction was done by reading each `.py` file in `/usr/lib/python3.12/unittest/` and identifying all `from . import`, `from .X import`, and `from unittest.X import` statements. Only imports referencing other modules within the `unittest` package were counted. Standard library imports (sys, os, etc.) and third-party imports were excluded.
