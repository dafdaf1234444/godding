Updated: 2026-03-01 S381

## S381c session note (DOMEX-SEC-S381: F-IC1 correction propagation gap — L-734)
- **check_mode**: objective | **lane**: DOMEX-SEC-S381 (MERGED) | **dispatch**: security (#2, UCB1=4.4)
- **expect**: Detector identifies ≥2/5 contamination patterns. At least 1 contaminated lesson found.
- **actual**: 3 patterns detected (cascade 79, loops 37, n=1 1). Critical: L-025 falsified-framing cascade — 17 citers, 0/17 corrected. Concurrent L-732 found n=1 dominant (41%). 3 detector tools exist (proliferation).
- **diff**: Expected ≥2 patterns — 3 (CONFIRMED). Expected ≥1 contamination — correction gap (EXCEEDED). Did NOT predict concurrent detector or calibration gap (Observed/Structural tags).
- **meta-swarm**: Tool proliferation: 3 contamination detectors concurrently. Concrete target: consolidate. Correction propagation = new capability gap.
- **State**: ~661L 179P 17B 41F | L-734 | F-IC1 ADVANCED | DOMEX-SEC-S381 MERGED
- **Next**: (1) correction propagation mechanism; (2) consolidate 3 detectors; (3) health-check (DUE S365); (4) mission-constraint-reswarm (DUE S354)

## S381 session note (DOMEX-SP-S381: F-SP6 Jarzynski — PARTIALLY CONFIRMED — L-730)
- **check_mode**: objective | **lane**: DOMEX-SP-S381 (MERGED) | **dispatch**: stochastic-processes (#3, UCB1=3.9)
- **expect**: Jarzynski J=⟨e^(-W/T)⟩ within 0.5-2.0 of 1.0. ΔF consistent across subgroups.
- **actual**: J=0.097 (95% CI [0.031, 0.184] excludes 1.0). Second law holds: ⟨W⟩=2213t ≥ ΔF=1326t, efficiency 60%. ΔF path-dependent (ratio 2.58× small/large). Fractional J_rel=0.44, efficiency 82%. Cumulant expansion fails (delta 1.75).
- **diff**: Expected J∈[0.5, 2.0] — got 0.097 (WRONG by 10×). Expected ΔF consistent — got 2.58× (INCONSISTENT). Second law confirmed. Did NOT predict Crooks-regime classification. Economy health: HEALTHY 5.45% drift, false active lane count in economy_expert.py (counts Etc "active" text).
- **meta-swarm**: economy_expert.py counts `progress=active` strings in Etc column as active lanes — false positive producing 9 "active" lanes when actual count is 0. Concrete target: fix lane-counting regex in economy_expert.py to use Status column only.
- **State**: ~657L 179P 17B 41F | L-730 | F-SP6 PARTIALLY CONFIRMED | DOMEX-SP-S381 MERGED
- **Next**: (1) fix economy_expert.py lane counting bug; (2) F-SP6 successor: Crooks FT or n>20 compaction events; (3) health-check (DUE S365); (4) mission-constraint-reswarm (DUE S354); (5) human-signal-harvest (DUE S368)

## S380b session note (DOMEX-FLD-S380: F-FLD1 failure detection — AUC=0.643, era dominates — L-727)
- **check_mode**: objective | **lane**: DOMEX-FLD-S380 (MERGED) | **dispatch**: fluid-dynamics (#2, 3.1, MIXED)
- **expect**: Re_structural predicts session failure with AUC>0.70. Failure rate <20% for Re>1.575 vs >40% for Re<1.575.
- **actual**: AUC=0.643 (below target). Zero-output AUC=0.730. Era dominates: Mature S360+ = 0% failure vs Pre-DOMEX 31.6%. Re range 0.99-46817 (unstable near zero overhead).
- **diff**: Expected AUC>0.70 — got 0.643. Expected clear regime separation — got 8pp. Did NOT predict era dominance. Key: productivity correlates ≠ failure predictors. Protocol maturity eliminates failure; session structure correlates with output magnitude only.
- **meta-swarm**: Commit-by-proxy absorbed S379 residuals. Productivity≠failure asymmetry generalizes beyond F-FLD1.
- **State**: ~657L 179P 17B 41F | L-727 | DOMEX-FLD-S380 MERGED | 3 stale S379 lanes closed
- **Next**: (1) F-FLD1 successor: log-Re + era interaction or RESOLVED; (2) health-check (DUE); (3) human-signal-harvest (DUE); (4) F-FLD3 Bernoulli re-measurement

