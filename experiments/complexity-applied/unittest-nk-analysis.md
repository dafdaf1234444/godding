# NK Landscape Analysis: Python `unittest` Package

**Date**: 2026-02-26
**Tool**: `tools/nk_analyze.py` (3 runs: default, --verbose, --suggest-refactor)
**Python version**: 3.12
**Source**: `/usr/lib/python3.12/unittest/`

## 1. Raw NK Metrics

| Metric | Value |
|--------|------:|
| **N** (modules) | 13 |
| **K_total** (directed edges) | 27 |
| **K_avg** | 2.08 |
| **K/N** | 0.16 |
| **K_max** | 8 (`__init__`) |
| **Cycles** | 1 |
| **Composite** (K_avg * N + Cycles) | 28.0 |
| **Burden** (Cycles + 0.1 * N) | 2.3 |
| **Hub concentration** | 30% |
| **Architecture classification** | framework |
| **Total LOC** | 6,763 |

### Classification Logic

The tool classified unittest as "framework" because:
- N > 3 (not monolith)
- Cycles = 1, which is not > 3 (not tangled)
- hub_pct = 0.30, k_max = 8, N*0.3 = 3.9 -- hub_pct is not > 0.5 (not hub-and-spoke)
- K_avg = 2.08 > 2.0 (triggers framework classification)

## 2. Per-Module Detail Table (--verbose output)

| Module | LOC | K_out | K_in | Imports |
|--------|----:|------:|-----:|---------|
| `__init__` | 85 | 8 | 0 | async_case, case, loader, main, result, runner, signals, suite |
| `__main__` | 18 | 1 | 0 | main |
| `_log` | 86 | 1 | 1 | case |
| `async_case` | 142 | 1 | 1 | case |
| `case` | 1,456 | 3 | 6 | _log, result, util |
| `loader` | 495 | 3 | 2 | case, suite, util |
| `main` | 291 | 3 | 2 | loader, runner, signals |
| `mock` | 3,022 | 1 | 0 | util |
| `result` | 256 | 1 | 3 | util |
| `runner` | 292 | 3 | 2 | case, result, signals |
| `signals` | 71 | 0 | 3 | (none) |
| `suite` | 379 | 2 | 2 | case, util |
| `util` | 170 | 0 | 5 | (none) |

### In-Degree Ranking

| Module | K_in | Role |
|--------|-----:|------|
| `case` | 6 | Primary hub -- most-depended-on module |
| `util` | 5 | Utility leaf -- pure functions, zero outgoing deps |
| `result` | 3 | Mid-tier -- result aggregation |
| `signals` | 3 | Leaf -- signal handling, zero outgoing deps |
| `loader` | 2 | Standard |
| `main` | 2 | Standard |
| `runner` | 2 | Standard |
| `suite` | 2 | Standard |
| `_log` | 1 | Low |
| `async_case` | 1 | Low |
| `__init__` | 0 | Root (re-export facade) |
| `__main__` | 0 | Root (CLI entry) |
| `mock` | 0 | Isolated satellite -- no one imports it internally |

## 3. Cycle Analysis

**Cycle count**: 1

**Cycle**: `_log -> case -> _log`

The `_log` module imports `_BaseTestCaseContext` from `case`. The `case` module lazily imports `_log` inside the `assertLogs()` and `assertNoLogs()` methods. This is a managed mutual dependency -- the lazy import in `case.py` prevents an import-time circular import error.

**Modules participating in cycles**: `_log`, `case` (2 of 13 modules, 15.4%).

The remaining 11 modules form a clean DAG.

## 4. Hub Modules

### `case` (K_in=6, K_out=3, 1,456 LOC)

The gravitational center of the package. Six modules depend on it: `__init__`, `_log`, `async_case`, `loader`, `runner`, `suite`. It contains the `TestCase` class with the entire assertion library, test lifecycle management, skip/expected-failure decorators, and subtest support. Its high in-degree is domain-appropriate -- in a testing framework, the test case is the central abstraction everything revolves around.

### `util` (K_in=5, K_out=0, 170 LOC)

A pure leaf utility module with no outgoing dependencies. Five modules depend on it: `case`, `loader`, `mock`, `result`, `suite`. Provides `safe_repr`, `strclass`, and diff helpers. This is the ideal dependency pattern -- a stable foundation that creates no transitive coupling.

### `__init__` (K_out=8, K_in=0, 85 LOC)

The re-export facade. It imports 8 of 13 modules to surface the public API. This is structural, not functional -- it does not participate in any cycle and creates no coupling between the modules it imports.

### `mock` (K_out=1, K_in=0, 3,022 LOC)

The largest module by far (44.7% of total LOC) but structurally isolated. Its only internal dependency is `util` (for `safe_repr`). No other module imports `mock` internally. It is effectively a standalone sub-package (it was an independent PyPI package before Python 3.3).

## 5. Refactoring Suggestions (--suggest-refactor output)

The tool identified two candidates for cycle reduction:

| Module | Cycle Participation | Cycles After Removal | Composite After | Cycle Reduction |
|--------|-------------------:|--------------------:|----------------:|----------------:|
| `_log` | 1/1 | 0 | 25.0 | 100% |
| `case` | 1/1 | 0 | 18.0 | 100% |

**Tool recommendation**: Extract `_log` first.
- Participates in 1/1 cycles (100%)
- K_in=1, K_out=1
- Classified as "cycle driver" (K_in/K_out ratio = 1.0)

**Analysis**: Removing `_log` eliminates the only cycle and drops composite from 28.0 to 25.0. Removing `case` would drop composite further to 18.0, but that is impractical -- `case` is the central abstraction. The realistic refactoring path is to merge `_log` back into `case` (eliminating the cycle by removing the module boundary) or to break the dependency by having `_log` accept a context class via parameter rather than importing it from `case`.

## 6. Three-Way Comparison: json vs unittest vs email

| Metric | json | unittest | email |
|--------|-----:|---------:|------:|
| **N** | 5 | 13 | 29 |
| **K_total** | 2 | 27 | 44 |
| **K_avg** | 0.40 | 2.08 | 1.52 |
| **K/N** | 0.08 | 0.16 | 0.052 |
| **K_max** | 2 | 8 | 5 |
| **Cycles** | 0 | 1 | 2 |
| **Composite** | 2.0 | 28.0 | 46.0 |
| **Burden** | 0.5 | 2.3 | 4.9 |
| **Hub %** | 100% | 30% | 11% |
| **Architecture** | hub-and-spoke | framework | distributed |
| **Total LOC** | 1,316 | 6,763 | 10,323 |

### What Explains the Differences

**json (composite=2.0)**: The simplest architecture. Only 5 modules, only 2 internal edges (both from `__init__` to `decoder` and `encoder`), zero cycles. The hub concentration is 100% because all coupling flows through `__init__`. The low composite is a direct consequence of small N (5) and near-zero K_avg (0.4). The `json` package is essentially 3 independent modules (`decoder`, `encoder`, `scanner`) plus a facade.

**unittest (composite=28.0)**: Mid-range complexity. The composite of 28.0 comes from two factors: (1) K_avg of 2.08 multiplied by N of 13 yields 27.0, and (2) one cycle adds 1.0. The K_avg is high because unittest is a framework where modules must coordinate -- TestCase needs TestResult, TestRunner needs both, TestLoader needs TestCase and TestSuite. The single cycle is managed (lazy import). The `__init__` facade contributes 8 of 27 edges; excluding it would reduce K_avg to ~1.58 and composite to ~19.0.

**email (composite=46.0)**: The highest complexity, driven primarily by scale. N=29 is the dominant factor -- even though K_avg (1.52) is lower than unittest's (2.08), multiplying by 29 yields 44.1, plus 2 cycles = 46.0. The email package has a `mime.*` sub-hierarchy (8 modules) that inflates N significantly. Its 2 cycles (`contentmanager <-> message <-> policy`) are in the semantic core where content handling and policy enforcement are inherently intertwined. The distributed architecture (hub_pct = 11%) means coupling is spread across many modules rather than concentrated in one hub.

### Key Insight: Composite = K_avg * N + Cycles

The composite formula amplifies the interaction between average coupling and module count:

- **json**: 0.4 * 5 + 0 = 2.0 (low K_avg, low N, no cycles)
- **unittest**: 2.08 * 13 + 1 = 28.0 (high K_avg, medium N, 1 cycle)
- **email**: 1.52 * 29 + 2 = 46.0 (medium K_avg, high N, 2 cycles)

This shows that N is the dominant scaling factor. Email's composite is 1.64x unittest's despite lower K_avg, because its module count is 2.23x higher. The K_avg * N product captures the total coupling surface area -- the number of dependency relationships a maintainer must understand.

### Burden Score Comparison

| Package | Burden (Cycles + 0.1*N) | Interpretation |
|---------|------------------------:|----------------|
| json | 0.5 | Minimal maintenance burden |
| unittest | 2.3 | Low burden -- 1 managed cycle, moderate N |
| email | 4.9 | Moderate burden -- 2 real cycles, high N |

Burden emphasizes cycles over module count (cycles are weighted 1.0 vs 0.1 for N). This makes email's 2 cycles a larger contributor to its burden than its 29 modules.

## 7. Structural Patterns

### Pipeline Architecture

The functional modules form a clear execution pipeline:

```
loader --> suite --> case --> result
  |                   |        ^
  v                   v        |
 main ------------> runner ----+
                       |
                       v
                    signals
```

Discover tests (loader) -> group tests (suite) -> run tests (case) -> collect results (result) -> display results (runner).

### Two-Layer Design

**Foundation layer** (K_out=0): `util`, `signals`
**Application layer**: `case`, `result`, `suite`, `loader`, `runner`, `main`, `mock`, `_log`, `async_case`
**Facade layer**: `__init__`, `__main__`

### Mock as Isolated Mass

`mock` is 44.7% of total LOC but contributes only 1 of 27 edges (3.7% of coupling). Its LOC-to-coupling ratio is the most favorable in the package.

## 8. Summary

| Property | Value | Assessment |
|----------|-------|------------|
| Composite score | 28.0 | Mid-range on the stdlib spectrum |
| Burden score | 2.3 | Low maintenance risk |
| Architecture | framework | Appropriate for a testing framework |
| Cycles | 1 (managed via lazy import) | Acceptable |
| Primary hub | `case` (K_in=6) | Domain-appropriate concentration |
| Largest isolate | `mock` (3,022 LOC, K=1) | Excellent decoupling |
| Leaf modules | `util`, `signals` | Clean foundation |
| Refactoring target | `_log` (cycle elimination) | Low priority given cycle is managed |
| vs json | 14x higher composite | Expected: 2.6x more modules, 5.2x higher K_avg |
| vs email | 0.61x composite | Lower N compensates for higher K_avg |
