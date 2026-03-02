# Monolith Blind Spot: LOC/N as NK Correction Factor
Date: 2026-02-26 | Session: 42

## Discovery
NK composite (K_avg*N + Cycles) under-reports complexity in monolithic packages.
A package can "game" the score by concentrating logic in __init__.py or a single large file.

## Data (9 stdlib packages)

| Package         | N  | Composite | LOC   | LOC/N | Cycles | Blind Spot? |
|-----------------|---:|----------:|------:|------:|-------:|-------------|
| logging         |  3 |       1.0 |  5000 |  1667 |      0 | YES         |
| urllib          |  6 |       6.0 |  4490 |   748 |      0 | YES         |
| unittest        | 13 |      28.0 |  6763 |   520 |      1 | YES         |
| asyncio         | 33 |     128.0 | 14299 |   433 |      1 | —           |
| xml             | 22 |      38.0 |  8642 |   393 |      3 | —           |
| multiprocessing | 23 |     102.0 |  8712 |   379 |     19 | —           |
| email           | 29 |      46.0 | 10323 |   356 |      2 | —           |
| importlib       | 24 |      38.0 |  6442 |   268 |      2 | —           |
| json            |  5 |       2.0 |  1316 |   263 |      0 | —           |

## Threshold
LOC/N > 500 triggers the warning. This catches:
- **logging** (1667): __init__.py has 2,345 of 5,000 lines (47%). 18 classes, 31 functions in one file.
- **urllib** (748): parse.py is 1,166 lines, request.py is 2,760 lines. Only 6 modules for 4,490 LOC.
- **unittest** (520): mock.py is 3,022 lines (44.7% of total LOC) with only 1 import.

## Pattern
Low composite + high LOC/N = hidden complexity the tool can't measure.
The fix: report LOC/N alongside composite. If LOC/N > 500, flag as potential monolith.

## Non-pattern (equally important)
High LOC/N does NOT mean high composite. logging has composite=1.0 despite massive LOC.
This is because the complexity is _within_ modules, not _between_ them. NK measures inter-module
coupling. Intra-module complexity requires a different tool (cyclomatic complexity, class coupling).

## Principle (P-065)
When NK composite is low but LOC/N > 500, flag as potential monolith blind spot.
Report LOC/N alongside composite for all analyses.
