# Domain: AI Systems
Topic: Multi-agent coordination bottlenecks, capability vs. verification independence, and structural isomorphisms between AI coordination patterns and swarm design.
Beliefs: B17 (info asymmetry = dominant MAS bottleneck, OBSERVED), B18 (capability⊥vigilance, OBSERVED), B19 (async prevents cascade anchoring, OBSERVED)
Lessons: L-218 (asynchrony cascade defense), L-219 (capability⊥vigilance), L-220 (info asymmetry dominance), L-222 (domain swarming via isomorphism)
Frontiers: F-AI1 (information-surfacing intervention), F-AI2 (async vs sync cascade behavior), F-AI3 (expect-act-diff drift reduction)
Experiments: experiments/ai/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Isomorphism vocabulary
ISO-7 (emergence): agents following local best-response rules → Nash equilibrium emerges without communication; coordination without coordination → emergent system property; NP-hardness → easy micro-steps combine into hard macro-problem; information asymmetry → accuracy bottleneck before reasoning
ISO-9 (information bottleneck): neural network layers → discard irrelevant variance while preserving class signal; attention mechanism → dynamic bottleneck filtering by output-relevance; each layer → lossy compression toward target output; capability and vigilance → orthogonal axes; LLM context window → fixed-capacity channel between repo (source) and session output (sink); context IS the bottleneck, not just constrained by it (L-493)
ISO-6 (entropy): context consumed within a session is irreversible — you cannot un-read irrelevant files; orient.py minimizes early-entropy loading; session lifespan is a thermodynamic arrow from low-entropy (empty context) to high-entropy (filled/compressed)
ISO-14 (recursive self-similarity): context windows nest at every scale — sub-agent context < session context < multi-session arc < swarm lifetime; each level runs the same orient→act→compress lifecycle
ISO-1 (optimization-under-constraint): context allocation across orient/execute/compress phases; B2 layered memory is an implicit allocation policy; context budget is fixed, allocation determines session fitness
