# F53: Two-Factor Model Validation — Extended with Static vs Runtime

**Date**: 2026-02-26 | **Session**: 40

## Original Model (F68)
Composite < 50 AND cycles < 3 → stable; composite > 100 OR cycles > 10 → needs intervention.

## New Insight: Static vs Runtime Cycles
The `--lazy` analysis (F44) reveals that `analyze_package()` already counts runtime cycles (all imports). Static cycles (top-level only) are often much lower.

| Package | N | K_avg | StCyc | RtCyc | StComp | RtComp | 2Factor(static) |
|---------|---|-------|-------|-------|--------|--------|-----------------|
| json | 5 | 0.40 | 0 | 0 | 2.0 | 2.0 | STABLE |
| logging | 3 | 0.33 | 0 | 0 | 1.0 | 1.0 | STABLE |
| http | 5 | 0.40 | 0 | 0 | 2.0 | 2.0 | STABLE |
| unittest | 13 | 2.08 | 0 | 1 | 27.0 | 28.0 | STABLE |
| email | 29 | 1.52 | 0 | 2 | 44.1 | 46.0 | STABLE |
| urllib | 6 | 1.00 | 0 | 0 | 6.0 | 6.0 | STABLE |
| collections | 2 | 0.00 | 0 | 0 | 0.0 | 0.0 | STABLE |
| importlib | 24 | 1.50 | 0 | 2 | 36.0 | 38.0 | STABLE |
| xml | 22 | 1.59 | 1 | 3 | 36.0 | 38.0 | STABLE |
| requests | 18 | 3.00 | 0 | 0 | 54.0 | 54.0 | MODERATE |
| click | 16 | 3.56 | 6 | 8 | 63.0 | 65.0 | MODERATE |
| multiprocessing | 23 | 3.61 | 1 | 19 | 84.0 | 102.0 | MODERATE |
| jinja2 | 25 | 3.64 | 13 | 18 | 104.0 | 109.0 | INTERVENE |
| asyncio | 33 | 3.85 | 1 | 1 | 128.1 | 128.0 | INTERVENE |

## Key Findings

### 1. Static cycles change the model predictions
- **multiprocessing**: INTERVENE (19 runtime) → MODERATE (1 static). The 50 lazy imports are deliberate architecture, not code smell.
- **email**: 0 static cycles confirms lazy import discipline keeps static graph acyclic.
- **unittest**: 0 static cycles — the case→_log cycle is deliberately broken by lazy import.

### 2. Lazy import ratio as signal
| Package | Lazy | CycBrk | Ratio | Interpretation |
|---------|------|--------|-------|---------------|
| multiprocessing | 50 | 33 | 66% | Deliberate factory architecture |
| click | 18 | 3 | 17% | Mostly init deferral |
| jinja2 | 10 | 4 | 40% | Mixed |
| xml | 10 | 2 | 20% | Mostly init deferral |
| email | 8 | 1 | 12% | Almost all init deferral |

### 3. Three-layer model (refined)
The two-factor model should consider THREE metrics:

| Layer | What it measures | When to use |
|-------|-----------------|-------------|
| **Static composite** | Import-time coupling | Build/deployment risk |
| **Runtime composite** | Full coupling | Maintenance burden |
| **Hidden cycles** (runtime - static) | Lazy import discipline | Architecture health |

**Refined thresholds:**
- Static composite < 50 AND static cycles < 3 → STABLE at import time
- Runtime composite > 100 OR runtime cycles > 10 → needs maintenance attention
- High hidden cycles + low static cycles = good architecture (e.g., multiprocessing)
- High static cycles = architectural debt (e.g., jinja2 with 13 static)

### 4. New data points confirm model
The 3+ additional data points (click, jinja2, importlib) validate the two-threshold model:
- click (63/65, 6 static): MODERATE — matches reality (active development, manageable)
- jinja2 (104/109, 13 static): INTERVENE — matches reality (known complex template engine)
- importlib (36/38, 0 static): STABLE — matches reality (well-designed, lazy discipline)

## Conclusion
F53 is now validated with 14 packages. The static vs runtime distinction from F44 adds a third dimension that improves the model. Packages with high hidden-cycle count but low static cycles are *well-designed complex systems* (multiprocessing), not problematic ones.
