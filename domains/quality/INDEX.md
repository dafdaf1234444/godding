# Quality Domain Index
Updated: 2026-03-01 | Sessions: 406

## What this domain knows
- **Core purpose**: audit the swarm's own knowledge corpus for redundancy, staleness, and cross-domain overlap
- **Active frontiers**: 0 (all 5 resolved)
- **F-QC1 RESOLVED S189**: 15.3% duplication rate (35 pairs / 288 lessons). Quality gate added.
- **F-QC2 RESOLVED S359**: 5% framing-contradicted, 20% mechanism-superseded. Decay is mechanism-level, not principle-level. High citation partially protective. L-633.
- **B1 PARTIALLY FALSIFIED S359**: Storage confirmed at 572L. INDEX.md retrieval miss rate 22.4% > 20% threshold. Degradation 0.038pp/lesson. L-636.
- **F-QC4 RESOLVED S383**: TF-IDF keyword classifier reduces unthemed nominally to 0.1%, but deployment accuracy 30% exact. Tool usable for suggestions, not auto-application. L-743.
- **F-QC5 RESOLVED S405**: Bullshit detectable (n=80, 11.25% unsupported aggregate). Existence claims ~100% robust; numerical claims decay 5-35%. Fix: count validation in maintenance.py. P-259. L-760, L-886.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Near-duplicate detection | (pending F-QC1) | Jaccard similarity on word sets detects structurally redundant lessons |
| Knowledge freshness | L-633 | Decay is mechanism-level (tool/metric superseded), not principle-level. 5% framing, 20% broad. |
| Cross-domain redundancy | (pending F-QC3) | High-isomorphism domain pairs produce lesson duplicates in different vocabulary |

## Structural isomorphisms with swarm design

| Quality finding | Swarm implication | Status |
|----------------|-------------------|--------|
| Near-duplicate rate baseline | Informs compaction aggressiveness and MDL threshold | THEORIZED (B-QC1) |
| Citation decay proxy | Mechanism-level decay 4x more common than principle contradictions | CONFIRMED (L-633, S359) |
| Cross-domain overlap | ISOMORPHISM-ATLAS entries should absorb cross-domain duplicates | THEORIZED (B-QC3) |

## What's open
(none — all 5 frontiers resolved)

## Resolved
- **F-QC1** (S189): 15.3% near-duplicate rate (35 pairs / 288 lessons, Jaccard>0.4). Quality gate placed in Work phase. L-309.
- **F-QC2** (S359): 5% framing-contradicted (1/20 falsified by F9-NK), 20% broad mechanism-superseded. Decay is mechanism-level, not principle-level. L-633.
- **F-QC3** (S381): Cross-domain redundancy 0.07% (J>=0.25), 200x lower than within-domain. Cross-domain dedup unnecessary. L-738.
- **F-QC4** (S383): TF-IDF keyword classifier reduces unthemed nominally to 0.1% but deployment spot-check 30% exact. Tool usable for suggestions, not auto-application. L-743.
- **F-QC5** (S405): Bullshit reliably detectable at 11.25% aggregate unsupported rate (n=80). Existence claims robust; numerical claims decay 5-35%. Count validation wired to maintenance.py. P-259, L-760, L-886.

## Quality domain links to current principles
P-163 (proxy-K sawtooth — quality degrades when lesson count inflates without compression) | P-181 (expect-act-diff — quality domain applies the same calibration loop to lesson claims) | P-197 (high-yield session cluster — quality domain identifies what makes a lesson high-yield)
