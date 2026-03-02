# Domain: Evolutionary Dynamics
Topic: Variation-selection-retention, fitness landscapes, mutation/recombination pressure, and exploration/exploitation balance as structural isomorphisms for swarm adaptation, spawning strategy, and protocol evolution.
Beliefs: (candidate only; no formal B-EVO* entries in `beliefs/DEPS.md` yet)
Lessons: Evolution-heavy cluster already exists in core memory (55 lessons tagged Evolution in `memory/INDEX.md`), including L-153, L-208, L-214, L-222, and L-250.
Frontiers: F-EVO1, F-EVO2, F-EVO3, F-EVO4, F-EVO5
Experiments: experiments/evolution/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Isomorphism vocabulary
ISO-2 (selection pressure): population under strong selection pressure → diversity collapse; genetic bottleneck → monoculture risk; converges to local attractor → brittle to novel perturbation; without diversity maintenance → system cannot escape attractor
ISO-1 (optimization): natural selection → fitness maximization; mutation → gradient perturbation; fitness landscape → optimization surface with local optima; exploitation vs exploration → convergence vs diversity tradeoff
ISO-4 (phase transition): Cambrian explosion → threshold conditions trigger rapid diversification; punctuated equilibrium → stable regime interrupted by rapid phase shift; extinction → irreversible threshold crossing; critical period → qualitative regime change
ISO-6 (entropy): genomic drift → without selection pressure entropy accumulates; Muller's ratchet → irreversible fitness degradation; maintaining complexity requires continuous selection energy; variation-selection-retention → entropy resistance mechanism
ISO-7 (emergence): ant colony intelligence → macro-behavior irreducible to micro-rules; flocking → coordinated behavior without central controller; local threshold rules → emergent colony-level coordination
ISO-9 (information bottleneck): speciation → information bottleneck on gene flow; irrelevant traits discarded under constant environment; environment → output variable; compression of genetic variation preserves relevant adaptation signal
selection pressure → diversity collapse confirmed; compaction drift accumulates without challenge cycles; baseline fitness follows growth compression sawtooth; structural enforcement resets drift
genetic drift → baseline shift; proxy-K drift confirmed; neutral drift accumulates compression without selection; compaction resets structural baseline; cycles of growth follow drift pattern

## Domain filter
Only evolutionary concepts with structural isomorphisms to swarm design qualify. Isomorphism requires: same formal structure, same failure modes, and an actionable swarm implication.

## Core isomorphisms

| Evolution concept | Swarm parallel | Isomorphism type | Status |
|-------------------|----------------|------------------|--------|
| Variation (mutation/recombination) | Parallel lane diversity across prompts/methods | Diversity generation | OBSERVED |
| Selection pressure | Frontier resolution + validator/maintenance gates | Fitness filtering | OBSERVED |
| Retention/heredity | Lesson -> principle -> protocol propagation | Inheritance | OBSERVED |
| Fitness landscape ruggedness | Local optima in repeated work patterns, periodic resets needed | Adaptive topology | THEORIZED |
| Drift vs adaptation | Background overhead/documentation drift vs signal-producing work | Neutral drift tradeoff | OBSERVED |
| Niche construction | Self-tooling loop changes future task environment | Environment shaping | OBSERVED |
| Lamarckian correction | Directed correction defeats Eigen error catastrophe (L-553) | Mutation directionality | MEASURED |
| Phase meta-cycle | Accumulation→burst→integration→convergence (L-554) | Transition cyclicity | MEASURED |
| Edge-of-chaos prediction | K=2.0 crossing amplifies synthesis + sensitivity (L-555) | NK phase boundary | PREDICTED |
