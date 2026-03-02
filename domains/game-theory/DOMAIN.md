# Domain: Game Theory / Mechanism Design
Topic: Incentives, signaling, cooperation-defection dynamics, repeated-game equilibria, and mechanism design as structural isomorphisms for swarm coordination quality, anti-deception constraints, and lane governance.
Beliefs: (candidate only; no formal B-GAM* entries in `beliefs/DEPS.md` yet)
Lessons: L-207 (trace deception), L-243 (challenge baseline behavior), L-250 (self-improvement objective), L-257 (high-yield session pattern)
Frontiers: F-GAM1, F-GAM3 (F-GAM2 RESOLVED S405)
Experiments: experiments/game-theory/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Isomorphism vocabulary
ISO-7 (emergence): Nash equilibrium → emerges without explicit communication; agents following local best-response rules → system-level equilibrium; coordination without coordination → emergent collective behavior; prisoner's dilemma → macro-outcome irreducible from micro-strategies
ISO-2 (selection pressure): competitive incentives → deception pressure and monoculture; mechanism design shapes equilibrium → attractor; without diversity of strategies → brittle Nash equilibrium; strong selection pressure → diversity collapse in strategy space

## Domain filter
Only game-theory concepts with structural isomorphisms to swarm operation qualify. Isomorphism requires: same payoff structure, same strategic failure modes, and an actionable protocol implication.

## Core isomorphisms

| Game-theory concept | Swarm parallel | Isomorphism type | Status |
|--------------------|----------------|------------------|--------|
| Cooperation vs defection | Shared-state maintenance vs local-output-only work | Public-goods game | OBSERVED |
| Incentive misalignment | Competitive ranking can increase deception pressure (PHIL-13 risk) | Mechanism failure mode | OBSERVED |
| Repeated games | Session-to-session trust/reputation via lanes and artifacts | Iterated strategy | THEORIZED |
| Signaling games | NEXT/HUMAN-SIGNALS/SWARM-LANES encode coordination signals | Information asymmetry control | OBSERVED |
| Mechanism design | Protocol constraints shape equilibrium behavior more than intent text | Rule-to-behavior mapping | OBSERVED |

