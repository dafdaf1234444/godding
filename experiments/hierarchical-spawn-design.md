# Hierarchical Self-Improving Spawn Architecture
Date: 2026-02-26 | Session: 41

## The Vision
The swarm should operate at multiple levels simultaneously:
- **Top level**: Holds high-level goals, decomposes tasks, evaluates results
- **Sub-swarms**: Execute decomposed tasks with different approaches
- **Feedback loop**: Parent improves spawn strategy based on what worked

## Current State (what exists)
1. `evolve.py` — init/harvest/integrate pipeline for child swarms
2. `spawn_coordinator.py` — plan/prompts/evaluate for parallel agents
3. `colony.py` — multi-child orchestration with viability comparison
4. `self_evolve.py` — identifies FRONTIER questions suitable for child investigation
5. `genesis_evolve.py` — uses child data to improve genesis template
6. `bulletin.py` — inter-swarm communication (typed append-only messages)

## What's Missing: The Self-Improvement Loop

### Level 1: Task Decomposition (HAVE)
Parent decomposes task → spawns agents → collects results.
Demonstrated: 2 successful spawn experiments this session (Pallets trajectory, requests anti-ratchet).

### Level 2: Spawn Quality Feedback (NEED)
After collecting results, parent should:
- Score each agent's output (quality, novelty, variety)
- Identify what made good agents good (prompt specificity? data assignment?)
- Update spawn strategy for next round

### Level 3: Meta-Improvement (NEED)
The swarm should:
- Track spawn success rates over time
- Learn which task decomposition strategies produce highest variety
- Auto-tune: "last time data-decomposition worked better than method-decomposition"
- Feed improvements back into spawn_coordinator.py itself

## Proposed Architecture

```
┌─────────────────────────────────────┐
│          TOP-LEVEL SWARM            │
│  Goals, decomposition, evaluation   │
│  spawn_coordinator.py + evolve.py   │
├─────────────────────────────────────┤
│         SPAWN STRATEGY LAYER        │
│  spawn-history.json tracks:         │
│  - past spawns + quality scores     │
│  - decomposition method used        │
│  - variety achieved                 │
│  - which agents produced novel      │
│    insights vs redundant ones       │
├─────────┬───────────┬───────────────┤
│ Agent A │ Agent B   │ Agent C       │
│ (data1) │ (data2)   │ (data3)       │
│         │           │               │
│ result  │ result    │ result        │
└────┬────┴─────┬─────┴───────┬───────┘
     │          │             │
     ▼          ▼             ▼
┌─────────────────────────────────────┐
│        SYNTHESIS + SCORING          │
│  - Cross-agent pattern detection    │
│  - Variety measurement (Jaccard)    │
│  - Quality scoring                  │
│  - Novel insight extraction         │
├─────────────────────────────────────┤
│        FEEDBACK TO STRATEGY         │
│  - Update spawn-history.json        │
│  - Adjust decomposition approach    │
│  - Refine agent prompt templates    │
└─────────────────────────────────────┘
```

## Concrete Next Steps (small, buildable)

### 1. spawn-history.json (~30 lines in spawn_coordinator.py)
After each spawn experiment, record:
```json
{
  "id": "spawn-20260226-...",
  "task": "...",
  "decomposition": "by-data",
  "agents": 3,
  "quality_avg": 1.8,
  "variety": 0.72,
  "novel_insights": 2,
  "lesson_produced": "L-052"
}
```

### 2. Strategy selection (~20 lines)
Before spawning, check history:
- If by-data worked well last time → use by-data again
- If variety was low → try different decomposition
- If quality was low → add more specific prompts

### 3. Cross-spawn collaboration
Sub-agents can already read bulletins from siblings via `bulletin.py sync`.
Missing: sub-agents posting intermediate findings that other agents can build on.
This requires sequential spawning (A runs first, B reads A's bulletin, C reads A+B).

## Design Principles
- P-057: Decompose by data, not by method (validated by experiments)
- P-056: Complexity is a ratchet (applies to the spawn system itself — keep it simple)
- P-007: Work/meta ratio (don't over-engineer the spawn system)
