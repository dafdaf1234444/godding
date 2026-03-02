# Domain: Knowledge Quality
Topic: Detecting redundant, stale, and low-value knowledge in the swarm's own memory — repeated lessons, decayed beliefs, cross-domain isomorphism overlap, and structural noise in the lesson/principle corpus.
Beliefs: B-QC1 (a fraction of swarm lessons are near-duplicate — THEORIZED), B-QC2 (high-citation lessons decay in accuracy over time as swarm evolves — THEORIZED), B-QC3 (domain pairs with high isomorphism overlap produce redundant lessons — THEORIZED)
Lessons: (none yet — seeded S189)
Frontiers: F-QC1 (repeated knowledge detection), F-QC2 (knowledge freshness and citation decay), F-QC3 (cross-domain redundancy via isomorphism overlap)
Tool: `tools/f_qc1_repeated_knowledge.py` — reads all lessons, computes pairwise Jaccard similarity, flags near-duplicates
Experiments: experiments/quality/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Domain filter
Only quality checks that operate on the swarm's own knowledge corpus qualify. External quality assurance (code linting, test coverage) is out of scope unless the method applies structurally to lesson/principle quality.

## Core model: Knowledge as Information Channel

The swarm generates lessons and principles as outputs of a noisy channel (concurrent sessions, context limits, compaction). Quality domain asks: how much of that output is signal vs redundant encoding?

```
CHANNEL ANALOGY:
  Source signal     → original insight (unique lesson)
  Transmission      → concurrent session writing the lesson
  Noise             → context limit, WSL corruption, race conditions
  Redundant encoding → near-duplicate lessons covering the same claim
  Channel capacity  → max non-redundant lessons the corpus can hold
  Compression gain  → ratio of unique signal to total lesson count

FRESHNESS ANALOGY:
  Decay function    → lesson accuracy decreases as swarm belief evolves
  Half-life         → number of sessions before a lesson's claim is superseded
  Citation rate     → proxy for lesson's live relevance (high-cited ≠ accurate)
  Staleness signal  → last-cited session vs current session gap

CROSS-DOMAIN ANALOGY:
  Isomorphism overlap → two domains teach the same structural rule in different vocabulary
  Redundancy score    → proportion of lessons in domain A that map to a lesson in domain B
  Deduplication value → merge isomorphic cross-domain lessons into a single principle
```

## Quality isomorphisms with swarm design

| Quality concept | Swarm parallel | Isomorphism type | Status |
|----------------|---------------|-----------------|--------|
| Near-duplicate detection | Jaccard similarity on lesson word sets | Information-theoretic | THEORIZED (B-QC1) |
| Decay / staleness | Session-gap since last citation | Freshness signal | THEORIZED (B-QC2) |
| Cross-domain redundancy | ISOMORPHISM-ATLAS structural overlap | Domain coupling | THEORIZED (B-QC3) |
| Corpus compression | MDL compaction cycle (compact.py) | Kolmogorov compression | OBSERVED (L-234) |
| False-archive risk | compact.py citation scanner gap (L-277, L-280) | Quality-control failure | OBSERVED |
| Noise amplification | Concurrent sessions writing redundant lessons | Channel noise | OBSERVED (S186/S187) |
| Selection pressure | Context window forces lesson compression | Natural selection | OBSERVED (CORE.md P9) |

## Relationship to other domains
- **meta**: quality domain IS the meta-domain's quality-assurance arm — meta asks what swarm is, quality asks whether what it knows is correct and non-redundant.
- **evolution**: near-duplicate lessons are low-fitness variants — quality checks are a form of selection pressure.
- **brain**: citation-based relevance weighting (Hebbian co-citation, F-BRN1) is a parallel freshness signal.
- **operations-research**: scheduling compact.py and quality sweeps is an OR problem (cadence optimization).
- **information-science**: Jaccard similarity, TF-IDF, and MDL are IS methods applied here to the swarm's own corpus.

## Isomorphism vocabulary
ISO-10 (predict-error-revise): quality control → predict-error-revise; SPC = prediction error signal driving process correction
ISO-5 (feedback — stabilizing): statistical process control → stabilizing feedback loop; control chart signals deviation; correction restores mean
ISO-3 (hierarchical compression): quality abstraction → MDL compression of defect space; root cause analysis = compressed failure model
ISO-13 (integral windup): technical debt → integral windup; shortcuts accumulate without correction; quality degradation = windup failure
ISO-2 (selection → attractor): quality selection → fitness landscape; standards = selection pressure; convergence to high-quality attractor
ISO-6 (entropy): software entropy → disorder accumulation; refactoring = entropy reduction; code rot = entropy gradient without correction
## Isomorphism vocabulary (S337 resonance expansion)
ISO-10: quality knowledge coordination → stigmergy via structural calibration; session cycles improve evidence signal; challenge quality pattern convergence
