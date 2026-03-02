# Stdlib NK Comparison — unittest vs argparse vs logging
**Date**: 2026-02-26 | **Session**: 43 | **Method**: 3 parallel Task agents with worktree isolation

## Summary Table

| Package | N | K_avg | K_max | K/N | Cycles | Architecture |
|---------|---|-------|-------|-----|--------|--------------|
| json | 5 | 0.16 | — | 0.16 | 0 | Facade + engine |
| http.client | 24 | — | 10 | 0.068 | 0 | God-class risk |
| email | 28 | — | — | 0.06 | 9 | Lazy-import cycles |
| **unittest** | 13 | 2.08 | 8 (__init__) / 3 (core) | 0.173* | 1 (managed) | Hub-spoke + pipeline spine |
| **argparse** | 29 cls | 1.62 raw / 1.21 adj | 15 (_ActionsContainer) | 1.62 raw | 2 (deliberate) | Honest monolith (registry + god-class) |
| **logging** | 3 | 1.00 | 2 (config) | 1.00 | 0 | Monolith-with-satellites |

*unittest density = 0.173 (27 edges / 156 possible)

## Cross-cutting findings

### 1. Scale matters more than metrics
- logging looks clean at module level (N=3, 0 cycles) but __init__.py contains 8 subsystems and 2,345 lines
- argparse looks terrible at raw K/N (1.62) but adjusting for soft coupling (registry lookups) drops it to 1.21
- unittest has highest density (0.173) but best cycle discipline of any medium-sized package

### 2. Coupling type matters
- **Hard coupling** (direct instantiation, method calls): real complexity driver
- **Soft coupling** (registry lookups, lazy imports): inflates K but manageable
- argparse's 12 register() calls inflate K_max to 15, but they're lookup table entries, not call-graph edges

### 3. Architecture patterns from stdlib
| Pattern | Example | Signature | Maintenance prediction |
|---------|---------|-----------|----------------------|
| Hub-spoke + spine | unittest | High density, low K_max in core, managed cycles | Stable, refactorable |
| Honest monolith | argparse | Single file, god-class + strategy pattern, high raw K | Stable but hard to split |
| Monolith-with-satellites | logging | Low N, clean inter-module DAG, hidden intra-module complexity | Deceptively simple |
| Facade + engine | json | Very low K/N, small N | Easiest to maintain |

### 4. Cycle management strategies observed
- **unittest**: lazy import (case._log cycle broken by import-inside-method)
- **argparse**: inner-factory pattern (deliberate, not pathological)
- **email**: lazy imports for 9 cycles (scale problem, not well-managed)
- **logging**: zero cycles (clean layered DAG)

## New principle
P-083: NK analysis must be run at multiple granularities (file, class, function). Single-scale analysis masks hidden complexity — logging's clean inter-module DAG hides 8 subsystems; argparse's raw K/N is misleading without coupling-type adjustment.

## What this resolves
This is the "real domain work" that COURSE-CORRECTION asked for. 3 stdlib packages analyzed in parallel using native Task tool + worktree isolation. The spawn loop is closed.
