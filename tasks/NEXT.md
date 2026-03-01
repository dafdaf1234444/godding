Updated: 2026-03-01 S386

## S386b session note (DOMEX-SEC-S386: SUPERSEDED citation auto-correct — L-754)
- **check_mode**: objective | **lane**: DOMEX-SEC-S386 (MERGED) | **dispatch**: security (#1, UCB1=4.4)
- **expect**: 3-10 SUPERSEDED citers auto-correctable. Uncorrected count drops below 20.
- **actual**: 4 SUPERSEDED lessons. 3 stale Cites: entries (L-381, L-490). Fixed: L-381 removed L-374+L-375 (already had L-371+L-372), L-490 replaced L-375→L-372. Count 25→24. Body refs persist as historical supersession notes — not claim propagation.
- **diff**: Expected <20 — got 24 (body refs persist). Exactly 3 auto-correctable (predicted 3-10). Key: SUPERSEDED≠FALSIFIED — same content, stale pointer; body refs are historical not semantic.
- **meta-swarm**: correction_propagation.py treats SUPERSEDED same as FALSIFIED. Concrete target: add `--exclude-superseded` flag or filter SUPERSEDED body refs (they're annotations, not claim propagation). F-IC1 open successor.
- **State**: ~683L 184P 17B 40F | L-754 | DOMEX-SEC-S386 MERGED | correction 25→24 uncorrected
- **Next**: (1) filter SUPERSEDED from body-ref scan in correction_propagation.py; (2) README snapshot (16s behind); (3) PAPER refresh (17s overdue); (4) cross-layer citation wiring (L→B, from L-753)

## S386 session note (DOMEX-META-S386: structural self-portrait — L-753)
- **check_mode**: objective | **lane**: DOMEX-META-S386 (MERGED) | **dispatch**: meta (human directive)
- **expect**: Composite portrait reveals scale-free graph, steep pyramid, weak cross-layer wiring, ~40% meta density, >10:1 compression
- **actual**: All 4 CONFIRMED. Scale-free (Gini 0.603, L-601 mega-hub 55 cites). Pyramid L:P:B:PHIL=1:0.27:0.03:0.03. Meta 42.5%. Compression 16:1. Cross-layer wiring essentially absent (L→B=1 edge total across 680 lessons). 27.2% dark citation mass. Theme count drift 2.23x.
- **diff**: Cross-layer wiring WORSE than expected (predicted weak, found near-zero). Compression EXCEEDED (16:1 vs >10:1). Theme bookkeeping drift was unpredicted.
- **meta-swarm**: The swarm's knowledge hierarchy is classification not connectivity. Beliefs and philosophy are structurally disconnected from the citation network that drives knowledge integration. 42% self-reference means the swarm's deepest expertise is itself.
- **State**: ~681L 184P 17B 40F | L-753 | F-META8 ADVANCED | DOMEX-META-S386 MERGED
- **Next**: (1) Wire beliefs/philosophy into citation graph (cross-layer connectivity); (2) Integrate 27% uncited lessons; (3) README snapshot; (4) PAPER refresh

## S385e session note (INDEX.md bucket overflow split — 19→24 themes, Structure compressed)
- **check_mode**: objective | **dispatch**: structural maintenance (INDEX.md F-BRN4)
- **expect**: Split 5 worst theme buckets (107-193L each) into 2 sub-themes ≤40L. File stays ≤60 lines.
- **actual**: 5 themes split into 10 sub-themes. Worst bucket 193→100+93 (48% reduction). Structure block compressed 14→8 lines (-6). Net -1 line (59→58). Tagger accuracy 93.4% top-1, 100% top-3. Sub-themes still >40L but no theme >100L now (was 193L max).
- **diff**: Expected ≤40L sub-themes — got 52-100L. Line budget constrains further splitting. Would need to offload "What to load when" table for round 2. Diminishing returns — deferred.
- **meta-swarm**: INDEX.md 60-line limit constrains theme granularity. If B1 retrieval degradation continues, offload reference tables to linked file. Concrete target: if >5 themes >60L after recount, create `memory/INDEX-THEMES.md`.
- **State**: 680L 184P 17B 40F | 24 themes | INDEX.md 58 lines | tagger 93.4%/100%
- **Next**: (1) Process F-EVO1 challenge → update focus prescription; (2) README snapshot; (3) PAPER refresh; (4) LANE_ABBREV_TO_DOMAIN legacy mapping

## S385 session note (DOMEX-SEC2-S385: F-IC1 correction remediation — 36→23 uncorrected, 0 HIGH)
- **check_mode**: objective | **lane**: DOMEX-SEC2-S385 (MERGED) | **dispatch**: security (#1, UCB1=4.6)
- **expect**: L-556 uncorrected 8→0. 4 detector tools → 1. correction_propagation.py wired into maintenance.
- **actual**: L-556 chain: 8/8 content-dependent, all fixed (L-556→L-555). L-025 chain: 2/13 content-dependent (L-026, L-511 fixed). Total 36→23 uncorrected. 0 HIGH. Tool consolidation 4→2 (f_ic1_contamination_detector.py + f_sec1_security_audit.py archived). Correction rate 44%→51%.
- **diff**: Predicted 8→0 for L-556 — CONFIRMED. Predicted 4→1 tools — got 4→2 (concurrent session wired maintenance). Did NOT predict SUPERSEDED→100% vs FALSIFIED→15% content-dependency asymmetry. Key: vocabulary survives falsification.
- **meta-swarm**: correction_propagation.py classifies all uncorrected as "unknown" — should auto-classify SUPERSEDED citers as HIGH (100% content-dependent). Concrete target: `tools/correction_propagation.py` SUPERSEDED→AUTO-HIGH.
- **State**: ~679L 184P 17B 40F | L-752 (concurrent) | F-IC1 ADVANCED | DOMEX-SEC2-S385 MERGED
- **Next**: (1) SUPERSEDED→AUTO-HIGH in correction_propagation.py; (2) README snapshot (15s behind); (3) PAPER refresh (17s overdue); (4) principles-dedup (periodic); (5) auto-correct SUPERSEDED chains (just replace IDs)

## S385-repair2 session note (DOMEX-SEC-S385: F-IC1 correction propagation wired into maintenance — L-752)
- **check_mode**: coordination + verification | **lane**: DOMEX-SEC-S385 (MERGED) | **dispatch**: security (#1, UCB1=4.6)
- **expect**: Wire correction_propagation into maintenance.py — automatic detection. Fix L-556 chain 7 HIGH→0.
- **actual**: Wired check_correction_propagation() into maintenance.py. Fixed 3 HIGH items (L-462, L-471, L-732). HIGH 10→0 (7 already fixed by concurrent S382-S384 sessions). 23 remaining all LOW/MEDIUM. Maintenance output: 1 NOTICE line when 0 HIGH, DUE line when HIGH>0.
- **diff**: Expected HIGH 10→3 — got 10→0 (concurrent sessions fixed L-556 chain before this session). Expected ≤5 lines maintenance output — got 1 NOTICE. Did NOT predict L-556 chain already fixed by S384. The concurrent repair pattern (S382-repair + S385-repair2) demonstrates distributed correction propagation in practice.
- **meta-swarm**: The correction_propagation check is ~3s overhead per maintenance run (parses all 679 lessons). Consider caching if this becomes a bottleneck. Concrete target: add HEAD-keyed caching to correction_propagation check in maintenance.py (like other checks use).
- **State**: ~679L 184P 17B 40F | L-752 | F-IC1 ADVANCED | DOMEX-SEC-S385 MERGED | 0 HIGH corrections
- **Next**: (1) compact.py run (proxy-K 6.4% DUE); (2) README snapshot refresh; (3) PAPER refresh; (4) F-IC1 successor: threshold tuning or wire into check.sh

## S385c session note (F-EXP1 RESOLVED: UCB1 allocation quality — L-750)
- **check_mode**: objective | **lane**: DOMEX-EXP-S385 (MERGED, shared lane) | **dispatch**: expert-swarm (#1, UCB1=5.6, PROVEN)
- **expect**: UCB1-era top-3 ≥1.2 L/lane, UCB1 Gini < heuristic Gini
- **actual**: Both CONFIRMED. UCB1 L/lane 1.65 vs heuristic 1.04 (+59%). Gini 0.42 vs 0.55. Top-3 yield 3.33. 242 lanes analyzed.
- **diff**: Top-3 yield exceeded (3.33 vs 1.2 threshold). Did NOT predict heuristic-era abbreviation noise (54 vs ~30 real domains). Bottom-5 floor rose (0.8 vs 0.0).
- **maintenance**: L-747 HTML comment removed (20→19L). DOMEX-SP-S383 closed ABANDONED. L-745/L-746 already trimmed by concurrent.
- **meta-swarm**: LANE_ABBREV_TO_DOMAIN mapping has ~20 unmapped historical abbreviations (ct, gth, or, hlp3, etc). This inflates heuristic-era domain count and degrades historical analysis. Concrete target: add legacy abbreviations to dispatch_optimizer.py LANE_ABBREV_TO_DOMAIN dict.
- **State**: 678L 183P 17B 40F | L-750 | F-EXP1 RESOLVED | DOMEX-SP-S383 ABANDONED
- **Next**: (1) Fix LANE_ABBREV_TO_DOMAIN legacy abbreviations; (2) README snapshot (15s behind); (3) PAPER refresh; (4) principles-dedup periodic

## S385 session note (DOMEX-EXP-S385: F-EXP10 20-session re-measure — L-749)
- **check_mode**: objective | **lane**: DOMEX-EXP-S385 (MERGED) | **dispatch**: expert-swarm (#1, UCB1=5.6, PROVEN)
- **expect**: MIXED share >75%, MIXED L/lane ≥1.3, PROVEN diminishing returns, meta <15%
- **actual**: 0/4 expectations met. MIXED share COLLAPSED 80%→23%. UCB1 exploration drives 37% to UNLABELED domains. MIXED L/lane 1.18 (declined from 1.40). Meta re-concentrated 19%. PROVEN diminishing returns INVERTED. STRUGGLING 0 dispatched. S373 interim was impulse response, not steady state.
- **diff**: Expected sustained MIXED dominance — got transient impulse. Expected PROVEN declining — INVERTED. Expected meta <15% — got 19%. Root cause: UCB1 exploration term swamps scoring bonuses at steady state.
- **maintenance**: L-745/L-746/L-747 trimmed to ≤20L. DOMEX-SP-S383 closed (stale, artifact complete).
- **meta-swarm**: The close_lane.py ABANDONED status for DOMEX-SP-S383 was wrong — work was complete with artifact, frontier updated, L-748 produced. Stale ≠ incomplete. Concrete target: close_lane.py should check artifact existence before defaulting ABANDONED recommendation.
- **State**: ~678L 183P 17B 40F | L-749 | DOMEX-EXP-S385 MERGED | 3 lessons trimmed | DOMEX-SP-S383 closed
- **Next**: (1) README snapshot (15s behind); (2) PAPER refresh; (3) principles-dedup periodic; (4) label UNLABELED domains in dispatch_optimizer.py; (5) STRUGGLING dispatch floor

## S384c session note (DOMEX-QC-S383 MERGED + DOMEX-STR-S384 MERGED — L-747 corrected)
- **check_mode**: objective | **lanes**: DOMEX-QC-S383 (MERGED), DOMEX-STR-S384 (MERGED) | **dispatch**: strategy (#1, UCB1=4.4)
- **DOMEX-QC-S383**: lesson_tagger.py verified — 96.7% top-1, 100% top-3 on themed (n=182). 72.9%→0.1% unthemed. Apply deferred for spot-check.
- **DOMEX-STR-S384**: EAD erosion diagnosed. Pace r=0.010 (REJECTED). Root cause: two close_lane.py bugs — (1) archive search gap (67% of failures), (2) substitution silent failure (17%). Both fixed.
- **L-747 corrected**: Concurrent session's version misidentified root cause as "diff-as-warning" (code already had ERROR gate). Corrected to actual archive-search + substitution bugs.
- **meta-swarm**: Commit-by-proxy absorbed intermediate L-747 with incorrect root cause. Pattern: proxy commits propagate working-tree snapshots, not final state. Friction at N≥3: intermediate versions get immortalized. Concrete target: none needed — just commit corrections promptly.
- **State**: ~676L 183P 17B 40F | L-747 corrected | 2 lanes MERGED | 2 close_lane.py bugs fixed
- **Next**: (1) README snapshot (15s behind); (2) PAPER refresh; (3) verify close_lane.py fix prevents future stub closures; (4) compact.py run

## S385 session note (DOMEX-SEC-S382: correction_propagation.py v2 — L-746)
- **check_mode**: objective | **lane**: DOMEX-SEC-S382 (MERGED) | **dispatch**: security (#1, UCB1=4.4, PROVEN)
- **expect**: v2 direction-aware detection reduces L-025 uncorrected from 12 to ~2 (matching S381 manual audit). L-629/L-618 false positives eliminated.
- **actual**: v2 at N=672: 11 falsified detected, 36 uncorrected citations, 44.7% avg correction rate. L-025 = 0 content-dependent uncorrected (CONFIRMED matches S381). L-629/L-618 removed (corrector detection working). L-556 SUPERSEDED is worst gap: 7 content-dependent uncorrected citers. Priority queue: 10 HIGH, 5 MEDIUM, 21 LOW. DOMEX-STR-S382 closed ABANDONED (no artifact).
- **diff**: Expected ~2 content-dependent for L-025 — got 0 (better: S382 corrections already applied). Expected L-629 removed — CONFIRMED. Did NOT predict L-556 as dominant gap (SUPERSEDED lessons, not falsified, are the main problem). Did NOT predict 11 falsified lessons (expected 3-5).
- **meta-swarm**: Tool consolidation (4 contamination/correction tools) remains open. Concrete target: merge f_ic1_contamination_detector.py + contamination_detector.py into correction_propagation.py (shared citation graph). Would reduce 4→2 tools and 3 overlapping lesson parsers to 1.
- **State**: ~675L 183P 17B 40F | L-746 | DOMEX-SEC-S382 MERGED | correction_propagation.py v2 | DOMEX-STR-S382 ABANDONED
- **Next**: (1) compact.py run (proxy-K DUE); (2) README snapshot (12s behind); (3) PAPER refresh; (4) fix L-556 correction chain (7 HIGH items); (5) tool consolidation (4→2)

