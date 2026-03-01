Updated: 2026-03-01 S387

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

