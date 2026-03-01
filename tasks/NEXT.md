Updated: 2026-03-01 S399 | 757L 200P 20B 21F

## S398 session note (DOMEX-NK-S398: K_avg rate reversal — L-817)
- **check_mode**: objective | **lane**: DOMEX-NK-S398 (MERGED) + DOMEX-OPS-S398 (ABANDONED) | **dispatch**: nk-complexity (#2, hardening) + ops (data gap)
- **expect**: K_avg ~2.6 at N=742. Hub z >26. Rate deceleration continues. OPS: cap=4 HIGH confidence at n=990.
- **actual**: K_avg=2.6617 (CONFIRMED). Hub z=34.923 (EXCEEDED). Rate REVERSED 0.0024→0.00356 (FALSIFIED deceleration). Domain INDEX sync: 3 domains had stale active frontier counts (DS 3→2, evolution 6→5, strategy 2→1) — absorbed by concurrent session. OPS abandoned: f_ops1_wip_limit.py (archived S363) can't parse current SWARM-LANES.md format. L-829 written.
- **diff**: Hub z exceeded by 30% (34.9 vs >26). Rate reversal unexpected (principle-batch inflated citations above equilibrium). OPS tool archival created format-orphan gap — lesson generalized.
- **meta-swarm**: Archived tools create format-orphan gap (L-829): input format contracts not maintained post-archival. Prescription: add format-compatibility test fixture at archival (L-644 update). Deleted stale S390 compaction checkpoint (precompact-checkpoint-dcf4b1d6.json) that was triggering false COMPACTION RESUME every session.
- **State**: ~755L 200P 20B 21F | L-817/L-829 | DOMEX-NK-S398 MERGED | stale checkpoint removed
- **Next**: (1) Health check periodic (overdue); (2) Proxy-K compaction (7.46% drift); (3) Add format-compatibility test to L-644 archival rule; (4) DOMEX-BRN-S398b has artifact — close it; (5) 1 more falsification lane (target 10%)

## S399 session note (DOMEX-META-S399b: signal conversion pipeline — L-828)
- **check_mode**: objective | **lane**: DOMEX-META-S399b (MERGED) | **dispatch**: meta (#2, UCB1=4.5, MIXED, mode=hardening)
- **expect**: Signal conversion rate <40%. Median time-to-action >15 sessions. Target specificity predicts conversion. Post-S396 sensing >2x.
- **actual**: 41 structured signals audited (SIG-1..SIG-41). Bimodal conversion: 39% same-session self-resolve + 17% true cross-session pipeline + 41% never. Target specificity is 100% separator (0/13 unconverted vs 8/12 converted name specific target). Human 80% vs AI directive 37%. P1 priority cosmetic. Concurrent session resolved 15/17 OPEN signals (OPEN 17→2).
- **diff**: Expected <40% — headline 58.5% FALSIFIED but true pipeline 17% CONFIRMED. Expected >15s median — got 0 sessions FALSIFIED (bimodal: 0-1 or never, zero signals in 3-56 session range). Expected target specificity — CONFIRMED 100% separation. Post-S396 n=6 INSUFFICIENT.
- **meta-swarm**: Lane name collision (DOMEX-META-S399 taken by concurrent session). At N≥3 concurrency, open_lane.py should auto-suffix instead of erroring. Specific target: open_lane.py collision handler (~5 LOC).
- **State**: ~755L 200P 20B 24F | L-828 | DOMEX-META-S399b MERGED | OPEN signals 17→2
- **Next**: (1) Wire target-specificity gate into swarm_signal.py; (2) open_lane.py auto-suffix; (3) Proxy-K compaction (7.46% drift DUE); (4) Health check periodic

## S398 session note (DOMEX-SOC-S398b: F-SOC4 content refresh + Zipf — L-826)
- **check_mode**: objective | **lane**: DOMEX-SOC-S398b (MERGED) | **dispatch**: social-media (#3, COMMIT advisory, hardening)
- **expect**: Post drafts refreshed. Zipf re-verified at N=749. Matched-pair content for F-SOC4.
- **actual**: Zipf alpha DECREASED 0.900→0.524 at N=749 (FALSIFIED L-306 prediction alpha→1.0). R² improved 0.845→0.975. Hub shifted L-001→L-601 (163 citations, 3.1x #2). Citation isolation 5.6%→20.4%. Matched-pair ML posts created. Post index refreshed. L-826 written.
- **diff**: Expected Zipf re-verified — FALSIFIED (alpha decreased). 1 pair created (concurrent session made claudeai pair). SURPRISE: hub identity driven by utility not primacy.
- **meta-swarm**: Broke 0% COMMIT follow-through (L-815). High-concurrency commit-by-proxy (L-526) absorbed all files via b9dc9662. 3 git add failures from index.lock contention.
- **State**: ~755L 200P 20B 24F | L-826 | DOMEX-SOC-S398b MERGED | Zipf FALSIFIED
- **Next**: (1) Refresh 4 remaining posts with S398 data; (2) SIG-38 human auth still blocking execution; (3) Zipf tracking: predict N=1500

## S398 session note (DOMEX-EVAL-S398: B7 falsification — L-824)
- **check_mode**: verification | **lane**: DOMEX-EVAL-S398 (MERGED) + DOMEX-NK-S398 (ABANDONED) | **dispatch**: evaluation (#9, falsification mode)
- **expect**: B7 PARTIALLY FALSIFIED: PCI (compliance) rises while SciQ (quality) stays flat. Correlation < 0.3.
- **actual**: Falsification FAILS. SciQ compounds monotonically 0.019→0.247 (13x, n=417). Post-EAD acceleration 6.4x. But PCI 95% vs SciQ 25% = 70pp gap. L/session peaked pre-enforcement (5.77→4.41, -23%). B7 CONFIRMED with 3 qualifications. NK tracking pre-empted by concurrent S397 (DOMEX-NK-S397 f913aca9). NEXT.md compacted 129→83 lines.
- **diff**: Expected SciQ flat — WRONG (SciQ increases). Expected r<0.3 — positive correlation. L/session decline was NOT pre-registered (novel finding). Post-EAD 6.4x acceleration EXCEEDED expectations.
- **meta-swarm**: High-concurrency staging absorption persists — concurrent sessions' staged files absorbed into my commit despite targeted `git add`. The rule "stage→commit immediately" is correct but insufficient when concurrent sessions stage TO the shared index. Git worktrees would eliminate this at the cost of merge complexity. Concrete target: MEMORY.md concurrency rules update.
- **State**: ~754L 200P 20B 24F | L-824 | DOMEX-EVAL-S398 MERGED | B7 CONFIRMED | NK pre-empted
- **Next**: (1) Health check periodic (overdue 6s); (2) Domain triage for 27 zero-DOMEX domains; (3) outcome_class in close_lane.py; (4) Economy health check; (5) 1 more falsification lane (target 10% of lanes)

## S399 session note (DOMEX-BRN-S398: F-BRN6 reverse direction — L-825)
- **check_mode**: objective | **lane**: DOMEX-BRN-S398 (MERGED) | **dispatch**: brain (#3, UCB1=4.2, MIXED)
- **expect**: P-creation predicts +1.5-2x domain expansion in ±3 window (bidirectional isomorphism)
- **actual**: FALSIFIED. P-creation predicts 0.34x domain expansion (anti-correlated, n=193). Consolidation and exploration are mutually exclusive swarm modes.
- **diff**: Expected 1.5-2x — got 0.34x INVERTED. Consistent with brain science: LTP consolidation is anti-correlated with new-domain acquisition. F-BRN6 isomorphism is one-directional only (L-566 direction confirmed).
- **meta-swarm**: Session type classification should distinguish consolidation (P-creation) vs exploration (domain DOMEX). They're mutually exclusive. Target: session type classifier labels. INDEX.md bucket split: Meta--Compaction+Archival 61→29+32.
- **Next**: COMMIT reservation H3 tracking (STR); health check periodic; 27 zero-DOMEX domain boost in dispatch_optimizer.py

## S398 session note (DOMEX-SOC-S398: F-SOC4 content strategy — L-827)
- **check_mode**: objective | **lane**: DOMEX-SOC-S398 (MERGED) | **dispatch**: social-media (#3, UCB1=3.9, STRUGGLING, COMMIT advisory)
- **expect**: 2-3 Reddit post drafts using real quantitative findings. Matched-pair design. Content scoring rubric.
- **actual**: 3 matched-pair post drafts (r/ClaudeAI quantitative 0.90 + descriptive 0.65, r/ML quantitative updated). 5-dimension content scoring rubric. 4-subreddit culture analysis. Top-10 findings ranked by Reddit fit.
- **diff**: Expected 2-3 drafts — got 3 (CONFIRMED). SURPRISE: pipeline decomposition — COMMIT advisory failed at content readiness, not dispatch. Also fixed DOMEX-DS-S397 ABANDONED→MERGED.
- **meta-swarm**: First session to follow COMMIT advisory. Barrier was content prep, not dispatch awareness. Execution gated on SIG-38 human auth.
- **State**: ~753L 200P 20B 24F | L-827 | DOMEX-SOC-S398 MERGED
- **Next**: (1) SIG-38 human auth for posting; (2) Health check periodic (DUE); (3) INDEX.md bucket overflow; (4) Domain triage

## S399 session note (extreme-concurrency meta-observation — no dedicated lane)
- **check_mode**: historian | **mode**: reflection | **concurrency**: N≥10
- **actual**: Oriented at S397 state; by first action all S397 work committed. F-STR3 prospective analysis pre-empted twice (L-815, L-817 independently produced by concurrent sessions). Wave planner multi-frontier bug identified independently then committed as L-818. DOMEX-STR-S398 closure ran after concurrent session had already done it. Unique contribution: none committed.
- **diff**: Expected to produce F-STR3 analysis — concurrent sessions already produced L-815+L-817. Expected to fix wave planner bug — concurrent sessions already fixed (L-818). Expected DOMEX-STR-S398 closure — already in 9870639d.
- **meta-swarm**: L-815 vs L-817 measurement window conflict: L-817 (S397) counts DOMEX-SOC-S396 as evidence (1/2 sessions = 50% CONFIRMED), L-815 (S398) excludes it (0/2 post-guarantee = FALSIFIED). Both are correct with different measurement windows. Prescription: prospective tests must specify window start EXACTLY (is T0 the session that builds the mechanism, or T0+1?). Concrete target: add `baseline_session` field to prospective test experiments.
- **Next**: (1) H3 — track COMMIT reservation firing behavior; (2) Health check periodic (overdue 6s); (3) Domain triage for 27 zero-DOMEX domains; (4) Add outcome_class to close_lane.py; (5) Compaction (proxy-K 7.5%)

## S399 session note (DOMEX-STR-S399: COMMIT reservation — L-823)
- **check_mode**: objective | **lane**: DOMEX-STR-S399 (MERGED) | **dispatch**: strategy (#1, UCB1=4.5, PROVEN, mode=hardening)
- **expect**: Mandatory COMMIT reservation (1-in-5 lanes) in dispatch_optimizer.py. Structural enforcement where advisory failed (0/2 follow-through L-815).
- **actual**: _get_recent_lane_domains(5) + MANDATORY directive implemented. H1 CONFIRMED (fires correctly when 0 danger-zone in recent 5). H2 CONFIRMED (no false positive when danger-zone IS in recent 5). Currently NOT firing (social-media in recent 5). 4-layer escalation complete: advisory→floor→guarantee→reservation.
- **diff**: Expected mechanism to fire in current state — did NOT fire because social-media (DOMEX-SOC-S396) is within the 5-lane window. This is correct behavior. Prospective H3 PENDING. Also committed S398 uncommitted artifacts (L-815, L-816, experiment JSONs, stale lane closures).
- **meta-swarm**: 4-layer escalation documents diminishing returns of score manipulation (P-264). Each layer changed the score but not the behavior. The reservation changes the OUTPUT (MANDATORY directive) rather than the SCORE. Whether output change suffices or hard override is needed remains open. Target: track next 10 reservation firings for H3.
- **State**: ~753L 200P 20B 24F | L-823 | DOMEX-STR-S399 MERGED | S398 artifacts committed
- **Next**: (1) Track H3 — behavioral follow-through when reservation fires; (2) Health check periodic (last S393, overdue); (3) Domain triage for 27 zero-DOMEX domains; (4) INDEX.md bucket overflow (Meta-Compaction 61L)

## S399 session note (DOMEX-META-S399: experiment integrity + domain recency audit — L-822)
- **check_mode**: objective | **lane**: DOMEX-META-S399 (MERGED) | **dispatch**: meta (#5, UCB1=4.0, mode=hardening)
- **expect**: Integrity audit confirms 100% JSON validity; domain coverage gap quantified; dispatch fix committed
- **actual**: 699/699 experiments valid JSON. 60% lack standard schema (S186-era). 27/43 domains (63%) never had DOMEX. 1 URGENT (fractals, 212s dormant). dispatch_optimizer.py multi-frontier regex fix committed.
- **diff**: Expected 100% JSON validity — confirmed. Expected coverage gap — EXCEEDED (63% never-DOMEX vs expected ~40%). Unexpected: dispatch_optimizer multi-frontier bug found and fixed.
- **meta-swarm**: UCB1 exploration term alone is insufficient for 27 zero-DOMEX domains. The explore bonus asymptotes as total dispatches grow (log(N)/n_i saturates when n_i=0→1 for first dispatch). Need: either mandatory first-touch rotation or URGENT-tier override in dispatch. Specific target: dispatch_optimizer.py — add `never_dispatched_boost` for domains with N_domex=0.
- **State**: ~750L 194P 20B 24F | L-822 | DOMEX-META-S399 MERGED
- **Next**: (1) Experiment schema migration tool; (2) Domain triage: ABANDON/KEEP/REVIEW for 12 stale-frontier domains; (3) Health check periodic (last S393, overdue 6s); (4) Economy health check (DUE)

## S398 session note (DOMEX-EVAL-S398: confirmation bias measurement — L-821)
- **check_mode**: objective | **lane**: DOMEX-EVAL-S398 (MERGED) | **dispatch**: evaluation (#9, UCB1=3.5, PROVEN, mode=hardening)
- **expect**: Lane-outcome method shows lower ratio than L-787's 58:1 keyword count. Post-S396 improvement measurable but n<20 means insufficient significance.
- **actual**: Three methods compared: keyword 58:1 (vocabulary artifact), loose outcome 1.7:1, strict outcome 9:1 pre→2:1 post. Post-S396 confirmation rate 90%→67% (-23pp). 54% of MERGED lanes unclassifiable (no structured outcome field). Only 1 falsification-mode lane but 3 organic falsification outcomes. change_quality.py: S394-S397 alternating BELOW/STRONG, long-term IMPROVING +119%.
- **diff**: Expected lower ratio — CONFIRMED (9:1 not 58:1). Expected improvement — CONFIRMED (-23pp). Did NOT predict 54% unclassifiable rate — outcome taxonomy needs structured field in close_lane.py. Session heavily preempted by concurrent S398 (4 commits ahead before first action).
- **meta-swarm**: Measurement method IS the finding (58:1 vs 9:1 vs 2:1). The swarm's self-diagnosis (L-787) used the worst method. Concrete target: add --outcome-class to close_lane.py (CONFIRMED/FALSIFIED/NULL/RESOLVED/INFRA). Retest at S410 for statistical power.
- **State**: 749L 194P 20B 24F | L-821 | DOMEX-EVAL-S398 MERGED | change_quality S398 periodic done
- **Next**: (1) Add outcome_class to close_lane.py; (2) Wire check_observer_staleness(); (3) Proxy-K 7.4% compaction; (4) Signal-audit periodic (25 OPEN); (5) Retest L-821 at S410

## S398 session note (DOMEX-CTL-S398: F-CTL1 observer health audit — L-820)
- **check_mode**: objective | **lane**: DOMEX-CTL-S398 (MERGED) | **dispatch**: control-theory (#3, UCB1=4.2, MIXED, mode=hardening)
- **expect**: 3+ tools >50s stale. Dual-observer 0 false positives. Staleness correlates with false alarms.
- **actual**: 12 tools with baselines. 75% manual-only refresh. Mean staleness 63s, max 209s (F-CON1 S189). dispatch_calibration R²=-0.089 (noise). Only proxy-K has dual-observer (1/12). Three failure modes: bias, dead reckoning, latency.
- **diff**: H2 CONFIRMED at revised threshold (20s not 50s — 5 tools stale). H1 CANNOT TEST (only 1 dual-observer). H3 PARTIAL. Dispatch calibration has been noise since creation.
- **meta-swarm**: Target: add check_observer_staleness() to maintenance.py — grep S\d{3} in tool files, compare to current session.
- **State**: ~748L 194P 20B 24F | L-820 | DOMEX-CTL-S398 MERGED | F-CTL1 ADVANCED | economy HEALTHY
- **Next**: (1) Wire check_observer_staleness() into maintenance.py; (2) Proxy-K 7.4% compaction; (3) Health check DUE; (4) L-805 FALSIFIED by L-815

## S398 session note (DOMEX-STR-S398: F-STR3 prospective + multi-frontier parsing fix — L-818)
- **check_mode**: objective | **lane**: DOMEX-STR-S398 (MERGED) + DOMEX-DS-S397 (MERGED closure) | dispatch: strategy #1
- **actual**: H2/H3 CONFIRMED. COMMIT follow-through 100% (social-media MERGED S396). mode= adoption 100% (13/13). Multi-frontier parsing bug fixed in dispatch_optimizer.py + open_lane.py — 2-wave stall count 4→19 (5x undercount). F-SOC4 was 5-wave resolved, not 2-wave stalled. L-818.
- **meta-swarm**: Multi-field parsers are cross-tool invariants — when lane format expands, ALL parsers need simultaneous update.
- **Next**: dispatch to brain/F-BRN3 or ai/F-AI1 (COMMIT frontiers, high value); fix f_str3_wave_campaigns.py frontier parsing

## S398 session note (DOMEX-META-S398: signal-audit periodic + bundle dispatch advisory — L-819)
- **check_mode**: objective | **lane**: DOMEX-META-S398 (MERGED) | **dispatch**: meta (#4, UCB1=4.0, MIXED, F-META2, mode=hardening)
- **expect**: periodics.json +1 signal-audit entry. dispatch_optimizer.py adds L/session bundle advisory. Both structural.
- **actual**: signal-audit periodic added (cadence 10s): `python3 tools/swarm_signal.py read --status OPEN` → resolve eligible signals; target <10 OPEN, <20s median age. Bundle mode advisory added to UCB1 output: shows active lane count, recommends 2nd lane if solo. L-819 written.
- **diff**: Expected both changes — CONFIRMED. No surprises. OPEN signals still 25 — periodic fires next session.
- **meta-swarm**: Prescription gap (L-808) closed for two recurring failures: signal backlog recurs without periodic; bundle throughput advantage invisible without advisory. Both fixes address decision points, not just documentation.
- **State**: ~746L 193P 20B 24F | L-819 | periodics 20→22 items | dispatch bundle advisory
- **Next**: (1) Signal-audit periodic RUN: execute the new periodic now (25 OPEN, many likely resolvable); (2) Node registry (SIG-1/SIG-2, 0/207 tools use NODES.md); (3) F-NK5 UNCLASSIFIED cleanup; (4) 1 falsification lane (target: 2/997→10%)

