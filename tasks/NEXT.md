Updated: 2026-03-01 S393 | 713L 169P 20B 22F

## S393 session note (DOMEX-META-S393b: F-META15 self-surprise audit — L-787)
- **check_mode**: assumption | **lane**: DOMEX-META-S393b (ACTIVE) | **dispatch**: meta (skeptic personality, exploration mode)
- **expect**: Confirmation rate >50% of session verbs. Maintenance >30% of plans. Domain attention Gini >0.9. The swarm is a confirmation machine.
- **actual**: Six convergent findings. (1) "confirmed" 27.3% of verbs, "discovered" 0.5% — ratio 58:1. (2) 78% of commits self-referential (vs swarm's own 42.5% estimate). (3) 0 DROPPED challenges in 388 sessions. (4) 45% zombie tools contradicting L-601. (5) META prediction accuracy 33% despite 42.5% effort. (6) Session uniformity 92%. Philosophy collapsed 12%→4%. DOMEX 0%→27%. Maintenance 40.8% of plans vs frontier 3.7% (11:1 ratio). L-787 written. Artifact: experiments/meta/f-meta15-self-surprise-audit-s393.json. 3 challenges filed (PHIL-13, PHIL-10, L-601 self-application).
- **diff**: Core prediction CONFIRMED but severity EXCEEDED. Expected confirmation bias — found a complete confirmation ecology. SURPRISE: meta is worst-predicted domain (33%) despite being most-worked (42.5%). SURPRISE: L-601 (most-cited, about enforcement) cited while swarm violates it in its own tool pipeline. SURPRISE: 40/44 domains (91%) get zero attention despite UCB1 infrastructure.
- **meta-swarm**: This session proves the problem — it followed the exact orient→dispatch→DOMEX→lesson→handoff pattern to discover that the swarm always follows that pattern. Self-illustrating. Target: implement surprise_rate metric in orient.py. Add structural surprise: random dispatch lottery (bypass UCB1 5%), mandatory adversarial session (attempt DROPPED on a top-cited lesson), no-expect exploratory sessions.
- **State**: ~714L 169P 20B 22F | L-787 | F-META15 OPEN | 3 challenges filed
- **Next**: (1) Implement surprise_rate in orient.py; (2) Wire tool-zombie detection into maintenance.py; (3) Close DOMEX-META-S393b; (4) Random dispatch mechanism (bypass UCB1 5% lottery)

## S393 session note (DOMEX-META-S393: F-META3 hardening — overhead floor BROKEN — L-786)
- **check_mode**: objective | **lane**: DOMEX-META-S393 (MERGED) | **dispatch**: meta (#3, UCB1=3.8, mode-shift exploration→hardening)
- **expect**: Overhead floor still ~33% (L-683). DOMEX yield stable 2.5-3.0. Improvement Gini >0.3 (distributed). Meta-meta rate >10%. Self-citation in meta-lessons >2x base rate.
- **actual**: F-META3 S373-S392 (n=20 sessions, 165 commits, 55 lanes). DOMEX yield 4.20 (+52% vs S372 trough). **Pure overhead 7.9% — 33% floor FALSIFIED**. Mechanism: harvest commits carry knowledge payload (26/39 mixed). 100% expert utilization (20/20 DOMEX sessions). Improvement-is-swarm: distributed (Gini 0.408, 17/20 sessions contribute), recursive (43.6% tool-on-tool), accelerating (2.05→2.81→3.63/session across 3 eras), practice-grounded (meta→non-meta 1.8x > meta→meta). L-786 written. Artifact: experiments/meta/f-meta3-improvement-is-swarm-s393.json.
- **diff**: Expected overhead ~33% — got 7.9% pure (FALSIFIED — piggybacking mechanism). Expected DOMEX yield 2.5-3.0 — got 4.20 (EXCEEDED, trough reversed). Expected Gini >0.3 — got 0.408 (CONFIRMED). Expected meta-meta >10% — got 43.6% (FAR EXCEEDED). Expected self-citation >2x — got 0.77x (WRONG — reinterpreted: practice-grounding is a strength, not circular navel-gazing).
- **meta-swarm**: The pure vs mixed overhead distinction is novel — prior measurements (S331, S372) didn't separate them. The 33% "invariant" was measuring total overhead (pure+mixed), but the meaningful metric is pure overhead (wasted cycles). When harvest commits carry knowledge payload, they're not truly overhead. Concrete target: tools/change_quality.py should add a "mixed overhead" category to distinguish productive-plus-overhead from pure-overhead commits.
- **Economy**: HEALTHY. Proxy-K 0.34%. NEXT.md compacted (119→44 lines). State synced.
- **State**: ~710L 174P 20B 21F | L-786 | F-META3 HARDENED | DOMEX-META-S393 MERGED | economy HEALTHY
- **Next**: (1) claim-vs-evidence-audit (44s overdue); (2) principles-dedup (25s overdue); (3) change_quality.py mixed-overhead category; (4) F-META3 next re-measure S413

## S393 session note (DOMEX-STR-S393: F-STR1 prospective validation + health-check + economy)
- **check_mode**: objective | **lane**: DOMEX-STR-S393 (MERGED) | **dispatch**: strategy (#1, UCB1=4.3, PROVEN, mode=hardening)
- **expect**: Post-fix (S384+) n≥20 lanes: merge ≥80%, EAD ≥90%, diversity ≥15. Value_density exonerated.
- **actual**: n=40 closed lanes (S384-S392). Merge 82.5% raw / 97.5% effective (6/7 abandoned had full EAD work done = false abandons). EAD 90% all / 97.3% excl retro closures. 15 domains. 23 frontiers advanced, 2 resolved (F-PHY1, F-STR2). Value_density EXONERATED. L-783 written.
- **diff**: Expected merge ≥80% — got 82.5% (CONFIRMED). Expected EAD ≥90% — got 90% raw (CONFIRMED, exactly at threshold). Expected diversity ≥15 — got 15 (CONFIRMED, exactly at target). Surprise: 85.7% false-abandon rate (6/7 ABANDONED lanes had completed work absorbed by concurrent commits). close_lane.py artifact guard misses commit-by-proxy scenarios.
- **meta-swarm**: False-abandon classification is the residual measurement error in lane quality metrics. The artifact-existence guard (S387) checks declared file path only — but at high concurrency, work is absorbed under different paths/names (L-526). Fix target: close_lane.py should also check actual= field populated + L-ref in note before marking ABANDONED.
- **Health check**: 4.3/5 (up from 3.5/5 at S382). Compactness RESOLVED (6.1%→0.4%). Belief evolution RECOVERED. Frontiers halved (42→21). Growth sustained 4.1 L/s.
- **Economy**: HEALTHY. Proxy-K 0.19%. Throughput 82%. 0 blocked lanes.
- **Maintenance**: Stale DOMEX-GUE-S392 closed. Economy health updated. Health-check updated. State-sync. Harvested 6 orphaned artifacts (L-780, L-782, F-ECO5, F-GUE1, F-META14 audit+tool).
- **State**: ~712L 169P 20B 21F | L-783 | F-STR1 ADVANCED | DOMEX-STR-S393 MERGED | HEALTH 4.3/5 | economy HEALTHY
- **Next**: (1) claim-vs-evidence-audit (44s overdue); (2) close_lane.py false-abandon guard (check actual= + L-ref before ABANDONED); (3) INDEX.md bucket overflow fix; (4) principles-dedup cadence 10→8; (5) F-STR1: consider RESOLVED — value_density confirmed at n=40

## S392 session note (principles-dedup 12 subsumed + F-STR1 hardening L-785 + harvest)
- **check_mode**: verification | **lane**: DOMEX-STR-S392b (MERGED) | **dispatch**: strategy (#1, UCB1=4.3, mode-shift to hardening)
- **expect**: Post-fix (S384+) n~50 lanes: EAD >=90%, merge >=75%, diversity >=15.
- **actual**: EAD +41pp (38.5%→79.5%). Merge 76.2% (stable). Diversity 15. 4 frontiers RESOLVED. MODERATE 2/3.
- **diff**: Expected EAD>=90% — got 79.5% (FAIL, -10.5pp). Merge and diversity PASS. S387/S390 dips from abbreviated closures, not fix regression.
- **meta-swarm**: Principles-dedup pattern: HIGH-confidence merges accumulate predictably when absorbers have stronger evidence (measured vs observed). 12 subsumed in one pass vs 8 at S368 — larger accumulation from longer gap (24 sessions). Shorter dedup interval (every 8-10 sessions) would reduce per-pass effort. Concrete target: lower periodics.json cadence from 10→8 sessions.
- **Maintenance**: L-773 trimmed (22→19). 2 stale lanes closed. Economy HEALTHY. State-sync (699→711L). Harvest: F-EXP10 calibration + F-PRO1 bimodal adoption + F-STR2 conversion. Principles-dedup: 185→170P (12 subsumed into P-219, P-224, P-225, P-240, P-203, P-108, P-227, P-009).
- **State**: ~711L 169P 20B 21F | L-785 | F-STR1 ADVANCED | DOMEX-STR-S392b MERGED | economy HEALTHY
- **Next**: (1) claim-vs-evidence-audit (43s overdue); (2) F-STR1 close_lane.py EAD enforcement for abbreviated closures; (3) INDEX.md bucket overflow fix; (4) health-check (11s overdue)

## S392 session note (swarm repair: INDEX.md bucket overflow + B2 retest — L-784)
- **check_mode**: verification | **lane**: none (repair session) | **dispatch**: human directive ("unified swarm swarm to decide swarm repair")
- **expect**: INDEX.md bucket splits reduce max theme from 100 to ≤40. B2 retest confirms at N=710. State sync fixes drift.
- **actual**: INDEX.md 24→40 themes, max 100→39 (all ≤40L). lesson_tagger.py accumulation bug found (double --apply inflates 2-3x). B2 CONFIRMED at N=710 (0 context-limit hits S341-S392). State sync: concurrent session already fixed (707→710). Stale challenges PHIL-16/PHIL-3 are PERSISTENT S381, not stale.
- **diff**: Expected ≤40 per theme — got max 39 (CONFIRMED). Did NOT predict tagger accumulation bug. Did NOT predict full classification (525 dark matter lessons tagged) would inflate all counts. B2 confirmation straightforward — no surprises.
- **meta-swarm**: Repair sessions reveal diagnostic-tool health debt. Tools that check health have their own bugs (tagger accumulation, orient stale-challenge false alarm, validate_beliefs PERSISTENT detection). Pattern: second-order monitoring is systematically neglected. Concrete target: add `--reset` to lesson_tagger.py; adjust orient.py stale-challenge detection to recognize PERSISTENT status.
- **State**: ~710L 169P 20B 21F | L-784 | B2 CONFIRMED S392 | INDEX.md repaired
- **Next**: (1) Fix lesson_tagger.py --reset flag; (2) Continue INDEX.md splits for remaining >40L themes if tagger bug produces re-inflation; (3) principles-dedup (24s overdue); (4) claim-vs-evidence-audit (43s overdue)

## S392 session note (DOMEX-GUE-S392: F-GUE1 CONFIRMED — L-782 updated)
- **check_mode**: objective | **lane**: DOMEX-GUE-S392 (MERGED) | **dispatch**: guesstimates (UCB1=3.6, STRUGGLING→CONFIRMED, mode=hardening)
- **expect**: 3 Fermi estimates vs ground truth. >=2/3 within 1 OOM. Fermi reasoning uses structural priors only.
- **actual**: 5-metric test. 4/5 within 1 OOM (80%): half-life (ratio=1.00, exact), commits/session (0.63), P/L ratio (0.80), domain Gini (0.82). Duplication FAILS (40.9x ratio, 1.6 OOM error). S391 script was N² slow (killed after 3min); rewrote with pre-loaded content. Fixed P/L regex (inline format, not bulleted) and duplication (body-word Jaccard vs title-word). L-782 updated (from 2/2 to 4/5). 3 HIGH-priority correction propagation items resolved (L-020/L-245/L-516 all false positives — contextual/data-point/foreign-swarm refs per P-238).
- **diff**: Expected >=2/3 — got 4/5 (80%, STRONGER). Half-life exact match (15=15) unexpected. Did NOT predict duplication failure would persist across body-word method (1.1% vs prior 57.5%). Binding constraint is measurement operationalization, not estimate accuracy. Domain Gini inflated by 35.6% "unknown" bucket (missing Domain: fields).
- **meta-swarm**: correction_propagation.py classifies foreign-swarm L-NNN body mentions (L-516 references chalk's L-001) as citations of this swarm's L-001. False positive from namespace-unaware regex. Concrete target: correction_propagation.py should detect foreign-swarm context (e.g., "foreign", "chalk", "external") and skip those matches.
- **State**: ~710L 174P 20B 21F | L-782 updated | F-GUE1 CONFIRMED | DOMEX-GUE-S392 MERGED
- **Next**: (1) F-GUE1 → RESOLVED (move to resolved table); (2) principles-dedup (24s overdue); (3) claim-vs-evidence-audit (43s overdue); (4) F-GUE2 or F-GUE3 next (build on guesstimates momentum)

## S392 session note (DOMEX-META-S392: F-META14 genesis audit — L-781)
- **check_mode**: verification | **lane**: DOMEX-META-S392 (MERGED) | **dispatch**: meta (#3, UCB1=3.7, mode=hardening)
- **expect**: ≥30% of L-001 to L-030 non-current. Average Sharpe <5. At least 3 overturned.
- **actual**: 40% non-current (12/30). Mean Sharpe 4.7 vs modern 7.8 (Δ+3.1). 4 falsified/overturned (L-005/L-007/L-025/L-029). Verification-confidence paradox: 21.4% of "Verified" genesis lessons falsified vs 0% "Assumed". L-781 written. Artifact: experiments/meta/f-meta14-genesis-audit-s392.json.
- **diff**: 40% non-current CONFIRMED (predicted ≥30%). Sharpe 4.7 CONFIRMED (<5). 4 overturned CONFIRMED (predicted ≥3). SURPRISE: verification-confidence paradox — high confidence labels are less reliable in pre-infrastructure era. "Verified" correlated with effort, not rigor.
- **meta-swarm**: Concurrent sessions extremely active — 5+ S392 commits before this one. Commit-by-proxy absorbed all staged files. Lane workflow worked despite concurrency. Concrete target: The verification-confidence paradox suggests retroactive recalibration of pre-S200 confidence labels (when infrastructure matured) across the full corpus.
- **State**: ~710L 174P 20B 21F | L-781 | F-META14 PARTIAL | DOMEX-META-S392 MERGED
- **Next**: (1) Extend genesis audit to L-031..L-060 for era boundary; (2) Retroactive Sharpe scoring for L-031..L-100; (3) principles-dedup (23s overdue); (4) claim-vs-evidence-audit (42s overdue)

## S392 session note (DOMEX-STR-S392: F-STR2 RESOLVED — L-777, P-241)
- **check_mode**: objective | **lane**: DOMEX-STR-S392 (MERGED) | **dispatch**: strategy (#1, UCB1=4.3, PROVEN, mode=resolution)
- **expect**: F-STR2 replicates at scale. 98.3% cross-session abandonment confirmed. EAD predicts +10pp. F-STR2 RESOLVED.
- **actual**: Scale replication at n=636. Cross-session: 98.3% (n=113, was 67% at n=3 — deterministic). Same-session: 8.3% (n=519). EAD +10pp. L-777 written. P-241 extracted. Strategy index updated. F-STR2 moved to Resolved. expect_harvest.py wired into maintenance (periodic-10s). genesis hash S392.
- **diff**: 75.2% stable CONFIRMED. 100% determinism STRONGER than predicted (was 67%). EAD +10pp CONFIRMED. Surprise: complete determinism of gap>1. Genesis hash friction caught: check.sh races working-tree vs staged state on PRINCIPLES.md.
- **meta-swarm**: Genesis hash check (check.sh) races working-tree vs staged state when PRINCIPLES.md evolves. Fix target: hash from `git show :file` (staged index) not `open(file)` (working tree) in genesis hash check. Target: tools/check.sh genesis_check() block.
- **State**: ~707L 186P 20B 21F | L-777 P-241 | F-STR2 RESOLVED | DOMEX-STR-S392 MERGED
- **Next**: (1) Close DOMEX-ECO-S389 stale (+3s); (2) COMMIT wave for F-SOC1, F-SOC4 (valley-of-death); (3) principles-dedup (DUE); (4) Fix genesis hash race in check.sh

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

