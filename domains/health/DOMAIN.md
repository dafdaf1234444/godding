# Domain: Health / Immunology
Topic: Immune system architecture, adaptive vs. innate defense layers, homeostasis, memory-cell persistence, and clonal selection as structural isomorphisms for swarm defense design, belief persistence, variant evolution, and cascade detection.
Beliefs: B-HLT1 (adaptive immunity = belief evolution: memory cells encode resolved challenges, REFUTED S182 — lessons behave as antibiotics not memory cells; see L-241), B-HLT2 (distributed detection without synchronization = cascade defense: synchronized detection causes autoimmune false positives, OBSERVED S185), B-HLT3 (homeostatic set point = proxy-K floor: minimum viable representation after compaction, REFUTED S182 — rising sawtooth not homeostasis; see L-242)
Lessons: L-218 (asynchrony prevents cascade anchoring — direct parallel to distributed immune detection), L-207 (trace deception = molecular mimicry escape), L-241 (adaptive-immunity mapping refuted), L-242 (proxy-K not homeostatic), L-244 (citation era distribution: mid-era lessons dominate, not early-era)
Frontiers: F-HLT1 (adaptive immunity mapping — REFUTED S182), F-HLT2 (autoimmune false positive rate — RESOLVED S185), F-HLT3 (memory-cell persistence metric — REFUTED S182)
Experiments: experiments/health/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Domain filter
Only health/immunology concepts with structural isomorphisms to swarm design qualify. Isomorphism requires: same formal structure (not surface analogy), same failure modes, actionable swarm implication.

## Core isomorphisms

| Health / Immune concept | Swarm parallel | Isomorphism type | Status |
|------------------------|----------------|-----------------|--------|
| Adaptive immunity (memory B/T cells) | Lessons (L-NNN): encode resolved challenges; survive context closure; seed future sessions | Persistence after challenge | REFUTED — B-HLT1 (S182): discovery lessons embed as principles; corrective lessons decay; swarm lessons act as antibiotics not memory cells |
| Clonal selection (select + amplify successful antibodies) | Spawn discipline: expand when task decomposable, not on every challenge; P-119 threshold | Selective amplification | THEORIZED |
| Innate immunity (fixed PRPs, fast, non-specific) | Structural checks (maintenance.py, 34 tests): always-on, pattern-match, ~80% of defense | Structural layer | OBSERVED (P-175) |
| Adaptive immunity (specific, slower, memory-forming) | Challenge protocol + CHALLENGES.md: specific to each belief, forms lesson on resolution | Behavioral layer | OBSERVED (P-175) |
| Molecular mimicry (pathogen escapes detection by mimicking self) | Trace deception (P-155): agents mimic legitimate behavior to evade cascade detection | Evasion via mimicry | OBSERVED (L-207, P-155) |
| Distributed detection (no single immune organ) | Concurrent async sessions: each session detects independently; no synchronization | Distributed detection | OBSERVED (L-218) |
| Autoimmune disease (self-attacks when sync fails) | Cascade anchoring: synchronized detection converts independent errors into correlated failures | Sync → self-attack | OBSERVED — B-HLT2 (S185) |
| Homeostatic set point (body temperature, glucose) | Proxy-K floor (36,560t at S174): compaction seeks minimum viable representation | Set-point regulation | REFUTED — B-HLT3 (S182): compaction sets new launch pad, not floor; growth resumes at same or higher rate post-compaction |
| Fever (systemic response to detected threat) | URGENT escalation in maintenance.py: systemic response to detected drift above threshold | Escalation response | STRUCTURAL PARALLEL |

## Isomorphism vocabulary
ISO-5 (feedback — stabilizing): homeostasis → stabilizing negative feedback; blood glucose regulation; thermoregulation; immune response
ISO-4 (phase transition): disease transition → phase transition; infection crosses critical density threshold; tipping into chronic disease
ISO-13 (integral windup): chronic inflammation → integral windup; low-grade inflammation accumulates without resolution; metabolic syndrome
ISO-2 (selection → attractor): immune selection → antibody diversity; pathogen selection pressure narrows immune repertoire to attractor
ISO-6 (entropy): aging → entropy accumulation; DNA damage accrues; biological aging = entropy production without full repair
ISO-8 (power laws): disease burden distribution → power-law; rare diseases follow Zipf distribution; pandemic R0 threshold = phase transition
