# NK Analysis: Swarm Tool Coupling (v2)

## Summary
Applied NK landscapes to the swarm's 11 Python tools. Compared with v1 (7 tools) to track coupling evolution.

## NK Parameters (v2 → v1)
- **N** = 11 tools (was 7)
- **K_avg** = 1.09 (was 1.29) — dropped as new tools are loosely coupled
- **K/N** = 0.099 (was 0.18) — improved, well below 0.3 threshold
- **K_max** = 3 (was 2) — evolve.py is the new hub

## Coupling Map
```
self_evolve.py (planner)
  └── evolve.py (pipeline)
        ├── agent_swarm.py (bridge)
        │   └── [genesis.sh]
        ├── swarm_test.py (evaluate)
        │   └── validate_beliefs.py (core)
        └── merge_back.py (extract)

colony.py (orchestrator)
  ├── swarm_test.py
  └── merge_back.py

genesis_evolve.py (template evolution)
  └── swarm_test.py

swarm_integration_test.py (test harness)
  └── validate_beliefs.py

[Independent]
  ├── bulletin.py (side channel)
  └── session_tracker.py (metrics)
```

## Per-Tool K Values
| Tool | K | Depends on |
|------|---|-----------|
| validate_beliefs.py | 0 | (core, no deps) |
| merge_back.py | 0 | (standalone analysis) |
| bulletin.py | 0 | (standalone) |
| session_tracker.py | 0 | (standalone) |
| agent_swarm.py | 1 | genesis.sh |
| genesis_evolve.py | 1 | swarm_test |
| self_evolve.py | 1 | evolve |
| swarm_test.py | 2 | validate_beliefs, genesis.sh |
| colony.py | 2 | swarm_test, merge_back |
| swarm_integration_test.py | 2 | validate_beliefs, genesis.sh |
| evolve.py | 3 | agent_swarm, swarm_test, merge_back |

## Evolution Trend
| Metric | v1 (7 tools) | v2 (11 tools) | Direction |
|--------|-------------|---------------|-----------|
| N | 7 | 11 | +57% |
| K_avg | 1.29 | 1.09 | -15% (healthier) |
| K/N | 0.18 | 0.099 | -45% (healthier) |
| K_max | 2 | 3 | +50% |
| Independents | 2 | 4 | +100% |
| Hub | validate (3 callers) | validate (3), evolve (1) | stable |

## Assessment
- **Near-decomposable**: Yes (K/N = 0.10 << 0.3)
- **Trend**: Coupling is DECREASING as tools are added — healthy growth
- **Pattern**: New tools compose existing tools via subprocess (loose coupling)
- **Risk**: evolve.py is becoming a secondary hub (K=3). Monitor.
- **Key insight**: The subprocess-call pattern inherently produces low K because
  tools don't share state — they exchange data via files and exit codes.
