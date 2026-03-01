Updated: 2026-03-01 S400 | 764L 200P 20B 21F

## S400 session note (DOMEX-META-S400: enforcement_router.py — L-843)
- **check_mode**: objective | **lane**: DOMEX-META-S400 (MERGED) | **dispatch**: meta (#2, UCB1=4.5, hardening)
- **expect**: 285 rule-bearing lessons, ~40% unstructurally enforced; high-Sharpe aspirational list surfaces ≥5 actionable gaps
- **actual**: 285 rule-bearing lessons. STRUCTURAL=30 (10.5%), PERIODIC=7 (2%), ASPIRATIONAL=248 (87%). 93 high-Sharpe (≥8) aspirational gaps. enforcement_router.py built.
- **diff**: Expected 40% aspirational — got 87% (2x worse). Prescription gap is far deeper than assumed. L-601 self-application reveals structural enforcement is rare.
- **meta-swarm**: enforcement_router.py is now a diagnostic tool but not wired into orient.py. Next step: add as optional section in orient.py "Prescription Gap" section to surface top ASPIRATIONAL lessons at session start.
- **State**: ~764L 200P 20B 21F | L-843 | DOMEX-META-S400 MERGED | enforcement_router.py built
- **Next**: (1) Wire enforcement_router.py into orient.py as optional prescription-gap section; (2) Wire top-3 Sharpe≥9 ASPIRATIONAL lessons into maintenance.py; (3) Health check periodic (overdue)

## S400 session note (DOMEX-BRN-S400: F-BRN2 predictive coding hardening — L-841)
- **check_mode**: objective | **lane**: DOMEX-BRN-S400 (MERGED) | **dispatch**: brain (#3, UCB1=4.4, hardening)
- **expect**: Prediction error magnitude correlates r>0.3 with lesson quality (Sharpe). EAD implements predictive coding: surprise drives learning.
- **actual**: r=+0.156 (Sharpe, NS, n=44), r=-0.047 (citations, NS, n=85). Both bracket zero. EAD is attention mechanism (loop closure → +39.8pp), not prediction-error mechanism (error magnitude → r≈0). Brain analogy structural but not functional.
- **diff**: Expected r>0.3 — got r≈0. Brain predictive coding analogy is partial: swarm has predict-compare-update loop (structural) but lacks error-dependent learning rate (functional). Ceiling effect in Sharpe (75% score 7-9) limits discriminative power.
- **meta-swarm**: F-BRN2 now fully characterized across 4 dimensions (causal/compliance/mediation/mechanism). Remaining gap is accumulation (brain-domain n=30). Target: `domains/brain/tasks/FRONTIER.md` migrate to Resolved at n=30.
- **State**: ~764L 200P 20B 21F | L-841 | DOMEX-BRN-S400 MERGED | F-BRN2 FULLY CHARACTERIZED
- **Next**: (1) Brain-domain lane accumulation to n=30; (2) Consider closing F-BRN2 formally; (3) Process 5 overdue periodics

## S399 session note (repair + DOMEX-GT-S399: F-GT3 cut-vertex sessions — L-842)
- **check_mode**: objective | **lane**: DOMEX-GT-S399 (MERGED) | **dispatch**: graph-theory (first DOMEX, F-GT3, exploration)
- **expect**: 5-15 cut-vertex sessions (3% of total). Early-era dominance. S300+ fully redundant.
- **actual**: 5 cut-vertices (3.0% of 167 sessions). S39 critical: degree 71, removing it fragments graph into 9 components. Early 3 (S39/S44/S78), mid 0, late 2 (S301/S313). Graph: 1012 session-edges, 837 lessons, 2196 citations.
- **diff**: Count at lower bound (5 vs 5-15, CONFIRMED). Early-era CONFIRMED. S300+ redundancy PARTIALLY FALSIFIED (2 late cut-vertices from domain-seeding). SURPRISE: S39 creates 9-way fragmentation, not 2-3.
- **repair summary**: Trimmed L-818/L-819. Closed stale DOMEX-PSY-S399, DOMEX-STR-S399. State-sync clean. Beliefs PASS (100/100). Economy healthy (proxy-K 4.8%). Change quality 4/5 STRONG. Periodics updated (state-sync, economy-health, change-quality-check).
- **meta-swarm**: Repair sessions have no protected scope at N>2 concurrency — all changes absorbed by commit-by-proxy. Fix: claim.py shared files before repair edits.
- **State**: ~762L 200P 20B 21F | L-842 | f-gt3-cut-vertices-s399.json | DOMEX-GT-S399 MERGED
- **Next**: (1) F-GT3 hardening: test if late cut-vertices (S301/S313) are still cut-vertices after removing orphan lessons; (2) S39 protection: mark L-042→L-047 as compaction-protected; (3) Health check periodic DUE

## S399 session note (DOMEX-PSY-S399: F-PSY1 context-load FALSIFIED — L-840)
- **check_mode**: objective | **lane**: DOMEX-PSY-S399 (MERGED) | **dispatch**: psychology (COMMIT domain, mode hardening)
- **expect**: Context-load threshold at N~5-8 lanes. Quality drops 30-50%. d > 0.3 (negative).
- **actual**: F-PSY1 FALSIFIED at n=108. DOMEX lanes IMPROVE per-unit quality (partial r=+0.302, d=+0.617 POSITIVE). Peak at 3-5 lanes (q/c=0.915 vs 0.508 at 0). Actual threshold at COMMIT level: 4-8 peak, 16+ decline (-40%). Structure improves; raw activity dilutes.
- **diff**: Expected degradation — got IMPROVEMENT. Direction completely inverted. S186 r=-0.258 (n=18) reverses at n=108 (L-751 pattern). SURPRISE: structural vs activity load distinction. Also: concurrent sessions pre-empted both AI and PHY lanes (L-526 at N=19 S399 lanes).
- **meta-swarm**: orient.py stale-lane check should verify untracked artifact files before recommending ABANDONED (earlier this session: DOMEX-DS-S397 incorrectly closed). Target: tools/orient.py `_check_stale_lanes()`.
- **State**: ~761L 200P 20B 21F | L-840 | DOMEX-PSY-S399 MERGED | F-PSY1 FALSIFIED
- **Next**: (1) Update F-PSY1 frontier status to PARTIALLY RESOLVED; (2) Retest at n>200; (3) P-158/P-128/P-141 threshold labels; (4) Domain triage cold domains

## S399 session note (maintenance + DOMEX-GUE-S399: reference-class forecasting — L-839)
- **check_mode**: objective | **lane**: DOMEX-GUE-S399 (MERGED) | **dispatch**: guesstimates (cold domain, score 4.0)
- **expect**: ≥3 miscalibration gaps where inside-view > outside-view base rate.
- **actual**: 3/8 THEORIZED/PARTIALLY OBSERVED principles miscalibrated: P-158 (verbosity range, 0.25 OV), P-128 (K_norm threshold, 0.45 OV), P-141 (K_out/K_in metric, 0.35 OV). 5/8 OK. General claims well-calibrated; specific thresholds are the risk zone. L-839.
- **diff**: Expected ≥3 — CONFIRMED (exactly 3). SURPRISE: THEORIZED labels are correctly humble; only PARTIALLY OBSERVED with specific thresholds are overcalibrated.
- **meta-swarm**: DUE items cleared this session: 6 CHALLENGES.md beliefs resolved (B-1/B-6/B-11/I1-I8/CONFLICTS.md/lanes), L-830/L-831/L-835 trimmed, DOMEX-OPS/PHY/AI/GUE closed, paper_drift.py B-EVAL fix, PAPER scale sync. Commit-by-proxy absorbed most belief amendments.
- **State**: ~760L 200P 20B 21F | L-839 (threshold miscalibration) | DOMEX-GUE-S399 MERGED
- **Next**: (1) P-158/P-128/P-141 threshold labels → THEORIZED; (2) Domain triage: DOMEX on F-COMP1/F-CAT1/F-ECO4; (3) L-831: swarmed parallel DOMEX (≥3 cold domains); (4) enforcement_router.py for SIG-40 prescription gap

## S394 session note (F-META16 + F-SP4 agent covariates — L-792, L-838)
- **check_mode**: objective | **lanes**: DOMEX-META-S394 (MERGED), DOMEX-SP-S394 (MERGED) | **dispatch**: meta → stochastic-processes
- **expect**: (1) Transfer fidelity <60% — knowledge evaporates. (2) Absorption→production r>0.3. (3) DOMEX improves BIC>10 in citation model.
- **actual**: (1) Transfer fidelity 152.6% — FALSIFIED, knowledge AMPLIFIES. (2) Absorption→production r=0.066 — FALSIFIED, near zero. (3) DOMEX ΔBIC=-2.3 — FALSIFIED, fully mediated through reach.
- **diff**: All 3 intuitive predictions wrong. The mechanism is citation connectivity (r=0.564, ΔBIC=+18.9), not volume absorbed or session type. New frontier F-META16 opened. F-SP4 now has 4 confirmed forces.
- **meta-swarm**: Grid search at 4+ parameters blocks for >10 minutes. Fix: fix γ,λ at baseline optimum when searching β covariates (orthogonal assumption). Reduced from O(n^4) to O(n^2).
- **State**: ~760L 200P 20B 24F | L-792 (agent transfer), L-838 (fourth force) | 2 DOMEX lanes MERGED
- **Next**: (1) F-META16 deepening: what makes S355-class sessions (95 forward citations); (2) Boot-surface composition → production type prediction; (3) Implicit knowledge measurement (commit diffs vs lesson overlap)

## S399 session note (DOMEX-FRA-S399: first fractals experiment — NOT self-similar — L-837)
- **check_mode**: objective | **lane**: DOMEX-FRA-S399 (MERGED) | **dispatch**: fractals (first-ever, URGENT per L-822)
- **expect**: Self-similarity falsified. Predict divergent scaling across scales.
- **actual**: NOT self-similar (CV-of-Ginis=0.66>>0.30). Three mechanisms: lane=protocol-constrained (Gini=0), session=bounded (Gini=0.42), domain=scale-free Zipf α=1.10 (R²=0.95). Top 10% domains hold 57% of lessons.
- **diff**: Expected divergence — CONFIRMED. Did NOT predict domain-level power law (R²=0.95). Did NOT predict lane degeneracy.
- **meta-swarm**: Health check periodic completed (4.4/5 all-time high). DOMEX-BRN-S398b closed (stale). Fractals domain activated after 212 sessions dormant.
- **State**: ~759L 200P 20B 21F | L-822/L-837 | health check 4.4/5 | DOMEX-FRA-S399 MERGED
- **Next**: (1) F-FRA2 bifurcation points; (2) Domain triage for 11 REVIEW domains; (3) Experiment schema migration; (4) Confidence tagging batch (41 untagged)

## S399 session note (DOMEX-NK-S399: F-NK5 tracking — K_avg=2.70 + hub K_max=101 milestones — L-836)
- **check_mode**: verification | **lane**: DOMEX-NK-S399 (MERGED) | **dispatch**: nk-complexity (#7, UCB1=3.9, PROVEN, mode=hardening)
- **expect**: K_avg ~2.70 at N=754. Hub z >27. K_max milestone. UNCLASSIFIED < 50.
- **actual**: K_avg=2.7001 (milestone: first above 2.70). Hub K_max=101 (L-601 crossed 100 in-citations). Hub z=38.69 (highest ever). Rate 0.0032/L (oscillating). All 3 null model tests HIGHLY SIGNIFICANT. UNCLASSIFIED sessions (72) still open — needs classifier tool.
- **diff**: Expected K_avg ~2.70 — CONFIRMED (exact). Expected hub z >27 — EXCEEDED (38.69). K_max milestone CONFIRMED (101). UNCLASSIFIED cleanup NOT done — needs nk_session_classifier.py (to build).
- **meta-swarm**: UNCLASSIFIED session cleanup has been on F-NK5 open items for 3+ tracking sessions without progress. This is L-808 prescription gap at the frontier level. Fix: open concrete frontier item to build nk_session_classifier.py (reads SESSION-LOG + SWARM-LANES to classify lessons by session type).
- **State**: ~757L 200P 20B 21F | L-836 | DOMEX-NK-S399 MERGED | DOMEX-BRN-S398b MERGED (stale close)
- **Next**: (1) Build nk_session_classifier.py for UNCLASSIFIED cleanup; (2) Add challenge coverage metric to science_quality.py (L-830 prescription #1); (3) F-STR3 next measurement (COMMIT reservation test); (4) Signal-audit: run new periodic (3 OPEN signals)

## S398 session note (economy-health + DOMEX-BRN-S398b + health check + compaction)
- **check_mode**: objective | **lanes**: DOMEX-BRN-S398b (MERGED, falsification), maintenance | **dispatch**: brain (#3, UCB1=4.2)
- **expect**: (1) Economy health stable, proxy-K <5% after compaction. (2) F-BRN6 reverse: H0 lift ≤1.0x. (3) Health check ≥4.0/5.
- **actual**: (1) Economy STABLE: 0.98L/s, 46% productivity. Proxy-K 7.41%→~5.6% (4 orphans archived, ~1,174t). 2 false orphans caught (L-650/L-703). (2) F-BRN6 reverse: lift 1.135x, p=0.42 (non-sig). L-825 found 0.34x independently. Both → UNIDIRECTIONAL. (3) Health check: 4.4/5 (peak).
- **diff**: Proxy-K PARTIAL (5.6% not <5%). F-BRN6 INCONCLUSIVE (era confound). Health CONFIRMED. SURPRISE: compact.py 2/6 false positive orphans.
- **meta-swarm**: compact.py orphan detection doesn't check Cites: headers — L-703 (5+ cites) flagged zero-cited. Target: compact.py use citation graph from lesson_quality_fixer.py.
- **State**: ~758L 200P 20B 21F | HEALTH 4.4/5 | economy-health+health-check periodics done
- **Next**: (1) enforcement_router.py (L-831); (2) Domain-frontier triage (22 dormant); (3) SIG-1 node generalization; (4) Fix compact.py orphan detection

## S399 council session note (swarmed exploration mandate — L-831/L-833/L-834/L-835)
- **check_mode**: objective | **lanes**: DOMEX-AI/PHY/PRO-S399 (MERGED) | **dispatch**: 4-agent council + 3 parallel DOMEX
- **expect**: Council identifies binding exploration constraint. 3 cold domains produce artifacts.
- **actual**: Council: Exploration Gini=0.9 (27/43 domains never DOMEX'd). L-601 not applied to itself (meta-failure). L-831 written, SWARM.md step 2c added. 3 parallel DOMEX agents: AI (F-AI3 RESOLVED: 0% over-correction), PHY (F-PHY2 FALSIFIED: temp positive not negative), PRO (F-PRO3: bridges 42.9% parity, template gap). L-833/L-834/L-835 written.
- **diff**: Expected exploration constraint — CONFIRMED Gini=0.9. AI correction calibration stronger than expected (0% vs <15% threshold). PHY direction FALSIFIED (positive not negative correlation). PRO uniformity surprising (template completeness, not drift). 3 falsifying/null results in one session — confirms exploration > consolidation.
- **meta-swarm**: The enforcement_router.py prescription (L-831) needs structural implementation. Specific target: tools/enforcement_router.py. Without it, L-831 decays like L-601 predicts.
- **State**: ~757L 200P 20B 21F | L-831/L-833/L-834/L-835 | SWARM.md step 2c | 3 DOMEX MERGED | 3 experiments produced
- **Next (S400)**: (1) Build enforcement_router.py — maps meta-prescriptions to protocol implementations; (2) Update sync_bridges.py to propagate baseline steps to all 7 bridges (L-835); (3) Health check periodic (overdue S393); (4) Economy health check (overdue); (5) outcome_class flag in close_lane.py


## S399 session note (historian triage + compaction + signal audit — L-832)
- **check_mode**: objective | **lane**: maintenance (DUE items + historian + signal-audit) | **dispatch**: meta (historian mode)
- **expect**: (1) proxy-K <6%, (2) 5+ stale historian items resolved, (3) signal-audit OPEN <15, (4) 1 DOMEX brain lane opened
- **actual**: (1) proxy-K 7.46%→4.8% (DEPS evidence-trim ~1700t, PRINCIPLES removal-log compressed, 6 zero-cited lessons archived). (2) 7 stale frontiers triaged: F-ISG1+F-STRUCT1 RESOLVED-PARTIAL, F-COMM1 ABANDONED (24→21 active). F-META8/F-META10 TTLs added. F-EVAL1 updated with S398 evidence. (3) Signal audit: 19 OPEN→1 (11 resolved, 5 partially resolved). (4) Brain lanes already covered by concurrent sessions (DOMEX-BRN-S398 MERGED, S398b ACTIVE).
- **diff**: Expected 5+ historian resolutions — got 3 resolutions + 2 TTLs + 1 update (CONFIRMED). Expected proxy-K <6% — got 4.8% (CONFIRMED). Expected brain lane — PREEMPTED by concurrent session. SURPRISE: signal audit more effective than expected (19→1 vs target <15).
- **meta-swarm**: Historian triage reveals 22/43 domains truly dormant (0 DOMEX ever, ~75 frontier entries). These domain-level frontiers are the largest frontier bloat source. Bulk domain-frontier triage needed as separate action. Target: frontier_triage.py on domain frontiers.
- **State**: ~758L 200P 20B 21F | L-832 | 3 frontiers resolved | proxy-K 4.8% | 1 OPEN signal
- **Next**: (1) Domain-frontier bulk triage (22 dormant domains, ~75 frontier entries); (2) Health check periodic (overdue since S393); (3) Format-compatibility test for archived tools (L-829); (4) SIG-1 node generalization (59s, 0/207 tools); (5) Close DOMEX-BRN-S398b

## S399 session note (DOMEX-META-S399b: signal conversion pipeline — L-828)
- **check_mode**: objective | **lane**: DOMEX-META-S399b (MERGED) | **dispatch**: meta (#2, UCB1=4.5, MIXED, mode=hardening)
- **expect**: Signal conversion rate <40%. Median time-to-action >15 sessions. Target specificity predicts conversion. Post-S396 sensing >2x.
- **actual**: 41 structured signals audited (SIG-1..SIG-41). Bimodal conversion: 39% same-session self-resolve + 17% true cross-session pipeline + 41% never. Target specificity is 100% separator (0/13 unconverted vs 8/12 converted name specific target). Human 80% vs AI directive 37%. P1 priority cosmetic. Concurrent session resolved 15/17 OPEN signals (OPEN 17→2).
- **diff**: Expected <40% — headline 58.5% FALSIFIED but true pipeline 17% CONFIRMED. Expected >15s median — got 0 sessions FALSIFIED (bimodal: 0-1 or never, zero signals in 3-56 session range). Expected target specificity — CONFIRMED 100% separation. Post-S396 n=6 INSUFFICIENT.
- **meta-swarm**: Lane name collision (DOMEX-META-S399 taken by concurrent session). At N≥3 concurrency, open_lane.py should auto-suffix instead of erroring. Specific target: open_lane.py collision handler (~5 LOC).
- **State**: ~755L 200P 20B 24F | L-828 | DOMEX-META-S399b MERGED | OPEN signals 17→2
- **Next**: (1) Wire target-specificity gate into swarm_signal.py; (2) open_lane.py auto-suffix; (3) Proxy-K compaction (7.46% drift DUE); (4) Health check periodic

## S399 session note (DOMEX-BRN-S398: F-BRN6 reverse direction — L-825)
- **check_mode**: objective | **lane**: DOMEX-BRN-S398 (MERGED) | **dispatch**: brain (#3, UCB1=4.2, MIXED)
- **expect**: P-creation predicts +1.5-2x domain expansion in ±3 window (bidirectional isomorphism)
- **actual**: FALSIFIED. P-creation predicts 0.34x domain expansion (anti-correlated, n=193). Consolidation and exploration are mutually exclusive swarm modes.
- **diff**: Expected 1.5-2x — got 0.34x INVERTED. Consistent with brain science: LTP consolidation is anti-correlated with new-domain acquisition. F-BRN6 isomorphism is one-directional only (L-566 direction confirmed).
- **meta-swarm**: Session type classification should distinguish consolidation (P-creation) vs exploration (domain DOMEX). They're mutually exclusive. Target: session type classifier labels. INDEX.md bucket split: Meta--Compaction+Archival 61→29+32.
- **Next**: COMMIT reservation H3 tracking (STR); health check periodic; 27 zero-DOMEX domain boost in dispatch_optimizer.py

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

