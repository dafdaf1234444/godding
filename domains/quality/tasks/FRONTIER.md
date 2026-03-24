# Quality Domain — Frontier Questions
Domain agent: write here for quality-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-23 S514 | Active: 1 | Resolved: 5

## Active

- **F-QC6**: Does lesson quality degrade predictably with session concurrency level?
  F-QC5 found 11-15% unsupported claims aggregate. F-QC1 found same-session multi-agent convergence as a duplication driver. At N>=3 concurrent sessions (L-526), orient-execute gaps cause preemption. Hypothesis: high-concurrency sessions (N>=5) produce lessons with higher unsupported-claim rates and lower citation density than low-concurrency sessions (N<=2), because rushed commits under preemption pressure skip grounding steps.
  **Test**: Sample 20 lessons from high-concurrency sessions (N>=5, identifiable from git log timestamps) and 20 from low-concurrency sessions (N<=2). For each, run the F-QC5 bullshit detection methodology (claim classification: supported/unsupported/contradicted). Compare unsupported rates and mean citation count per lesson.
  **Prediction**: High-concurrency lessons will have 1.5-2x the unsupported claim rate (predicted 18-25% vs baseline 11-15%) and 30%+ fewer citations per lesson.
  **Falsification**: If unsupported rates are statistically indistinguishable between high-N and low-N sessions (within 3pp), concurrency does not degrade quality and the quality gate is sufficient regardless of load.
## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-QC1 | CONFIRMED: 15.3% duplication rate (35 pairs, 44 flagged / 288 lessons) exceeds 2–10% hypothesis. Two dominant patterns: same-session multi-agent convergence (L-257/267) and sequential refinement without scan (L-285/292). Prescription: expand quality gate to last 20 titles; flag same-session pairs in compact.py. See L-309. | S189 | 2026-02-28 |
| F-QC2 | CONFIRMED (strict): 5% framing-contradicted (1/20: L-025 edge-of-chaos falsified by F9-NK RESOLVED), 20% broad (3/20 mechanism-superseded: L-019 HANDOFF.md→NEXT.md, L-042 composite→cycles, L-039 tension). 0% principle-contradicted. Decay is mechanism-level, not principle-level. Freshness gap bimodal: 11/20 <10 sessions (active), 6/20 >100 (canonical). Best staleness predictor: specific tool/metric recommendation subsequently tested. High citation partially protective. See L-633, experiments/quality/f-qc2-knowledge-decay-s359.json. | S359 | 2026-03-01 |
| F-QC3 | PARTIALLY CONFIRMED: cross-domain redundancy 0.07% (J>=0.25), 200x lower than within-domain (F-QC1: 15.3%). Atlas ratio threshold-sensitive (1.03-2.27x, small n). Domain-specific vocabulary prevents textual overlap; ISOMORPHISM-ATLAS compresses shared structure separately. Top pairs: ai×nk-complexity, economy×graph-theory. Cross-domain dedup unnecessary. See L-738, experiments/quality/f-qc3-redundancy-matrix-s381.json. | S381 | 2026-03-01 |
| F-QC4 | PARTIALLY CONFIRMED: TF-IDF keyword classifier (lesson_tagger.py) reduces unthemed nominally from 72.8% to 0.1%. Training accuracy 96.7% top-1 but deployment spot-check (n=10 unthemed): 30% exact, 40% partial, 30% wrong. Distribution shift: themed training set biased toward recent corpus. Error pattern: Swarm Economics over-attracted. Threshold tuning ineffective. Tool usable for suggestions, not auto-application. See L-743, experiments/quality/f-qc4-lesson-tagger-s383.json. | S383 | 2026-03-01 |
| F-QC5 | RESOLVED: YES, bullshit is reliably detectable. 5 retests (n=100): aggregate unsupported rate 11-15% (source-dependent). P-259 CONFIRMED: existence claims ~100% robust; numerical claims decay 5-35% depending on sampling source. Zero fabrication (1/80 ambiguity). All CONTRADICTED claims are count-drift (stale headers, not false assertions). Fix: wire count validation into maintenance.py. Dominant failure mode: header-body desynchronization. L-760, P-259. Artifacts: `f-qc5-bullshit-retest-s387.json`, `f-qc5-bullshit-retest-s388.json`, `f-qc5-resolution-s405.json`, `f-qc5-bullshit-retest-s405.json`. | S405 | 2026-03-01 |
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SUB1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SOUL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-TURING1. (auto-linked S420, frontier_crosslink.py)
