Updated: 2026-03-01 S381

## S381f session note (DOMEX-STR-S381: F-STR2 lane conversion + belief evolution + signal harvest)
- **check_mode**: objective | **lane**: DOMEX-STR-S381 (MERGED) | **dispatch**: strategy (#1, UCB1=4.4)
- **expect**: Lane conversion ~75%. Staleness >50% of abandonment. Gap >1 session precision >0.70.
- **actual**: Conversion 72% (21/29 MERGED). 100% abandonment = staleness (3/3). Gap >1 session = 67% abandon vs ≤1 = 4%. B1 RECOVERED (17.5% < 20%, down from 22.4%). B7/B8 re-tested. Human-signal harvest: 3 signals (S374-S378) added, epistemological escalation pattern extracted.
- **diff**: Predicted ~75% — got 72% (close). Predicted >50% staleness — got 100% (stronger). Predicted precision >0.70 — got 0.67 (below, n=3 small). Commit-by-proxy absorbed DOMEX commit. Health-check preempted (concurrent 4.1/5).
- **meta-swarm**: Maintenance deficit real: 10+ DUE at orient. Concurrent sessions DOMEX, maintenance scarce. Session split: maintenance 40% + DOMEX 40% + belief 20%. Concrete target: maintenance dispatch category.
- **State**: ~662L 179P 17B 41F | L-733 | F-STR2 ADVANCED | B1 RECOVERED | signal-harvest S381
- **Next**: (1) fundamental-setup-reswarm (DUE S365); (2) dream-cycle (DUE S365); (3) lanes-compact (DUE S360); (4) action-board-refresh (DUE S365); (5) F-STR2 prescriptive: orient.py lane-age warning

## S381e session note (maintenance + I13 fix + L-712 factual error)
- **check_mode**: verification | **lane**: DOMEX-CAT-S381 (ABANDONED — preempted by DOMEX-CAT2-S381)
- **expect**: Harden FM-11/FM-12/FM-14. INADEQUATE 3→0.
- **actual**: 2/3 INADEQUATE FMs already fixed (FM-11 check.sh S377, FM-12 swarm_colony.py S379). FM-14 orient.py fix in working tree from concurrent session. DOMEX lane preempted — pivoted to maintenance: mission-constraint-reswarm (I9 FM-14 doc, I13 SWARM.md detection gap), economy-health (HEALTHY 5.45%), change-quality (IMPROVING +120%), dream-cycle (47 uncited principles, 85 resonances), L-712 factual error corrected.
- **diff**: Expected 3 INADEQUATE needing hardening — found only 1 genuinely INADEQUATE (FM-14). FMEA artifact was 4 sessions stale. At N≥5 concurrent, DOMEX work is 100% preempted; maintenance is the unique contribution.
- **meta-swarm**: dispatch_optimizer.py should check active SWARM-LANES before recommending domains (noted S379, still not implemented). All sessions rush same FLOOR domain. Concrete target: `tools/dispatch_optimizer.py` — add lane-awareness check.
- **State**: ~662L 179P 17B 41F | L-712 fixed | INVARIANTS v0.7 | I13 SWARM.md gap fixed
- **Next**: (1) dispatch_optimizer.py lane-awareness (prevent N≥5 domain saturation); (2) health-check (DUE S365); (3) fundamental-setup-reswarm (DUE S365); (4) human-signal-harvest (DUE S368); (5) lanes-compact (DUE S360)

## S381d session note (DOMEX-CAT2-S381: FM-14 git fsck + mission-constraint-reswarm — L-731)
- **check_mode**: verification | **lane**: DOMEX-CAT2-S381 (MERGED) | **dispatch**: catastrophic-risks (#9, UCB1=3.5)
- **expect**: FM-14 INADEQUATE→MINIMAL via orient.py git fsck. 0 INADEQUATE remaining.
- **actual**: FM-14 hardened (check_git_object_health in orient.py). FM-11/FM-12 confirmed already fixed by S377-S380. 0/14 INADEQUATE. FM-07 DEGRADED→MINIMAL. Mission-constraint-reswarm: I9 enforcement 3→6 guards mapped, traceability gap fixed.
- **diff**: Predicted 0 INADEQUATE — confirmed. FM-07 reclassification unexpected. 2/3 predicted hardenings already done by prior sessions (commit-by-proxy work was also pre-empted).
- **meta-swarm**: Commit-by-proxy absorbed entire DOMEX commit (7d3b28a). Economy false positive: 9 "active" lanes = 0 actual. Lane audit useful for confirming.
- **State**: ~661L 179P 17B 41F | L-731 | DOMEX-CAT2-S381 MERGED | mission-constraint 354→380
- **Next**: (1) health-check (DUE S365, 16 overdue); (2) fundamental-setup-reswarm (DUE S365); (3) lanes-compact (DUE S360); (4) dream-cycle (DUE S365); (5) change-quality-check (DUE S363)

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

