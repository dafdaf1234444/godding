# NK Landscape Analysis: Python `logging` Package

**Date**: 2026-02-26
**Python version**: 3.12.x (CPython, `/usr/lib/python3.12/logging`)
**Tool**: `tools/nk_analyze.py`

## 1. Raw Tool Output

### 1.1 Basic Run (`python3 tools/nk_analyze.py logging`)

```
=== NK ANALYSIS: logging ===

  Path: /usr/lib/python3.12/logging
  Total LOC: 5000
  Architecture: monolith

  NK Metrics:
    N (modules):          3
    K_total (edges):      1
    K_avg:                0.33
    K/N:                  0.111
    K_max:                1 (config)
    Cycles:               0
    K_avg*N + Cycles:     1.0
    Burden (Cyc+0.1N):   0.3
    Hub concentration:    100%
```

### 1.2 Verbose Run (`python3 tools/nk_analyze.py logging --verbose`)

Module-level detail:

```
  Modules:
    Module                       LOC  K_out  K_in  Imports
    ----------------------------------------------------------------------
    __init__                    2345      0     0  (none)
    config                      1050      1     0  handlers
    handlers                    1605      0     1  (none)
```

### 1.3 Refactor Run (`python3 tools/nk_analyze.py logging --suggest-refactor`)

```
  logging has 0 cycles -- no refactoring needed for cycle reduction.
  Composite score: 1.0
```

### 1.4 Lazy Import Analysis (`python3 tools/nk_analyze.py logging --lazy`)

```
  Total lazy imports (internal): 0
  Cycle-breaking lazy imports:   0
  Static cycles (top-level):     0
  Runtime cycles (all imports):  0
  F44 Hypothesis Verdict: NO_LAZY
```

## 2. Metrics Summary

| Metric | Value | Notes |
|--------|------:|-------|
| N (modules) | 3 | `__init__`, `config`, `handlers` |
| K_total (edges) | 1 | Tool detects only `config -> handlers` |
| K_avg | 0.33 | K_total / N |
| K/N | 0.111 | K_avg / N |
| K_max | 1 | `config` (imports `handlers`) |
| Cycles | 0 | Clean DAG |
| Composite (K_avg*N + Cycles) | 1.0 | Lowest in the benchmark set |
| Burden (Cycles + 0.1*N) | 0.3 | Lowest in the benchmark set |
| Hub concentration | 100% | K_max / K_total = 1/1 |
| Architecture classification | monolith | N <= 3 triggers monolith classification |
| Total LOC | 5,000 | `__init__`: 2345, `handlers`: 1605, `config`: 1050 |

## 3. Tool vs. Reality: The Edge Count Discrepancy

The tool reports **K_total = 1**, but manual inspection of the source reveals **3 actual dependency edges**:

| From | To | Import Statement | Tool Detects? |
|------|----|------------------|:---:|
| `config` | `handlers` | `import logging.handlers` | Yes |
| `config` | `__init__` | `import logging` | No |
| `handlers` | `__init__` | `import logging` | No |

**Why the discrepancy**: The tool's `_resolve_import_name` function requires `len(parts) > 1` for absolute imports -- i.e., it catches `import logging.handlers` (parts = `["logging", "handlers"]`) but not `import logging` (parts = `["logging"]`), because a single-part import matching the package name is ambiguous between "importing the package itself" and "importing something external." Inside a package, `import logging` in `handlers.py` is an import of the parent `__init__.py`, but the tool cannot distinguish this from a hypothetical external package named `logging`.

**Corrected metrics** (if counting all 3 edges):

| Metric | Tool Value | Corrected Value |
|--------|----------:|---------------:|
| K_total | 1 | 3 |
| K_avg | 0.33 | 1.00 |
| K/N | 0.111 | 0.333 |
| K_max | 1 | 2 (config) |
| Composite | 1.0 | 3.0 |
| Burden | 0.3 | 0.3 (unchanged; no cycles) |

Even with the corrected value of 3.0, logging remains among the lowest-complexity packages.

## 4. Architecture Classification

The tool classifies logging as **monolith**. This is triggered by the rule `if n <= 3: return "monolith"` in the classifier -- any package with 3 or fewer modules is automatically classified as monolith regardless of other metrics.

This classification is actually correct for a deeper reason: `__init__.py` contains 2,345 of 5,000 lines (47%), 18 classes, and 31 top-level functions. The "monolith" label reflects the reality that most of the package's logic is concentrated in a single file. The package has a layered DAG structure, but the core layer is itself a monolith.

The dependency graph is a clean 3-layer DAG:

```
Layer 0 (foundation):     __init__     (2345 LOC, 0 out-edges, 2 in-edges)
Layer 1 (extensions):     handlers     (1605 LOC, 1 out-edge, 1 in-edge)
Layer 2 (configuration):  config       (1050 LOC, 2 out-edges, 0 in-edges)
```

## 5. Cycle Analysis

**Zero cycles.** The dependency graph is a strict DAG. No module has a path back to itself.

Modules participating in cycles: none.

The lazy import analysis confirms zero internal lazy imports, meaning no hidden runtime cycles either. This makes logging one of the cleanest packages structurally. The F44 hypothesis (lazy imports exist to break cycles) is not testable here.

Note: `handlers.py` and `config.py` do use lazy imports for *external* dependencies (e.g., `smtplib`, `configparser`, `multiprocessing`), but not for internal cross-module imports.

## 6. Hub Analysis

**Hub by out-degree**: `config` (K_out = 2 corrected, 1 per tool) -- depends on both other modules. This is architecturally expected: a configuration module must know about the things it configures.

**Hub by in-degree**: `__init__` (K_in = 2 corrected, 0 per tool) -- both other modules depend on it. This is the natural gravity well of a core module that defines all base classes.

**Hub concentration**: 100% (tool value). All detected edges originate from a single module (`config`). In the corrected graph, `config` still accounts for 2/3 of all edges.

The hub structure is healthy: `__init__` is a pure provider (high in-degree, zero out-degree), while `config` is a pure consumer (high out-degree, zero in-degree). This is the "clean layering" pattern.

## 7. Refactoring Suggestions

The tool's refactoring engine reports: "logging has 0 cycles -- no refactoring needed for cycle reduction." This is the correct output given zero cycles.

However, the tool's cycle-focused refactoring misses the main issue: **`__init__.py` is an under-decomposed monolith**. If decomposed into its logical components, the package would look like:

| Proposed Module | Contents | Approx LOC |
|----------------|----------|----------:|
| `_levels` | Level constants, `addLevelName`, `getLevelName`, `_checkLevel` | ~100 |
| `_records` | `LogRecord`, `LogRecordFactory`, `makeLogRecord` | ~200 |
| `_formatting` | `Formatter`, `PercentStyle`, `StrFormatStyle`, `StringTemplateStyle`, `BufferingFormatter` | ~300 |
| `_filtering` | `Filter`, `Filterer` | ~100 |
| `_handlers_base` | `Handler`, `StreamHandler`, `FileHandler` | ~400 |
| `_hierarchy` | `Logger`, `RootLogger`, `Manager`, `PlaceHolder` | ~600 |
| `_adapter` | `LoggerAdapter` | ~100 |
| `__init__` | Public API surface, `getLogger`, `basicConfig`, convenience functions | ~500 |
| `config` | (unchanged) | ~1050 |
| `handlers` | (unchanged) | ~1605 |

This would yield approximately N=10, K~12-15, composite~15-20 -- more honestly reflecting the package's internal complexity.

## 8. Cross-Package Comparison

| Package | N | K_total | K_avg | K/N | Cycles | Composite | Burden | Architecture |
|---------|--:|-------:|------:|----:|-------:|----------:|-------:|:------------|
| **logging** | **3** | **1** | **0.33** | **0.111** | **0** | **1.0** | **0.3** | **monolith** |
| json | 5 | 2 | 0.40 | 0.08 | 0 | 2.0 | 0.5 | hub-and-spoke |
| email | 29 | 44 | 1.52 | 0.052 | 2 | 46.0 | 2.9 | distributed |

### What explains the differences?

**logging (composite=1.0) vs json (composite=2.0)**:
- Both are cycle-free, so the composite difference is purely from K_avg * N.
- json has more modules (5 vs 3) but both have minimal internal coupling.
- json's `__init__.py` imports `decoder` and `encoder`, giving it K_total=2 vs logging's tool-detected K_total=1.
- Both share the pattern of a dominant `__init__.py` that re-exports functionality.
- json's architecture is classified as "hub-and-spoke" because N > 3, while logging falls into the automatic "monolith" bucket.
- Key difference: json is better decomposed -- its decoder and encoder are separate modules with clear boundaries. Logging stuffs the equivalent functionality into `__init__.py`.

**logging (composite=1.0) vs email (composite=46.0)**:
- email has 29 modules (nearly 10x logging's 3), so even moderate coupling (K_avg=1.52) produces a large K_avg * N term (44.1).
- email has 2 cycles, adding 2 to the composite score.
- email is a genuinely decomposed package: MIME types, encoders, headers, charset handling, and policy modules are all separate files. This decomposition is honest -- it reflects the real internal complexity of email parsing/generation.
- logging achieves a low composite score not primarily through good design but through **under-modularization**. With 5,000 LOC across only 3 files, the LOC-per-module ratio is 1,667 -- far higher than email's 172 LOC-per-module.
- Burden scores differ dramatically (0.3 vs 2.9) primarily because email has cycles and 10x the module count.

### The LOC/N ratio as a hidden complexity indicator

| Package | LOC | N | LOC/N | Composite |
|---------|----:|--:|------:|----------:|
| logging | 5,000 | 3 | 1,667 | 1.0 |
| json | 1,316 | 5 | 263 | 2.0 |
| email | ~5,000 | 29 | 172 | 46.0 |

Logging's LOC/N of 1,667 is an order of magnitude higher than email's 172. This suggests the NK composite score, taken alone, under-reports complexity for under-modularized packages. A package can achieve a low composite score by concentrating all logic in `__init__.py`, avoiding the edges that come from decomposition. The composite score measures *inter-module* complexity but is blind to *intra-module* complexity.

## 9. Key Findings

1. **logging scores 1.0 composite, the lowest in the benchmark set.** This is factually correct per the tool's methodology.

2. **The tool under-counts edges (1 vs 3 actual).** The `import logging` pattern used by submodules to access `__init__` is not detected. Even corrected, the composite would be 3.0 -- still very low.

3. **Zero cycles, zero lazy internal imports.** The DAG is clean and there is no deferred coupling.

4. **The monolith classification is accurate.** 47% of code lives in `__init__.py`. The real architectural complexity is hidden inside that single file.

5. **The low composite score is partly an artifact of under-modularization.** Logging's 5,000 LOC would produce a higher (and more honest) composite score if the core were decomposed into its 5-8 logical components.

6. **Coupling quality is mixed.** `handlers -> __init__` uses only public API (clean). `config -> __init__` reaches into 5 private attributes (fragile).

7. **The NK composite metric has a blind spot for monolithic packages.** A supplementary metric like LOC/N or a "monolith penalty" would improve accuracy for packages with N < 5.
