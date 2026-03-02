# F101: True Swarming Architecture Design
Conducted: Session 51 (2026-02-27)
Method: 3 parallel sub-agents investigating domain sharding, personality persistence, and hierarchical spawning
Human directive: swarming behavior IS the value; sub-colonies with different personalities; parent→child→grandchild

---

## Context

The user expressed that the swarm's goal is the self-evolving, autonomous swarming behavior — not the specific domain findings (NK, distributed systems). Three concrete gaps were identified:

1. **Scaling ceiling**: max ~2 concurrent agents due to hot-file contention (INDEX.md, FRONTIER.md)
2. **No persistent personalities**: sub-colonies require full repo forks, doesn't scale to 10+
3. **No hierarchical swarming**: current design is 1-level deep; no parent→child→grandchild protocol

This document synthesizes three parallel design investigations into a concrete architecture.

---

## Part 1: Domain Sharding (F101 — removes hot-file ceiling)

### Three-tier file ownership

**Tier 0 — Global read-only (no write conflicts)**
```
beliefs/CORE.md, CLAUDE.md, memory/VERIFY.md, memory/DISTILL.md
memory/HEALTH.md, beliefs/CONFLICTS.md
```

**Tier 1 — Domain-owned (one domain per agent, no cross-domain conflicts)**
```
domains/nk-complexity/tasks/FRONTIER.md      ← NK agent writes here
domains/nk-complexity/beliefs/DEPS.md
domains/nk-complexity/memory/INDEX.md
domains/nk-complexity/memory/lessons/NK-NNN.md

domains/distributed-systems/tasks/FRONTIER.md
domains/distributed-systems/beliefs/DEPS.md
domains/distributed-systems/memory/INDEX.md
domains/distributed-systems/memory/lessons/DS-NNN.md

domains/meta/tasks/FRONTIER.md               ← meta/architecture agent writes here
domains/meta/beliefs/DEPS.md
domains/meta/memory/INDEX.md
domains/meta/memory/lessons/META-NNN.md
```

**Tier 2 — Synthesizer-only (one synthesizer session per cycle)**
```
memory/GLOBAL-INDEX.md         ← synthesized from domain indexes
tasks/GLOBAL-FRONTIER.md       ← synthesized from domain frontiers
beliefs/META-DEPS.md           ← cross-domain beliefs
memory/PRINCIPLES.md           ← append-only sections, domain agents can append to their section
```

### Minimum viable change (Phase 1)

1. Populate `domains/*/tasks/FRONTIER.md` with domain-specific questions (copy from global FRONTIER)
2. Add one paragraph to CLAUDE.md: "Domain sessions read `domains/<name>/tasks/FRONTIER.md` and write only to their domain. Do not write to `tasks/FRONTIER.md`."
3. Note in `tasks/FRONTIER.md`: "Cross-domain questions only. Domain questions migrated."

**Parallelism ceiling after each phase:**
- Phase 1 (FRONTIER sharding): 2 → 3 concurrent agents
- Phase 2 (INDEX sharding): 3 → 5+ agents
- Phase 3 (DEPS sharding + validate_beliefs.py update): 5+ → ~10 agents

### Soft locking (prevents same-domain conflicts)

Each domain gains `domains/<name>/tasks/CLAIMS.md` (append-only):
```
2026-02-27T14:00Z | S51 | F75: decompose-by-data task types
```
Advisory only. An agent reads claims before picking a task. Conflict = one resolvable merge.

### Synthesizer role

NOT a permanent coordinator — just any meta-mode session that notices GLOBAL-INDEX is stale (>3 sessions since last synthesis). Reads all domain indexes, updates GLOBAL-INDEX, promotes cross-domain beliefs to META-DEPS. Stigmergic: the signal (stale timestamp) drives the action.

---

## Part 2: Sub-Colony Personality System

### Core design: `personality.md` overlay

Personality is NOT a CLAUDE.md mutation. It is an overlay file in the colony root.

```
<colony-root>/personality.md     ← the character (static, survives session turnover)
<colony-root>/.swarm_meta.json   ← updated with "personality" field
```

CLAUDE.md gets one new line in session start: "Read `personality.md` if it exists — your character for this colony."

No fork required. A colony shares the parent's CLAUDE.md and tools (via relative paths or symlinks). Only personality.md and .swarm_meta.json differ per colony.

### personality.md format

```markdown
# Personality: <name>
Colony: <colony-name>
Character: <one sentence>

## Identity
You are the <name> instance. <2-3 sentences epistemic stance.>

## Behavioral overrides
### What to emphasize
- <concrete imperative>
### What to de-emphasize
- <what to skip or compress>
### Decision heuristics
When facing ambiguity, prefer: <bias>
When adding a belief, ask first: <characteristic question>
```

### Five archetypes

| Name | Character | Key behavioral difference |
|------|-----------|--------------------------|
| **Skeptic** | Challenges before accepting | Belief throttle at 40% theorized; PARTIAL unless 3+ data points |
| **Builder** | Ships artifacts as primary unit of knowledge | Every session produces working artifact in workspace/ |
| **Explorer** | Optimizes for surface area | Adds 2+ new frontier questions per resolution; never applies throttle |
| **Synthesizer** | Connects existing knowledge across domains | Reads last 5 lessons before writing; always updates DEPS |
| **Adversary** | Actively tries to break highest-confidence beliefs | Selects most-depended-on belief, designs falsification test first |

### Spawn command

```bash
python3 tools/evolve.py init <child-name> "<task>" --personality skeptic
```

Fanout (N personalities, same question):
```bash
python3 tools/evolve.py fanout F76 --personalities skeptic,builder,explorer,adversary
```

Templates live in `tools/personalities/<name>.md`. The `--personality` flag:
1. Writes `personality.md` to child dir from template
2. Adds `"personality": "skeptic"` to `.swarm_meta.json`
3. Adds one line to child's CLAUDE.md session start

### What personalities produce differently on the same question

Running all 4 personalities on "what predicts Go error handling quality?":
- Skeptic: challenges every finding, produces tight falsification conditions, low volume
- Builder: produces a script to measure the predictor, validates empirically
- Explorer: opens 6 sub-questions from the main question, finds adjacent unknowns
- Adversary: tries to break B13 (EH as dominant failure cause), finds the edge cases

The Synthesizer role is the harvest mechanism: after all four run, a synthesis session reads their outputs and produces the cross-personality convergence pattern.

---

## Part 3: Hierarchical Swarming Protocol

### Spawn decision rule (when to spawn vs. work solo)

Spawn if ALL THREE hold:
1. Task decomposes into 2+ independent data items (not methods — P-057)
2. Each sub-task requires 5+ files or meaningful standalone analysis
3. Sub-tasks write to different domains (no shared hot files)

At depth ≥ max_depth: always solo regardless of above.

### .swarm_meta.json extension

```json
{
  "name": "child-name",
  "topic": "...",
  "parent": "/path/to/parent",
  "depth": 1,
  "max_depth": 2,
  "role": "researcher",
  "coordinator_session": "S51",
  "assigned_frontier": "F76",
  "context_budget_lines": 400
}
```

**depth** = 0 (root, no file), 1 (child), 2 (grandchild). max_depth = 2. No recursion beyond depth 2.

Why max_depth=2: parallelism ceiling exhausts independent write domains by depth 3; grandchildren already receive minimal context; diminishing novelty returns beyond two levels.

### Coordinator role

When a session has `"role": "coordinator"` in .swarm_meta.json (or decides to act as coordinator because 3+ questions are parallelizable):

1. **Select**: pick 3-5 frontier questions (Critical/Important, parallelizable, non-conflicting writes)
2. **Spawn**: `evolve.py init <child> "<question>" [--personality <type>]` for each
3. **Monitor**: passive — Task tool calls are in flight
4. **Harvest**: `evolve.py harvest + integrate` for each child when complete
5. **Synthesize**: write one cross-child lesson, update GLOBAL-FRONTIER
6. **No research**: coordinator does not do NK analysis or DS verification

### Context routing per level

| Level | Mandatory | Routed | Excluded | Budget |
|-------|-----------|--------|----------|--------|
| Coordinator (L0) | Full mandatory load | Full task context | — | Unlimited |
| Child (L1) | CORE.md + child INDEX + AGENT-TASK + .swarm_meta | Up to 5 parent files + 3 matching lessons | Parent INDEX, parent DEPS, other children | 400 lines |
| Grandchild (L2) | .swarm_meta + AGENT-TASK + parent-child CORE | Data files for assigned item + 2 matching lessons | Root parent anything, other grandchildren | 200 lines |

### Results flow (Option C — pull model)

```
grandchild → commits → writes lesson → writes bulletin
child harvests grandchildren: evolve.py harvest|integrate per grandchild → synthesis lesson
coordinator harvests children: evolve.py harvest|integrate per child → marks FRONTIER
```

Existing evolve.py pull model handles all of this. No new tools needed.

### swarm.md additions (~25 lines, 3 insertions)

**Section 1 (Where am I)** — add:
```
- Check .swarm_meta.json for "role": "coordinator" → pure orchestration, no research
- Check .swarm_meta.json "depth" field → if depth >= max_depth, spawn prohibited
```

**Section 3 (Pick work)** — replace parallelism paragraph with:
```
Spawn if ALL THREE: (1) 2+ independent data items, (2) each needs 5+ files, (3) no shared hot files.
Depth >= max_depth overrides to solo.
If spawning: check depth. Spawn at depth+1. Run context_router.py --budget 400. Use evolve.py init.
Launch parallel via Task tool. Harvest all: evolve.py harvest + integrate per child. Write synthesis lesson.
If coordinator: pick 3-5 questions, spawn one per, monitor, harvest all, synthesize, do not research.
```

**Session modes table** — add:
```
| coordinator | Orchestrating 3+ parallel children | (swarm.md section 3) |
```

---

## Convergence across the three designs

All three agents independently converged on:
- **Pull model** (parent harvests children, not children pushing to parent)
- **.swarm_meta.json as coordination metadata carrier** (depth, role, personality)
- **No new tools needed** — extend evolve.py, add personality templates, update swarm.md
- **Soft locking, not hard locking** (claims file, advisory; human scheduling at current scale)
- **Synthesizer role is stigmergic** (driven by stale-timestamp signal, not by a dedicated process)

Cross-convergence P-089: 3/3 agents = adopt-level confidence.

---

## Implementation sequence

| Phase | What | Effort | Unlocks |
|-------|------|--------|---------|
| 1a | Domain FRONTIER files + CLAUDE.md line | 2 hours | 3 concurrent agents |
| 1b | personality.md format + 5 templates + evolve.py --personality flag | 1 session | Persistent personality colonies |
| 1c | swarm.md 3 insertions + .swarm_meta.json depth fields | 1 hour | Hierarchical spawning protocol |
| 2 | Domain INDEX files + GLOBAL-INDEX + synthesize.py | 1 session | 5+ concurrent agents |
| 3 | Domain DEPS + validate_beliefs.py update | 1 session | ~10 concurrent agents |

Phase 1 (a+b+c) is the minimum viable true swarm. It enables:
- 3 domain agents working concurrently without conflict
- Each with a different personality
- Parent→child→grandchild with depth limit
- Results flowing back via existing evolve.py

---

## Open questions (new frontier)

- **F104**: Does personality persistence actually produce different findings on the same question, or do LLMs converge regardless of character overlay? First test: fanout 4 personalities on F76, compare outputs.
- **F105**: What is the right max_depth? Is 2 too conservative? Try depth=3 on one experiment.
- **F106**: Does a synthesizer personality outperform ad-hoc harvest in extracting cross-colony patterns?
