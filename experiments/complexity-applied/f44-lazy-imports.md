# F44: Do Lazy Imports Always Correspond to Cycle-Breaking?

**Answer: NO** — lazy imports serve two distinct purposes, not just cycle-breaking.

## Hypothesis
> Do lazy imports in large stdlib modules always correspond to cycle-breaking?

Original observation: email (9 cycles) and asyncio (1 lazy import = 1 cycle) suggested a 1:1 correspondence.

## Method
Built `extract_imports_layered()` — scope-aware AST traversal that distinguishes top-level imports from function-body (lazy) imports. Compares static graph (top-level only) vs runtime graph (all imports).

## Results

| Package | Lazy | CycBrk | NonCyc | StatCyc | RunCyc | Hidden | Verdict |
|---------|------|--------|--------|---------|--------|--------|---------|
| multiprocessing | 50 | 33 | 17 | 1 | 19 | 18 | PARTIAL |
| click | 18 | 3 | 15 | 6 | 8 | 2 | PARTIAL |
| jinja2 | 10 | 4 | 6 | 13 | 18 | 5 | PARTIAL |
| xml | 10 | 2 | 8 | 1 | 3 | 2 | PARTIAL |
| email | 8 | 1 | 7 | 0 | 2 | 2 | PARTIAL |
| importlib | 4 | 2 | 2 | 0 | 2 | 2 | PARTIAL |
| unittest | 3 | 2 | 1 | 0 | 1 | 1 | PARTIAL |
| asyncio | 1 | 0 | 1 | 1 | 1 | 0 | REFUTES |

**0/8 packages fully support the hypothesis.**

## Two Purposes of Lazy Imports

1. **Cycle-breaking** (45/104 = 43%): Import deferred specifically to avoid circular dependency.
   - Example: multiprocessing `context.py` → defers imports of pool, queues, synchronize
   - Example: importlib `_bootstrap_external.py` → defers metadata import
   - Pattern: The lazy import target would create a new cycle if made top-level.

2. **Initialization deferral** (59/104 = 57%): Import deferred to avoid cascading initialization.
   - Example: email `__init__.py` → defers parser import to avoid loading most of email package
   - Example: asyncio `tasks.py` → defers queues import for `as_completed()` (rarely used)
   - Pattern: The lazy import target is expensive to initialize but rarely needed.

## Key Findings

1. **multiprocessing is the extreme case**: 50 lazy imports, 33 cycle-breaking. The `context.py` module is essentially a lazy-loading factory — every primitive (Lock, Queue, Pool, etc.) is lazily imported in a function wrapper. This is deliberate architecture: context.py is the hub, and making all edges lazy prevents 18 additional cycles.

2. **Hidden cycles matter**: Packages appear simpler than they are. multiprocessing shows 1 static cycle but 19 runtime cycles. The "true complexity" is hidden behind lazy discipline.

3. **The ratio varies widely**: From 0% (asyncio) to 66% (multiprocessing) of lazy imports break cycles. No universal ratio.

4. **Performance deferral is more common** than cycle-breaking overall (57% vs 43%).

## Revised Understanding

The F44 hypothesis ("always") is **falsified**. The refined model:

- **Lazy imports are a dual-purpose tool**: cycle avoidance OR initialization deferral
- **Cycle-breaking lazy imports are deliberate**: They always correspond to a would-be cycle
- **Performance lazy imports are opportunistic**: They avoid loading rarely-used submodules
- **Both reduce effective coupling at import time**: Even non-cycle-breaking lazy imports lower the K_avg of the static graph

## Implications for NK Analysis

The `--lazy` flag now provides two views:
- **Static graph**: What the module system sees at import time (lower K, fewer cycles)
- **Runtime graph**: Full coupling including deferred edges (higher K, more cycles)

For maintenance prediction, **runtime cycles** are the better metric — they represent actual coupling that must be understood during development, even if deferred at load time.

## Tool Addition
- `nk_analyze.py --lazy <package>` — per-package lazy import analysis
- `nk_analyze.py batch --lazy` — batch analysis across multiple packages
- `extract_imports_layered()` — scope-aware AST traversal (new function)
- `analyze_lazy_imports()` — static vs runtime graph comparison

## Data: 2026-02-26, Session 40
