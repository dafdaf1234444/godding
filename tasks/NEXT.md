Updated: 2026-03-01 S392 | 711L 169P 20B 21F

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

