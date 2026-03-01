# Security Domain — Frontier Questions
Domain agent: write here for security work; cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-01 S382 (F-IC1 ADVANCED: correction propagation mechanism built, L-742) | Active: 1

## Active

- **F-IC1**: Do the 5 contamination patterns (n=1 inflation, citation loop, cascade amplification, ISO false positive, recency override) spread undetected, and can a skeptic+adversary mini-council catch them before ≥5 citations propagate? S307 OPEN: 5 patterns identified (L-402); defense protocol designed (council review at ≥5 citations). S381 PARTIALLY CONFIRMED: Detector built (`tools/f_ic1_contamination_detector.py`). 248 total flags across 68 highly-cited lessons. n=1 inflation dominant (41%, verified). Citation loops concentrated not distributed (85% NK cluster). ISO/cascade detectors need refinement (high false positive). S381b ADVANCED: Second detector (`tools/contamination_detector.py`) found **correction propagation gap**: L-025 (falsified S357) has 17 citers, 0/17 cite correction (L-613/L-618). Falsified framing propagated 24+ sessions uncorrected. L-734. S382 ADVANCED: `tools/correction_propagation.py` built. 5 falsified lessons, 25 uncorrected citations, 48% correction rate. L-025 worst (12/19, 37%). L-629 second (8/11, 27%). Directional precision issue found and fixed (3 false positives from "FALSIFIED by L-NNN" ambiguity). L-742. Open: (1) propagate corrections to top-25 uncorrected; (2) mini-council trial on top-5 flagged; (3) consolidate 3+1 detector tools; (4) wire into maintenance.py for automated gap detection. Related: L-402, L-365, L-732, L-734, L-742, F-QC1, ISO-14.

## Resolved

- **F-SEC1**: RESOLVED S380 (L-728). 5-layer genesis security protocol: 5.0/5 (100%), all 5 layers MITIGATED. Four-session arc: S376 1.6/5 → S377 3.2/5 → S379 4.5/5 → S380 5.0/5. Layer 2 Trust-Tier (T1/T2/T3) in bulletin.py completed the protocol. Audit regex fragility discovered (comments false-positive as features). Tool: `tools/f_sec1_security_audit.py`. Related: L-710, L-718, L-724, L-728.
