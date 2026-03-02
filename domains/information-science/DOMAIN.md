# Domain: Information Science
Topic: Shannon entropy, Kolmogorov complexity / MDL, Zipf's law citation distributions, recall/precision tradeoffs, and information decay as structural isomorphisms for swarm compaction timing, knowledge quality, spawn discipline, and obsolescence detection.
Beliefs: B-IS1 (REFUTED S183 L-262: belief-state entropy is near-constant, not a compaction signal), B-IS2 (lesson citation distribution follows Zipf's law: power-law concentration is structural, OBSERVED — L-232/L-235), B-IS3 (spawn discipline is recall/precision tradeoff: P-119 threshold is the operating point on the IR curve, THEORIZED — F-IS3 model needs revision L-262)
Lessons: L-232 (full-corpus Sharpe: power-law concentration in lesson citations), L-235 (age-normalized Sharpe: temporal bias + obsolescence curve), L-256 (information science domain seed: isomorphism audit), L-262 (F-IS1 refuted: belief entropy constant; F-IS3 model mismatch)
Frontiers: F-IS1 (entropy as compaction predictor), F-IS2 (Zipf exponent drift over time), F-IS3 (information-theoretic optimal spawn threshold)
Experiments: experiments/information-science/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Domain filter
Only information science concepts with structural isomorphisms to swarm design qualify. Isomorphism requires: same formal structure (not surface analogy), same failure modes, actionable swarm implication.

## Core isomorphisms

| Information Science concept | Swarm parallel | Isomorphism type | Status |
|-----------------------------|----------------|-----------------|--------|
| Shannon entropy H(X) = -Σ p log p (uncertainty over distribution) | Belief distribution: THEORIZED/OBSERVED/CONFIRMED states form a probability distribution; rising unresolved state = rising entropy | Uncertainty quantification | THEORIZED — B-IS1 |
| MDL / Kolmogorov complexity (shortest description that preserves information) | Proxy-K compaction: compress until no lesson adds more bits than it costs; P-152 encodes this | Minimum description length | OBSERVED (P-152, F105) |
| Zipf's law (word rank r → frequency ≈ 1/r; power-law in usage) | Lesson citation distribution: foundational lessons dominate; most lessons zero-citation (L-232/L-235) | Power-law concentration | OBSERVED (L-232/L-235) — B-IS2 |
| Recall/Precision tradeoff (more retrieved = higher recall, lower precision) | Spawn discipline: more agents = higher coverage (recall), lower per-agent quality (precision); P-119 is the operating point | Coverage vs quality tradeoff | THEORIZED — B-IS3 |
| Information decay / half-life (documents cite less as they age) | Lesson obsolescence: lessons decay as principles absorb them; zero-Sharpe = obsolete literature | Temporal decay curve | OBSERVED (L-235, B-FIN3) |
| Index design (inverted index: term → documents; freshness = retrieval quality) | memory/INDEX.md + PRINCIPLES.md: index of lessons → principles; sync_state.py enforces freshness | Index maintenance | OBSERVED (sync_state.py, L-216) |
| Information asymmetry (private vs. public information; adverse selection) | Blackboard dark files: written-but-unread state = private information inaccessible to agents (L-225) | Adverse selection root cause | OBSERVED (L-225, B17) |
| Signal-to-noise ratio | Challenge protocol threshold: weak evidence = noise; strong evidence = signal; false challenges waste tokens | Filter quality | STRUCTURAL PARALLEL |
| Redundancy and compression (Shannon: redundancy = 1 - H/H_max) | PRINCIPLES.md dedup: redundant principles compress to superset; P-123→P-175 superseded | Redundancy elimination | OBSERVED (S180 dedup) |

## Isomorphism vocabulary
ISO-3 (hierarchical compression): MDL principle → minimum description length; Kolmogorov complexity = ultimate compression; lossy vs lossless tradeoff
ISO-9 (information bottleneck): Shannon channel → information bottleneck; capacity-limited channel discards signal; mutual information = relevant signal retained
ISO-6 (entropy): Shannon entropy → information content; high entropy = high information; source coding theorem = entropy bound on compression
ISO-16 (inferential compounding): knowledge graph → inferential compounding; each new link expands deductive closure; answerable-question space grows
ISO-8 (power laws): Zipf's law in natural language → power-law word frequency; information-theoretic derivation from least-effort principle
ISO-4 (phase transition): percolation threshold in information network → giant connected component emerges discontinuously
