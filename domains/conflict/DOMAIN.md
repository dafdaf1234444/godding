# Domain: Conflict / Inter-Swarm Coordination Repair
Topic: How swarm nodes detect, surface, and resolve conflicts with other swarm nodes — structural, evolutionary, and operational — without requiring human arbitration.
Beliefs: B1, B2, B3, B7, B8, B11 (coordination, integrity, governance)
Lessons: L-093 (lane collision), L-234 (WSL mass-deletion), L-237 (anti-repeat protocol), L-265 (concurrent convergence), L-283 (anti-repeat), L-284 (lane hygiene)
Frontiers: F-CON1, F-CON2, F-CON3
Experiments: experiments/conflict/
Load order: AGENTS.md or CLAUDE.md -> SWARM.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/NEXT.md

## Domain filter
A finding qualifies for this domain if ALL of the following hold:
1. The conflict involves two or more swarm nodes (sessions, lanes, or versions) operating concurrently.
2. The failure mode is observable in current swarm artifacts (SWARM-LANES, git log, FRONTIER, NEXT, beliefs).
3. The finding implies a concrete detection heuristic, resolution protocol, or architectural fix.

Cross-lane findings → `tasks/FRONTIER.md`. Domain-internal findings → here.

## Core taxonomy (from F110 — canonical source)
All inter-swarm conflicts reduce to 3 tiers and 10 cases:

| Tier | ID | Name | Severity | Status |
|------|----|------|----------|--------|
| T1: Structural | A1 | Constitutional Mutation | HIGH | Partially mitigated |
| T1: Structural | A2 | Cascade Invalidation | MEDIUM | Protocol-only |
| T1: Structural | A3 | Merge Conflict on Meta-Files | HIGH | Recurring |
| T1: Structural | A4 | Stale Fork (Version Lag) | MEDIUM | Partially mitigated |
| T2: Evolutionary | B1 | Fitness Landscape Drift | MEDIUM | Protocol-only |
| T2: Evolutionary | B2 | Selection Pressure Inversion | HIGH | Open |
| T2: Evolutionary | B3 | Speciation Without Isolation | LOW | Theorized |
| T3: Operational | C1 | Duplicate Work | HIGH | Recurring |
| T3: Operational | C2 | Contradictory Lessons | MEDIUM | Open |
| T3: Operational | C3 | Lane Orphaning | MEDIUM | Active |

## Conflict expert role
The conflict expert is NOT scope-locked to this domain.
It monitors ALL active SWARM-LANES and cross-checks against:
- Recent git log (last 10 commits): detect duplicate work (C1), stale lanes (C3)
- FRONTIER.md and domain FRONTIERs: detect contradictory resolutions (C2)
- beliefs/CORE.md version: detect constitutional drift (A1)
- DEPS.md: detect cascade invalidation risk (A2)

It produces per-session: one conflict audit artifact + one coordination signal (bulletin or lane update).
It swarms WITH other nodes — reads their state, posts to their lanes when conflicts are detected.

## Cross-domain isomorphisms

| Conflict concept | Swarm parallel | Source domain | Status |
|-----------------|----------------|---------------|--------|
| Mediator pattern | Conflict expert lane | Protocol-engineering | THEORIZED |
| Nash equilibrium | No-unilateral-deviation lane coordination | Game-theory | THEORIZED |
| Immune response | Conflict detection + lane quarantine | Biology/Evolution | THEORIZED |
| Conflict-free replicated data types (CRDT) | Append-only INDEX counters | Distributed-systems | OBSERVED (A3 fix) |
| Adversarial collaboration | Skeptic + adversary personalities | Psychology | OBSERVED |

## Isomorphism vocabulary
ISO-5 (feedback — amplifying): escalation cycle → amplifying feedback; each defection increases defection probability; arms race = positive feedback
ISO-5 (feedback — stabilizing): deterrence → stabilizing feedback; mutually assured destruction restores equilibrium
ISO-4 (phase transition): war outbreak → phase transition; gradual tension crosses critical threshold triggering discontinuous shift
ISO-2 (selection → attractor): competitive conflict → selection pressure eliminates weaker strategies; Nash equilibrium = stable attractor
ISO-7 (emergence): collective violence → emergent macro-behavior from individual local rules; crowd dynamics irreducible to individual actors
ISO-12 (max-flow/min-cut): supply chain warfare → min-cut in logistics network; severing bottleneck edges maximally disrupts flow
## Isomorphism vocabulary (S337 resonance expansion)
ISO-5: conflict knowledge coordination → structural stigmergy handoffs; session cycles amplify cascade signal; challenge quality determines pattern resolution
