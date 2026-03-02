# NK Complexity Analysis: Python `logging` stdlib

**Date**: 2026-02-26
**Python version**: 3.12.x
**Source**: `/usr/lib/python3.12/logging/`

## Summary Card

```
Package: logging
N (modules): 3
K_avg: 1.00
K_max: 2 (config.py -- imports both __init__ and handlers)
K/N: 1.00
Cycles: 0 (clean DAG)
Architecture pattern: monolith-with-satellites (layered DAG, but __init__ is 47% of code)
Comparison: K/N=1.00 is higher than json (0.16), http.client (0.068), email (0.06),
            but misleading -- small N inflates the ratio. Graph density (50%) is moderate.
Key insight: logging's low N masks a monolith; the real complexity lives inside
             __init__.py (2,345 lines, ~8 logical components), not between modules.
```

## 1. Module Inventory (N = 3)

| # | Module | File | Lines | Role |
|---|--------|------|------:|------|
| 1 | `logging` | `__init__.py` | 2,345 | Core: LogRecord, Logger, Handler, Formatter, Filter, Manager, convenience API |
| 2 | `logging.handlers` | `handlers.py` | 1,605 | 14 specialized handler classes (rotating, socket, syslog, SMTP, HTTP, etc.) |
| 3 | `logging.config` | `config.py` | 1,050 | Configuration: fileConfig(), dictConfig(), socket listener |
| | **Total** | | **5,000** | |

## 2. Dependency Edges (K)

### 2.1 Raw Edge Count

| From (importer) | To (imported) | Import Statement | K for edge |
|-----------------|---------------|-----------------|:----------:|
| `handlers.py` | `__init__.py` | `import logging` (line 26) | 1 |
| `config.py` | `__init__.py` | `import logging` (line 30) | 1 |
| `config.py` | `handlers.py` | `import logging.handlers` (line 31) | 1 |

**Total K = 3 directed edges.**

No edge from `__init__.py` to either sub-module. No edge from `handlers.py` to `config.py`.

### 2.2 Dependency Graph

```
          __init__.py (2,345 lines)
           ^        ^
          /          \
   handlers.py    config.py
   (1,605 lines)  (1,050 lines)
                     |
                     v
                  handlers.py
```

Layered DAG:
- Layer 0 (foundation): `__init__`
- Layer 1 (extensions): `handlers`
- Layer 2 (configuration): `config`

### 2.3 Per-Module K

| Module | K_out (imports from package) | K_in (imported by package) | Degree |
|--------|:--:|:--:|:--:|
| `__init__` | 0 | 2 | 2 |
| `handlers` | 1 | 1 | 2 |
| `config` | 2 | 0 | 2 |

### 2.4 Attribute-Level Coupling (depth of dependency)

**handlers.py -> __init__ (7 distinct attributes, all public)**:
- `logging.FileHandler` -- base class for BaseRotatingHandler, WatchedFileHandler
- `logging.Handler` -- base class for SocketHandler, SysLogHandler, SMTPHandler, NTEventLogHandler, HTTPHandler, BufferingHandler, QueueHandler
- `logging.DEBUG`, `logging.INFO`, `logging.WARNING`, `logging.ERROR`, `logging.CRITICAL` -- level constants

**config.py -> __init__ (13 distinct attributes, 5 private)**:
- Public (8): `logging.Formatter`, `logging.Filter`, `logging.Handler`, `logging.PlaceHolder`, `logging.NOTSET`, `logging.root`, `logging.getLogger`, `logging.shutdown`
- Private (5): `logging._acquireLock`, `logging._releaseLock`, `logging._checkLevel`, `logging._handlers`, `logging._handlerList`

**config.py -> handlers (5 distinct attributes, all public)**:
- `logging.handlers.MemoryHandler`
- `logging.handlers.QueueHandler`
- `logging.handlers.QueueListener`
- `logging.handlers.SMTPHandler`
- `logging.handlers.SysLogHandler`

## 3. NK Metrics

| Metric | Value | Formula/Notes |
|--------|------:|---------------|
| N | 3 | .py files in package |
| K (total edges) | 3 | directed intra-package import edges |
| K/N | 1.00 | 3/3 |
| K_avg | 1.00 | average out-degree per module |
| K_max (out-degree) | 2 | config.py |
| K_max (in-degree) | 2 | __init__.py |
| K_max_possible | 6 | N*(N-1) for directed graph |
| Graph density | 0.50 | K / K_max_possible |

## 4. Cycle Analysis

**Cycles found: 0**

The dependency graph is a strict DAG. Verification:
- `__init__` imports nothing from the logging package
- `handlers` imports only `logging` (i.e., `__init__`)
- `config` imports `logging` and `logging.handlers`

No A->B->A patterns exist. No transitive cycles exist.

This is notable compared to `email` (N=28, 9 lazy-import cycles). The logging package achieves cycle freedom through its layered architecture.

## 5. Comparison with Benchmarks

| Package | N | K | K/N | K_avg | K_max | Cycles | Pattern |
|---------|--:|--:|----:|------:|------:|-------:|---------|
| `json` | 5 | ~4 | 0.16 | 0.80 | 2 | 0 | facade + engine |
| `http.client` | 24 | ~5 | 0.068 | ~0.21 | 10 | ? | god-class risk |
| `email` | 28 | ~5 | 0.06 | ~0.18 | ? | 9 | lazy-cycle web |
| **`logging`** | **3** | **3** | **1.00** | **1.00** | **2** | **0** | **monolith + satellites** |

### Interpretation of the K/N Gap

The K/N = 1.00 looks alarming compared to json's 0.16 or email's 0.06, but this is a **small-N artifact**:

- With N=3, the minimum non-trivial K/N is 0.33 (one edge)
- Graph density (50%) is the more meaningful metric; json at equivalent density would have K=10, K/N=2.0
- The real issue is not *coupling between modules* but *under-decomposition within modules*

### What the Numbers Actually Mean

| Comparison | Logging vs. Benchmark | Implication |
|------------|----------------------|-------------|
| vs. json | Higher K/N but similar K_max | json decomposes better (5 files vs 3), reducing ratio |
| vs. http.client | Lower K_max (2 vs 10) | No god-class risk in inter-module coupling |
| vs. email | Zero cycles vs. 9 | Logging's layered DAG is structurally cleaner |

## 6. Architecture Pattern: Monolith-with-Satellites

The logging package exhibits a **monolith-with-satellites** pattern:

1. **The monolith** (`__init__.py`, 2,345 lines, 47% of codebase): Contains ~8 logical components that are not separated into modules:
   - Level management (constants + name mapping)
   - LogRecord + factory
   - Formatting (Formatter, PercentStyle, StrFormatStyle, StringTemplateStyle, BufferingFormatter)
   - Filtering (Filter, Filterer)
   - Handler base infrastructure (Handler, StreamHandler, FileHandler)
   - Logger hierarchy (Logger, RootLogger, Manager, PlaceHolder)
   - LoggerAdapter
   - Module-level convenience API (getLogger, basicConfig, debug, info, etc.)

2. **Satellite 1** (`handlers.py`): Clean extension through public inheritance. Good.

3. **Satellite 2** (`config.py`): Coupled to internals (5 private attributes). Fragile.

### If __init__.py Were Properly Decomposed

Estimated metrics for a hypothetical decomposition into ~8 modules:
- N_effective ~ 10
- K_effective ~ 12-15
- K/N_effective ~ 1.2-1.5
- This would more honestly reflect the actual internal coupling

## 7. Key Findings

1. **K/N = 1.00 is structurally misleading**: The ratio is inflated by small N, not by excessive coupling. Graph density of 50% is moderate.

2. **Zero cycles**: Clean layered DAG. Better than email (9 cycles). This is the package's strongest structural property.

3. **The real problem is hidden complexity**: `__init__.py` is a 2,345-line monolith containing ~8 logical subsystems. NK analysis at the file level understates the true coupling.

4. **Mixed coupling quality**: handlers.py uses only public API (clean), while config.py depends on 5 private attributes (fragile).

5. **Hub identification**: `__init__` is the hub by in-degree (2); `config` is the hub by out-degree (2). Both are expected for this architecture.

## Work Shown

```bash
$ python3 -c "import logging; print(logging.__file__)"
/usr/lib/python3.12/logging/__init__.py

$ ls /usr/lib/python3.12/logging/*.py
__init__.py  config.py  handlers.py

$ wc -l /usr/lib/python3.12/logging/*.py
  2345 __init__.py
  1050 config.py
  1605 handlers.py
  5000 total

# Top-level intra-package imports:
# __init__.py: (none within logging package)
# handlers.py line 26: import io, logging, socket, os, pickle, struct, time, re
# config.py line 30: import logging
# config.py line 31: import logging.handlers

# Lazy/conditional intra-package imports: none found
```
