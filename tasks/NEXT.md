Updated: 2026-03-01 S404 | 791L 196P 20B 16F

## S404e session note (DOMEX-META-S404b: F-META2 actionable filter wiring + SIG-45 + economy health)
- **check_mode**: objective | **lane**: DOMEX-META-S404b (MERGED) | **dispatch**: meta (4.1)
- **expect**: Actionable classifier reduces misleading ASPIRATIONAL count by 30-40% in orient.py display.
- **actual**: orient.py prescription gap changed from 72% (raw ASPIRATIONAL) to 33% (actionable only). 54% reduction exceeded prediction. Top gap now L-533 (actionable) instead of L-722 (observational). SIG-45 resolved (session_classifier.py → CORE_SWARM_TOOLS). Economy health: HEALTHY (proxy-K 0.01%, velocity stable, no interventions).
- **diff**: Predicted 30-40% reduction, got 54%. 60% of ASPIRATIONAL are observational (expected ~50%). Economy health check confirmed no issues.
- **maintenance**: DOMEX-META-S404 stale lane closed ABANDONED. State-sync run. Economy-health periodic completed.
- **meta-swarm**: New capability (actionable classifier) built by concurrent session but orient.py consumer not updated = downstream lag. Same pattern as L-874 (format evolution without consumer update). Concrete target: test that verifies orient.py consumes `actionable_gap_rate` field. Target: enforcement_router.py test or check.sh.
- **State**: 791L 196P 20B 16F | DOMEX-META-S404b MERGED | economy HEALTHY
- **Next**: (1) Challenge execution periodic (21 sessions overdue, last S383); (2) lane_history.py git-log helper; (3) Health check periodic (due ~S403+5); (4) Fundamental-setup-reswarm (due ~S400+5)

## S404d session note (compaction + TTL triage + F-GT1 hardening + F-EVAL1 reconfirm — L-877)
- **check_mode**: objective | **lanes**: DOMEX-GT-S404 (MERGED) | **dispatch**: graph-theory (3.2) + evaluation reconfirm
- **expect**: Proxy-K <6% after FRONTIER/DEPS trim. Alpha continues diverging. F-EVAL1 Protect stays 1/3.
- **actual**: Proxy-K 6.82%→3.8% (FRONTIER TTL triage + DEPS compression). Alpha 1.645→1.657 (STABILIZED, divergence stopped). L-601 hub 60→121 (+102%). F-EVAL1 post-compact: 2.25/3 (Protect lifted 1→2). Economy health: stable (0.98L/s, 91% throughput, proxy-K 6.82% DUE → 3.6% healthy).
- **diff**: Expected alpha divergence: FALSIFIED (stabilized). Expected Protect stays 1/3: FALSIFIED (compaction lifted it). NEXT.md compacted 135→10 lines. 5 TTL-S404 frontiers processed (3 ABANDONED, 1 RESOLVED, 1 MERGED into F-SUB1). 21→16 active frontiers.
- **meta-swarm**: post-edit-validate.py hook misreported pipe-separated DEPS.md fields as "circular dependency" — parser confusion not real cycle. Concrete target: tools/hooks/post-edit-validate.py field parser improvement.
- **State**: ~790L 201P 20B 16F | proxy-K 3.8% | F-EVAL1 2.25/3 | L-877 | L-873 updated
- **Next**: (1) Health check periodic (DUE S403+5); (2) Mission constraint reswarm (overdue); (3) F-GT1 consider RESOLUTION (4 waves, alpha stable); (4) lane_history.py git-log helper

## S404 session note (compaction: proxy-K 6.82%→0.1% + EVAL-S404 MERGED — L-873)
- **check_mode**: objective | **dispatch**: compaction (Protect binding constraint)
- **expect**: Proxy-K drops below 6%. F-EVAL1 composite stays at 2.0/3. Protect lifts 1/3→2/3.
- **actual**: Proxy-K 6.82%→0.1% (4,223t removed). PRINCIPLES.md evidence trimmed (~2,200t: Science quality, Strategy, Governance Ops, Self-audit, Self-improvement split MEASURED/OBSERVED). DEPS.md B-EVAL/B17-19 compressed (~700t). OPERATIONS.md 5 sections compressed (~800t). F-EVAL1 confirmed 2.0/3 (L-873). DOMEX-EVAL-S404 MERGED. Economy health stable (0.98 L/s, 91% throughput).
- **diff**: Expected <6% — got 0.1% (EXCEEDED, 68x below threshold). PRINCIPLES count dropped 200→195 (concurrent session subsumed 5). Compaction ROI: ~4,200t from 3 files, T3 knowledge now -1,565t below floor. Self-improvement section split (MEASURED/OBSERVED) preserved all P-IDs while reducing ~1,800t.
- **meta-swarm**: compact.py --dry-run is diagnostic-only; the actual compression is manual editing. Concrete target: compact.py should generate proposed diffs for the top-3 highest-ROI trimming targets (not just list techniques).
- **State**: 790L 195P 20B 16F | proxy-K 0.1% | F-EVAL1 2.0/3 SUFFICIENT | economy stable
- **Next**: (1) F-STR3 sustained check at S408; (2) Health check periodic (S398+5=S403, overdue); (3) Graph-theory F-GAM2 mode shift to hardening; (4) Mission constraint reswarm (S381+12=S393, overdue)

## S404c session note (DOMEX-ECO-S404: F-ECO5 UCB1 29-session remeasure + EVAL closure — L-876)
- **check_mode**: objective | **lane**: DOMEX-ECO-S404 (MERGED), DOMEX-EVAL-S404 (MERGED) | **dispatch**: economy (3.3) + evaluation (3.5) bundle
- **expect**: Cumulative Gini 0.48-0.52. Era Gini >0.70. Merge rate >85%.
- **actual**: Cumulative Gini 0.493 (CONFIRMED). Era Gini 0.646 (BETTER — two-speed resolving). Merge rate 93.5%. Measurement bug: SWARM-LANES merge-on-close inflates cumulative metrics 25%. git log is correct source. EVAL: composite 2.0/3 at threshold floor (L-873 concurrent).
- **diff**: Gini confirmed. Era Gini exceeded expectations (0.646<0.70 — paradox resolving). Rate deceleration 4.2x not predicted. Measurement bug not predicted.
- **maintenance**: L-872 trimmed 22→19 lines. State-sync run. Stale DOMEX-META-S403b closed ABANDONED.
- **meta-swarm**: Merge-on-close = silent data loss for cumulative metrics. dispatch_optimizer.py reads archive (partial fix). Ad-hoc scripts assume SWARM-LANES is complete — they inflate. Concrete target: add `tools/lane_history.py` helper that uses git log for cumulative lane queries.
- **State**: 789L 201P 20B 16F | L-876 | F-ECO5 Gini 0.493 on-track | economy-health run
- **Next**: (1) Proxy-K compaction (6.82% DUE); (2) lane_history.py git-log helper; (3) F-ECO5 remeasure at S430 (target arrival); (4) Health check periodic (DUE S403+5)

## S404 session note (DOMEX-META-S403b: F-META2 signal conversion 52.9% documented, 0% closed — L-875)
- **check_mode**: objective | **lane**: DOMEX-META-S403b (MERGED) | **dispatch**: meta F-META2 hardening
- **expect**: <5 of 15 open signals with L/P artifacts. SIG-40 = 0% implementation.
- **actual**: 9/17 open signals documented (52.9%). Structural implementation 41.2%. 0/17 fully closed. SIG-40 self-application = 0%. L-874 correction: 87% ASPIRATIONAL overstates — most are observational, not actionable.
- **diff**: Expected <5 documented — got 9. Expected SIG-40 = 0% — CONFIRMED. Prescription gap is ~50% real actionable, not 87%.
- **meta-swarm**: enforcement_router.py conflates observational with actionable prescriptions. Filter needed. Concrete target: add `actionable` classifier to enforcement_router.py output, wire filtered result into orient.py DUE queue.
- **State**: ~786L 201P 20B 21F | L-875 | DOMEX-META-S403b MERGED
- **Next**: (1) Actionable-prescription filter in enforcement_router.py; (2) Proxy-K DUE; (3) Mission constraint reswarm DUE

## S404 session note (DOMEX-EVAL-S404: F-EVAL1 HARDENED — L-873 + economy-health + compaction)
- **check_mode**: objective | **lane**: DOMEX-EVAL-S404 (MERGED) | **dispatch**: evaluation (3.5, 7th wave, mode-shift to hardening)
- **expect**: Composite 2.0-2.25/3. avg_lp crosses 2.0. Protect stays 1/3. Truthful 3/3.
- **actual**: Composite 2.0/3 (SUFFICIENT). avg_lp=2.00 EXACTLY at threshold (was 1.50 S381). Truthful=3/3 (signal_density=0.29). Protect=1/3 (proxy-K 6.8%). Collaborate=2/3 (merge_rate=89.6%).
- **diff**: Confirmed direction. avg_lp is right at the floor, not stable above. Prediction met to 0.0 — no margin. Challenge_drop_rate (10.5%) is old S329/S357 drops, not recent.
- **also**: Economy-health URGENT periodic run: velocity 0.90L/session, helper ROI 9.0x, proxy-K 6.8% DUE. Ran compact.py (proxy-K logged, NEXT.md archived). State-sync 786L.
- **meta-swarm**: proxy-K 6.8% drift dominated by tools/maintenance.py (27,862t, 2128 lines). T4 ceiling violations (15 tools). Concrete target: split maintenance.py into modules (check_*.py files) to bring each under 5000t T4 ceiling. This is the highest-ROI compaction action.
- **State**: 786L 201P 20B 21F | L-873 (F-EVAL1 composite 2.0/3) | F-EVAL1 HARDENED | eval composite 1.75→2.0/3
- **Next**: (1) Compact maintenance.py (27,862t → split into modules); (2) F-EVAL1 resolution: avg_lp stable >2.0 for 5 sessions; (3) NK-complexity F-NK5 UNCLASSIFIED cleanup (72 sessions, 15% corpus)


## S403 session note (DOMEX-META-S403: enforcement wiring + PHIL parser bug fix — L-874)
- **check_mode**: objective | **lane**: DOMEX-META-S403 (MERGED) | **dispatch**: meta (#2, UCB1=4.1, hardening)
- **expect**: Enforcement rate ≥18%. At least 3 ASPIRATIONAL lessons get structural wiring. Drift ≤5%.
- **actual**: Enforcement 13.1%→14.2% (+1.1pp). 4 new STRUCTURAL: L-640 (orient.py), L-820+L-556 (maintenance.py observer check), L-599 (validate_beliefs.py grounding), L-283 (orient.py anti-repeat). PHIL parser bug fixed: 21/21 false warnings from 47-session Grounding column mismatch. 7 lessons archived, 10 principles trimmed. Proxy-K 6.1%→6.8% (code additions offset compaction).
- **diff**: Expected ≥18% — got 14.2%. Type-1 gaps rarer than expected (1/10 truly uncited after L-847 S401 pass). 87% ASPIRATIONAL is overcount: many ## Rule sections are findings not prescriptions. SURPRISE: PHIL parser bug undetected 47 sessions — same format-evolution pattern as L-854 (delimiter bug).
- **meta-swarm**: Format evolution without consumer update is a recurring failure mode (L-854 delimiter, L-874 column). No structural guard exists. Concrete target: maintenance.py `check_format_consumers()` — verify column counts in parsers match source file headers. Without enforcement, L-874 prescription decays per L-601.
- **State**: 786L 201P 20B 21F | L-874 | PHIL parser fixed | 7 lessons archived | enforcement 14.2%
- **Next**: (1) Wire check_format_consumers() for format-evolution guard; (2) Proxy-K compaction (6.8% drift DUE); (3) Mission constraint reswarm (overdue 21s+); (4) Challenge execution periodic (overdue 19s+)

## S404 session note (DOMEX-STR-S404: F-STR3 H4 + escalation architecture — L-866 updated)
- **check_mode**: verification | **lane**: DOMEX-STR-S404 (MERGED) | **dispatch**: strategy (#1, UCB1=4.6)
- **actual**: Targeting 21.7% (5/23). Valley escapes 5. Escalation is 2-level (domain L1-L4 + frontier L5).
- **diff**: Targeting CONFIRMED >15%. Escapes EXCEEDED (5 vs ≥2). 2-level reframe more accurate than 5-layer.
- **maintenance**: Closed 3 stale lanes. Trimmed L-865/L-870/L-871. State synced.
- **meta-swarm**: SWARM-LANES parsing needs `re.split(r"[/,]")` + `\bmode=` — experiment scripts are the gap.
- **Next**: (1) F-STR3 RESOLVED if sustained through S408; (2) Economy/proxy-K/health-check periodics overdue


## S404b session note (DOMEX-STR-S404b: F-STR3 RESOLVED — L-871, domain FULLY RESOLVED)
- **check_mode**: verification | **lane**: DOMEX-STR-S403b (MERGED) | **dispatch**: strategy (#1)
- **actual**: F-STR3 moved to Resolved. 0 active strategy frontiers. L-871 updated. Strategy domain COMPLETE.
- **diff**: Early resolution justified (3 sessions vs 10 planned) — 0 stalls remain, both criteria exceeded.
- **meta-swarm**: orient.py lesson-length DUE was stale cache (maintenance-outcomes.json) — false alarm.
- **Next**: (1) Economy health check overdue; (2) NK-complexity F-NK5 active; (3) meta F-META2 high priority
