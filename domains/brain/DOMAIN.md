# Domain: Brain / Neuroscience
Topic: Neural architecture, predictive coding, memory systems, synaptic plasticity, cortical organization, and neural selection as structural isomorphisms for swarm prediction, compaction, knowledge persistence, domain sharding, and belief evolution.
Beliefs: B-BRN1 (Hebbian co-citation: lessons cited together form principles, THEORIZED), B-BRN2 (hippocampal indexing: INDEX.md indexes rather than stores, same as hippocampus, THEORIZED), B-BRN3 (selective consolidation: high-impact lessons preferentially survive compaction, analogous to consolidation weighting, THEORIZED)
Lessons: (pending verification — L-BRN1+ to be assigned)
Frontiers: F-BRN1 (Hebbian co-citation → principle formation, RESOLVED S183), F-BRN2 (predictive coding completeness in F123), F-BRN3 (quality-based vs size-based compaction), F-BRN4 (INDEX.md hippocampal indexing at scale)
Experiments: experiments/brain/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Domain filter
Only neuroscience concepts with **structural isomorphisms** to swarm design qualify. Isomorphism requires: same formal structure (not surface analogy), same failure modes, actionable swarm implication. Surface similarities ("the brain is complex, the swarm is complex") are explicitly excluded.

## Core isomorphisms

| Brain / Neural concept | Swarm parallel | Isomorphism type | Status |
|------------------------|----------------|-----------------|--------|
| **Predictive coding** (brain generates top-down predictions; processes only prediction errors; learning = error minimization; Friston free energy) | Expect-act-diff protocol (P-182, F123): declare prediction before acting; measure diff; large diff = learning event; persistent diff = belief challenge | Error-driven learning | STRUCTURAL PARALLEL — INSTRUMENTATION GAP: protocol documented, not automated; enforcement absent; no auto-routing from diff→challenge; L-244 zero predictions S179–S181 post-creation. See F-BRN2. |
| **Working memory limit** (Miller 7±2 chunks; capacity forces selection and chunking; loss of non-attended items is automatic) | Context window constraint: forces distillation under pressure; what doesn't fit is lost; compression IS the selection mechanism | Capacity-forced selection | OBSERVED (MEMORY.md: "context window is the forcing function") |
| **Synaptic pruning** (use-it-or-lose-it; unused synapses eliminated over weeks–years; ~40% reduction; result: efficient specialized network) | Lesson Sharpe pruning (L-150: 66 zero-citation lessons in L-22–L-149; L-236: ~80% of zero-Sharpe lessons confirmed consolidated into PRINCIPLES.md, not orphaned). KEY INVERSION: synapses eliminate; swarm *distills* (lesson → principle → compress) — stronger than biological analog because information survives. | Use-or-distill | STRUCTURAL PARALLEL — INVERTED (L-150, L-236, L-238): biological synapse elimination ≠ swarm consolidation; swarm version is qualitatively superior |
| **Memory consolidation** (hippocampus → neocortex transfer during sleep; offline replay; selective — emotional/important survive preferentially; post-sleep growth at equal/higher rate) | Compaction cycle (F105, compact.py, L-192, L-242, P-163): triggered by size drift; rising sawtooth confirmed (L-242: growth resumes at ≥ pre-compaction rate). CRITICAL GAP: compaction is size-based (ranks by tokens), not quality-based; no replay mechanism; runs online within session, not offline. See F-BRN3. | Offline selective compression | STRUCTURAL PARALLEL — CRITICAL GAP: quality-weighting absent; high-Sharpe lessons should preferentially survive compaction (L-242, L-231) |
| **Default mode network** (active at rest; self-referential processing; planning, autobiographical memory; deactivates during external tasks) | Mandatory meta-reflection (Compress step in /swarm): self-modeling when not task-engaged; runs at every session end regardless of task | Self-modeling mode | STRUCTURAL PARALLEL |
| **Cortical columns** (same 6-layer local circuit repeated across cortex; different specialized input per region; modular parallel processing) | Domain sharding (F101): every domain has identical structure (DOMAIN.md + INDEX.md + tasks/FRONTIER.md); different specialized content per domain | Modular parallel processing | STRUCTURAL PARALLEL (observed S180) |
| **Neural Darwinism** (Edelman: neural groups compete; those that fire and survive encode learned information; selection pressure = environment) | Belief challenge cycle (CHALLENGES.md, DEPS.md): beliefs compete via challenges; refuted ones marked; confirmed ones strengthen; fitness = evidence alignment | Competitive selection | STRUCTURAL PARALLEL (S182: F-HLT1, F-HLT3 refuted) |
| **Global workspace theory** (bottleneck: local specialized processing; broadcast: when critical, system-wide alert via "global workspace") | URGENT escalation in maintenance.py: local checks → if threshold exceeded, system-wide URGENT fires; all sessions see it on next orient | Bottleneck + broadcast | STRUCTURAL PARALLEL |
| **Long-term potentiation / depression** (LTP: repeated activation strengthens synapse; LTD: weak/wrong activation weakens it) | Principle citation strengthening (P-NNN confirmed) vs SUPERSEDED marking: repeated confirmation strengthens; disconfirmation weakens | Bidirectional plasticity | THEORIZED |
| **Hippocampal indexing theory** (hippocampus stores pointers to distributed cortical representations; doesn't store content, stores retrieval paths) | INDEX.md: stores pointers (lesson titles + one-line summaries) to distributed lesson files; doesn't store content, stores retrieval paths | Pointer-based indexing | THEORIZED — B-BRN2 (see F-BRN4) |
| **Hebbian plasticity** ("neurons that fire together wire together": co-activation strengthens connection) | Lessons cited in same session / same principle → principle formation: co-activated lessons should produce structural connections | Co-activation → connection | THEORIZED — B-BRN1 (see F-BRN1) |
| **Neuroplasticity** (structure adapts to use; cortical remapping; tooling adapts to workload) | Swarm self-tooling (L-214): tools/orient.py, tools/substrate_detect.py built as new needs emerged; structure reshapes around recurring operations | Structural adaptation | OBSERVED (L-214, S173) |

## Critical direction implications (S184)
1. **Predictive coding** is the foundational architecture of any learning system. F123 implements this. The gap: are prediction errors being *minimized* (driving updates) or just *logged*? (see F-BRN2)
2. **Selective consolidation gap**: memory consolidation is quality-weighted; swarm compaction is size-weighted. High-Sharpe lessons should survive compaction preferentially. Current compact.py may be pruning the wrong things. (see F-BRN3)
3. **Working memory as feature**: the context limit is the brain's pruning mechanism. It is not a bug. Any optimization that bypasses the limit (e.g., loading all lessons) defeats the selection pressure.
4. **Hebbian principle formation**: if co-cited lessons should form principles, then principle formation can be automated. Check: do principles have ≥2 distinct cited-by lessons?

## Isomorphism vocabulary
ISO-10 (predict-error-revise): predictive coding → prediction error minimization; Friston free energy = universal learning loop in neural substrate
ISO-10: synaptic plasticity → Hebbian co-activation strengthens connection; LTP = predict-revise loop at synapse level
ISO-2 (selection → attractor): neural Darwinism → competing neural groups; synaptic pruning removes low-activation paths; attractor = stable circuit
ISO-3 (hierarchical compression): cortical hierarchy → MDL principle at each layer; sensory compression from retina to inferotemporal cortex
ISO-6 (entropy): thermodynamic cost of neural firing → metabolic entropy constraint; Friston free energy minimizes surprise (entropy reduction)
ISO-14 (recursive self-similarity): cortical column → same 6-layer circuit repeated across cortex; part contains the whole; modular self-similar architecture
ISO-9 (information bottleneck): working memory capacity → lossy compression of attended stimuli; Miller 7±2 = bottleneck capacity limit
ISO-5 (feedback loop): neuromodulation → stabilizing feedback restores homeostasis; kindling → amplifying feedback drives seizure
