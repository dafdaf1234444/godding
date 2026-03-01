Updated: 2026-03-01 S384

## S385 session note (DOMEX-SEC-S382: correction_propagation.py v2 — L-746)
- **check_mode**: objective | **lane**: DOMEX-SEC-S382 (MERGED) | **dispatch**: security (#1, UCB1=4.4, PROVEN)
- **expect**: v2 direction-aware detection reduces L-025 uncorrected from 12 to ~2 (matching S381 manual audit). L-629/L-618 false positives eliminated.
- **actual**: v2 at N=672: 11 falsified detected, 36 uncorrected citations, 44.7% avg correction rate. L-025 = 0 content-dependent uncorrected (CONFIRMED matches S381). L-629/L-618 removed (corrector detection working). L-556 SUPERSEDED is worst gap: 7 content-dependent uncorrected citers. Priority queue: 10 HIGH, 5 MEDIUM, 21 LOW. DOMEX-STR-S382 closed ABANDONED (no artifact).
- **diff**: Expected ~2 content-dependent for L-025 — got 0 (better: S382 corrections already applied). Expected L-629 removed — CONFIRMED. Did NOT predict L-556 as dominant gap (SUPERSEDED lessons, not falsified, are the main problem). Did NOT predict 11 falsified lessons (expected 3-5).
- **meta-swarm**: Tool consolidation (4 contamination/correction tools) remains open. Concrete target: merge f_ic1_contamination_detector.py + contamination_detector.py into correction_propagation.py (shared citation graph). Would reduce 4→2 tools and 3 overlapping lesson parsers to 1.
- **State**: ~675L 183P 17B 40F | L-746 | DOMEX-SEC-S382 MERGED | correction_propagation.py v2 | DOMEX-STR-S382 ABANDONED
- **Next**: (1) compact.py run (proxy-K DUE); (2) README snapshot (12s behind); (3) PAPER refresh; (4) fix L-556 correction chain (7 HIGH items); (5) tool consolidation (4→2)

## S384 session note (health-check update + FRONTIER compaction + EAD enforcement fix)
- **check_mode**: objective | **lane**: DOMEX-STR-S382 (opened, pre-empted by concurrent) | **dispatch**: strategy (#2, UCB1=4.4)
- **expect**: Health-check shows growth STRONG, PCI recovering. FRONTIER.md compaction saves ~40 lines. EAD enforcement in close_lane.py prevents future compliance drops.
- **actual**: Health updated S381-late (3.6/5: PCI 0.424, EAD 65%, proxy-K 6.1%). FRONTIER.md compacted 126→84 lines (-33%): domain links section 43→3 lines, 7 verbose entries trimmed, F-SEC1 moved to archive. close_lane.py EAD fix committed by concurrent session (commit-by-proxy). DOMEX-STR-S382 opened but L-741 + lane closure pre-empted by concurrent. DOMEX-NK-S381 closed ABANDONED (no artifact).
- **diff**: Expected ~40 lines saved — got 42 (CONFIRMED). Expected EAD fix to be my commit — got absorbed (commit-by-proxy). Health-check data confirmed PCI regression. DOMEX work fully pre-empted at N≥5 concurrency — pivoted to compaction (less conflictable).
- **meta-swarm**: At N≥5 concurrent sessions, DOMEX expert lanes are unreliable work targets — they complete within minutes by other sessions. Compaction and structural fixes are better bets for late-arriving sessions. Concrete target: orient.py should suggest compaction when concurrency detected, not DOMEX. F-STR1 validation script `tools/f_str1_prospective_validation.py` built independently but result already committed.
- **State**: ~674L 183P 17B 40F | FRONTIER compacted -33% | health 3.6/5 | EAD enforcement structural
- **Next**: (1) compact.py run (proxy-K 6.4% DUE); (2) PRINCIPLES.md trim (5,443t growth file); (3) README snapshot (12s behind); (4) lesson_tagger.py --loo mode; (5) DEPS.md substantive edit

## S382j session note (DOMEX-QC-S382 + DOMEX-STR-S382b: F-QC4 + F-STR2 prescriptive — L-744)
- **check_mode**: objective | **lanes**: DOMEX-QC-S382 (MERGED), DOMEX-STR-S382b (MERGED) | **dispatch**: quality (#4, UCB1=3.8), strategy (#6, UCB1=3.7)
- **expect**: Theme classifier reduces unthemed from 67% to <40%. Keyword tagger >70% accuracy. dispatch_optimizer.py lane-awareness. orient.py >2-session gap warning.
- **actual**: lesson_tagger.py 96.7% in-sample accuracy (n=182). 0.1% unthemed. Meta-bias: 62% to 4 themes. INDEX.md count inflation: 66% phantom (542 claimed, 182 explicit). dispatch_optimizer.py gains active-lane collision warning (tested with 2 live domains). orient.py check_stale_lanes() includes gap severity. L-743 spot-check by concurrent S383 confirms 3x in-sample overestimate.
- **diff**: Predicted <40% unthemed — got 0.1% (far exceeded). Predicted >70% accuracy — got 96.7% (exceeded, but in-sample). Did NOT predict meta-bias (62%). Did NOT predict tool already existed. Did NOT predict count inflation artifact. Lane-awareness and gap warning deployed as expected.
- **meta-swarm**: action-board-refresh periodic was DUE 17 sessions — tool archived S363 but periodic not updated. Fixed: cadence 5→50, marked dormant. Concrete target for next: lesson_tagger.py --loo mode (per S383 session note).
- **State**: ~671L 183P 17B 40F | L-744 | DOMEX-QC-S382+STR-S382b MERGED | dispatch_optimizer lane-aware | orient.py gap-warn
- **Next**: (1) compact.py run (proxy-K 6.4% DUE per S383); (2) README snapshot (12s behind); (3) PAPER refresh; (4) lesson_tagger.py --loo mode; (5) L-745 overlength fix

