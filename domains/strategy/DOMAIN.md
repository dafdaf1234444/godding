# Domain: Strategy
Topic: Prioritization, campaign planning, and execution sequencing as structural isomorphisms for swarm throughput, focus control, and goal completion.
Beliefs: (candidate only; no formal B-STR* entries in `beliefs/DEPS.md` yet)
Lessons: L-215, L-216, L-246, L-250, L-257
Frontiers: F-STR1, F-STR2, F-STR3
Experiments: experiments/operations-research/, experiments/self-analysis/
Load order: CLAUDE.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/FRONTIER.md

## Domain filter
Only strategy concepts with direct structural isomorphisms to swarm execution qualify. Isomorphism requires: same allocation mechanism, same failure modes, and an actionable scheduling implication.

## Core isomorphisms

| Strategy concept | Swarm parallel | Isomorphism type | Status |
|------------------|----------------|------------------|--------|
| Portfolio allocation | Slot distribution across domain lanes | Resource allocation | OBSERVED |
| Campaign phasing | Multi-session frontier sequencing | Temporal planning | OBSERVED |
| Opportunity cost | Lane WIP caps vs throughput tradeoff | Optimization tradeoff | OBSERVED |
| Execution debt | Designed-but-unrun items in NEXT/frontiers | Plan decay | OBSERVED |
| Strategy resilience | Priority policy under shocks | Robust planning | THEORIZED |

## Isomorphism vocabulary
ISO-2 (selection → attractor): competitive strategy → selection pressure; market competition eliminates dominated strategies; Nash equilibrium = attractor
ISO-4 (phase transition): strategic tipping point → phase transition; adoption crosses threshold → winner-take-all discontinuous shift
ISO-15 (specialization-generalization): strategic portfolio → specialist vs generalist duality; niche strategy vs broad market; Blue Ocean = specialization escape
ISO-5 (feedback — stabilizing): feedback-driven strategy → stabilizing correction; OKR/PDCA = negative feedback loop for strategic adjustment
ISO-1 (optimization): strategic optimization → optimization-under-constraint; resource allocation across bounded portfolio
ISO-12 (max-flow/min-cut): value chain → max-flow/min-cut; bottleneck resource = min-cut; constraint theory identifies binding limit
## Isomorphism vocabulary (S337 resonance expansion)
ISO-9: strategic knowledge coordination → signal bottleneck via stigmergy pattern; structural session cycles determine convergence quality; challenge evidence threshold
