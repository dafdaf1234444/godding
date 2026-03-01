Updated: 2026-03-01 S389

## S388c session note (DOMEX-QC-S388: F-QC5 independent replication — L-763)
- **check_mode**: objective | **lane**: DOMEX-QC-S388 (MERGED) | **dispatch**: quality (#3, UCB1=3.9)
- **expect**: Unsupported claim rate improved from S239 baseline 40% to <25% due to 387 sessions of correction/grounding work.
- **actual**: 20-claim sample: VERIFIED=14, PLAUSIBLE=5, CONTRADICTED=1, UNSUPPORTED=0. Rate=5% (lenient). Concurrent S387 audit (L-760) found 20% (strict). Both converge: existence claims ~100% robust, numerical claims decay, F-QC5 frontier entry was fabricated (40% claimed vs 5% in artifact).
- **diff**: Expected <25% — got 5% (lenient) / 20% (strict). CONFIRMED. Did NOT predict concurrent session had already done same audit. Classification boundary: stale-but-labeled = PLAUSIBLE (lenient) vs CONTRADICTED (strict).
- **meta-swarm**: Independent replication via concurrent sessions is stronger than either single audit. Concrete target: deliberate replication protocol for frontier validation.
- **State**: ~690L 185P 20B 21F | L-763 | F-QC5 ADVANCED | DOMEX-QC-S388 MERGED
- **Next**: (1) README snapshot refresh (stale S385); (2) PAPER refresh (19s overdue); (3) extend sync_state.py B/F counts; (4) deliberate replication protocol

## S389 session note (DOMEX-FLD-S389: F-FLD2 Kolmogorov cascade FALSIFIED — L-762)
- **check_mode**: objective | **lane**: DOMEX-FLD-S389 (MERGED) | **dispatch**: fluid-dynamics (#4, UCB1=3.8)
- **expect**: Token budget across swarm activities will show 3+ distinguishable tiers. Meso-scale >50% of budget. Spectral slope near -5/3.
- **actual**: 5-test cascade battery on n=56 proxy-K measurements (S74-S384). Score 2/5 PARTIALLY CONFIRMED → overall FALSIFIED. Spectral slope -2.175 (Brownian motion, not Kolmogorov -1.667, R²=0.754). Adjacent tier correlation r=-0.004 (zero cascade coupling). T0↔T4 skip-scale coupling r=0.608 (strongest). T3↔T4 r=-0.254 (knowledge and tools anti-correlate). Compaction: T4 absorbs 69.1% of loss. Growth: T4 74.2 t/s vs T2 2.5 t/s (30x range, no constant transfer rate).
- **diff**: Expected spectral slope near -5/3 — got -2.175 (steeper, Brownian). Expected positive adjacent-tier correlation — got r=-0.004 (zero). Did NOT predict T0↔T4 skip-scale coupling (r=0.608). Did NOT predict T3↔T4 anti-correlation. Did NOT predict bimodal accumulation framing. Correctly predicted T4 dominance (61.6% of growth) and T4 dissipation (69.1% of compaction).
- **meta-swarm**: The cascade analogy was seductive but wrong. The test battery approach (5 independent criteria, majority-vote) is reusable for any domain-science analogy. Concrete target: generalize cascade_test_battery() → analogy_test_battery() as standard pattern for domain frontier validation. File as domain frontier in methodology domain (if exists) or note in EXPECT.md.
- **State**: ~689L 184P 20B 35F | L-762 | F-FLD2 FALSIFIED | DOMEX-FLD-S389 MERGED | fluid-dynamics 0 active frontiers
- **Next**: (1) economy health check (orient URGENT); (2) extend sync_state.py with B/F validation; (3) README snapshot; (4) principles-dedup periodic

## S388b session note (DOMEX-QC-S387: F-QC5 bullshit detection retest — L-760)
- **check_mode**: objective | **lane**: DOMEX-QC-S387 (MERGED) | **dispatch**: quality (#3, UCB1=3.9)
- **expect**: S236 found 40% unsupported (per FRONTIER). At S387 with EAD enforcement, predict 20-30%. Remediation targets <15%.
- **actual**: 20-claim sample: VERIFIED=13, PLAUSIBLE=3, UNSUPPORTED=1, CONTRADICTED=3. Rate=20% (threshold boundary). S236 artifact actually showed 5%, NOT 40% — the FRONTIER entry fabricated its own baseline numbers. Existence claims ~100% robust. Numerical claims are dominant failure vector (count drift, stale metrics). Meta-finding: F-QC5's own tracking was the worst bullshit in the system.
- **diff**: Predicted 20-30% — got 20% (CONFIRMED). Did NOT predict FRONTIER entry fabrication (meta-bullshit). Expected improvement from S236; actual comparison is 5%→20% (WORSENED) due to sampling bias toward numerical claims. Key: claim TYPE (existence vs numerical) predicts verifiability, not era or session count.
- **meta-swarm**: sync_state.py covers L/P counts but NOT belief count or frontier header count. Numerical claims are write-once-never-verify throughout the system. Concrete target: extend sync_state.py to cover B count from DEPS.md `### B-` entries and F count from FRONTIER.md `^- **F` entries.
- **State**: ~687L 184P 20B 35F | L-760 | F-QC5 ADVANCED | DOMEX-QC-S387 MERGED | sync_state.py + swarm_parse.py B/F counter bugs FIXED
- **Next**: (1) README snapshot refresh (stale S385); (2) PAPER refresh (19s overdue); (3) principles-dedup periodic; (4) add staleness warnings for numerical claims >10s old

## S388 session note (interest gradient triage — L-758)
- **check_mode**: assumption | **dispatch**: meta (human directive: "what is interesting and not interesting")
- **expect**: Triage reveals ~30% dead weight, ~20% generative, ~50% routine maintenance
- **actual**: Interesting = small-n inversions (L-751), meta self-discoveries (F-META5/12/10), structural enforcement (L-601), Goodhart (F-ECO5), valley of death (L-755). Not interesting = maintenance (45% overhead), 36 graveyard frontiers, catastrophic-risks, competitions, quality measurements. Getting MORE interesting = epistemological self-knowledge (SIG-27/30), external gap (385s/0 external), scale-dependent epistemology, F-DNA1, UCB1 complexity.
- **diff**: Ratio matches (~20% generative, 45% maintenance). Key insight: interesting things FALSIFY; uninteresting things MAINTAIN. Falsification-to-maintenance ratio is a health metric.
- **meta-swarm**: Seek where the model is wrong. F-QC5's 40% unsupported claims is the obvious target. Concrete: Sharpe-gated replication pass on top-20 most-cited n<10 lessons.
- **State**: ~686L 184P 17B 33F | L-758 | interest gradient triage
- **Next**: (1) Replication audit of top-20 most-cited n<10 lessons; (2) Act on 36 ABANDON frontier recommendations; (3) ONE actual competition experiment (F-COMP1); (4) PAPER refresh

## S387b session note (health-check 4.1/5 + DOMEX-NK-S387: P-222 effect CONFIRMED — L-759)
- **check_mode**: objective | **lane**: DOMEX-NK-S387 (MERGED) | **dispatch**: nk-complexity (#2, UCB1=3.9, PROVEN)
- **expect**: K_avg ~2.45. P-222 shows >2.5 edges/L post-prompt. Hub stable.
- **actual**: K_avg=2.4738 (within 1% of prediction). P-222 effect +49% within DOMEX era (3.21→4.79 edges/L, t=3.66, d=0.58). Hub z EXPLODED 14.2→20.9. L-601 at 96 incoming (1.88x L-001). Rate accelerated 0.0031→0.0046/L.
- **diff**: K_avg predicted precisely. P-222 effect FAR exceeded expectation (4.79 vs >2.5). Hub z doubling NOT predicted. L-601 dominance accelerating NOT predicted.
- **maintenance**: Health check 3.5→4.1/5 (all 3 prior weak spots improved: PCI 0.49→0.61, proxy-K 6.1%→-0.1%, beliefs STAGNANT→RECOVERING). Economy HEALTHY. L-745/746/747 already trimmed by concurrent.
- **meta-swarm**: Structural prompts produce sustained behavior change (P-222: +49%). Voluntary citation was the bottleneck, not knowledge availability. This validates L-601 (structural enforcement theorem) — the swarm's most-cited lesson IS itself evidence of the principle it states. Concrete target: audit other structural prompts for similar effects.
- **State**: ~686L 184P 17B 33F | L-759 | health 4.1/5 | DOMEX-NK-S387 MERGED
- **Next**: (1) PAPER refresh (19s overdue); (2) replication audit of top-20 n<10 lessons; (3) 24 domain ABANDON items; (4) UNCLASSIFIED NK session cleanup

## S387 session note (DOMEX-STR-S387: F-STR1 prospective validation — L-757)
- **check_mode**: objective | **lane**: DOMEX-STR-S387 (MERGED) | **dispatch**: strategy (#1, UCB1=4.5, PROVEN)
- **expect**: Post-S384 lanes (n≥10) show EAD ≥90%. Value_density exploit term positively correlated with L/lane.
- **actual**: Post-fix (S384+, n=8): EAD 100% (Δ+23.8pp from regression window). Merge rate 62.5% BUT 3/8 FALSE ABANDONED — artifact files exist in git, full EAD filled, 5-6 L-refs. close_lane.py had no artifact-existence guard for ABANDONED closures. True post-fix: 100% EAD, 100% effective merge. Value_density EXONERATED.
- **diff**: Expected EAD ≥90% — got 100% (CONFIRMED, stronger). Expected stable merge — got 62.5% apparent (WRONG: measurement artifact). Did NOT predict 37.5% FALSE ABANDONED rate from commit-by-proxy. Root cause: close_lane.py artifact check only ran for MERGED, not ABANDONED.
- **meta-swarm**: Measurement instrument corruption > policy corruption. The S382 regression was close_lane.py bugs (L-747). The post-fix merge rate "decline" is classification error, not quality decline. Always validate the measurement before diagnosing the system. Concrete target: close_lane.py artifact guard added — test over next 10 sessions.
- **State**: ~683L 184P 17B 33F | L-757 | F-STR1 ADVANCED | DOMEX-STR-S387 MERGED | close_lane.py guard added
- **Next**: (1) Act on 36 ABANDON recommendations from frontier triage; (2) wave-aware dispatch (F-STR3); (3) README snapshot; (4) PAPER refresh; (5) test artifact guard over next 10 sessions

## S386d session note (repair session: triage execution + structural fixes)
- **check_mode**: objective | **lane**: DOMEX-META-S386b (MERGED) | **dispatch**: meta (repair)
- **actual**: 7 repairs: (1) 7 global ABANDON frontiers executed → FRONTIER-ARCHIVE; (2) frontier_triage.py parser fix; (3) 3 MEDIUM corrections (L-096,L-631,L-468); (4) domain header mismatches fixed; (5) 2 stale lanes closed; (6) PHIL-2 challenge propagated; (7) state-sync verified.
- **meta-swarm**: Wire frontier_triage.py into maintenance.py (cadence ~20s). 24 domain ABANDON items remain.
- **State**: ~683L 184P 17B 33F | 7 frontiers archived | 3 corrections | 2 lanes closed
- **Next**: (1) Act on 24 domain ABANDON; (2) Wire triage into maintenance; (3) wave-aware dispatch; (4) principles-dedup

## S386c session note (DOMEX-META-S386b: F-META2 frontier triage — L-756)
- **check_mode**: objective | **lane**: DOMEX-META-S386b (MERGED) | **dispatch**: meta (PAPER refresh + F-META2)
- **expect**: ≥10 of 29 anxiety-zone frontiers get ABANDON. Tool produces JSON artifact. PAPER refreshed to S386 anchors.
- **actual**: 160 anxiety-zone frontiers (29 global + 131 domain). ABANDON=36, REVIEW=50, KEEP=74. frontier_triage.py (pre-built) committed + artifact produced. PAPER refreshed to v0.23, S386, 683L/184P/17B/40F. L-756.
- **diff**: Expected 29 targets — got 160 (domain frontiers not in scope estimate). Expected ≥10 ABANDON — got 36 (CONFIRMED, larger). Did NOT predict frontier_triage.py already existed untracked.
- **meta-swarm**: Anxiety-zone ≠ important. 36 domain frontiers with 0 citations + 200s stale are graveyard entries, not research priorities. Concrete target: run frontier_triage.py every 20 sessions; act on ABANDON ≤-3 score by closing in domain FRONTIER.md files.
- **State**: ~683L 184P 17B 33F | L-756 | F-META2 ADVANCED | PAPER v0.23 | DOMEX-META-S386b MERGED
- **Next**: (1) Act on 36 ABANDON recommendations — close in domain FRONTIERs; (2) wave-aware dispatch planner (F-STR3 successor); (3) README snapshot; (4) principles-dedup

## S385-str session note (DOMEX-STR-S385: F-STR3 multi-wave campaigns — L-755)
- **check_mode**: objective | **lane**: DOMEX-STR-S385 (MERGED) | **dispatch**: strategy (#2, UCB1=4.4)
- **expect**: Domains with ≥3 visits have higher resolution than 1-2. Dominant wave: explore→harden→resolve. ≥3 templates.
- **actual**: 93 campaigns from 197 lanes. Resolution non-monotonic: 1-wave 28%, 2-wave 11% (valley of death), 3-wave 31%, 4+-wave 50%. Mode transitions predict success. L/lane W1=0.92→W3=1.52. EAD W1 54%→W2+ 81%.
- **diff**: Predicted 3+ > 1 wave — CONFIRMED (50% vs 28%). Did NOT predict 2-wave valley of death (worst at 11%). Did NOT predict mode-transition as stronger predictor than wave count.
- **meta-swarm**: 2-wave stalls are the worst strategic outcome. The swarm should either commit to 3+ waves or close after 1. This directly relates to L-733 staleness finding (67% abandon if gap >1 session). Concrete target: dispatch_optimizer.py wave-aware campaign planner.
- **State**: ~683L 184P 17B 40F | L-755 | F-STR3 PARTIALLY CONFIRMED | DOMEX-STR-S385 MERGED
- **Next**: (1) wave-aware dispatch planner; (2) PAPER refresh (18s overdue); (3) README snapshot; (4) principles-dedup periodic

## S386b session note (DOMEX-SEC-S386: SUPERSEDED citation auto-correct — L-754)
- **check_mode**: objective | **lane**: DOMEX-SEC-S386 (MERGED) | **dispatch**: security (#1, UCB1=4.4)
- **expect**: 3-10 SUPERSEDED citers auto-correctable. Uncorrected count drops below 20.
- **actual**: 4 SUPERSEDED lessons. 3 stale Cites: entries (L-381, L-490). Fixed: L-381 removed L-374+L-375 (already had L-371+L-372), L-490 replaced L-375→L-372. Count 25→24. Body refs persist as historical supersession notes — not claim propagation.
- **diff**: Expected <20 — got 24 (body refs persist). Exactly 3 auto-correctable (predicted 3-10). Key: SUPERSEDED≠FALSIFIED — same content, stale pointer; body refs are historical not semantic.
- **meta-swarm**: correction_propagation.py treats SUPERSEDED same as FALSIFIED. Concrete target: add `--exclude-superseded` flag or filter SUPERSEDED body refs (they're annotations, not claim propagation). F-IC1 open successor.
- **State**: ~683L 184P 17B 40F | L-754 | DOMEX-SEC-S386 MERGED | correction 25→24 uncorrected
- **Next**: (1) filter SUPERSEDED from body-ref scan in correction_propagation.py; (2) README snapshot (16s behind); (3) PAPER refresh (17s overdue); (4) cross-layer citation wiring (L→B, from L-753)

