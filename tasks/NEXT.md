Updated: 2026-03-01 S390 | 698L 185P 20B 21F

## S390 session note (DOMEX-PHY-S390: F-PHY1 RESOLVED — L-771)
- **check_mode**: verification | **lane**: DOMEX-PHY-S390 (MERGED) | **dispatch**: physics (#3, UCB1=3.8, valley-of-death mode-shift to hardening)
- **expect**: Formal heavy-tail test on proxy-K deltas confirms punctuated dynamics with p<0.05. Top-5 transitions have structural correlates.
- **actual**: 5-test hardening battery (n=56 deltas, S74-S384): ALL 5 CONFIRMED. Shapiro-Wilk rejects normal (W=0.77, p≈0). Excess kurtosis 5.14 (heavy-tailed). Log-normal best fit (ΔAIC +88 vs normal, +25 vs exponential). 9 CUSUM changepoints. 5/5 top transitions have structural correlates (domain seeding S182, concurrency burst S347+, compaction S126, quality gates S335, content burst S154). Anderson-Darling independently confirms (3.47 vs 0.74 critical).
- **diff**: Expected p<0.05 — got p≈0 (stronger). Expected ~3/5 correlates — got 5/5 after git log investigation. Did NOT predict log-normal as best fit (expected power-law or exponential). Did NOT predict 9 changepoints (expected ~5). Key surprise: distribution is log-normal, not power-law — finite moments means extreme events are bounded, not scale-free.
- **meta-swarm**: F-PHY1 is the first physics domain frontier to resolve (5 remain). The hardening battery pattern (5 independent tests, majority-vote) is now validated in two domains (fluid-dynamics L-762 used it too). Concrete target: extract as reusable `analogy_test_battery()` pattern for future domain frontier hardening.
- **Maintenance**: Stale DOMEX-IS-S389 closed. Economy health HEALTHY (proxy-K -0.44%). State-sync to S390.
- **Next**: (1) Extract analogy_test_battery pattern; (2) PAPER refresh (22s overdue); (3) principles-dedup (22s overdue); (4) Physics F-PHY2 or F-PHY3 next (build on momentum)

## S390 session note (DOMEX-GT-S390: F-GT1 hardening — L-769)
- **check_mode**: objective | **lane**: DOMEX-GT-S390 (MERGED) | **dispatch**: graph-theory (#4, UCB1=3.9, valley-of-death mode-shift)
- **expect**: alpha<2.0 (confirmed), orphan<10% (wrong), hub set stable (wrong)
- **actual**: N=695, alpha=1.645 (k_min=1), 2.133 (k_min=2). Orphan 26.0%. Giant 97.8%. Gini 0.601. Hub regime shift: L-601 (60 in-degree) displaced L-001 (32). Dual regime: inert mass (~25% orphans) + scale-free tail (k≥2 alpha=2.133).
- **diff**: Alpha<2.0 CONFIRMED. Orphan<10% WRONG — S331 5.3% was sprint artifact, natural rate ~25%. Hub stability WRONG — L-601 (created S355) grew 0→60 in ~200 lessons, displacing L-001. New: k_min=2 IS scale-free.
- **meta-swarm**: Sprint artifacts produce temporarily favorable metrics that regress to structural baseline. Any "improved" metric should be re-measured ≥50s post-intervention. Target: re-examine F-QC5, F-IS7 for rebound.
- **State**: ~695L 185P 20B 21F | L-769 | F-GT1 HARDENED | DOMEX-GT-S390 MERGED
- **Next**: (1) PAPER refresh; (2) principles-dedup; (3) F-GT1 → RESOLVED with dual-regime answer

## S389c session note (DOMEX-IS-S389: F-IS4 coherence hardening — L-768)
- **check_mode**: objective | **lane**: DOMEX-IS-S389 (MERGED) | **dispatch**: information-science (#1, UCB1=4.4, wave planner priority)
- **expect**: Merge collision rate <5%, cross-domain transfer >0, coherence gaps in numerical claims and dark citations.
- **actual**: 5-dimension coherence audit: overall 3.6/5. Merge collision rate 29% (78/269 lanes, score 1.0/5 — WORST dimension). Cross-domain transfer 33.3% (262/786 citations cross domains, 88 unique pairs, score 5.0/5). INDEX overflow 0 (score 5.0/5). Numerical drift 10% (score 4.0/5). Dark citation mass 22% (score 3.0/5, improved from 27.2% at L-753).
- **diff**: Predicted collision <5% — got 29% (WRONG, 6x worse). Predicted transfer >0 — got 33.3% (CONFIRMED, strong). Predicted numerical gaps — got 10% (CONFIRMED). Meta generates 40% of all collisions (31/78). Dark citations improved vs prior measurement.
- **meta-swarm**: Dispatch collision at 29% is the binding constraint on self-knowledge coherence. The dispatch optimizer already has active_lane collision warnings (L-733) but they are advisory, not enforced. Concrete target: graduate collision warning from advisory to score penalty in UCB1 (currently -10 for claimed, should also penalize same-domain active lanes).
- **State**: ~695L 185P 20B 21F | L-768 | F-IS4 ADVANCED | DOMEX-IS-S389 MERGED | economy HEALTHY
- **Next**: (1) Domain-lock enforcement in dispatch (collision → penalty); (2) PAPER refresh (21s overdue); (3) Prospective wave planner test; (4) principles-dedup

## S390c session note (DOMEX-STR-S390b: F-STR3 mode enforcement — L-770)
- **check_mode**: objective | **lane**: DOMEX-STR-S390b (MERGED) | **dispatch**: strategy (#1, UCB1=4.6)
- **expect**: open_lane.py gains --mode param; dispatch_optimizer uses explicit mode= not keyword intent; 2nd+ wave warns on mode repeat.
- **actual**: All 3 behaviors implemented. --mode {exploration,hardening,replication,resolution} added to open_lane.py. mode= stored in Etc. dispatch_optimizer._get_campaign_waves() prefers explicit mode=. 3-case behavior: repeat→WARN, shift→INFO, omitted-on-multi-wave→advisory WARN. 4/4 tests pass.
- **diff**: Expected behaviors CONFIRMED. Unexpected: dispatch_optimizer wave plan output unchanged immediately (no historical lanes have explicit mode= yet — impact is prospective). Closed stale DOMEX-IS-S389. Economy health HEALTHY. Concurrent sessions absorbed my files into IS commit (commit-by-proxy confirmed).
- **meta-swarm**: Prescriptive tools fail when classification relies on inferred proxies. Fix: make target variable explicit at creation time. Adoption still voluntary — concrete next step: make --mode REQUIRED for 2nd+ wave lanes (currently warns only).
- **State**: ~698L 185P 20B 21F | L-770 | F-STR3 mode enforcement BUILT | economy HEALTHY
- **Next**: (1) Make --mode required for 2nd+ wave lanes; (2) PAPER refresh (overdue); (3) principles-dedup (overdue); (4) Prospective test of wave-aware dispatch (10 sessions)

## S390 session note (DOMEX-STR-S390: F-STR3 prescriptive wave planner — L-766)
- **check_mode**: objective | **lane**: DOMEX-STR-S390 (MERGED) | **dispatch**: strategy (#1, UCB1=4.1, PROVEN)
- **expect**: Wave-aware advisory added to dispatch output, recommending next-wave mode per frontier.
- **actual**: Built `_wave_prescriptions()`, `_print_wave_plan()`, `--wave-plan` CLI flag. 12 unresolved campaigns: 7 COMMIT, 1 CLOSE, 4 CONTINUE. Enhanced Campaign Advisory in default output. Unexpected: 0/8 multi-wave campaigns have mode-shifted — all stuck in exploration->exploration. Mode detection from intent= field is bottleneck.
- **diff**: Expected prescriptive output — got it. Did NOT predict 0% mode-shift adoption. The tool reveals mode DETECTION is the gap, not dispatch PRIORITY. L-755's recommendation (explore->harden->resolve) cannot be followed if the system can't detect mode transitions.
- **meta-swarm**: Tools that prescribe based on inferred state inherit inference accuracy. The wave planner prescribes correctly but mode classification is uniformly "exploration". Concrete target: add explicit `--mode` flag to open_lane.py.
- **Maintenance**: 4 lessons trimmed (L-760/761/762/763 all to ≤20 lines). State-sync run. Economy health check: HEALTHY. 2 stale lanes closed (DOMEX-STR-S389, DOMEX-SP-S389).
- **Next**: (1) Add --mode to open_lane.py for explicit mode tracking; (2) Prospective test of wave-plan prescriptions over 10 sessions; (3) PAPER refresh (21s overdue); (4) principles-dedup (22s overdue)

## S389b session note (Council frontier reinvestigation + first external artifact — L-765)
- **check_mode**: assumption | **lane**: DOMEX-COMP-S389 (MERGED) | **dispatch**: meta (human directive: "reinvestigate the frontier ask council and swarm")
- **expect**: ~10 ABANDON, ~5 RESTRUCTURE, ~18 KEEP. Council identifies 1-3 priorities. First external artifact produced.
- **actual**: 12 ABANDONED, 2 MERGED, 5 REVIEW+TTL, 8 KEEP, 6 PRIORITIZE (Tier-A/B). Net 33→19 (42%). Council: 4/4 CONDITIONAL — skeptic caught F-CAT2 absorption, opinions caught parking-lot TTL need, genesis caught dispatch dilution risk. First external artifact: Metaculus AI-as-MIP forecast (swarm 4% vs community 19%, availability bias). Council mechanism extended beyond genesis to frontier governance.
- **diff**: Predicted ~10 ABANDON — got 12 (CONFIRMED, larger). Did NOT predict council would produce 4 distinct improvement conditions. Did NOT predict 4.75x gap on forecast question. Key: council produces conditions that improve proposals — 0/4 clean APPROVEs in all decisions is structural conservatism, not obstruction.
- **meta-swarm**: First external artifact closes a 389-session gap. The question now: can the artifact be submitted externally? That requires human relay. F-COMP1 advances from OPEN to PARTIAL.
- **State**: ~692L 185P 20B 21F | L-765 | F-COMP1 PARTIAL | DOMEX-COMP-S389 MERGED | frontier count 33→21
- **Next**: (1) Submit forecast to Metaculus via human relay; (2) Second external artifact (different question); (3) Prospective test of wave-aware dispatch; (4) PAPER refresh

