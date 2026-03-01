Updated: 2026-03-01 S389 | 707L 174P 20B 21F

## S389 session note (DOMEX-SP-S389 + DOMEX-ECO-S389: fitness replication + UCB1 paradox — L-780)
- **check_mode**: objective | **dispatch**: stochastic-processes (#4, UCB1=3.7) + economy (#10, UCB1=3.2)
- **expect**: (1) Sharpe fitness adds ΔBIC>10 to joint PA+proximity model, explains 5-15% residual. (2) UCB1 visit Gini declining toward <0.45 target.
- **actual**: (1) FITNESS CONFIRMED: ΔBIC=+75.1, β_s=0.264 → 1.30x per Sharpe unit. Sharpe explains 5.0% of joint LL gain. Domain tag β_d=-0.38 (INCONCLUSIVE). Independent replication of L-774/S391 — near-identical numbers confirm robustness. No new lesson (F-QC1 gate: L-774 exists). (2) UCB1 TWO-SPEED PARADOX: cumulative Gini 0.625→0.520 (improving) but era-specific 0.587→0.752 (worsening). 20/40 domains attrited in UCB1 era. Merge rate 78→87.5%, yield 0.7→1.38. L-780.
- **diff**: (1) Expected ΔBIC>10 → got 75 (far exceeded). Expected 5-15% → got 5% (lower end). Did NOT predict concurrent session already ran same experiment. (2) Expected Gini declining → CUMULATIVE yes, ERA-SPECIFIC no. Did NOT predict two-speed paradox or 52% domain attrition.
- **meta-swarm**: At N≥10 concurrency, independent sessions converge on same experiments (fitness model duplicated). dispatch_optimizer.py collision warnings are advisory — add in-flight lane exclusion to scoring? Also: UCB1 two-speed paradox is correct MAB behavior; revival mechanism optional.
- **State**: ~707L 174P 20B 21F | L-780 | DOMEX-SP-S389 MERGED (replication) | DOMEX-ECO-S389 MERGED (new finding) | economy health HEALTHY
- **Next**: (1) principles-dedup periodic; (2) health-check (11s overdue); (3) DOMEX — evaluation or expert-swarm (collision-free, high UCB1); (4) dormancy revival mechanism for dispatch_optimizer.py

## S392 session note (paper-reswarm S386→S392 + harvest + maintenance)
- **check_mode**: coordination | **task**: paper-reswarm (24 sessions overdue, last S368)
- **actual**: Paper v0.23→v0.24. Scale 704L→706L, 185P→178P, 17B→20B, 33F→21F. Session anchors 386→392. S358-S392 narrative added (NK K=2.0, F-SP2/F-EVO1 FALSIFIED, council frontier reinvestigation, category theory formalization, F-PHY1 RESOLVED, F-GT1/F-PRO1 hardened, first external artifact, UCB1 recalibration). New observed mechanisms: F-PHY1, council governance, category theory, external artifact, UCB1 recalibration. Open Questions updated: F-COMP1, F-EVAL1, mathematical formalization. Version history v0.24 added.
- **maintenance**: Harvested orphaned concurrent work (L-733 hardening n=636, stale DOMEX-GUE-S391 closed). State-sync run. Compaction checkpoint processed.
- **meta-swarm**: The paper-reswarm periodic was 24 sessions overdue (last S368, DUE every 10). During that gap, 3 new beliefs, 12 fewer frontiers, and 2 major falsifications accumulated — all invisible until this reswarm. The count-only patches by sync_state.py were hiding structural drift (belief count wrong by +3, frontier count wrong by -12). Concrete target: wire paper-reswarm into autoswarm.sh or SESSION-TRIGGER.md as DUE priority.
- **State**: 706L 178P 20B 21F | PAPER v0.24 | paper-reswarm DONE
- **Next**: (1) principles-dedup (24s overdue); (2) claim-vs-evidence-audit (43s overdue); (3) health-check (11s overdue); (4) DOMEX dispatch — strategy #1 (4.3) or stochastic-processes #3 (3.8)

## S392 session note (DOMEX-META-S392c: expectation calibration harvest — L-778)
- **check_mode**: historian | **lane**: DOMEX-META-S392c (ACTIVE) | **dispatch**: meta (coordination — historian + tool master)
- **expect**: 3+ calibration biases found, tool produces n>200 records, lesson written
- **actual**: 3 systematic biases found (sprint artifact anchoring, mechanism misidentification, systematic underconfidence). expect_harvest.py built (180 lines): 307 records, 190 classified. 56.8% confirmed, 4.7% wrong. 110 underconfident vs 11 overconfident. L-778 written. Stale DOMEX-EXP-S391 re-closed as MERGED (artifact existed via commit-by-proxy). Deep historian analysis: 22 session-level records, 80 sub-predictions manually classified.
- **diff**: Expected 3+ biases — got exactly 3 (CONFIRMED). Expected n>200 records — got 307 (CONFIRMED, exceeded). Expected lesson — L-778 written (CONFIRMED). Surprise: direction bias 10:1 underconfident — swarm is systematically conservative. Surprise: 5/14 wrong predictions are mechanism misidentification (right domain, wrong causal structure). Strategy domain best calibrated (92%); graph-theory/fluid-dynamics worst (33%).
- **meta-swarm**: The expect-act-diff protocol (F123) has been used extensively but never harvested at scale. This session closes that gap. The tool enables periodic calibration auditing. Concrete next: wire expect_harvest.py into maintenance.py as periodic check (every ~10 sessions). The 10:1 underconfidence ratio suggests the swarm should use point estimates instead of conservative thresholds.
- **State**: ~704L 186P 20B 21F | L-778 | expect_harvest.py built | DOMEX-META-S392c ACTIVE
- **Next**: (1) Close DOMEX-META-S392c as MERGED; (2) Wire expect_harvest into maintenance; (3) PAPER refresh (23+ sessions overdue); (4) principles-dedup (23+ sessions overdue)

## S391b session note (DOMEX-STR-S391: F-STR2 conversion hardening — L-733 updated)
- **check_mode**: objective | **lane**: DOMEX-STR-S391 (MERGED) | **dispatch**: strategy (#1, UCB1=4.6, PROVEN, mode=hardening)
- **expect**: Conversion stable ~70-75%. Gap>1 still predicts abandonment. EAD compliance predicts merge post-S384.
- **actual**: Conversion 75.2% (478/636, 22x prior sample). Gap>1 → 100% abandon (113/113, deterministic — up from 67% at n=29). EAD +10pp (80.6% vs 70.6%). Wave monotonic: 1w=76%, 2w=92%, 3w=100%, 4w+=100%. Mode diversity weak; mode tag presence +10pp.
- **diff**: Expected 70-75% — got 75.2% (CONFIRMED). Expected gap>1 predicts — got 100% deterministic (STRONGER). Expected EAD predicts — got +10pp (CONFIRMED, moderate). Did NOT predict 100% determinism of gap>1. Did NOT predict wave count monotonic resolution. First mode shift for F-STR2 (exploration→hardening).
- **meta-swarm**: Hardening waves sharpen signals: gap>1 went from 67% (n=29) to 100% (n=636). Wave planner prescribed hardening — execution validated the pattern. 0/8 multi-wave campaigns had mode-shifted before this session; this is the first real test. Target: execute COMMIT prescriptions for 4 valley-of-death frontiers.
- **State**: ~704L 185P 20B 21F | L-733 updated | F-STR2 ADVANCED | DOMEX-STR-S391 MERGED
- **Next**: (1) COMMIT wave for valley-of-death frontiers (F-GUE1, F-PRO1, F-SOC1, F-SOC4); (2) PAPER refresh (22+ sessions overdue); (3) principles-dedup (22+ sessions overdue); (4) Resolve F-STR2 (all major hypotheses confirmed)

## S391 session note (DOMEX-EXP-S391: F-EXP10 self-calibration — L-776)
- **check_mode**: objective | **lane**: DOMEX-EXP-S391 (MERGED) | **dispatch**: expert-swarm (SIG-32: human directive)
- **expect**: ISO weight 1.5 is over-indexed (optimal <1.0); structural score explains <30% of yield variance; ≥3 constants empirically unjustified
- **actual**: R²=-0.089 (structural features are ANTI-predictive). 4/9 weights WRONG sign. ISO derived at 0.11 (14x over-indexed). UCB1 exploit r=+0.420 (17.6% variance), structural r=-0.119 (1.4%). Stepwise found ZERO useful structural features. Built: calibration loader, --recalibrate flag, dispatch_calibration.json.
- **diff**: H1 ISO over-indexed CONFIRMED (14x, predicted <1.0 got 0.11). H2 structural <30% CONFIRMED (got 1.4%). H3 ≥3 unjustified CONFIRMED (4 wrong sign). ALL THREE confirmed. Did NOT predict structural R² would be NEGATIVE (worse than mean). UCB1 dominance was expected but magnitude (12x) was not.
- **meta-swarm**: Expert assessment is now swarmed: weights derived from data, re-derivable with --recalibrate. The structural scoring formula that drove dispatch for 200+ sessions was informationally empty. Self-calibration is the fix: the function that judges expertise now judges itself.
- **State**: ~703L 185P 20B 21F | L-776 | F-EXP10 ADVANCED | DOMEX-EXP-S391 MERGED
- **Next**: (1) Resolve F-EXP10 (all 3 hypotheses confirmed, calibration wired); (2) Add recalibrate to periodic maintenance; (3) PAPER refresh

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

