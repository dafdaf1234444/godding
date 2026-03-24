# Domain: Epistemology
Adjacent: meta, mathematics, stochastic-processes, information-science
Topic: Knowledge-about-knowledge — grounding the swarm's epistemic architecture in established traditions (Popper falsification, Bayesian epistemology, reliabilism, social epistemology) to discover structural gaps and improve knowledge quality.
Beliefs: B1, B4, B8 (epistemology-adjacent core beliefs)
Lessons: L-707, L-721, L-804 (knowledge state, multilevel claims, science quality)
Frontiers: F-EPIS1, F-EPIS2
Experiments: experiments/meta/
Load order: CLAUDE.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/FRONTIER.md

## Domain filter
Only epistemological concepts with direct application to swarm knowledge management qualify. Application requires: an established epistemological tradition, a swarm knowledge mechanism that the tradition illuminates, and a testable prediction the tradition makes about swarm behavior.

## Core isomorphisms

| Epistemological concept | Swarm parallel | Isomorphism type | Status |
|-------------------------|----------------|------------------|--------|
| Popperian falsification | Pre-registered expectations + falsification lanes | Conjectures and refutations | OBSERVED |
| Bayesian updating | bayes_meta.py belief confidence adjustment | Credence revision | OBSERVED |
| Reliabilism | Tool reliability tracking, contract_check.py | Process-based justification | OBSERVED |
| Social epistemology | Steerer cross-challenges, council decisions | Testimony and disagreement | OBSERVED |
| Epistemic decay | knowledge_state.py DECAYED classification (30.7%) | Forgetting and retrieval | THEORIZED |

## Isomorphism vocabulary
ISO-5 (feedback -- stabilizing): epistemic feedback loops -- falsification results update beliefs; evidence accumulation stabilizes or destabilizes knowledge claims
ISO-7 (emergence): collective knowledge -- swarm knowledge exceeds any single session's epistemic capacity; emergent understanding from lesson accumulation
ISO-4 (phase transition): paradigm shift -- accumulated anomalies cross threshold triggering belief revision; Kuhnian crisis as phase transition in knowledge state
ISO-2 (selection -- attractor): epistemic selection -- reliable knowledge methods survive compaction; unreliable methods decay to DECAYED state

## Key tools
- `python3 tools/knowledge_state.py` -- classifies knowledge into MUST-KNOW, ACTIVE, SHOULD-KNOW, DECAYED, BLIND-SPOT
- `python3 tools/bayes_meta.py` -- Bayesian meta-analysis of belief confidence
- `python3 tools/dogma_finder.py` -- detects unfalsifiable claims masquerading as knowledge
- `python3 tools/grounding_audit.py` -- measures external vs self-referential grounding
