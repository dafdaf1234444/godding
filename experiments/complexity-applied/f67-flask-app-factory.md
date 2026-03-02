# F67: Does Flask's App Factory Pattern Reduce Cycles?
Date: 2026-02-26 | Status: RESOLVED — YES

## Question
Flask has 34 cycles (composite=130.0). The app factory pattern is the
recommended way to structure Flask applications. Does it actually reduce
the internal cycle count?

## Method
Simulated module extraction using nk_analyze.py's --suggest-refactor output
and manual cycle analysis. Tested three scenarios:
1. Remove `globals.py` (simulates pure app factory, no proxy globals)
2. Remove `globals.py` + `sansio.app` (simulates full extraction)
3. Identify which cycles involve `globals`

## Results

| Scenario | N | K_avg | Cycles | Composite | Cycle Reduction |
|----------|---|-------|--------|-----------|-----------------|
| Current | 24 | 4.00 | 34 | 130.0 | — |
| No globals | 23 | 3.48 | 24 | 104.0 | 29% |
| No globals + sansio.app | 22 | 2.82 | 15 | 77.0 | 56% |

## Analysis

### globals.py is the cycle hub
- `globals.py` imports 4 modules: app, ctx, sessions, wrappers
- `globals.py` is imported by 12 modules (75% of Flask)
- It participates in 15/34 cycles (44%)
- The bi-directional dependency (globals→ctx→globals) is the root cause

### The app factory pattern helps but doesn't fix everything
Removing `globals.py` eliminates 10 cycles (29% reduction). But 24 cycles
remain because the coupling between sansio.app, helpers, wrappers, and
debughelpers creates independent cycle chains.

The app factory pattern addresses the *usage* pattern (no global app instance)
but doesn't restructure the *import* pattern. Flask's modules still import
each other circularly regardless of how users structure their code.

### The real fix would require 2 extractions
1. Extract `globals.py` → eliminates 10 cycles (29%)
2. Extract `sansio.app` → eliminates 9 more cycles (total 56%)
Combined composite drops from 130.0 to 77.0 — comparable to click (68.0).

## Connection to B10
This validates P-051 (cycle participation count predicts extraction targets):
- `sansio.app` participates in 20/34 cycles → best extraction candidate
- `globals.py` participates in 15/34 → second best
- Together they account for 56% of all cycles

## Conclusion
F67: **YES**, the app factory pattern concept (eliminating globals) reduces
cycles by 29%. But the full 56% reduction requires also extracting sansio.app.
Flask's tangled architecture (K_avg=4.0) creates cycles that persist even
without the globals pattern.
