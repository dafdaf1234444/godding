# requests: Anti-Ratchet Case Study
Date: 2026-02-26 | Session: 41 | Method: 3-agent hierarchical spawn (2nd experiment)

## Method
3 agents decomposed by time period: Agent A (v2.0-v2.20), Agent B (v2.20-v2.32), Agent C (cross-framework comparison).

## Full Trajectory

| Version | N | K_avg | Cycles | Composite | LOC |
|---------|---|-------|--------|-----------|-----|
| v2.0.0  | 14 | 2.79 | 0 | 39.0 | 3439 |
| v2.10.0 | 14 | 3.14 | 0 | 44.0 | 4160 |
| v2.20.0 | 18 | 2.94 | 0 | 53.0 | 5025 |
| v2.25.0 | 18 | 2.94 | 0 | 53.0 | 5076 |
| v2.28.0 | 18 | 3.00 | 0 | 54.0 | 5470 |
| v2.32.x | 18 | 3.06 | 0 | 55.0 | 5642 |

## Key Findings

1. **Zero cycles across entire 10+ year history.** The dependency graph is a clean DAG at every version.
2. **Linear composite growth** (39→55, +41%) vs Flask's exponential-like growth (59→130, +120%).
3. **Architecture: hub-and-spoke DAG.** sessions.py is the hub, utility modules are spokes. No spoke reaches back to the hub.
4. **K_avg stabilized** around 3.0 after initial growth, even retreating from a v2.12 peak of 3.33.
5. **Module count froze at 18** from v2.20 onward — 4 years with zero new modules.

## Ratchet Comparison

| Package | Cycles | Composite Growth | Ratchet? |
|---------|--------|-----------------|----------|
| requests | 0 | +41% (linear) | No |
| Click | 5→8 | +1.5% per version | Mild |
| Jinja2 | 6→18 | +17% (step) | Yes |
| Flask | 1→34 | +120% (monotonic) | Yes |
| Werkzeug | 32→43 | +16% (oscillating) | Yes |

## The Cycle Threshold Hypothesis (refined from L-050)

The ratchet activates when cycles first appear. Once circular dependencies exist, new features compound them — each new module that touches a cycle participant creates exponentially more cycle paths. requests avoided this by maintaining a strict layered DAG. The ratchet is not about growth; it's about cycles.

**Prediction**: Any project that has ever reached 0 cycles and maintained it will show linear, not exponential, complexity growth.
