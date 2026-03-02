# F69: Context Limit Coordination — Design Document
Date: 2026-02-26 | Status: Prototype

## Problem Statement
When CLAUDE.md + INDEX.md + knowledge files exceed a single session's context window,
how should spawns coordinate? Currently each session loads ~78 mandatory lines and
routes to relevant subset. But as knowledge grows, even the mandatory load will
need to shrink, and no single agent will be able to hold the full picture.

## Current State
- Total knowledge: 5120 lines (~20K tokens)
- Mandatory load: 78 lines (~312 tokens)
- Context window: ~200K tokens (current model)
- Growth rate: ~500 lines/session (tools + lessons + experiments)
- **Estimated sessions until context limit**: ~360 sessions at current growth rate
  (but growth accelerates as tools get more complex)

## Architecture Levels

### Level 0: Single Session (current — works up to ~50K tokens knowledge)
```
Session → reads all mandatory files → works → commits
```
No coordination needed. Every session can hold the full picture.

### Level 1: Context Router (implemented — works up to ~200K tokens)
```
Session → context_router.py selects relevant files → reads subset → works
```
The context router (tools/context_router.py) selects files based on task keywords.
Each spawn gets only what it needs. Parent sessions still hold enough context to
plan spawns intelligently.

### Level 2: Coordinator Spawns (needed at ~200K-1M tokens)
```
Coordinator → reads summaries only → plans spawn tree
  ├── Spawn A → reads domain-specific full context
  ├── Spawn B → reads different domain context
  └── Spawn C → reads cross-domain summary
Coordinator ← collects results ← writes synthesis
```
Key change: the coordinator cannot read full files, only summaries.
Summaries must be maintained automatically (auto-distill on commit).

### Level 3: Peer Coordination (needed at ~1M+ tokens)
```
Agent A (domain expert) ←→ Agent B (domain expert)
                ↕                     ↕
        shared blackboard (filesystem)
```
No coordinator. Agents read/write to typed bulletin boards.
Each agent is a domain expert that can answer queries from other agents.
Coordination emerges from stigmergy — shared filesystem traces.

## Design Decisions

### What changes at Level 2?

1. **Auto-summary generation**: Every file gets a 1-line summary in INDEX.md
   or a companion .summary file. Updated on commit via pre-commit hook.

2. **Domain ownership**: Files are tagged with their primary domain.
   context_router.py already maps domains → files. This becomes formal.

3. **Spawn task generation**: Instead of "read these files and do X", spawns get
   "you own this domain; here are your full files and summaries of everything else."

4. **Result aggregation**: Spawns write structured results to a shared directory.
   Coordinator reads results, not the spawn's full context.

### What changes at Level 3?

1. **Bulletin-based queries**: Agent A can write "QUERY: what's the composite
   score for multiprocessing?" to a bulletin. Agent B (complexity domain expert)
   reads the bulletin and writes the answer.

2. **No coordinator**: All agents are peers. Human sets initial tasks.
   Agents self-organize via filesystem traces.

3. **Conflict resolution**: When two domain experts disagree, the conflict
   protocol (beliefs/CONFLICTS.md) governs. Evidence beats assertion.

## Concrete Next Steps

### For Level 1 (done):
- [x] context_router.py — keyword-based file selection
- [x] inventory command — shows total knowledge size
- [ ] Integrate context_router into evolve.py init (auto-select files for spawns)

### For Level 2 (next):
- [ ] Auto-summary generation (pre-commit hook or tool)
- [ ] Domain ownership tags in INDEX.md
- [ ] Structured result format for spawn output
- [ ] Coordinator protocol in OPERATIONS.md

### For Level 3 (future):
- [ ] Query/answer bulletin protocol
- [ ] Domain expert spawn template
- [ ] Self-organizing task allocation
- [ ] Conflict resolution across domains

## Risk: Premature Optimization
Per P-031: migrate when the trigger fires, not when the argument sounds good.
Current knowledge is 5120 lines (~20K tokens). Model context is ~200K tokens.
We have ~10x headroom. Level 1 is sufficient for now.

**Trigger for Level 2**: Total knowledge exceeds 50K lines or mandatory load
exceeds 200 lines. Monitor via `context_router.py inventory`.

## Connection to NK Analysis
This IS the NK problem applied to the swarm itself:
- N = number of knowledge files
- K = cross-references between files
- Cycles = circular dependencies in knowledge structure

Current swarm tools/ has K=0 (F64). But knowledge files have higher K
(DEPS.md references beliefs, lessons reference principles, etc.).
As K grows, coordination cost grows. Context routing is the swarm's
own strategy for managing its K/N ratio.
