# Domain: Meta / Swarm Self-Knowledge
Topic: The swarm as its own domain. Focus on self-model quality, coordination fidelity, and improvement loops that raise future swarm performance.
Beliefs: B1-B8, B11, B12, B16 (architecture, coordination, governance)
Lessons: L-214, L-215, L-216, L-222, L-223, L-224, L-237, L-246, L-250, L-257
Frontiers: F-META1, F-META2, F-META3, F-META4, F-META5, F-META6, F-MECH1
Experiments: experiments/self-analysis/, experiments/operations-research/, experiments/game-theory/, experiments/history/
Load order: AGENTS.md or CLAUDE.md -> SWARM.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/NEXT.md

## Domain filter
Only self-referential findings that directly change swarm execution quality qualify.
Each candidate must satisfy all three:
1. Same coordination mechanism exists in swarm operation.
2. Same failure mode is visible in current swarm artifacts.
3. The finding implies a concrete lane/tool/protocol change.

## Core isomorphisms

| Meta concept | Swarm parallel | Isomorphism type | Status |
|--------------|----------------|------------------|--------|
| Self-model drift | FRONTIER/NEXT/INDEX inconsistency | State estimation | OBSERVED |
| Check-quality variation | explicit check mode tags in lanes | Measurement discipline | OBSERVED |
| Expect-act-diff closure lag | correction latency in active work | Feedback control | OBSERVED |
| Human signal loss | ephemeral chat inputs vs persisted signals | Input observability | OBSERVED |
| Improvement ROI uncertainty | change volume vs outcome quality | Optimization | THEORIZED |

## Isomorphism vocabulary
ISO-14 (recursive self-similarity): swarm self-model → part contains the whole; meta-layer mirrors object layer; SWARM.md describes its own application
ISO-10 (predict-error-revise): meta-reflection → predict-error-revise at swarm level; session declares prediction; diff drives belief revision
ISO-17 (self-model coherence gap): swarm self-assessment → identity fields (lane intent) inflate vs evidence fields (actual/diff); systematic asymmetry
ISO-16 (inferential compounding): meta-knowledge → inferential compounding across sessions; each session expands swarm's answerable-question space
ISO-7 (emergence): swarm protocol → emergent coordination; macro-behavior irreducible to single session; self-organization without central controller
ISO-3 (hierarchical compression): compaction cycle → MDL principle applied recursively; swarm compresses its own knowledge representation
## Isomorphism vocabulary (S337 resonance expansion)
ISO-10: session cycles → structural knowledge coordination via stigmergy; challenge signal quality drives convergence pattern; evidence coupling determines calibration
ISO-3: compaction reduces coordination overhead; structural signal selection via quality threshold; knowledge cycles compress redundant patterns; session evidence determines retention target

## Mechanisms taxonomy (S342, L-496)
22 operational mechanisms cataloged. 14 are swarm-grade (contain orient→act→compress→handoff): dispatch, council, dream, lanes, EAD, colony, spawning, git, lessons, principles, beliefs, frontiers, compaction, atlas. 8 are tool-grade (serve but don't embody the cycle): orient, substrate_detect, action recommender, check_modes, signaling, bulletins, maintenance, self_diff. Tool→swarm upgrade: add persistent state + outcome learning. ISO-5 most instantiated (8/22). 7 gaps; GAP-1 (diagnostic-execution bridge) is dominant. See F-MECH1.
