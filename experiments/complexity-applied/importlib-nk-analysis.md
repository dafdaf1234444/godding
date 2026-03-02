# NK Landscape Analysis: Python `importlib` Package

**Date**: 2026-02-26
**Python version**: 3.12.3
**Package**: `importlib` (stdlib)
**Source**: `/usr/lib/python3.12/importlib/`
**Tool**: `nk_analyze.py` automated analysis + manual source inspection

---

## 1. Module Inventory (N)

The `importlib` package contains **N = 24** Python modules across 6,442 lines of code, organized in three sub-packages: the core import machinery, `metadata` (package metadata), and `resources` (resource access).

| # | Module | Lines | Role |
|---|--------|------:|------|
| 1 | `__init__` | 138 | Package entry: `import_module()`, `reload()`, bootstrap wiring |
| 2 | `_abc` | 39 | Loader ABC (thin wrapper) |
| 3 | `_bootstrap` | 1,551 | **Core import machinery** (frozen into interpreter, zero internal deps) |
| 4 | `_bootstrap_external` | 1,745 | **Path-based import** (frozen, lazy imports to metadata/readers) |
| 5 | `abc` | 239 | Abstract base classes: MetaPathFinder, SourceLoader, etc. |
| 6 | `machinery` | 20 | Re-exports from _bootstrap/_bootstrap_external |
| 7 | `readers` | 12 | Compat shim for resources.readers (deprecated) |
| 8 | `simple` | 14 | Compat shim for resources.simple (deprecated) |
| 9 | `util` | 268 | Utility functions: `source_hash()`, `spec_from_file_location()` |
| 10 | `metadata` | 966 | `importlib.metadata` sub-package entry (Distribution, entry_points) |
| 11 | `metadata._adapters` | 89 | Metadata adapter utilities |
| 12 | `metadata._collections` | 30 | FreezableDefaultDict, Pair |
| 13 | `metadata._functools` | 104 | method_cache, pass_none |
| 14 | `metadata._itertools` | 73 | always_iterable, unique_everseen |
| 15 | `metadata._meta` | 63 | PackageMetadata, SimplePath type hints |
| 16 | `metadata._text` | 99 | Text parsing utilities |
| 17 | `resources` | 36 | `importlib.resources` sub-package entry (files, as_file) |
| 18 | `resources._adapters` | 168 | SpecLoaderAdapter, CompatibilityFiles |
| 19 | `resources._common` | 207 | Core resource resolution logic |
| 20 | `resources._itertools` | 38 | Iteration helpers |
| 21 | `resources._legacy` | 120 | Legacy API (deprecated) |
| 22 | `resources.abc` | 173 | Traversable, TraversableResources ABCs |
| 23 | `resources.readers` | 144 | FileReader, ZipReader, MultiplexedPath, NamespaceReader |
| 24 | `resources.simple` | 106 | SimpleReader implementation |

**N = 24** modules, **6,442** total lines.

The two largest modules -- `_bootstrap` (1,551) and `_bootstrap_external` (1,745) -- account for **51.1%** of total code. These are the frozen bootstrap modules that implement Python's core import machinery. They are designed to have minimal internal dependencies because they must be available before the full import system is operational.

---

## 2. Dependency Map (K)

### 2.1 Full Directed Edge List

Each line reads "A depends on B" (A imports from B):

```
__init__               -> _bootstrap, _bootstrap_external
_abc                   -> _bootstrap
_bootstrap             -> (none)
_bootstrap_external    -> metadata [LAZY], readers [LAZY]
abc                    -> _abc, _bootstrap_external, machinery, resources
machinery              -> _bootstrap, _bootstrap_external
metadata               -> abc
readers                -> resources, resources.readers
resources              -> abc  [NOTE: likely resources.abc, see Sec. 3.2]
resources._adapters    -> abc  [NOTE: likely resources.abc, see Sec. 3.2]
resources._common      -> abc  [NOTE: likely resources.abc, see Sec. 3.2]
resources._itertools   -> (none)
resources._legacy      -> (none)
resources.abc          -> (none)
resources.readers      -> abc  [NOTE: likely resources.abc, see Sec. 3.2]
resources.simple       -> abc  [NOTE: likely resources.abc, see Sec. 3.2]
simple                 -> resources, resources.simple
util                   -> _abc, _bootstrap, _bootstrap_external
metadata._adapters     -> (none)
metadata._collections  -> (none)
metadata._functools    -> (none)
metadata._itertools    -> (none)
metadata._meta         -> (none)
metadata._text         -> (none)
```

**Total directed edges: K = 24**

### 2.2 In-Degree (most depended-on modules)

| Module | In-degree | Assessment |
|--------|----------:|------------|
| `abc` | **6** | **Primary hub** -- ABCs for finders, loaders, resources |
| `_bootstrap` | **4** | Core import machinery (frozen, zero-dep foundation) |
| `_bootstrap_external` | **4** | Path-based import (frozen) |
| `resources` | **3** | Resources sub-package entry |
| `_abc` | **2** | Loader ABC wrapper |
| `machinery` | **1** | Re-export shim |
| `metadata` | **1** | Metadata sub-package |
| `readers` | **1** | Compat shim |
| `resources.readers` | **1** | Reader implementations |
| `resources.simple` | **1** | Simple reader |

### 2.3 Out-Degree (most dependencies per module)

| Module | Out-degree | Role |
|--------|----------:|------|
| `abc` | **4** | Hub: defines ABCs, imports from bootstrap + sub-packages |
| `util` | 3 | Utility: imports from _abc, _bootstrap, _bootstrap_external |
| `__init__` | 2 | Entry: wires bootstrap modules |
| `_bootstrap_external` | 2 | Lazy imports: metadata, readers |
| `machinery` | 2 | Re-exports from both bootstrap modules |
| `readers` | 2 | Compat: forwards to resources.readers |
| `simple` | 2 | Compat: forwards to resources.simple |
| All `resources.*` | 1 | Sub-package modules: import `abc` |

---

## 3. Cycle Analysis

### 3.1 Detected Cycles: 3

The tool detected three cycles:

**Cycle 1: `_bootstrap_external -> metadata -> abc -> _bootstrap_external`**
```
_bootstrap_external.py (line 1453,1554: from importlib.metadata import MetadataPathFinder)
  --> metadata/__init__.py (line 27: from importlib.abc import MetaPathFinder)
  --> abc.py (line 2: from . import _bootstrap_external)
  --> _bootstrap_external.py
```

**Cycle 2: `_bootstrap_external -> metadata -> abc -> machinery -> _bootstrap_external`**
```
_bootstrap_external.py (lazy: from importlib.metadata import MetadataPathFinder)
  --> metadata/__init__.py (from importlib.abc import MetaPathFinder)
  --> abc.py (from . import machinery)
  --> machinery.py (from ._bootstrap_external import ...)
  --> _bootstrap_external.py
```

**Cycle 3: `abc -> resources -> abc`**
```
abc.py (line 18: from .resources import abc as _resources_abc)
  --> resources/__init__.py (line 20: from .abc import ResourceReader)
  --> abc.py (?)
```

### 3.2 Cycle Assessment: Mostly Lazy Imports and One Likely False Positive

**Cycles 1-2 are broken by lazy imports.** The `_bootstrap_external` module's imports of `metadata` and `readers` occur inside method bodies, not at module top-level:

```python
# _bootstrap_external.py line 1194 (inside FileLoader.get_resource_reader):
from importlib.readers import FileReader

# _bootstrap_external.py line 1424 (inside NamespaceLoader.get_resource_reader):
from importlib.readers import NamespaceReader

# _bootstrap_external.py line 1453 (inside PathFinder.invalidate_caches):
from importlib.metadata import MetadataPathFinder

# _bootstrap_external.py line 1554 (inside PathFinder.find_distributions):
from importlib.metadata import MetadataPathFinder
```

These lazy imports are **deliberate** -- `_bootstrap_external.py` is frozen into the interpreter and cannot have top-level imports of high-level packages like `metadata` and `resources`. The comment at the top of the file warns: "When editing this code be aware that code executed at import time CANNOT reference any injected objects!"

**Cycle 3 is likely a tool artifact.** The `resources/__init__.py` import `from .abc import ResourceReader` resolves to `importlib.resources.abc` (the file `resources/abc.py`), NOT to `importlib.abc`. The tool's import resolver has a known limitation with sub-package relative imports that causes it to map this to the top-level `abc` module. Manual inspection confirms `importlib.resources` does not import `importlib.abc` -- it imports `importlib.resources.abc`, which is a leaf module with zero dependencies. **This cycle does not exist in practice.**

**Net real cycles: 0 (all detected cycles are either lazy-import-broken or false positives).**

This is significant: importlib has **zero real circular dependencies at import time** despite the tool reporting 3.

---

## 4. NK Metrics

### 4.1 Tool-Reported Metrics

| Metric | Value | Notes |
|--------|------:|-------|
| **N** | 24 | Number of modules |
| **K_total** | 24 | Total directed dependency edges |
| **K_avg** | 1.00 | Average dependencies per module |
| **K/N** | 0.042 | Dependency density ratio (lowest of any large package) |
| **K_max** | 4 | Maximum out-degree (`abc`: hub module) |
| **K_max_in** | 6 | Maximum in-degree (`abc`) |
| **Cycles (tool)** | 3 | 2 lazy-import-broken + 1 likely false positive |
| **Cycles (real)** | 0 | After manual inspection |
| **Composite (tool)** | **27.0** | 1.00 * 24 + 3 |
| **Composite (adjusted)** | **24.0** | 1.00 * 24 + 0 (removing non-real cycles) |
| **Hub concentration** | 17% | `abc` accounts for 4/24 edges |
| **Architecture** | distributed | Low coupling, many leaf modules |

### 4.2 Sub-Package Breakdown

| Sub-package | Modules | K_total (internal) | Leaf modules | Role |
|-------------|--------:|-------------------:|-------------:|------|
| Core (importlib/) | 9 | 17 | 1 (`_bootstrap`) | Import machinery |
| metadata/ | 7 | 1 | 6 | Package metadata |
| resources/ | 8 | 6 (adjusted) | 3 | Resource access |

The `metadata` sub-package is remarkably decoupled: 6 of 7 modules are leaves with zero internal dependencies. Only `metadata/__init__.py` has an outward dependency (on `abc`). This is clean sub-package design.

---

## 5. Comparison with Existing Data

### 5.1 Cross-Package Ranking by Composite Score

| Package | Lang | N | K_avg | K/N | Cycles | K_avg*N+Cycles | Architecture |
|---------|------|--:|------:|----:|-------:|---------------:|-------------|
| logging | Py | 3 | 1.00 | 1.000 | 0 | 3.0 | monolith |
| json | Py | 5 | 0.80 | 0.160 | 0 | 4.0 | facade |
| Express 5 | JS | 6 | 1.00 | 0.167 | 0 | 6.0 | facade |
| Express 4 | JS | 11 | 1.36 | 0.124 | 0 | 15.0 | facade + router |
| xml | Py | 22 | 1.09 | 0.050 | 2 | 26.0 | distributed |
| http.client | Py | 11 | 2.40 | 0.215 | 0 | 26.4 | hub-and-spoke |
| **importlib** | **Py** | **24** | **1.00** | **0.042** | **3 (0 real)** | **27.0 (24.0 adj.)** | **distributed** |
| unittest | Py | 13 | 2.08 | 2.077 | 1 | 27.0 | pipeline |
| Rust serde | Rust | 24 | 1.25 | 0.052 | 0 | 30.0 | trait-centric |
| argparse | Py | 29 | 1.66 | 1.655 | 0 | 48.1 | registry |
| requests | Py | 55 | 3.06 | 0.170 | 0 | 55.0 | framework |
| email | Py | 28 | 1.86 | 0.066 | 9 | 61.1 | facade + lazy |
| Go net/http | Go | 27 | 3.19 | 0.118 | 3 | 89.0 | monolithic |
| multiprocessing | Py | 23 | 3.61 | 0.157 | 19 | 102.0 | tangled |
| asyncio | Py | 33 | 3.85 | 0.117 | 1 | 128.0 | framework |

importlib lands at **27.0** (tool-reported) or **24.0** (adjusted), placing it in the same tier as `xml` (26.0), `http.client` (26.4), and `unittest` (27.0).

### 5.2 importlib vs. asyncio and multiprocessing: Why the Huge Gap

importlib (composite 27) vs. asyncio (128) and multiprocessing (102) is a **5x difference** despite all being large, critical stdlib packages. The explanation:

| Factor | importlib | asyncio | multiprocessing |
|--------|-----------|---------|-----------------|
| N | 24 | 33 | 23 |
| K_avg | **1.00** | **3.85** | **3.61** |
| K_total | 24 | 127 | 83 |
| Cycles | 3 (0 real) | 1 | 19 |

The difference is almost entirely in **K_avg**: importlib averages 1.0 dependency per module while asyncio averages 3.85. importlib achieves this through:

1. **Massive leaf layer**: 13 of 24 modules (54%) have zero internal dependencies
2. **Sub-package isolation**: metadata and resources are internally self-contained
3. **Bootstrap constraint**: _bootstrap and _bootstrap_external are designed to work before the import system exists, forcing zero-dependency architecture
4. **Lazy import discipline**: Cross-boundary imports (bootstrap -> metadata/resources) are always lazy

### 5.3 importlib vs. email: Similar N, Very Different K

Both have ~24-28 modules, but email (composite=61.1, 9 cycles) has nearly double the coupling. Email's MIME type hierarchy creates cross-module dependencies, while importlib's sub-packages are cleanly separated.

---

## 6. Structural Patterns

### 6.1 Architecture: Distributed with Bootstrap Core

importlib has a **three-zone** architecture:

```
Zone 1 — Bootstrap Core (frozen into CPython):
  _bootstrap (1,551 LOC, 0 deps)    — core import machinery
  _bootstrap_external (1,745 LOC)    — path-based import, lazy deps only

Zone 2 — Public API Layer:
  __init__      — entry point, wires bootstrap
  abc           — abstract base classes (HUB: K_out=4, K_in=6)
  machinery     — re-exports from bootstrap
  util          — utility functions
  _abc          — Loader ABC

Zone 3 — Sub-packages (high isolation):
  metadata/     — 7 modules, 1 outward dep (abc), 6 leaf modules
  resources/    — 8 modules, ~1 outward dep (resources.abc), 3 leaf modules

Compatibility shims (deprecated):
  readers       — forwards to resources.readers
  simple        — forwards to resources.simple
```

This is a **layered + isolated sub-package** architecture. The bootstrap modules form the foundation, the API layer provides abstractions, and the sub-packages extend functionality with minimal cross-coupling.

### 6.2 Hub Analysis: `abc` is the Gravitational Center

The `abc` module (in-degree 6, out-degree 4) is the primary structural hub. It:
- **Defines** MetaPathFinder, PathEntryFinder, ResourceLoader, InspectLoader, ExecutionLoader, FileLoader, SourceLoader
- **Imports from** _abc, _bootstrap_external, machinery, resources
- **Is imported by** metadata, resources, resources._adapters, resources._common, resources.readers, resources.simple

This is a classic **interface hub** pattern: many modules depend on the ABCs it defines. The coupling is directional (dependents import abc, not the reverse at import time), which is the healthy form of hub coupling.

### 6.3 Leaf Modules: 13 of 24 (54%)

| Module | Lines | In-degree | Sub-package |
|--------|------:|----------:|------------|
| `_bootstrap` | 1,551 | 4 | core |
| `metadata._adapters` | 89 | 0 | metadata |
| `metadata._collections` | 30 | 0 | metadata |
| `metadata._functools` | 104 | 0 | metadata |
| `metadata._itertools` | 73 | 0 | metadata |
| `metadata._meta` | 63 | 0 | metadata |
| `metadata._text` | 99 | 0 | metadata |
| `resources._itertools` | 38 | 0 | resources |
| `resources._legacy` | 120 | 0 | resources |
| `resources.abc` | 173 | 0* | resources |
| `resources._adapters` | 168 | 1** | resources |
| `resources._common` | 207 | 1** | resources |
| `resources.readers` | 144 | 1 | resources |

*resources.abc has in-degree 0 from the tool's perspective but is actually imported by resources modules via relative imports that the tool partially misresolves.

**54% leaf modules** is the highest ratio of any large package analyzed (asyncio has 24%, email has ~25%). This reflects importlib's design philosophy: sub-package internal modules are self-contained utilities that don't reach back into the package's core.

### 6.4 The Bootstrap Constraint as Architectural Discipline

The most interesting structural feature of importlib is the **bootstrap constraint**: `_bootstrap.py` and `_bootstrap_external.py` are frozen into the CPython interpreter at compile time. They cannot have any imports that depend on the full import system being available. This constraint forces:

1. `_bootstrap` has **zero** internal dependencies
2. `_bootstrap_external` uses only **lazy imports** for metadata/readers (inside method bodies)
3. The `__init__.py` carefully sequences bootstrap wiring before allowing any other imports

This is Python's import system importing itself -- a bootstrapping problem that naturally produces clean, minimal coupling.

---

## 7. Is importlib Over-Coupled?

### Verdict: No. importlib is one of the least coupled large packages in the stdlib.

Evidence:

1. **K_avg = 1.00** -- the lowest of any package with N > 10
2. **K/N = 0.042** -- the second-lowest density ratio after email (0.066), but with far fewer cycles
3. **Zero real cycles** -- all detected cycles are either lazy-import-broken or tool artifacts
4. **54% leaf modules** -- the highest leaf ratio of any large package
5. **Sub-package isolation** -- metadata and resources are nearly self-contained

### Comparison with expectations:

importlib is Python's import machinery -- one might expect it to be highly coupled because it sits at the foundation of the entire language. Instead, it is **remarkably clean**. The reasons:

1. **The bootstrap constraint** forces minimal coupling at the core
2. **Sub-packages were added later** (metadata in 3.8, resources in 3.7) with clean boundaries
3. **The ABC pattern** centralizes interface definitions in one hub module, allowing dependents to couple only to abstractions
4. **Lazy imports** in _bootstrap_external break what would otherwise be cycles

This is an example of **forced discipline producing good architecture** -- the bootstrapping requirement left no choice but to minimize coupling.

---

## 8. Refactoring Suggestions

### 8.1 Tool Output

The tool suggested extracting `abc` to eliminate all 3 detected cycles (100% reduction). However, since the real cycle count is 0, **no refactoring is needed for cycle reduction**.

### 8.2 Potential Improvements (for coupling reduction, not cycle breaking)

1. **Deprecation cleanup**: `readers.py` and `simple.py` are compatibility shims that could be removed when their deprecation period ends, reducing N from 24 to 22 and eliminating 4 edges.

2. **Tool improvement**: The `nk_analyze.py` import resolver should distinguish lazy imports (inside function/method bodies) from top-level imports, and should correctly resolve relative imports within sub-packages. This would eliminate the 3 false-positive cycles.

3. **`abc` module splitting**: The `abc` module serves double duty as both the import ABC hub and the resources ABC backward-compatibility shim (line 18: `from .resources import abc as _resources_abc`). When the deprecation in `__getattr__` completes (targeted for Python 3.14), this backward-compat import can be removed, reducing `abc`'s out-degree from 4 to 3.

---

## 9. Key Findings

1. **importlib is structurally clean** -- N=24, K=24, composite=27.0 (or 24.0 adjusted), placing it in the same tier as xml and unittest despite being a larger, more critical package.

2. **Zero real circular dependencies** -- all 3 tool-detected cycles are either broken by lazy imports (2) or are tool artifacts from sub-package import misresolution (1).

3. **The bootstrap constraint is an architectural gift** -- by requiring _bootstrap and _bootstrap_external to work before the import system exists, Python's design forces the two largest modules (51% of code) to have minimal coupling.

4. **54% leaf modules** -- the highest ratio of any large package analyzed, driven by the metadata and resources sub-packages keeping their internal utilities isolated.

5. **`abc` is the sole hub** (K_in=6, K_out=4) -- a healthy interface-hub pattern where dependents import abstractions, not implementations.

6. **Sub-package isolation works** -- metadata (7 modules, 1 outward dep) and resources (8 modules, ~1 outward dep) demonstrate that Python sub-packages can achieve near-zero cross-boundary coupling when deliberately designed.

7. **Tool limitation identified** -- `nk_analyze.py` has a sub-package relative import resolution issue that produces false-positive cycles. This affects any package with nested sub-packages (importlib/resources/, importlib/metadata/).

8. **K_avg = 1.00 at N = 24** -- importlib proves that large module count does not require high coupling. Compare with asyncio (N=33, K_avg=3.85) and multiprocessing (N=23, K_avg=3.61).

9. **Lazy imports confirm F44 pattern** -- the 4 lazy imports in _bootstrap_external all serve to break potential circular dependencies with metadata and resources, consistent with the pattern seen in asyncio and email.

---

## Appendix A: Tool Limitations for This Package

The `nk_analyze.py` tool has two limitations that affect importlib's analysis:

### A.1 No Lazy Import Detection

The tool counts all `import` and `from...import` statements regardless of whether they occur at module top-level or inside function/method bodies. For `_bootstrap_external`, all 4 imports of metadata/readers are inside methods and are thus lazy imports that do not create real circular dependencies at import time.

**Impact**: 2 of 3 detected cycles are lazy-import-broken.

### A.2 Sub-Package Relative Import Misresolution

For files inside `importlib/resources/`, the tool's `extract_imports()` function fails to correctly resolve relative imports to the `resources` sub-package. When `importlib/resources/__init__.py` does `from .abc import ResourceReader`, the tool resolves this to the top-level `abc` module (`importlib.abc`) rather than `resources.abc` (`importlib.resources.abc`). This is caused by a `ValueError` exception in the `Path.relative_to()` call when the sub-package path doesn't match the expected `pkg_base / package_name` structure.

**Impact**: 1 false-positive cycle (`abc -> resources -> abc`) and likely undercounting of edges within the resources sub-package.

### A.3 Sub-Package Internal Dependencies Not Fully Captured

For the same reason, imports like `from ._common import ...` inside `importlib/resources/` are resolved to `_common` rather than `resources._common`, and since `_common` is not a valid module name, these edges are silently dropped. The actual internal coupling within the `resources` sub-package is slightly higher than the tool reports.

**Impact**: K_total is likely underreported by 3-5 edges within the resources sub-package. This would raise K_avg to approximately 1.12-1.21 and composite to approximately 27-29. The overall assessment (low coupling, clean architecture) remains unchanged.
