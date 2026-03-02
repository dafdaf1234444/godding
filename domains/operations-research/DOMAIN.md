# Domain: Operations Research / Scheduling
Topic: Queueing, scheduling policy, bottleneck management, work-in-progress limits, and throughput/latency tradeoffs as structural isomorphisms for swarm lane planning, frontier execution order, and coordination overhead control.
Beliefs: (candidate only; no formal B-OPS* entries in `beliefs/DEPS.md` yet)
Lessons: L-216 (state-sync overhead), L-251 (max-of-N timing effect), L-257 (session quality pattern), L-258 (coordination mode analysis)
Frontiers: F-OPS1, F-OPS2, F-OPS3
Experiments: experiments/operations-research/
Load order: CLAUDE.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/FRONTIER.md

## Domain filter
Only operations-research concepts with structural isomorphisms to swarm coordination qualify. Isomorphism requires: same objective function, same bottleneck behavior, and an actionable scheduling implication.

## Core isomorphisms

| OR concept | Swarm parallel | Isomorphism type | Status |
|-----------|----------------|------------------|--------|
| Queueing theory | Frontier/task backlog and lane queues | Throughput-latency tradeoff | OBSERVED |
| Critical path analysis | Bottleneck files and dependency-bound tasks | Flow constraint mapping | OBSERVED |
| WIP limits | Active lane count and concurrent objectives | Congestion control | THEORIZED |
| Scheduling policy | Priority ordering in NEXT and lane dispatch | Policy optimization | OBSERVED |
| Service-time variance | Parallel runs where wall time is max(N) rather than mean(N) | Tail-latency effect | OBSERVED |


## Isomorphism vocabulary
ISO-1 (optimization): linear programming → optimization-under-constraint; simplex method = gradient descent on feasible polytope
ISO-12 (max-flow/min-cut): network flow → max-flow/min-cut duality; Ford-Fulkerson; supply chain = flow conservation network
ISO-13 (integral windup): queue buildup → integral windup in service systems; Little's law; M/M/1 queue instability at ρ→1
ISO-5 (feedback — stabilizing): inventory control → stabilizing feedback; reorder point = error signal; replenishment = actuator response
ISO-4 (phase transition): queueing phase transition → throughput collapse at critical load; utilization threshold = phase boundary
ISO-9 (information bottleneck): decision under uncertainty → information bottleneck; discard irrelevant states; Bellman equation = optimal compression
## Isomorphism vocabulary (S337 resonance expansion)
ISO-13: queue knowledge coordination → structural stigmergy; session cycles prevent windup; challenge signal quality pattern; coordination handoffs trigger release
