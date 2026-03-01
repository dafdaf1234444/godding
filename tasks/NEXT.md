Updated: 2026-03-01 S378

## S377 session note (DOMEX-META2-S377: F-META10 epistemological state model — L-719)
- **check_mode**: objective | **lane**: DOMEX-META2-S377 (MERGED) | **dispatch**: meta (SIG-27 P1 human directive)
- **expect**: knowledge_state.py classifies 640L into 5 epistemic states. SHOULD-KNOW > ACTIVE in >=30% of domains. Per-domain profiles computable. Dispatch integration feasible.
- **actual**: 993 items classified (644L + 186P + 20B + 141F). 3/3 F-META10 hypotheses PASS: SHOULD-KNOW > ACTIVE in 89.5%, revival 0.52%/s (<1%), gap-ranked dispatch 5/5 different from UCB1. 165 BLIND-SPOT items (16.6%). Domain metadata gap: 91% lessons lack Domain: fields.
- **diff**: SHOULD-KNOW dominance predicted >=30% — got 89.5% (much stronger). Dispatch integration confirmed. Did NOT predict 91% domain metadata gap. Did NOT predict 62 orphaned principles. Revival 0.52%/s validates L-633 decay pattern.
- **meta-swarm**: Tool partially built by concurrent S377 session. This session improved: domain normalization, BLIND-SPOT detection, P/B citation tracking, hypothesis testing, dispatch integration. Next: batch Domain: field addition.
- **State**: ~652L 179P 17B 41F | L-719 | DOMEX-META2-S377 MERGED | F-META10 step 1 CONFIRMED
- **Next**: (1) batch Domain: field addition (91% gap); (2) integrate gap-score into dispatch; (3) economy-health (DUE); (4) health-check (DUE); (5) proxy-K compaction

## S377 session note (DOMEX-SEC-S377: F-SEC1 enforcement wiring — L-718)
- **check_mode**: objective | **lane**: DOMEX-SEC-S377 (MERGED) | **dispatch**: security (#1, UCB1=∞, first visit)
- **expect**: Wiring Layer 1 (bundle hash) + Layer 4 (FM-10) into check.sh raises F-SEC1 score from 1.6/5 to >=3.0/5. At least 2 layers fully MITIGATED.
- **actual**: Score 1.6/5→3.2/5 (64%, STRONG). 2/5 fully MITIGATED. Both checks PASS. Genesis hash verified. NEVER-REMOVE atoms guarded at commit time.
- **diff**: Predicted >=3.0/5 — got 3.2/5 (exceeded). Predicted 2 MITIGATED — confirmed. Did NOT predict contract_check.py already partially served Layer 4. Passive defense (dead channel) remains most effective mechanism.
- **meta-swarm**: L-601 confirmed at THIRD layer (quality S331, EAD S360, security S377). First DOMEX in security domain closes 70-session gap since S307. Also: proxy-K 7.0%→5.3% + orphan rescue (L-707/708/709).
- **State**: ~650L 179P 17B 41F | L-718 | DOMEX-SEC-S377 MERGED | F-SEC1 ADVANCED
- **Next**: (1) Layer 3 merge_back.py; (2) Layer 5 colony depth limit; (3) F-IC1 contamination audit; (4) economy-health; (5) health-check

## S378b session note (DOMEX-META-S378: F-META11 agent time profiling — L-717)
- **check_mode**: objective | **lane**: DOMEX-META-S378 (MERGED) | **dispatch**: meta (SIG-28 human directive)
- **expect**: Overhead >50% of commits; concurrency amplifies overhead; no prior measurement exists.
- **actual**: 569 commits classified (S307-S377). Overhead:value ratio improved 6.0→0.50 over 70 sessions. Current: 45.5% overhead overall, but S370-S379 = 65% value (first value-majority window). 100%-value sessions = single-DOMEX, 3-5 commits. Concurrency adds +3.4pp overhead. Top overhead categories: handoff (12.1%), state-sync (10.4%), trim (7.4%).
- **diff**: Predicted >50% overall — got 45.5% (close). Did NOT predict the dramatic improvement trend (6.0→0.50). Did NOT predict that session type (focused DOMEX vs cleanup) matters more than concurrency.
- **meta-swarm**: This directly answers SIG-28 ("swarm has to understand its agents better"). The tool + frontier create a persistent feedback loop: agents can now see their own time allocation via `agent_time_profile.py`. F-META11 tests whether this awareness changes behavior. Target: overhead <25% by S389.
- **State**: ~650L 179P 17B 41F | L-717 | DOMEX-META-S378 MERGED | agent_time_profile.py + F-META11
- **Next**: (1) wire agent_time_profile.py 1-line summary into orient.py; (2) measure 10-session window S380-S389; (3) health-check periodic (DUE); (4) economy-health (DUE)

## S378 session note (DOMEX-META3-S378: problem→expert routing — L-716)
- **check_mode**: objective | **lane**: DOMEX-META3-S378 (MERGED) | **dispatch**: meta (problem-demand driven)
- **expect**: 60% problems mappable to domain experts, >50% mismatch vs UCB1 top-3.
- **actual**: 76% mappable (26/34), 100% mismatch (0/5 overlap). UCB1 top-5 (security, gaming, strategy, graph-theory, fluid-dynamics) have ZERO detected problems. Problem top-5 (meta 12.8, expert-swarm 8.8, evolution 4.8, nk-complexity 4.0, economy 3.5) are all operational domains. UCB1 is exploration-optimal but problem-blind.
- **diff**: Predicted 60% mappable — got 76% (better). Predicted >50% mismatch — got 100% (worse). Did NOT predict meta dominance (12.8 = 11 problems). Abstract recursive signals (7/34) are unroutable — "swarm swarm swarm" directives lack concrete domain anchors.
- **meta-swarm**: This session IS what the human asked: "if swarm sees problem how it schedules swarming swarm the domain experts" — built the mechanism that routes detected problems to expert domains. The 100% mismatch finding proves UCB1 alone is insufficient for problem-driven swarms. Combined dispatch (UCB1 exploration + problem demand) now wired into swarm_cycle.py.
- **State**: ~649L 179P 17B 40F | L-716 | DOMEX-META3-S378 MERGED | problem_router.py | 3 stale lanes closed
- **Next**: (1) improve signal routing (7 NO_ROUTE signals need keyword anchors); (2) test augmented dispatch over 10 sessions (problem-demand vs UCB1); (3) health-check periodic (DUE); (4) economy-health (DUE); (5) wire problem_router into autoswarm.sh prompt generation

## S377b session note (DOMEX-GT-S377: F-GT2 dependency graph + chi — L-715)
- **check_mode**: objective | **lane**: DOMEX-GT-S377 (MERGED) | **dispatch**: graph-theory (#5, 3.5, FLOOR)
- **expect**: Unified dependency graph reveals hub-spoke tools, >80% implicit frontier deps, disconnected layers. Chromatic number computable.
- **actual**: 862 nodes, 1839 edges across 6 layers. Active chi=2, historical mean chi=1.66 (max 13, n=454 lanes). 147 cross-layer edges (76 tool→frontier, 71 lesson→tool). Frontier implicit rate 72.6%. Hub-spoke confirmed: orient(25 deps), L-601(34 citations). Scope-Key pollution: 112/575 lanes have close_lane.py as false scope.
- **diff**: Predicted hub-spoke — CONFIRMED. Predicted >80% implicit — got 72.6% (close). Predicted disconnected — CONFIRMED (68 isolated frontiers, 39 orphan tools). Did NOT predict Scope-Key pollution (112 false entries). Did NOT predict chi this low (1.66) — domain-scoping prevents conflicts naturally.
- **meta-swarm**: Scope-Key pollution is a systematic data quality bug in close_lane.py — it overwrites the original Scope-Key with its own path during lane closure. Concrete target: close_lane.py should preserve the original Scope-Key field from the last ACTIVE row. Also: concurrent session overwrote L-714 (slot contention, L-602 pattern), writing as L-715 instead.
- **State**: ~647L 179P 17B 40F | L-715 | DOMEX-GT-S377 MERGED | DOMEX-SEC-S376 + DOMEX-FLD-S376 ABANDONED (stale)
- **Next**: (1) Fix close_lane.py Scope-Key preservation; (2) reduce frontier implicit rate (add prereq fields); (3) health-check periodic (DUE); (4) economy-health (DUE); (5) F-GT3 cut-vertex analysis

## S376c session note (DOMEX-FLD-S376: F-FLD1 Reynolds AUC=0.870 — L-713, independent convergence)
- **check_mode**: objective | **lane**: DOMEX-FLD-S376 (MERGED) | **dispatch**: fluid-dynamics (#2, 5.5, FLOOR)
- **expect**: Re_swarm separates high-yield from low-yield sessions with AUC>0.65.
- **actual**: Re_structural = (lanes×domains)/(overhead+ε). AUC=0.870, accuracy 82.7% at Re_crit=1.575. Phase transition at Re≈2-4 (33pp jump). Turbulent 3.04x more productive. 8 formulations tested; Re_full circularity detected and resolved. Component AUC: overhead(inv) 0.837, lanes 0.827, domains 0.726. Era analysis: Codex era highest overhead (0.672), lowest productive rate (31%).
- **diff**: Predicted AUC>0.65 — got 0.870 (far exceeded). Did NOT predict circularity issue. Did NOT predict turbulent=productive inversion. Did NOT predict overhead alone nearly as predictive (0.837 vs 0.870). Convergent independent result with concurrent L-711 (different method, same turbulent=productive conclusion). Two lines of evidence strengthen F-FLD1.
- **meta-swarm**: Concurrent session (L-711) and this session independently built F-FLD1 experiments with different formulations and data pipelines but converging conclusions. This IS the complementarity mechanism from F-FIN1 (L-694): independent sessions produce non-redundant knowledge that cross-validates.
- **State**: ~647L 179P 17B 40F | L-713 | DOMEX-FLD-S376 MERGED | F-FLD1 MOSTLY CONFIRMED (2 lines)
- **Next**: (1) F-FLD3 Bernoulli focus-throughput with same dataset; (2) Re as early-warning for session failure; (3) proxy-K compaction (DUE); (4) health check periodic

## S377 session note (DOMEX-SEC-S376 completed: F-SEC1 dead-channel defense — L-712)
- **check_mode**: objective | **lane**: DOMEX-SEC-S376 (MERGED) | **dispatch**: security (#1, UCB1 ∞, first visit)
- **expect**: Layer 1 bundle integrity implementable and testable against 5 attack vectors. At least 3/5 attack vectors mitigated by existing infrastructure. Predicted: replay+injection blocked, poisoning partial, spoofing partial, fork bomb unaddressed.
- **actual**: 0/5 fully mitigated, 5/5 partial. Score 1.6/5 (32% MODERATE). Bundle hash generation exists (tamper detection verified) but not wired to startup. Key finding: defense-by-absence — Layer 2 passively blocked (no auto-merge = dead channel), Layer 5 fork bomb impossible (swarm_colony.py archived). 3/5 vectors require nonexistent inter-swarm features.
- **diff**: Predicted 3/5 mitigated — got 0/5 fully (wrong). Predicted replay blocked — got TOOL_EXISTS_NOT_WIRED (weaker). DID NOT predict defense-by-absence pattern: dead channels and archived tools provide stronger security than partial implementations. DID NOT predict all attack surfaces are theoretical (no active inter-swarm comms). Security investment trigger should be feature-activation, not age-since-design.
- **meta-swarm**: L-710 (from prior S376 attempt) captured the L-601 decay angle. L-712 captures the novel finding: attack surface reduction via absence. This session completed the stale DOMEX-SEC-S376 lane by producing the missing artifact. Concrete target: wire Layer 1 hash verification into check.sh BEFORE activating any inter-swarm feature.
- **State**: ~647L 179P 17B 40F | L-712 | DOMEX-SEC-S376 MERGED | F-SEC1 PARTIAL (32%)
- **Next**: (1) Wire Layer 1 bundle hash into check.sh pre-spawn gate; (2) proxy-K compaction (6.79% DUE); (3) UCB1 Gini re-measure at S385; (4) health check periodic; (5) F-IC1 contamination detector

## S376 session note (2 DOMEX lanes: ECO-S375 UCB1 default L-706 + FLD-S376b Reynolds regime L-711)
- **check_mode**: objective | **lanes**: DOMEX-ECO-S375 (MERGED), DOMEX-FLD-S376b (MERGED)
- **ECO-S375**: F-ECO5 UCB1 made default dispatch mode. 20% DARPA floor: 6 domains protected. Forward sim: 0 meta dispatches in 20 rounds. Score spread 39.8→4.9 (87.7%). Gini 0.570→0.525 (-7.9% over 20 rounds). L-706.
- **FLD-S376b**: F-FLD1 Reynolds regime measured. Re_swarm = (1-overhead)×commits/concurrent. R²=0.16 (below 0.3 target). Re_crit=0.6: turbulent 2.59x laminar. BUT simple commits outperforms (R²=0.37). Overhead orthogonal to quality (r=0.044). Hypothesis INVERTED: turbulent=productive. L-711.
- **meta-swarm**: Both experiments find the same pattern: formal structure (UCB1 for allocation, Reynolds for classification) captures real dynamics but the simplest component dominates. UCB1's exploration term dominates structural score; commit count dominates Reynolds ratio. Formal models add interpretive power, not predictive power.
- **State**: ~644L 179P 17B 40F | L-706, L-711 | 2 lanes MERGED | UCB1 is default dispatch mode
- **Next**: (1) Re-measure visit Gini at S385; (2) proxy-K compaction (6.79% DUE); (3) F-FLD1 early-warning test; (4) Thompson sampling Tier 2

## S376 session note (DOMEX-SEC-S376: F-SEC1 security audit — L-710)
- **check_mode**: objective | **lane**: DOMEX-SEC-S376 (MERGED) | **dispatch**: security (#1, UCB1 ∞, never visited)
- **expect**: 3/5 attack vectors blocked. Replay+injection blocked by hash. Poisoning partial. Fork bomb unaddressed.
- **actual**: 0/5 fully mitigated, 5/5 partial. Score 1.6/5 (32%). Bundle hash exists but never verified. merge_back.py never built. FM-10 never wired. Passive defense (dead bulletin channel) is strongest security layer.
- **diff**: Predicted 3/5 mitigated — got 0/5. Uniform partial-mitigation was NOT predicted. Passive defense > designed defense was NOT predicted. L-601 decay at 68-session timescale confirmed.
- **meta-swarm**: Human signal (SIG-25): "if domain knowledge + experts + memory + beliefs coordinated enough, tools swarm." Security audit validates this via negative: tools exist (hash gen, bulletin, colony) but aren't coordinated (no verification wiring). The coordination gap IS the security gap. Concrete target: `tools/check.sh` FM-10 guard is minimum viable wiring.
- **State**: ~644L 179P 17B 40F | L-710 | f_sec1_security_audit.py | DOMEX-SEC-S376 MERGED
- **Next**: (1) Wire Layer 1 bundle hash verification into check.sh; (2) Add max_depth to swarm_colony.py; (3) UCB1 20-session trial measurement (S385); (4) merge L-701/L-702 near-dup; (5) health check periodic

## S377c session note (DOMEX-META-S377c: epistemological state model — L-707)
- **check_mode**: objective | **lane**: DOMEX-META-S377c | **dispatch**: meta (human directive SIG-27)
- **expect**: DECAYED is largest category. SHOULD-KNOW > ACTIVE in >30% of domains. Revival rate <5%.
- **actual**: knowledge_state.py built (270 LOC). DECAYED 34.5% > MUST-KNOW 26.7% > ACTIVE 21.4% > SHOULD-KNOW 17.4%. SHOULD-KNOW > ACTIVE in 19+ domains. Revival rate 22% (92/418). "unknown" domain: 214 items, 169 DECAYED. F-META10 opened.
- **diff**: DECAYED largest CONFIRMED. SHOULD-KNOW dominance CONFIRMED. Revival rate WRONG (22% vs <5%). Domain fragmentation (100+ micro-domains from unnormalized Domain: field). MUST-KNOW count 215 unexpectedly high — tools create operational dependencies on lessons.
- **meta-swarm**: Third human signal (SIG-22→23→27) finally responded to epistemologically not operationally. Framework IS the contribution, not the tool. Operational responses to conceptual directives cause human re-signaling.
- **State**: ~637L 179P 17B 40F | L-707 | SIG-27 | F-META10 | knowledge_state.py
- **Next**: (1) normalize Domain: field; (2) integrate profiles into dispatch; (3) DECAYED→ACTIVE revival mechanism; (4) BLIND-SPOT detection; (5) re-measure S397

## S377b session note (DOMEX-GT-S377: unified dependency map — L-709)
- **check_mode**: objective | **lane**: DOMEX-GT-S377 (MERGED) | **dispatch**: graph-theory (human directive: "better dependency management")
- **expect**: Hub-spoke tools, >80% implicit frontier deps, disconnected layers.
- **actual**: 858 nodes, 1683 edges across 3 DISCONNECTED layers. Tool: orient.py=25 outgoing deps (super-hub). Frontier: 72.4% implicit (no deps), 67/145 isolated. Lesson: K_avg=2.28, 2.2% orphans. Tool density 5x lessons. Zero cross-layer edges.
- **diff**: Predicted >80% implicit — got 72.4% (better). Hub-spoke CONFIRMED. Disconnected layers CONFIRMED. Did NOT predict tool layer 5x denser than knowledge layer. Cross-layer gap was THE main finding — swarm tracks deps WITHIN layers but not ACROSS.
- **meta-swarm**: The dependency map IS the "better dependency management" the human asked for. F-DEP1 opened: add `prerequisite:` to frontiers + `answers:` to lessons = create cross-layer edges. Concrete target: frontier format needs a new field.
- **State**: ~642L 179P 17B 40F | L-709 | DOMEX-GT-S377 MERGED | F-DEP1 opened | tools/swarm_dependency_map.py
- **Next**: (1) Add prerequisite field to FRONTIER.md format; (2) orient.py 25-dep fragility extraction; (3) F-GT2 chromatic number computation; (4) re-run dependency map after 10 sessions

## S377 session note (DOMEX-META-S377: programmatic swarm cycle — L-708)
- **check_mode**: objective | **lane**: DOMEX-META-S377 (MERGED) | **dispatch**: meta (human directive)
- **expect**: swarm_cycle.py closes executor-layer gap. SENSE→PLAN→PROMPT pipeline makes session planning programmatic. 3x more specific prompts than anxiety_trigger.py.
- **actual**: Tool built (230 LOC). 5 state sources sensed (triggers, dispatch, signals, NEXT, lanes). 6 priority tiers. autoswarm.sh wired (Priority 0). Post-session MEASURE wired. Cycle log persists plans. Prompt specificity: 0→4 actionable items per session.
- **diff**: Expected 3x specificity — exceeded (0→4 items, infinite improvement). Did NOT predict sensing layer was already sufficient — gap was purely decision/execution bridge. Legacy trigger/anxiety logic (~100 lines bash) superseded by Python pipeline reading ALL state sources.
- **meta-swarm**: This session IS the directive: "programmatically swarm the swarm" = build code that automates the swarm's own decision-making. The tool applies swarm's own prioritization logic (triggers > dispatch > signals) but in code, not in AI context windows. Next iteration: use cycle log outcomes to learn which plan types produce best results (reinforcement).
- **State**: ~641L 179P 17B 39F | L-708 | DOMEX-META-S377 MERGED | swarm_cycle.py
- **Next**: (1) enable cron for autoswarm.sh (human decision); (2) cycle log → dispatch weight feedback (learn from outcomes); (3) signal_router.py to process 20 OPEN signals programmatically; (4) split-sample HMM validation (S376b follow-up); (5) change-quality-check DUE

## S376b session note (DOMEX-SP-S376: F-SP3 Viterbi burst alignment CONFIRMED — L-705)
- **check_mode**: verification | **lane**: DOMEX-SP-S376 (MERGED) | **dispatch**: stochastic-processes (#6, 40.6, DORMANT)
- **expect**: Viterbi decode recovers ≥2/3 known burst windows (S57, S186, S347) within ±5 sessions.
- **actual**: 3/3 recovered EXACTLY (not just within window). 12 burst clusters total. State distribution: quiescent 54.4%, production 9.6%, burst 36.0%. Precision 100%. S57 in S1..S69 genesis cluster, S186 in S178..S189 DOMEX-adoption cluster, S347 in S335..S352 high-concurrency cluster.
- **diff**: Predicted ≥2/3 — got 3/3. Predicted within ±5 — got EXACT hits (better). Did NOT predict 12 burst clusters or genesis mega-burst (69 sessions). Production state surprisingly narrow (9.6%) — swarm operates as switch not dial. Burst prevalence 36% vs original 18% (emission formula difference).
- **meta-swarm**: HMM parameters were fitted on 175 sessions (S370) but tested on 375 (mild train-on-test contamination). The burst recovery is binary hit/miss so contamination impact is low, but a proper validation would refit on S1-S300 and test on S301-S375. Concrete target: add `--refit` mode to `tools/f_sp3_viterbi_alignment.py` for split-sample validation.
- **State**: ~641L 179P 17B 39F | L-705 | DOMEX-SP-S376 MERGED | F-SP3 CONFIRMED
- **Next**: (1) annotate 12 burst clusters with known swarm events; (2) split-sample validation (refit S1-S300, test S301-S375); (3) proxy-K compaction (6.79% DUE); (4) paper-reswarm (15+ overdue); (5) change-quality-check (DUE)

## S375d session note (DOMEX-ECO-S375: UCB1 default activated + 20% floor — L-706)
- **check_mode**: objective | **lane**: DOMEX-ECO-S375 (MERGED) | **dispatch**: economy (#3, 43.8, DORMANT)
- **expect**: UCB1 produces Gini <0.50 in simulation. 20% floor guarantees min coverage. Simpler scoring (1 vs 12 constants).
- **actual**: UCB1 made default (was heuristic). 20% floor: 6 domains with <3 visits marked floor-protected. Forward sim: 0 meta dispatches in 20 rounds. Score spread 39.8→4.9 (87.7%). Gini 0.570→0.525 after 20 simulated rounds (-7.9%).
- **diff**: Predicted Gini <0.50 — got 0.525 (close but not reached in 20 rounds, stock effect from 542 existing visits). Floor working correctly (6 domains). Did NOT predict that simulation dispatches to domains NOT in open frontiers list (publication, coordination) — outcome_map includes resolved domains. Key: UCB1 sim confirmed 0 dispatches to meta in 20 rounds.
- **meta-swarm**: UCB1 implementation existed from prior session but wasn't default. Making it default = completing L-697 Tier 1 action. The 4 rounds of heuristic fixes (L-621/625/671/676) are now legacy code reachable via `--mode heuristic`. Concrete target: remove heuristic constants at S385 after visit Gini validation.
- **State**: ~639L 179P 17B 39F | L-706 | DOMEX-ECO-S375 MERGED | UCB1 is default dispatch mode
- **Next**: (1) Re-measure visit Gini at S385; (2) proxy-K compaction (6.79% drift); (3) paper-reswarm (15+ overdue); (4) Thompson sampling Tier 2; (5) change-quality-check (DUE)

## S374g session note (2 DOMEX lanes: FAR-S374 L-686 verified + EVO-S374 F-EVO3 RESOLVED L-704)
- **check_mode**: objective+verification | **lanes**: DOMEX-FAR-S374 (MERGED), DOMEX-EVO-S374 (MERGED)
- **FAR-S374**: F-FAR3 monoculture HHI verified. Raw r=-0.81 but partial r=-0.04 (meta confound). Prior session's uncommitted work independently verified and committed. L-686.
- **EVO-S374**: F-EVO3 RESOLVED. Cadence self-regulates: quality r=+0.40 (stable), destab +0.14→+0.09 (DECLINING), overhead +0.10→-0.05 (REVERSED). 3 epochs across 188 sessions. Tool rebuilt after S363 consolidation. L-704.
- **meta-swarm**: Orphaned uncommitted work pattern: prior session created tool + lesson + JSON but didn't commit. Inverse of commit-by-proxy (L-526). Target: `open_lane.py` should remind to commit after artifact production. Also: git_files_changed bulk approach needed (single git log vs per-session scanning).
- **State**: ~639L 179P 17B 39F | L-686 verified, L-704 | 2 lanes MERGED | F-FAR3 RESOLVED, F-EVO3 RESOLVED
- **Next**: (1) UCB1 trial + Gini re-measure; (2) paper-reswarm (15+ overdue); (3) L-701/L-702 near-dup merge; (4) F-FAR2 companion planting; (5) F-FAR1 fallow replication at n>50

## S376 session note (DOMEX-ECO-S376: UCB1 rank correlation — L-702)
- **check_mode**: objective | **lane**: DOMEX-ECO-S376 (MERGED) | **dispatch**: economy (#3, DORMANT)
- **expect**: UCB1 replaces 10+ constants. Coverage >85%. Gini <0.5.
- **actual**: Spearman rho=0.017, Kendall tau=-0.003, top-5 overlap 0/5. meta #1→#31 (n=79). security #13→#1 (n=0). Score inequality IS mechanism for visit equality. 13→1 constants.
- **diff**: Coverage/Gini not yet testable (need trial). Zero rank correlation unpredicted. Score-inequality-as-mechanism unpredicted.
- **Also**: stale DOMEX-HS-S375 closed (ABANDONED). Human signal "swarm swarm" logged (SIG-23). Concurrent S375 built UCB1 tool; this session measured it (builder→measurer natural division).
- **State**: ~636L 179P 17B 39F | L-702 | DOMEX-ECO-S376 MERGED
- **Next**: (1) UCB1 20-session trial, re-measure visit Gini; (2) merge L-701/L-702 near-dup; (3) paper-reswarm; (4) change-quality-check; (5) README snapshot

## S375c session note (DOMEX-ECO-S375: UCB1 dispatch implementation — L-701)
- **check_mode**: objective | **lane**: DOMEX-ECO-S375 (MERGED) | **dispatch**: economy (#3, 43.8, DORMANT)
- **expect**: UCB1 (c=1.414) replaces 12 heuristic constants. Score Gini decreases >30%. Coverage uniformity improves.
- **actual**: UCB1 `--mode ucb1` implemented. Score spread 39.8→4.9 (87.7% reduction). Top-10 overlap 3/10. Score Gini 0.299 > heuristic 0.178 (+68%). Concurrent S376 found rho=0.017 (zero rank correlation).
- **diff**: Predicted Score Gini decrease — WRONG direction (+68%). But this IS correct UCB1 behavior: score non-uniformity drives visit uniformity. Score spread reduction exceeded (87.7%). Did NOT predict score-visit uniformity inversion (Goodhart's Law pattern). Near-dup L-701/L-702 from concurrent independent implementation.
- **meta-swarm**: Concurrent duplication of same experiment (L-701 ≈ L-702, 50% overlap). open_lane.py should auto-claim task scope to prevent. Concrete target: wire `claim.py claim-task` into `open_lane.py` lane creation.
- **Also**: committed 7 orphaned lessons (L-693..L-699), trimmed 4 over-limit lessons, closed DOMEX-EVO-S374 (ABANDONED), state-sync.
- **State**: ~636L 179P 17B 39F | L-701 | DOMEX-ECO-S375 MERGED | 7 orphaned lessons committed
- **Next**: (1) UCB1 trial for 10 sessions (S376-S385), re-measure visit Gini; (2) merge L-701/L-702 near-dup; (3) wire claim.py into open_lane.py; (4) paper-reswarm; (5) F-META8 20-session re-measure

## S375b session note (lane triage + DOMEX-HS-S375: F-HS1 compaction deficit — L-700)
- **check_mode**: objective | **lane**: DOMEX-HS-S375 (MERGED) | **dispatch**: human-systems (DORMANT, first visit)
- **expect**: Swarm compaction deficit ~82:1 uniform. proxy-K correlates with lesson accumulation. Compaction <5% of production.
- **actual**: Three-tier operational-declarative gradient: tools 55% > principles 12.3% > lessons 2.7%. proxy-K 2.68x vs lessons 6.36x (sub-linear). F-HS1 answered: declarative knowledge resists compaction because no usage-based selection pressure.
- **diff**: Predicted ~82:1 uniform — got tier-dependent (1.8:1 to 37:1). Main finding (gradient) was NOT predicted. <5% confirmed for lessons only.
- **meta-swarm**: L-689 flagged "all metrics are endogenous" — this session's response is the HS experiment: self-applying bureaucratic theory to the swarm itself is exactly the kind of reflexive work that SHOULD use internal metrics. The finding (operational items compact, declarative don't) is directly actionable: build lesson utility scoring. Concrete target: `tools/compact.py` add `--lesson-archive` mode that scores by cite_count × recency.
- **Also**: closed 5 stale S374 lanes (DS MERGED, FIN MERGED, GAME MERGED, CACHE MERGED, IS ABANDONED). NEXT.md compacted 111→~75 lines.
- **State**: ~635L 179P 17B 39F | L-700 | DOMEX-HS-S375 MERGED | 5 lanes closed | change-quality run
- **Next**: (1) lesson utility scoring for compact.py; (2) UCB1 dispatch (L-696); (3) close_lane.py diff-tag enforcement for cal(E); (4) paper-reswarm periodic (15+ overdue); (5) STRUGGLING dispatch floor (5% min)

## S375 session note (DOMEX-META-S375: F-META5 decision calibration — L-698)
- **check_mode**: objective | **lane**: DOMEX-META-S375 (MERGED) | **dispatch**: meta (#2, 40.4)
- **expect**: Direction accuracy >60%. Surprise rate 30-50%. Calibration improving over time. cal(E) computable.
- **actual**: Direction cal(E)=0.548 (classifiable n=84/213). Magnitude median=1.02 (near-perfect). Surprise rate 16%. WRONG predictions produce 1.6x more lessons than CORRECT (63% vs 39%). MIXED = 81% surprise rate = optimal learning zone. 61% of diff fields unclassifiable.
- **diff**: Predicted >60% direction — got 54.8% (close). Predicted surprise 30-50% — got 16% (much lower). Did NOT predict direction-magnitude decoupling. Did NOT predict WRONG more productive than CORRECT. Did NOT predict MIXED = optimal learning zone. Key: cal(E)~0.55 may be approximately optimal.
- **meta-swarm**: EAD diff format is rich text but 61% unclassifiable. Specific target: `tools/close_lane.py` should enforce structured direction tags at diff start (CONFIRMED/FALSIFIED/PARTIAL/MIXED) for automated cal(E) tracking. This closes the diagnostic-to-feedback loop.
- **State**: ~628L 179P 17B 39F | L-698 | DOMEX-META-S375 MERGED | tool: f_meta5_decision_calibration.py
- **Next**: (1) close_lane.py diff-tag enforcement for automated cal(E); (2) wire cal(E) into dispatch weight (F-META5 design step 3); (3) paper-reswarm periodic (15+ overdue); (4) F-META8 re-measure at S375 (20 sessions reached); (5) STRUGGLING dispatch floor (5% min)

## S374f session note (2 DOMEX lanes: FIN-S374 L-694 + GAME-S374 L-695)
- **check_mode**: objective | **lanes**: DOMEX-FIN-S374 (MERGED), DOMEX-GAME-S374 (MERGED)
- **FIN-S374**: F-FIN1 complementarity analysis. Concurrent DOMEX sessions cross-cite at 12.9% = 17.9x random baseline (0.72%). All 7 concurrent sessions were domain-diverse. Factor-loaded diversification: shared context (14x same-session lift) + idiosyncratic domain findings. Cross-citation inversely correlates with domain count. L-694.
- **GAME-S374**: F-GAME3 citation impact. Inverted-U confirmed (n=142 frontiers). Flow zone (2-10 sessions): 1.30x global. Boredom (≤1): 1.09x. Anxiety (>15): 0.81x. Flow zone rarest (5.6%) but highest quality. Anxiety zone produces most lessons (3.5/frontier) but each less cited. L-695.
- **meta-swarm**: Session metadata parsing inconsistency discovered (14/623 lessons matched old regex). Fixed multi-format parser for both tools. Concurrent session S374 absorbed L-686-L-693 while this session ran, requiring lesson-slot collision avoidance. Both experiments are novel cross-domain applications (finance portfolio theory → knowledge production; game design flow theory → frontier difficulty).
- **State**: ~627L 179P 17B 39F | L-694, L-695 | 2 lanes MERGED
- **Next**: (1) accumulate n=20+ concurrent sessions for F-FIN1 complementarity power; (2) decompose anxiety frontiers into flow-zone sub-questions; (3) dispatch optimizer resolution-time scoring; (4) paper-reswarm periodic (14+ overdue); (5) session metadata format standardization (14/623 coverage gap)

## S374e session note (DOMEX-DS-S374: Jepsen gradient self-application — L-699)
- **check_mode**: objective | **lane**: DOMEX-DS-S374 (MERGED) | **dispatch**: distributed-systems (#1, 37.2)
- **expect**: Jepsen 4-layer architecture→determinism gradient (L-642) predicts swarm bugs. Accuracy >70%. Higher overall determinism than databases.
- **actual**: 24 swarm failures classified. 19/19 in-model accuracy (100%). Fifth infrastructure/substrate layer discovered (21% of bugs, not in Jepsen). Cliff not gradient: swarm determinism binary (100%/0%) vs Jepsen smooth decay. Threshold behavior at N=3/5/8. No Byzantine faults. Overall determinism 50-67% LOWER than Jepsen 60-80%.
- **diff**: Gradient transfer CONFIRMED. Accuracy exceeded (79-100% vs >70%). Overall determinism WRONG direction (lower, not higher) — infrastructure layer drags average down. Cliff behavior, fifth layer, and threshold activation were all unpredicted. Experienced L-602 (lesson-slot contention, 2 collisions) during experiment — live demonstration.
- **meta-swarm**: Human S374 signal "swarm has to know swarm state more" interpreted as self-knowledge directive. Applied via cross-domain experiment: DS expertise used to classify swarm itself. The experiment demonstrates the human's point — knowing the swarm's own failure taxonomy IS improved self-state-awareness. Concrete target: build auto-classifier that tags new bugs by architecture layer (like contract_check.py but for distributed failures).
- **State**: ~629L 179P 17B 39F | L-699 | DOMEX-DS-S374 MERGED
- **Next**: (1) Test gradient on third substrate (K8s, CI/CD); (2) auto-classifier tool for swarm bugs; (3) connect N=3/5/8 thresholds to F-SP2 throughput ceiling; (4) ISO-21 filing if third substrate holds; (5) paper-reswarm periodic (13+ overdue)

## S375 session note (swarm profiler tool — L-692)
- **check_mode**: objective | **task**: "profiler for swarm"
- **expect**: Unified profiling reveals tool bottlenecks invisible to per-tool timing. orient.py is dominant cost.
- **actual**: Built tools/swarm_profiler.py. 18 operations profiled. Total 56.2s. task_order.py (14.7s) is #1 bottleneck, NOT orient.py (11.0s). validate_beliefs.py (10.9s) is #2. Tool execution = 79% of overhead. Filesystem = 0.05%.
- **diff**: orient.py was NOT dominant (prediction wrong) — it's third after task_order.py and validate_beliefs.py. Bottleneck migration: L-637 + L-688 optimized orient, shifting bottleneck to unoptimized tools that were never measured. Quick mode (7.4s) viable for fast-path.
- **meta-swarm**: The profiler IS the meta-swarm reflection — it profiles the swarm's own tooling. Concrete target: task_order.py (14.7s→<5s via HEAD caching), validate_beliefs.py (10.9s→<5s). History tracking enables regression detection.
- **State**: ~626L 179P 17B 39F | L-692 | experiment: swarm-profiler-baseline-s375.json
- **Next**: (1) cache task_order.py dispatch call + LANES parse; (2) cache validate_beliefs.py cross-refs; (3) re-profile after optimizations; (4) wire --quick into orient.py preamble for fast orient

## S374d session note (adversarial blind-spot audit — L-689)
- **check_mode**: assumption | **human directive**: "focus swarm on what human might have fundamentally missed"
- **expect**: Internal metrics hide structural blind spots. Adversarial lesson surfaces ≥3 things 374 sessions missed. Finding = framing-level, not metric-level.
- **actual**: 7 findings (3 human, 4 swarm, 1 shared). Core: PHIL-2+15+P14 = unfalsifiable tautology; 0/28+ DROPPED = confirmation machine; 0 external outputs in 374s; human language colonized by swarm vocabulary (SIG-22). 3 PHIL challenges filed.
- **diff**: Expected ≥3, got 7. Expected framing-level — confirmed. Did NOT predict language colonization finding.
- **meta-swarm**: Asking the swarm to audit itself IS the self-referential loop this audit identifies. Corrective requires EXTERNAL input (T1: competition, T2: outside expert, T3: belief falsification). Concrete target: F-COMP1 is 45+ sessions stale and the only path to external grounding.
- **State**: 626L 179P 17B 39F | L-689 | 3 PHIL challenges filed
- **Next**: (1) F-COMP1 execution (BLOCKING); (2) T3 belief falsification by S400; (3) F-EVAL1 Truthful; (4) frontier→behavioral-change audit

## S374c session note (DOMEX-CACHE-S374: HEAD-keyed caching — L-688)
- **check_mode**: objective | **lane**: DOMEX-CACHE-S374 (MERGED) | **dispatch**: meta
- **expect**: HEAD-keyed cache saves >50% orient.py time on warm runs
- **actual**: orient.py 11.9s→4.4s (63% faster). maintenance.py 7.0s→0.5s (93% faster). 33/36 checks cacheable. Output IDENTICAL cold/warm. Cache: workspace/cache/head_cache.json (~54KB, gitignored).
- **diff**: Expected >50%, got 63% — exceeded target. Did NOT predict check_uncommitted would dominate warm floor at 2.4s (WSL git status). Also did NOT predict that runtime_portability (1.0s) is cacheable (env doesn't change within session).
- **meta-swarm**: Profiling before optimizing was critical — maintenance.py was 67% of orient.py, but within maintenance, check_uncommitted (2.4s, live) vs check_lessons (0.87s, cacheable) have different cache profiles. The architecture cleanly separates HEAD-dependent from live checks. Concrete next: inline maintenance.py into orient.py to eliminate subprocess overhead (0.3-0.5s).
- **State**: 622L 179P 17B 39F | L-688 | DOMEX-CACHE-S374 MERGED
- **Next**: (1) inline maintenance to eliminate subprocess overhead; (2) cache git status with short TTL for intra-task reuse; (3) profile at N>=5 concurrent — cache contention?

## S374b session note (task coordination: claim.py + task_order.py + orient.py — L-687)
- **check_mode**: coordination | **human directive**: "better task assignment coordination"
- **expect**: Three gaps at N>=3: no task-level claiming, identical recommendations, no concurrent visibility. Building all three enables automatic task divergence.
- **actual**: All three built and tested. claim.py: 6 new commands (claim-task/check-task/release-task/list-tasks/heartbeat/sessions) + 2 importable functions. task_order.py: fingerprint generation, claim-aware filtering (-100 score for claimed), --claim-top auto-claim. orient.py: concurrent activity section showing sessions + task claims.
- **diff**: No prediction errors — gaps were structural and obvious. Design choice: 600s TTL for tasks (5x file claims) was natural from task duration analysis.
- **meta-swarm**: The three coordination layers (file→task→session) mirror the three concurrency failure modes (edit collision→work duplication→invisible concurrency). This is an isomorphism with defense-in-depth (security domain). Concrete next: measure actual duplication rate before/after at N>=3 to validate.
- **State**: 622L 179P 17B 39F | L-687 | experiment: task-coordination-s374.json
- **Next**: (1) measure duplication reduction at N>=3 after 10 sessions; (2) wire heartbeat into orient.py auto-call; (3) add claim-task to open_lane.py for automatic dispatch claiming

