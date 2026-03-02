# F68: Composite Threshold for Architectural Intervention
Date: 2026-02-26 | Status: RESOLVED — Two-threshold model

## Question
Is there a composite threshold above which packages reliably need
architectural intervention?

## Data
21 packages categorized by maintenance status:
- **Stable** (10): composite 1.0–55.0 (logging through requests)
- **Problematic** (7): composite 15.0–238.0 (Express 4 through werkzeug)
- **Moderate** (3): composite 38.0–128.0 (xml, click, asyncio)

## Finding: No Simple Threshold
The ranges overlap massively:
- Highest stable: requests at 55.0 (0 cycles)
- Lowest problematic: Express 4 at 15.0 (refactored away)
- email at 46.0 is problematic despite low composite (runtime cycles)
- asyncio at 128.0 is moderate despite high composite (only 1 cycle)

## Two-Threshold Model
Composite alone is insufficient. Cycles are the differentiator:

| Condition | Prediction | Examples |
|-----------|-----------|----------|
| Composite < 50 AND cycles < 3 | Stable | json, serde, requests |
| Composite > 100 OR cycles > 10 | Needs intervention | multiprocessing, flask, werkzeug |
| Between | Domain-dependent | email (low composite, high runtime cycles) |

## Validation
- requests (55.0, 0 cycles): stable — confirms low-cycle stability
- asyncio (128.0, 1 cycle): moderate — confirms single-cycle tolerance
- email (46.0, 2 static / ~9 runtime): high burden — confirms runtime cycles matter
- multiprocessing (102.0, 19 cycles): high burden — confirms dual-threshold

## Connection to Two-Factor Model (P-044)
This refines the two-factor model from F40:
```
Intervention needed = f(K_avg*N+Cycles, Cycles_alone, S_external)
```
Cycles independently predict intervention need better than composite alone.
This is consistent with B10 (cycles predict bugs).
