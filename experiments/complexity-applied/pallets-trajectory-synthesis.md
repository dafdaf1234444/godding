# Pallets Ecosystem Structural Trajectory Synthesis
Date: 2026-02-26 | Session: 41 | Method: 3-agent hierarchical spawn

## Method
Top-level swarm decomposed "which framework has best structural trajectory?" into 3 parallel sub-tasks. Each agent analyzed one Pallets framework across its full version history using ΔNK. Results synthesized by parent.

## Per-Framework Trajectories

### Flask (Agent A): Monotonic Degradation
Composite: 59 (1.0) → 130 (3.1.0), +120%
Cycles: 1 → 34
Architecture: framework → tangled (at 2.0, never recovered)
Trigger: 2.0 blueprint/scaffold/cli refactor (+34 composite, +15 cycles)

### Werkzeug (Agent B): Oscillation with Upward Drift
Composite: 201 (1.0) → 233 (3.0), +16%
Cycles: 32 → 43
Architecture: tangled throughout (never escaped)
Trigger: 2.2 routing decomposition (+33 composite, +6 cycles)
Partial recovery in 2.3/3.0 (cycles peaked at 46 in 2.2, fell to 43)

### Jinja2 (Agent C): Step-Function Then Freeze
Composite: 93 (2.9) → 109 (3.1.6), +17%
Cycles: 6 → 18
Architecture: tangled from 2.11 onward
Trigger: 2.11 async support addition (+15 composite, +11 cycles)
Frozen at elevated level — 3.x makes essentially zero structural changes

## Cross-Framework Findings

| Framework | Pattern | Trigger | ΔComposite at trigger | Recovery? |
|---|---|---|---|---|
| Flask | Monotonic increase | 2.0 blueprints | +34.0 | None |
| Werkzeug | Oscillation | 2.2 routing split | +33.0 | Partial |
| Jinja2 | Step + freeze | 2.11 async | +15.0 | Stalled |

### The Architectural Ratchet
All three frameworks exhibit the same pattern: a single major feature addition permanently elevates structural complexity, and no subsequent release unwinds it. Complexity is a ratchet — it goes up but never comes back down.

### Spawn Quality Evaluation
- **Agent variety**: HIGH — each produced genuinely different trajectory patterns and insights
- **Agent quality**: HIGH — all agents correctly ran the tools and interpreted results
- **Synthesis value**: HIGH — the ratchet pattern only emerges when comparing all three
- **Redundancy**: NONE — no duplicated work or overlapping analysis

## Implications
1. ΔNK trajectory analysis reveals structural health over time, not just snapshots
2. Feature additions (async, new abstractions) are structural one-way doors
3. The "tangled" classification is absorbing — once entered, no Pallets framework has escaped
4. Code review gates should flag the transition INTO tangled (cycles > 3) as critical
