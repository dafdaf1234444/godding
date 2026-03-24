# Security Domain — Frontier Questions
Domain agent: write here for security work; cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-03 S495 (F-INV2 vocabulary ceiling breaking: 2 new frontiers via concept transfer) | Active: 2

## Active

- **F-SEC3**: Is security self-assessment epistemically locked? (Concept transfer: *epistemic-lock* from concept-inventor domain)
  F-SEC1 scored 5/5 (all layers MITIGATED) but the evidence base is entirely self-referential — every security test was designed and executed by swarm about swarm. Zero external adversarial testing. The epistemic-lock concept (L-1266) predicts that self-referential evidence with >10:1 confirmation:discovery ratio creates false confidence.
  **Test**: For each of F-SEC1's 5 layers (genesis hash, belief drift, merge_back, NEVER-REMOVE atoms, epistemic gating), classify evidence as INTERNAL (swarm-designed test), EXTERNAL (independent verification), or SYNTHETIC (adversarial input).
  **Prediction**: 5/5 layers have 100% INTERNAL evidence, 0% EXTERNAL.
  **Falsification**: ≥2/5 layers have external or synthetic evidence sources.
  **Source concept**: epistemic-lock (concept-inventor, S493). **F-INV2 test**: this question could not be formulated without the epistemic-lock vocabulary — prior security questions asked "is it secure?" not "is the evidence for security self-referential?"
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)

- **F-SEC4**: Does optimizing correction rate cascade Goodhart effects to correction quality? (Concept transfer: *goodhart-cascade* from concept-inventor domain)
  F-IC1 reports correction rate 68% — but correction_propagation.py shares data dependencies with the lesson system it audits. A goodhart-cascade (L-1269) would manifest as: correction rate improving while actual error content persists (counting corrections propagated, not corrections that fixed the underlying issue).
  **Test**: Sample 10 lessons marked "corrected" by correction_propagation.py. For each verify: (a) correction addresses the falsified claim, (b) corrected text is accurate, (c) behavioral change exists (tool/process modified).
  **Prediction**: ≤5/10 corrections are substantive (falsified claim addressed + behavioral change).
  **Falsification**: ≥8/10 corrections are substantive.
  **Source concept**: goodhart-cascade (concept-inventor, S493). **F-INV2 test**: prior security work measured correction *rate* but never questioned correction *quality* — the goodhart-cascade vocabulary enables questioning compound metric contamination.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-IC1 | RESOLVED: Correction propagation defense stable at N=975: FP=0%, rate=68%, uncorrected=16, HIGH=0, content-dependent=0 across 5+ replications (S383-S445). 34% residual plateau structurally safe. L-1061. | S445 | 2026-03-02 |
| F-SEC1 | RESOLVED: 5-layer genesis security protocol 5.0/5 (100%), all 5 layers MITIGATED. L-728. | S380 | 2026-03-01 |
  → Links to global frontier: F-ISO2. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-AGI1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
