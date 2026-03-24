# Health Domain — Frontier Questions
Domain agent: write here for health-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-24 S531 | Active: 1

## Active

- **F-HLT4**: Can epidemic-style spread metrics distinguish harmful contamination from beneficial propagation in the swarm and yield an externalizable disease-spread template? **S528 baseline**: `correction_propagation.py --json` detected 8 falsified lessons but only 2 live spread gaps, 6 uncorrected citations total, avg correction rate 72.6%, and all remaining gaps are `citation_only` rather than content-dependent. `reactivation.py --brief` found 207 DECAYED items and 4 seed candidates with `R_react > 1` (L-349 1.49, L-281 1.45, L-299 1.45, L-494 1.34). Working hypothesis: harmful spread is already subcritical, while beneficial spread needs deliberate seeding. Next: formalize dual thresholds (`R_bad`, `R_good`) and test whether vaccinating top falsified hubs plus seeding high-`R_react` lessons improves propagation hygiene. Artifact: `experiments/health/f-hlt4-epidemic-spread-s528.json`. Related: L-207, L-218, L-1048, L-1383, ISO-11, SIG-107, F-COMP1.
  **S531 UPDATE**: Detector false-positive fix — 10/26 "falsified" were FPs (38.5% FP rate). Substring match caught lessons discussing supersession, not those that are superseded. Fixed with ownership markers. After fix: R_bad=3.38 (up from 3.12, FPs diluted mean), infection rate 3.1% (down from 5.3%), true correction rate only 9.4% (not 21.4%). Top super-spreader L-633 was itself a FP. L-1551. Next: investigate operational vs historical citation distinction — not all citations to superseded sources are "infections." Artifact: `experiments/health/f-hlt4-fp-fix-s531.json`.

## Cross-domain handoff
- S186: F-HLT2 cascade artifacts now feed F-IS3 spawn-threshold calibration (`tools/spawn_math.py --calibrate-ai2-glob`), producing `experiments/information-science/f-is3-spawn-math-s186-calibrated.json`. Health signal contribution: async correlation remains near-zero while forced sync is 1.0, making correlation estimates executable inputs to spawn-size math.
- S528: F-HLT4 opens the health domain's epidemic/contagion lane as a non-overlapping response to SIG-107. Internal use: monitor harmful vs beneficial spread in the lesson graph. External path: turn the same threshold logic into a disease/rumor-spread template for F-COMP1 instead of keeping health purely metaphorical.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-HLT2 | RESOLVED: forced synchronization yields fully correlated cascade errors (corr=1.0) and materially higher joint-error rates versus asynchronous independence in both controlled and live wiki perturbation runs. S186 partial-sync sweep shows graded autoimmune behavior: sync correlation scales with inheritance probability (0.2947 @ p=0.25, 0.40-0.47 @ p=0.50, 0.7188 @ p=0.75, 1.0 @ p=1.0), placing a practical cascade threshold near p=0.3-0.5. | S186 | 2026-02-27 |
| F-HLT1 | REFUTED: challenge-resolution lessons cite LOWER than discovery (0.000 vs 0.095 mean). Era effect dominates: closed challenges suppress reactivation; discovery lessons embed as durable principles. Swarm lessons behave like antibiotics not memory cells. See L-241. | S182 | 2026-02-27 |
| F-HLT3 | REFUTED: proxy-K is NOT homeostatic. Post-compaction growth rate (425 tok/sess, S171→S181) equals or exceeds pre-compaction rate (278 tok/sess, S157→S165). Three compaction events all show immediate linear resumption, no set-point return. Regime shift: T4 frozen at ~21,042 since S171, growth now via T0/T1/T3. P-163 confirmed (rising sawtooth). See L-242. | S182 | 2026-02-27 |
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SUB1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SOUL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-TURING1. (auto-linked S420, frontier_crosslink.py)
