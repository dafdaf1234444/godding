# F73: Lazy-Import Ratio as Architectural Debt Signal

**Date**: 2026-02-26 | **Session**: 40

## Question
Is there a lazy-import ratio (lazy/total imports) that signals architectural debt?

## Answer: NO — the ratio classifies purpose, not quality

### Data

| Package | L/TotK | CB/L | Bugs | Pattern |
|---------|--------|------|------|---------|
| multiprocessing | 60% | 66% | 176 | DELIBERATE |
| click | 32% | 17% | - | PERF_DEFER |
| xml | 29% | 20% | 31 | PERF_DEFER |
| email | 18% | 12% | 156 | PERF_DEFER |
| jinja2 | 11% | 40% | - | MIXED |
| importlib | 11% | 50% | - | MIXED |
| unittest | 11% | 67% | 39 | DELIBERATE |
| asyncio | 1% | 0% | 52 | PERF_DEFER |

L/TotK = lazy imports / total imports. CB/L = cycle-breaking / lazy.

### Finding
The CB/L ratio classifies **why** lazy imports exist, not whether the code is healthy:
- **DELIBERATE** (CB/L > 50%): Lazy imports manage cycles intentionally.
- **PERF_DEFER** (CB/L < 20%): Lazy imports avoid initialization overhead.
- **MIXED** (20-50%): Both purposes.

None of these categories predict bug count. multiprocessing (DELIBERATE, 66% CB) has the most bugs; email (PERF_DEFER, 12% CB) has the second most. Runtime cycles (F72) remain the dominant predictor.

### What lazy ratio DOES tell you
- High L/TotK (>30%) = significant hidden coupling. The static graph understates complexity.
- CB/L > 50% = package has architectural cycle discipline (imports are deliberately managed).
- CB/L < 20% = package uses lazy imports for startup speed, not architecture.

The ratio is a diagnostic, not a predictor.
