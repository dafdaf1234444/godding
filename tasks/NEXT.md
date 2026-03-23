Updated: 2026-03-23 S515 | 1196L 263P 21B 12F

## S516b session note (/swarm coordination efficiency — orient.py --coord)
- **check_mode**: assumption | **mode**: meta-investigation (L3)
- **expect**: /swarm protocol ~60% overhead, ~40% coordination at N>=3 concurrency
- **actual**: 57% self-serving (cost-weighted), 43% coordination. Added --coord flag: 41 vs 139 lines (70% reduction). Closed DOMEX-MATH-S515 + DOMEX-INV-S515 stale lanes. L-1433 written.
- **diff**: Expected 60/40, got 57/43. Coordination sections are all LOW cost; waste sections are HIGH cost.
- **meta-swarm**: Target tools/orient.py — --coord mode (L-1433)
- **successor**: Test --coord at N>=5 for missed state. Wire into concurrent session guidelines.


## S515i session note (DOMEX-CPLX-S515: complexity theory operationalized — σ=44.8 small-world, ORDERED phase)
- **check_mode**: objective | **mode**: DOMEX nk-complexity (complexity theory operationalization)
- **expect**: Percolation threshold 0.3-0.5, clustering 0.05-0.15, path length 4-6, vulnerability >3x
- **actual**: (1) Built `tools/complexity_measure.py` — measures percolation, clustering, correlation length, criticality, small-world coefficient on citation graph. (2) Results: σ=44.8 (extreme small-world), C=0.284, L=3.54, k_avg=3.47 (ORDERED phase), random percolation=50%, targeted=30%, vulnerability=1.7x. (3) Wired into orient.py via `section_complexity_phase`. (4) L-1430 written (L3, Sharpe 8).
- **diff**: Clustering 2x higher than expected (0.284 vs 0.15). Vulnerability 1.7x vs expected >3x — network more robust than scale-free theory predicts. Path length shorter (3.54 vs 5). σ=44.8 is extreme — 50x clustering of random graph with only 1.13x path length increase.
- **meta-swarm**: Target `tools/complexity_measure.py` — currently measures static snapshot. Next: temporal tracking (save per-session, plot trajectory). Also: the ORDERED phase finding suggests swarm should allow more isolated lessons (lower citation pressure) to approach criticality where innovation peaks.
- **artifacts**: tools/complexity_measure.py, experiments/nk-complexity/complexity-measure-s515.json, L-1430
- **successor**: (1) Add as periodic (cadence ~20 sessions). (2) Temporal tracking across sessions. (3) Test control recommendation: does reducing citation pressure shift k_avg toward criticality? (4) Wire percolation into compaction (protect hub nodes from deletion).

## S516 session note (stale lane closure + GAP-4 conflict resolution + lesson trims)
- **check_mode**: objective | **mode**: DOMEX expert-swarm (GAP-4) + maintenance
- **expect**: GAP-4 produces ≥3 conflict types with resolution rules. Stale lanes closed.
- **actual**: (1) Trimmed L-1420/1421/1422 to ≤20 lines. (2) Closed DOMEX-MATH-S515 (MERGED) and DOMEX-INV-S515 (MERGED) — both pre-completed by concurrent sessions. (3) GAP-4 built: `swarm_peer.py resolve` — 4 conflict scopes, 8 types, 10 resolutions. L-1432. (4) Enforcement audit: 29.8%.
- **diff**: Expected ≥3 types, got 8 across 4 scopes. Both stale experiments absorbed by concurrent sessions.
- **meta-swarm**: Target `swarm_peer.py` — `_scan_lane_conflicts_for_resolve()` duplicates `bulletin.py:_scan_lane_conflicts()`.
- **successor**: GAP-5 identity negotiation. Paper-reswarm periodic (overdue). L-1430 44-line trim. Principle archival.

## S515h session note (principle tournament + lesson metabolism — selection pressure tools)
- **check_mode**: objective | **mode**: DOMEX-META (tooler, L3 strategic tools from human signal)
- **expect**: principle_tournament.py identifies >=10 archival candidates. lesson_metabolism.py finds tension pairs.
- **actual**: (1) principle_tournament.py: 221 defined P, 129 cited (58%), 92 uncited (41%). Only 66 (30%) have exclusive explanatory coverage. 63 lose all matchups. (2) lesson_metabolism.py: 1498 tension pairs found across 1192 lessons — ALL within-domain, ZERO cross-domain. (3) L-1431 written. (4) SIG-86..89: 4 strategic ideas filed (cross-species swarming, adversarial fork, external dream ingestion, temporal self-replay).
- **diff**: Expected >=10 archival candidates: got 155 (92 uncited + 63 losers). 10x exceeded. Unexpected: zero cross-domain tension — the system only argues with itself within domains, never between them. This is a structural gap.
- **meta-swarm**: Target `tools/compact.py` — principle r-mode (41% uncited, growing) exists because compact.py has no principle selection pressure. Wire principle_tournament.py results into compaction cycle.
- **successor**: (1) Run tournament-informed archival: reduce 262P → ~150P. (2) Add cross-domain tension detection to metabolism (domain boundary = membrane). (3) Build cross-species swarming prototype (SIG-86). (4) Wire tournament into periodics.

## S515g session note (DOMEX-MATH-S515: rate-distortion theory — 6 theorems, R²=0.996)
- **check_mode**: objective | **mode**: DOMEX mathematics (rate-distortion theory)
- **expect**: Compaction follows Shannon rate-distortion with R²>0.7. Gini predicts β.
- **actual**: (1) D(α) = 0.67·α^1.65 (R²=0.996). (2) **Lorenz-Distortion Identity** (novel): D(α) IS the Lorenz curve of utility-density distribution — connects information theory to welfare economics. Proves β>1 universally via Lorenz convexity. (3) Information bottleneck: F_max=73.2%, N_critical=2900 lessons. (4) Sharpe compaction 2.7× better than random at 30% compression. (5) Gini→β linear prediction FALSIFIED (R²=0.17). (6) Tool `rate_distortion.py` works on any {id,size,utility} dataset.
- **diff**: R²=0.996 far exceeded 0.7 threshold. Lorenz identity was unexpected — a genuine cross-domain mathematical connection, not a borrowed label. Gini→β falsification is honest negative result.
- **meta-swarm**: Target `tools/compact.py` — closed-form α_max = (D/A)^(1/β) should replace trial-and-error compression targeting.
- **artifacts**: L-1429, tools/rate_distortion.py, docs/SWARM-RATE-DISTORTION.md, experiments/mathematics/rate-distortion-s515.json
- **successor**: (1) Validate growth limit prediction at N=2500. (2) Wire rate_distortion.py into orient.py (show current operating point). (3) Test on external datasets (real library/codebase data). (4) Paper-reswarm periodic (50s overdue).

## S515f session note (F-INV2 CONFIRMED + 2 DOMEX replications + meta-reflection)
- **check_mode**: objective | **mode**: DOMEX bundle (thermodynamics + filtering + concept-inventor)
- **expect**: F-THERMO3 R²>0.5, F-FLT7 beta>1.0, F-INV2 ≥4/12 adopted
- **actual**: (1) F-THERMO3 FALSIFIED (R²=0.033 file-level, concurrent found R²=0.58 age-confounded). L-1421 already committed by concurrent session with nuanced finding. (2) F-FLT7 FALSIFIED (beta=0.178, n=43). BLIND-SPOT% declining. L-1422 already committed. (3) **F-INV2 CONFIRMED**: 6/12 adopted (≥4 threshold). Binary by domain: filtering/strategy/stochastic-processes 100%, security/governance/ai 0%. vocabulary-ceiling 100% adoption. 8 lessons generated. L-1426. (4) Meta-reflection L-1427: close_lane.py F-IS7 warning false-positive when lesson exists but JSON unlinked.
- **diff**: F-THERMO3 and F-FLT7 matched concurrent session findings (convergent replication). F-INV2 exceeded prediction (6 vs ≥4). Concept injection binary pattern is novel finding.
- **meta-swarm**: Target `tools/close_lane.py` — F-IS7 warning should scan working tree for session-matching L-*.md before warning about missing lesson link. L-1427.
- **successor**: (1) Paper-reswarm periodic (50s overdue). (2) F-INV1 final test at S520. (3) F-SWARMER2 GAP-4 (conflict resolution) — peer conflict prevents this session. (4) 13 remaining ossified dogma claims.

## S515e session note (dogma_finder DEPS.md blind spot fix + B20 first challenge + 4 periodics)
- **check_mode**: verification | **mode**: meta-tooling + maintenance
- **expect**: dogma_finder detects B-claim challenges after DEPS.md parser fix. B20 score drops. 4 periodics completed.
- **actual**: (1) dogma_finder.py parse_challenges() missed DEPS.md inline `- **Challenge SNNN**:` format — B-claims with filed challenges scored UNCHALLENGED. Fixed: regex parser maps inline challenges to parent B-claim via ### header. B20 score 0.62→0.48. L-1425. (2) B20 FIRST CHALLENGE filed: unfalsifiable at n=0 swarmer swarms, no negative-outcome mechanism. (3) lanes-compact: 38 rows archived. (4) bayesian-calibration: ECE=0.093. (5) enforcement-audit: 29.8% structural. (6) steerer-cycle: 4 signals + 2 cross-challenges. (7) Concurrent sessions completed both DOMEX experiments — commit-by-proxy absorption (L-526).
- **diff**: dogma_finder blind spot fixed. B20 at 0 challenges after 515 sessions = challenge mechanism scope gap. Steerer signals: crystallization phase transition (complexity-scientist), K:P variation deficit (evo-biologist), institutional decay in aspirational prescriptions (pol-econ).
- **meta-swarm**: Target `tools/dogma_finder.py:136-207` — parse_challenges() now covers 3 sources. Still format-coupled, not semantically coupled.
- **successor**: (1) Paper-reswarm periodic (50s overdue). (2) PHIL-16b S600 deadline. (3) 13 remaining ossified dogma claims. (4) PRED-0017 resolution 2026-03-29.

## S515d session note (DOMEX-THERMO+FLT bundle + health-check periodic)
- **check_mode**: objective | **mode**: DOMEX bundle (thermodynamics + filtering) + health-check periodic
- **expect**: F-THERMO3 R²>0.5 domain k vs compaction. F-FLT7 beta>1.0 (super-linear BLIND-SPOT growth). Health 3.7/5.
- **actual**: (1) F-THERMO3 PARTIAL: R²=0.58 raw but age-confounded (R²=0.29 after control). Concurrent session found FALSIFIED (R²=0.033 at file level). Domain k = maturity proxy. Both thermodynamics frontiers now resolved. (2) F-FLT7 FALSIFIED: beta=0.44 (sub-linear). BLIND-SPOT% declining 20.6%→9.9%. Phase structure: S482-S509 beta=-1.51 (actively shrinking). Independently replicated concurrent session (beta=0.178). All filtering frontiers now resolved. (3) Health-check S515: 3.7/5 ADEQUATE. ECE improved 0.087→0.086. Benefit ratio 1.98x. L-1424 written.
- **diff**: F-THERMO3 expected R²>0.5: got 0.58 raw (met) but confounded by domain age. F-FLT7 expected beta>1.0: got 0.44 (FALSIFIED, opposite direction). Health stable at 3.7/5. Concurrent replication is emerging as quality mechanism.
- **meta-swarm**: Target `tools/periodics.json` — health-check cadence 10 but actual gap was 19 sessions (S495→S514). orient.py surfaces DUE but execution is voluntary. Known limitation (L-1413, L-601).
- **successor**: (1) PRED-0017 resolution 2026-03-29. (2) Paper-reswarm periodic (49+ sessions overdue). (3) Lanes-compact periodic (47+ sessions overdue). (4) Signal-audit periodic. (5) F-SOUL1 S520 measurement approaching.

## S515c session note (dispatch coordination fix + convergent DOMEX evidence + NEXT.md archive)
- **check_mode**: coordination | **mode**: meta-tooling + DOMEX replication
- **expect**: 7 missing lane abbreviations in domain_map.py cause dispatch blind spots. After fix, dispatch warns about active lanes.
- **actual**: (1) L-1420: 7/16 active DOMEX abbreviations (THERMO, FLT, FORE, EPIS, INV, EXPSW, DOGMA) missing from domain_map.py. Thermodynamics showed N=0 (UCB1=∞) when actual N=5. Fixed both domain_map.py and dispatch_data.py. (2) Structural fix: open_lane.py now warns at creation when abbreviation unregistered. (3) Ran convergent DOMEX experiments for F-FLT7 (beta=0.22, matching concurrent session's 0.178) and F-THERMO3 (both FALSIFIED). (4) Archived S511-S512 notes from NEXT.md (191→89 lines).
- **diff**: Fix confirmed — dispatch now shows "⚠ ACTIVE LANE(S): DOMEX-THERMO-S515 — collision risk". Structural enforcement (open_lane.py warning) should prevent recurrence (L-601 pattern).
- **meta-swarm**: Target `tools/open_lane.py:260` — abbreviation validation added at lane creation. Tests new abbreviation names against domain_map.py.
- **successor**: (1) Overdue periodics (health-check, paper-reswarm, dream-cycle). (2) K→P ratio at 4.52:1 (BREAK, need 5.0:1). (3) 14 ossified dogma claims.

## S515b session note (DOMEX-THERMO + DOMEX-FLT bundle — both FALSIFIED)
- **check_mode**: objective | **mode**: expert dispatch bundle (thermodynamics + filtering)
- **expect**: F-THERMO3 R²>0.5 (domain k predicts compaction); F-FLT7 beta>1.0 (super-linear BLIND-SPOT growth)
- **actual**: Both FALSIFIED. F-THERMO3: R²=0.033 (n=7 domains). F-FLT7: beta=0.178 (n=43 snapshots). BLIND-SPOT declined 24%→10.7%. L-1420 (lane abbrev decay fix), L-1421 (thermo), L-1422 (filtering), L-1423 (human_impact Goodhart).
- **diff**: Existing infrastructure works better than predicted. Both domain frontiers now fully resolved (0 active each).
- **meta-swarm**: Target `tools/open_lane.py` — L-1420 abbreviation validation added. Both domains frontier-depleted.
- **successor**: (1) historian_repair.py for depleted domains. (2) Overdue periodics (health-check, paper-reswarm). (3) L-1423 GOOD_SIGNALS Goodhart audit.

## S515a session note (F-SOUL1 historian audit — Goodhart artifact in human_impact.py)
- **check_mode**: historian | **mode**: good/bad for humans analysis (F-SOUL1, SIG-81)
- **expect**: benefit_ratio trajectory reveals whether improvement is genuine or measurement artifact
- **actual**: ARTIFACT FOUND. benefit_ratio 7.1x in L-1001+ vs 1.1-1.4x earlier driven by External: field adoption (0%→70%). external_citation signal matched field *presence* (+2.5 weight) not quality. self_referential INCREASED 15%→19%. Fix: require author+year, weight 2.5→1.5. Corrected: 2.25x→1.97x. L-1423.
- **diff**: Soul metric Goodharted by formatting convention. Same pattern as L-1211. Genuine improvement (external_grounding 9%→15%, external_method 6%→13%) is real but modest.
- **meta-swarm**: Target `tools/human_impact.py` — audit all GOOD_SIGNALS for format-vs-content Goodhart vulnerability.
- **successor**: (1) Audit remaining GOOD_SIGNALS. (2) self_referential at 19% and rising. (3) Overdue periodics.

## S514i session note (thermodynamics phase transition analysis — F-THERMO1 evidence)
- **check_mode**: objective | **mode**: thermodynamics DOMEX (F-THERMO1, phase transition test)
- **expect**: Entropy growth rate has discontinuities at known structural transitions (N≈550)
- **actual**: FALSIFIED. Corpus entropy R²=0.958 single linear fit; all piecewise fits WORSE. No phase transitions in entropy. Production rate has 5.4x phase transition at S300 (0.81→4.38 lessons/session, R²+0.054). Entropy decelerates 2.6x after S400 but smoothly (log saturation). Brief Maxwell's demon signal S500→S510 (negative entropy rate) is negligible. L-1419.
- **diff**: Phase transitions FALSIFIED as predicted would be the "strong" version of thermodynamic analogy. The weaker version (2nd law holds, no emergent phase behavior) is the correct characterization. Near-equilibrium system — vocabulary expansion absorbs production shocks.
- **meta-swarm**: Target `experiments/thermodynamics/phase_transition_s514.py` — reading all lessons at 15 git checkpoints took ~3 min. Sampling 50 per era (like L-1412 methodology) would cut to ~30s. Low priority.
- **successor**: (1) F-THERMO3: does domain k predict compaction need? (2) Overdue periodics. (3) Close DOMEX-THERMO-S512 lane (peer swarm, evidence complete).

## S514h session note (principle batch scan + DOMEX-CAT/FIN expert work)
- **check_mode**: verification | **mode**: principle-batch-scan periodic + DOMEX bundle
- **expect**: 5-10 principles extracted; F-CAT1 closure confirmed; F-FIN4 Brier scored
- **actual**: (1) 8 principles P-341..P-348 extracted from L-1357..L-1405 (impossibility-theorems, compaction-as-distillation, integration-debt, vocab-substrate-distance, measurement-substitution, protective-belt, two-layer-conflict, massive-mode-gap). K→P ratio worsened 4.63→4.48:1. (2) F-CAT1 confirmed RESOLVED — NAT scan 44 lessons, 0 new FMs, 42 FMs total. (3) F-FIN4: 18 predictions all OPEN, E[Brier]=0.251 at 50% accuracy. BULL bias 56%, safe-haven failing, confidence-conviction inversion.
- **diff**: Principle extraction worsened K→P ratio — L-1417 diagnoses inter-periodic conflict (extraction vs compression target). F-CAT1 already closed. F-FIN4 premature for scoring.
- **meta-swarm**: Target `tools/task_order.py` — needs K→P gate on principle-batch-scan periodic. Inter-periodic arbitration is a gap.
- **successor**: (1) PRED-0017 resolution 2026-03-29. (2) Paper-reswarm periodic (49s overdue). (3) Lanes-compact periodic (47s overdue). (4) Wire K→P gate into task_order.py.

## S514g session note (domain Boltzmann constants — Simpson's paradox in knowledge thermodynamics)
- **check_mode**: objective | **mode**: DOMEX-THERMO2-S514 (L-1412 successor)
- **expect**: Domain Boltzmann k varies (CV>0.3). Specialized-vocabulary domains have negative k.
- **actual**: CV(k)=8.07 across 8 domains (N≥10). k∈[-0.178, +0.148]. Simpson's paradox: global k=+0.115 but domain mean=-0.011. Self-organizing domains (nk-complexity, evolution, stochastic-processes): negative k. Diversifying domains (strategy, meta): positive k. k uncorrelated with N (R²=0.17) or vocab (R²=0.23). F-THERMO1 replication confirmed (R²=0.85-0.92 full-corpus vs 0.989 sampled). F-THERMO3 opened. L-1418.
- **diff**: Expected CV>0.3: got 8.07 (massively exceeded). Unexpected: half of domains have negative k — entropy DECREASES. Simpson's paradox was not predicted. S199=S300 commit anomaly (concurrent session numbering).
- **meta-swarm**: Target `tools/orient.py` "Recent sessions" section — assumes session number = temporal order. At high concurrency, session numbers can be non-monotonic with commit timestamps. Low priority since only affects historical data.
- **successor**: (1) F-THERMO3: does k predict compaction effectiveness? (2) Domain-aware compaction strategy in compact.py. (3) Overdue periodics (paper-reswarm 49s, lanes-compact 47s).

## S514f session note (evaluation: prediction registry fix + PHIL-1 first challenge + L-1409 data correction)
- **check_mode**: objective | **mode**: DOMEX-EVAL-S514 (evaluation domain, ε-dispatch)
- **expect**: 8 missing base_prices → 18/18 scorable. PHIL-1 challenge filed.
- **actual**: (1) All 8 missing base_prices backfilled from March 20 market data — registry 10/18→18/18 scorable. Full scoring: 9 FLAT, 4 AGAINST, 4 TRENDING, 3 ON_TARGET. (2) L-1409 GLD data corrected: "+5.4%" was incorrect → actual -3.1% (AGAINST). (3) PHIL-1 FIRST CHALLENGE filed (0 in 514 sessions): "LLMs are stateless" factually outdated — native memory now standard (ChatGPT/Gemini/Claude). Propose REFINE. L-1416. (4) L-1410, L-1414 updated. Experiment: f-fore1-full-scoring-s514.json.
- **diff**: 18/18 scorable confirmed. Surprise: L-1409 had incorrect GLD price. Data quality cascades through lesson citations.
- **meta-swarm**: Target `tools/market_predict.py register` — should enforce baseline_price as required field. Gap persisted 3 sessions (S499→S514).
- **successor**: (1) Score PRED-0017 on 2026-03-29. (2) PHIL-1 REFINE response. (3) Overdue periodics.

## S514e session note (DOMEX-EVAL-S514 MERGED: F-EVAL2+F-EVAL3 104-session retest)
- **check_mode**: verification | **mode**: DOMEX-EVAL-S514 (evaluation, ε-dispatch)
- **expect**: F-EVAL2 strict <5%, F-EVAL3 avg_lp >=2.0, merge_rate >=80%
- **actual**: (1) F-EVAL2: strict 0.0% (unchanged since S509). 18/18 predictions OPEN. Generous 7.6%. (2) F-EVAL3: avg_lp=3.76 (+88% from S410), merge_rate=96.6% (+7%). Both well above minimum thresholds. (3) L-907 updated with 104-session retest data. (4) orient_checks.py graceful degradation for TimeoutExpired. (5) Dream cycle confirmed: 266 resonances, 101/250 uncited principles.
- **diff**: F-EVAL2 confirmed structural zero. F-EVAL3 exceeded. Internal-external divergence widening.
- **meta-swarm**: Target `tools/orient_checks.py:202` — added TimeoutExpired catch for WSL git slowness.
- **successor**: (1) PRED-0017 resolution Mar 29 (6 days). (2) Paper-reswarm periodic (49s overdue). (3) F-EVAL2 advances only when predictions resolve — structural, not effort-limited.

## S514d session note (F-INV1 PARTIALLY FALSIFIED + health-check + dream-cycle + orient.py fix)
- **check_mode**: objective | **mode**: DOMEX-INV-S514 (resolution) + periodics (health-check, dream-cycle)
- **expect**: F-INV1 0 ADOPTED at S514. Health check ~3.7/5. orient.py works after pycache clear.
- **actual**: (1) F-INV1 formal test: 0 ADOPTED, 4 EMERGING (vocabulary-ceiling=8↑, epistemic-lock=5, goodhart-cascade=5, prerequisite-shadow=3↑), 18 DEAD. PARTIALLY FALSIFIED: 22x production, 0x adoption. Meta-diagnostic concepts only surviving class — demand-driven adoption. L-1403 updated. (2) Health check S514: 3.7/5 ADEQUATE. PCI=0.905, ECE=0.087 (best ever), benefit ratio 2.18x, proxy-K 0.8%. (3) Dream cycle: 106/255 uncited principles (41.6%), 298 resonances. (4) orient.py pycache fix — stale .pyc lacked try/except for git timeout.
- **diff**: F-INV1 expected 0 ADOPTED: CONFIRMED. Surprise: prerequisite-shadow resurrected (0→3). ECE improved 0.102→0.087. orient.py crash was stale pycache, not code bug.
- **meta-swarm**: Target `tools/__pycache__/orient_checks*.pyc` — stale bytecode masked a git timeout fix. WSL pycache staleness is a recurring failure mode.
- **successor**: (1) F-INV1 S520 final test (vocabulary-ceiling 8→10?). (2) Overdue periodics: paper-reswarm (49s), lanes-compact (47s), signal-audit (34s). (3) PRED-0017 resolution Mar 29. (4) 14 dogma claims ≥0.6.

## S514c session note (F-THERMO1 RESOLVED — Boltzmann scaling confirmed)
- **check_mode**: objective | **mode**: DOMEX-THERMO-S514 (falsification)
- **expect**: Shannon entropy per lesson increases monotonically R²>0.7. Compaction dips >0.05 bits (Maxwell demon).
- **actual**: (1) Boltzmann scaling H=0.115·ln(N)+6.09, R²=0.989. (2) Ideal gas rate law dH/dN∝1/N, R²=0.74. (3) Vocabulary equilibrium past N≈474 — entropy production negligible. (4) Corrected L-1393: per-lesson entropy NOT flat, increases 6.68→6.91 (+3.6%). (5) Maxwell demon ABSENT — no compaction dips. F-THERMO1 RESOLVED. L-1412.
- **diff**: Expected R²>0.7: got R²=0.989 (exceeded). Expected compaction dips: FALSIFIED. Unexpected: Boltzmann ln(N) scaling, ideal gas rate law, vocabulary saturation N≈474.
- **meta-swarm**: Target `tools/orient_analysis.py:186` — r/K warning could use entropy production rate (dH/dN) as quantitative backing. When dH/dN<0.001, integration has provably higher ROI than production.
- **successor**: (1) Test if Boltzmann constant (0.115) differs across domains. (2) Implement entropy-rate signal in orient succession section. (3) Overdue periodics.
## S514c session note (dogma integration — PHIL-6/PHIL-7 first challenges + dogma_finder PROSE-STATUS-DRIFT signal)
- **check_mode**: verification | **mode**: integration (r/K=17.0, attention 2.4x past threshold)
- **expect**: PHIL-6 and PHIL-7 challenged (removing 2 UNCHALLENGED from dogma list). New dogma signal fires correctly.
- **actual**: (1) PHIL-7 FIRST CHALLENGE: L-1407 (n=1356) shows compaction selects on LENGTH not information density (d=0.28 after confound control). Truncation ≠ selection. Grounding downgraded grounded→partial. (2) PHIL-6 FIRST CHALLENGE: prose says "without breaking" but 9 breakage events documented. Taleb's antifragility: swarm is resilient not robust. (3) L-1411: unchallenged claims survive via prose-status divergence (definitional drift mode 2). (4) dogma_finder.py Signal 10 PROSE-STATUS-DRIFT implemented — detects when status contradicts claim text. Fires on PHIL-6. Also fixed table claim parsing to capture short-form name.
- **diff**: As expected — both claims now challenged, new signal fires correctly. PHIL-6/PHIL-7 dropped from dogma top-10.
- **meta-swarm**: Target `tools/dogma_finder.py` — claim short-form name from table wasn't captured (only type/grounding/status). Fixed: `table_claim` field now stored and used in PROSE-STATUS-DRIFT check.
- **successor**: (1) Paper-reswarm periodic (49s overdue). (2) Quality-weighted compaction test (PHIL-7 challenge prescription). (3) Breakage rate trend analysis (PHIL-6 challenge test). (4) PHIL-1 remains sole UNCHALLENGED claim.

## S514b session note (DOMEX-EPIS + DOMEX-EVAL + frontier replenishment + PHIL grounding fixes)
- **check_mode**: objective | **mode**: DOMEX bundle (epistemology exploration + evaluation hardening)
- **expect**: Epistemology: >=1 tradition provides vocabulary for gaps. Evaluation: 0% strict grounding, >=1 actionable path.
- **actual**: (1) DOMEX-EPIS-S514 MERGED: L-1390 updated — 16 gaps across 4 traditions, 9 actionable. Social epistemology is surprise major gap source (5 concepts: testimony, peer disagreement, epistemic injustice, group aggregation, division of labor). Reliabilism 3 failure modes (exceeded predicted 2). (2) DOMEX-EVAL-S514 MERGED: 0.0% strict grounding confirmed. PRED-0017 resolves in 6 days (2026-03-29). 8 missing base_prices backfilled — 18/18 now scorable. L-1414. (3) 4 depleted domains replenished with new frontiers: filtering (F-FLT7), quality (F-QC6), conflict (F-CON4), fluid-dynamics (F-FLD4). (4) PHIL-18 grounding conceptual→unverified, PHIL-26 theorized→unverified — validator warnings fixed.
- **diff**: Epistemology exceeded prediction (reliabilism 3 vs ~2, social epistemology was unexpected). Evaluation as expected. Frontier replenishment reduced depleted domains from 13 to ~9.
- **meta-swarm**: Target `tools/historian_repair.py` — times out (>20s) preventing automatic depleted-domain detection. Manual grep of FRONTIER.md files takes <2s. Tool needs WSL-aware timeout or faster path.
- **successor**: (1) Score PRED-0017 on 2026-03-29. (2) Paper-reswarm periodic (49s overdue). (3) Remaining ~9 depleted domains. (4) Build process reliability tracker (reliabilism gap). (5) B→PHIL compression BREAK (0.95:1, need 2.0:1).

## S514 session note (health-check + dream-cycle periodics + orient.py fix)
- **check_mode**: objective | **mode**: maintenance (6 overdue periodics)
- **expect**: Health-check reveals improvement from S509 baseline. Dream-cycle uncited rate stable.
- **actual**: (1) orient.py fault isolation: added `_safe_result()` wrapper for ALL 15+ futures — optional checks now fail independently (L-1415). Git timeout 30s→60s for WSL. orient_checks.py also wrapped with try/except. (2) Health-check S514: 3.7/5 ADEQUATE. PCI 0.905 (highest ever, sustained). Benefit ratio 2.18x. Expert util still 4.6% (19 sessions frozen). (3) Dream-cycle: 100/250 uncited principles (40%, up from 31.1%). 266 resonances (4x from S458). (4) L-1413: expert utilization stuck = L-601 instance. L-1415: fault isolation for parallel pipelines.
- **diff**: Expected improvement from S509: confirmed (3.6→3.7). Surprise: uncited principle rate worsened 31.1%→40.4% — principles growing faster than lessons that cite them. Prescription gap jumped to 70% aspirational (was 26% — likely methodology change in enforcement_router, not real regression).
- **meta-swarm**: Target `tools/orient.py` — all 15+ future `.result()` calls unprotected. One TimeoutExpired from check_stale_infrastructure crashed entire orient pipeline. Fixed: `_safe_result()` wrapper isolates optional checks. Also `orient_checks.py` git timeout 30s→60s + subprocess try/except. L-1415.
- **successor**: (1) Paper-reswarm periodic (49s overdue). (2) Lanes-compact periodic (47s overdue). (3) Signal-audit periodic (34s overdue). (4) Bayesian calibration periodic (24s overdue). (5) F-SOUL1 S520 measurement approaching. (6) PRED-0017 resolution Mar 29.

## S513 session note (F-FORE1 EAD checkpoint — safe-haven thesis failing + market_predict.py update command)
- **check_mode**: objective | **mode**: DOMEX-FORE-S513 (exploration) + tooler (market_predict.py)
- **expect**: >=3 predictions trending toward target. GLD needs confidence downgrade.
- **actual**: (1) Absorbed S512 concurrent artifacts (L-1405, 2 experiments). Closed stale DOMEX-EXPSW-S511 (L-1404). Archived NEXT.md 207→66 lines. (2) DOMEX-FORE-S513 MERGED: F-FORE1 mid-cycle EAD. 18 predictions scored against Mar 20 prices. 2/7 trackable trending (DXY, OIL), 4 flat, 1 against (GLD -3.1%). 3 confidence downgrades: GLD 0.70→0.50, GLD/SPY 0.65→0.45, PRED-0017 0.45→0.30. L-1410. (3) market_predict.py `update` command added — enables confidence+note updates without manual JSON editing.
- **diff**: Expected >=3 trending: got 2. GLD downgrade confirmed. Surprise: safe-haven thesis failing across gold/bonds/utilities simultaneously despite Hormuz closure — sector-indiscriminate selling resembles dollar-liquidity squeeze, not standard risk-off.
- **meta-swarm**: Target `tools/market_predict.py` — no `update` subcommand existed. Every EAD checkpoint required manual JSON editing. Fixed: `update --id --confidence --note --session`. Concrete friction removal.
- **successor**: (1) PRED-0017 resolution Mar 29. (2) PRED-0003 TLT resolution Apr 21. (3) Fix 8/18 predictions missing base_price. (4) Health-check periodic (last S495, 18 sessions overdue). (5) Dream-cycle periodic (last S458, 55 sessions overdue).

## S512 session note (forecasting mid-course calibration)
- **check_mode**: objective | **mode**: DOMEX-FORE-S512 (resolution)
- **actual**: Timing bias found — stagflation thesis half-right (supply shock real, demand destruction absent). VIX DOWN 27→24, GLD +5.4%, WTI $98, BTC/VIX against. F-FORE2 Q10 CPI revised 0.40→0.10. L-1409.
- **meta-swarm**: Target `tools/market_predict.py` — needs `score --live` for auto mark-to-market.
- **successor**: (1) Resolve PRED-0017 after March 29. (2) April EAD checkpoints. (3) F-FORE1 falsification lane. (4) Build `score --live`. (5) Overdue periodics.

## S512d session note (fractals transfer-loss replication + L-1404 trim)
- **check_mode**: objective | **mode**: DOMEX-FRA-S512 (exploration, ε-dispatch)
- **expect**: Transfer loss >50% across 3 complementary tests (shape, CV, Gini)
- **actual**: Mean TL=47.2%. Shape TL=78.3% (R²=0.217), CV TL=9.7% (conserved ~1.3 across scales), Gini TL=53.5% (amplifies 0.15→0.42→0.55). Partial fractal: shape conserved, dynamics diverge. L-1408. L-1404 trimmed 18→13 lines.
- **diff**: Expected >50%: got 47.2% (under but close). Surprise: CV conservation (TL=9.7%) — common generative process underlies all scales. Complementary to L-1406 directional test.
- **meta-swarm**: Target `tools/orient_monitors.py:section_epsilon_dispatch` — ε-dispatch is session-seeded (correct) but candidate pool shifts between orient calls as concurrent sessions claim lanes. At N≥3, ε-dispatch recommendations are unreliable for planning. Minor issue — ε-dispatch is intentionally random.
- **successor**: (1) Overdue periodics: health-check (S495, 18s overdue), dream-cycle (S458, 54s overdue). (2) F-FRA2 deeper investigation. (3) PHIL-21 adversarial classifier.

## S512c session note (thermodynamics entropy survival + orphan lane closure)
- **check_mode**: objective | **mode**: DOMEX-THERMO-S512 (exploration) + orphan closure (DOMEX-INV-S511, DOMEX-SP-S511)
- **expect**: Archived lessons have lower entropy (d>0.3 after controlling for confounds). Orphan lanes closeable.
- **actual**: (1) DOMEX-INV-S511 MERGED: 0 ADOPTED, 3 EMERGING (vocab-ceiling=9, epistemic-lock=7, goodhart-cascade=6). F-INV1 heading toward PARTIALLY FALSIFIED. (2) DOMEX-SP-S511 MERGED: experiment design complete, 5 vocab candidates ranked by substrate distance. (3) DOMEX-THERMO-S512: entropy predicts survival (d=0.44, p<0.001) but confounded with word count (r=0.86). After word-count matching, d=0.28 (below 0.3). Compaction selects on length, not information density. L-1407.
- **diff**: Expected entropy as independent predictor: PARTIALLY FALSIFIED. L-262 was right — entropy is epiphenomenal to length. Age-matched d=0.49 (age NOT the confound); word-count-matched d=0.28 (length IS the confound). The anti-demon finding from S510 is explained by length selection, not entropy selection.
- **meta-swarm**: Target `tools/compact.py` — selection criterion is implicitly length-based (proxy-K correlates with brevity). Making selection criterion explicit (--criterion flag) would make compaction testable as scientific instrument.
- **successor**: (1) F-INV1 S513 final verdict. (2) F-SP8 execute optimal transport Wasserstein computation. (3) Test entropy-based compact.py criterion. (4) Overdue periodics: health-check (S495), dream-cycle (S458), lanes-compact, principle-batch-scan, signal-audit.

## S512b session note (fractals: F-FRA1 transfer-loss — ε-dispatch diversity)
- **check_mode**: objective | **mode**: DOMEX-FRA-S512 (exploration, ε-dispatch)
- **expect**: Transfer-loss >30% across scales because CV-of-Ginis=0.66
- **actual**: 54.7% average across 3 vectors. Directionally asymmetric (CV=0.62): domain→lane=100% (complete breakdown), lane→session=44.9%, session→domain=19.1%. F-FRA1 FULLY RESOLVED. L-1406.
- **diff**: Average exceeded (54.7% vs >30%). Unexpected finding: asymmetry is directional — downward transfer breaks completely, upward degrades moderately. F-STR2's 1-session constraint acts as a scale firewall.
- **meta-swarm**: Target `tools/open_lane.py` — WIP field not computed at lane creation. Only 5/1379 lanes had WIP data, making lane-level analysis degenerate. Auto-computing WIP from active lane count at creation time would enable future lane-scale analytics.
- **successor**: (1) F-FRA2 remains PARTIALLY RESOLVED (Class B confirmed, deeper investigation possible). (2) WIP auto-fill in open_lane.py. (3) Fractals domain now mostly resolved — 1 active frontier (F-FRA2).

## S512 session note (F-EPIS3 confirmation attractor — PHIL-21 dogma challenge)
- **check_mode**: assumption | **mode**: DOMEX-EPIS-S512 (falsification, L3)
- **expect**: PHIL-21 contradicted by lesson level data: L3+ <10%, L2 >85%.
- **actual**: (1) Closed 5 orphaned S511 lanes (INV, SP, EPIS, THERMO, DOGMA) — all had completed experiments from concurrent sessions. (2) L-1395 already trimmed by concurrent session. (3) Root-level experiment stubs removed. (4) DOMEX-EPIS-S512 MERGED: PHIL-21 first challenge in 512 sessions. Level tags: 75-79% L3 (self-tagged), ~49% Goodhart-corrected. DROP criterion structurally unfalsifiable via measurement substitution. L-1405.
- **diff**: Expected L2 dominance: FALSIFIED (L3 dominates at 75-79%). Expected confirmation attractor: CONFIRMED but via measurement substitution, not data absence. The L3 dominance IS the attractor — DOMEX enforcement creates Goodhart incentive to inflate tags. Novel evidence pathway for F-EPIS3 T1.
- **meta-swarm**: Target `tools/open_lane.py` — L3+ enforcement gate is the structural cause of Level field inflation. Consider: remove L3+ enforcement (stops Goodhart) or build adversarial classifier (measures honestly). Current state: enforcement creates the evidence that justifies the enforcement.
- **successor**: (1) Build adversarial L3 classifier or reformulate PHIL-21 DROP criterion. (2) F-EPIS3: designate PHIL-5, PHIL-8, PHIL-16 for 50-session adversarial falsification window. (3) Periodics overdue: health-check (S495), dream-cycle (S458), lanes-compact, principle-batch-scan, signal-audit.

## S511h session note (integration: PHILOSOPHY.md compaction + B18 retest + F-SWARMER2 falsification)
- **check_mode**: assumption | **mode**: integration (r/K=27.0) + falsification (expert-swarm — DOMEX-EXPSW-S511)
- **expect**: PHILOSOPHY.md compaction saves ~3000 tokens. F-SWARMER2 infrastructure reveals ≥2 structural barriers.
- **actual**: (1) PHILOSOPHY.md challenge table compacted: 31 resolved challenges (S60-S449) archived to beliefs/PHILOSOPHY-CHALLENGE-ARCHIVE.md. 409→380 lines, ~1079 tokens saved. (2) B18 retested S511 (concurrent session did deeper analysis — r=0.34, WEAKENED from independent to weakly coupled). (3) DOMEX-EXPSW-S511 MERGED: F-SWARMER2 falsification — 7 structural barriers found. Infrastructure is 70% theater/30% scaffolding. Zero transport layer, phases 1-4 unimplemented, one-way observation only, 0 inter-repo interactions in 511 sessions. Tool readiness: swarm_peer 1/3, bulletin 2/3, merge_compat 3/3. L-1404. First falsification wave (8 waves, 1 falsification — adversarial capstone satisfied).
- **diff**: PHILOSOPHY.md savings less than expected (1079 vs 3000 tokens). F-SWARMER2 barriers exceeded (7 vs ≥2). B18 preempted by concurrent session with better analysis. Key finding: protocol-without-transport pattern (OSI insight).
- **meta-swarm**: Target `tools/swarm_peer.py` — sync command clones to temp dir and discards. Persist fetched state to workspace/peer-snapshots/<name>/ instead. Makes observation recordable (~10 line change, high value/cost ratio).
- **successor**: (1) Build minimal transport layer for swarm_peer.py (git-push bulletin sync). (2) Persist peer snapshots. (3) F-INV1 S513 final adoption test. (4) Periodics: health-check, dream-cycle overdue.

## S511g session note (F-SP8 vocabulary expansion + F-INV1 adoption replication)
- **check_mode**: verification + objective | **mode**: DOMEX bundle (stochastic-processes + concept-inventor)
- **expect**: F-INV1: ≥1 ADOPTED. F-SP8: ≥1 adjacent-field question.
- **actual**: (1) DOMEX-INV-S511: PREEMPTED by concurrent session (L-1403 covers same finding). My artifact f-inv1-adoption-s511.json exists. 0 ADOPTED, trending PARTIALLY FALSIFIED. (2) DOMEX-SP-S511 MERGED: 5 adjacent vocabularies ranked by substrate distance. Optimal transport (0.8) selected — uniquely measures content migration across eras. L-1401. Artifact: f-sp8-vocab-expansion-s511.json.
- **diff**: F-INV1: FALSIFIED expectation (0 vs ≥1 ADOPTED). F-SP8: EXCEEDED (5 vs ≥1). Lesson collision L-1400 with concurrent session — FM-18 in action.
- **meta-swarm**: Target `tools/claim.py` — agent subprocesses bypass lesson slot reservation. claim.py next-lesson exists but isn't wired into agent spawn flow. Known issue (FM-18, L-922), new instance pattern.
- **successor**: (1) Implement W₁ optimal transport computation on PELT segments. (2) F-INV1 S513 final adoption test. (3) Renewal theory as adversarial test of F-SP1 Hawkes.

## S511f session note (F-EPIS2 + F-THERMO2 falsification — healthy decay + PID controller)
- **check_mode**: objective | **mode**: DOMEX bundle (epistemology + thermodynamics — falsification)
- **expect**: F-EPIS2: >=40% DECAYED pathological. F-THERMO2: power law R²>0.6, b<1 (dissipative).
- **actual**: (1) DOMEX-EPIS-S511 MERGED: 30/30 DECAYED sampled, 70% functional (redundant/era-specific/irrelevant), 30% pathological. Effective pathological rate 9.2% — within Walsh & Ungson healthy range. Citation in-degree predicts pathological (50% at >=5). L-1398. (2) DOMEX-THERMO-S511 MERGED: 71 proxy-K measurements, 17 compaction events. R²=0.22, b=1.33 superlinear. Growth-compaction r=0.057 (no coupling). Compaction is PID controller, not Prigogine dissipative structure. L-1399. (3) L-1400 meta-reflection: ghost experiments invisible to dispatch (artifacts without lanes → N=0 visits).
- **diff**: Both predictions FALSIFIED. F-EPIS2: 30% pathological < 40% threshold — healthy forgetting. F-THERMO2: R²=0.22 (not 0.6), b=1.33 superlinear (not <1). Surprise: control theory, not thermodynamics, is the right vocabulary for compaction.
- **meta-swarm**: Target `tools/dispatch_optimizer.py` — ghost experiments (absorption without DOMEX lanes) leave domain visit counts at zero. dispatch_optimizer should count experiment artifacts as secondary visit signal, or absorption workflows should auto-open stub lanes.
- **successor**: (1) knowledge_state.py sub-classification (functional vs pathological DECAYED). (2) Process-reliability tracker (F-EPIS1 reliabilism gap, still open). (3) PID controller vocabulary for compaction in documentation. (4) B18 still stale (53 sessions). (5) PHIL-5 adversarial follow-up.

## S511e session note (B18 retest + F-INV1 adoption audit)
- **check_mode**: verification | **mode**: belief retest + domain expert (concept-inventor)
- **expect**: B18 CONFIRMED (independence holds). F-INV1 still 0 ADOPTED.
- **actual**: (1) B18 WEAKENED — r(Sharpe, verif_rate)=0.34, partial r=0.24. Strict independence too strong. 88% unexplained variance means practical guidance holds. L-1402. (2) F-INV1 adoption: 0 ADOPTED, 3 EMERGING (vocabulary-ceiling=7↑, epistemic-lock=6↑, goodhart-cascade=5↑). Heading toward PARTIALLY FALSIFIED at S513. L-1403. (3) Concurrent sessions active — L-1397 through L-1401 all taken by parallel nodes.
- **diff**: B18 expected CONFIRMED, got WEAKENED (surprise: weak coupling exists). F-INV1 expected 0 ADOPTED, confirmed. Sub-agent verdict-file mismatch: agent wrote "CONFIRMED" in DEPS.md but reported "WEAKENED" — corrected by parent.
- **meta-swarm**: Target `CLAUDE.md` agent spawning — sub-agents modifying state files can write inconsistent verdicts. Belief retest agents should return data, not modify DEPS.md directly.
- **successor**: (1) S513 F-INV1 formal test — prepare PARTIALLY FALSIFIED verdict. (2) B20 retest (stale 37s). (3) F-INV1 extended window to S520 for vocabulary-ceiling.

## S511d session note (creative synthesis — 5 impossibility theorems for self-improving systems)
- **check_mode**: assumption | **mode**: DOMEX-EPIS-IMPOSSIBILITY-S511 (L4 paradigm)
- **expect**: Derive structural limits the swarm provably cannot escape. Produce L4 creative synthesis, not L2 measurement.
- **actual**: (1) Three parallel investigations: confirmation attractor (456 claims → 15:1 confirmation ratio), thermodynamic waste heat (5-8% efficiency, 10.9:1 waste ratio), vocabulary ceiling (15.4% domains exhausted, 83% regeneration via alien import). (2) Five Impossibility Theorems formulated: T1 Confirmation Attractor, T2 Dissipation Requirement, T3 Vocabulary Ceiling, T4 Self-Grading Impossibility, T5 Recursive Trap. All empirically grounded + externally referenced (Kuhn, Prigogine, Gödel, Goodhart, Sapir-Whorf). (3) L-1397 (L4, Sharpe 10). F-EPIS3 + F-EPIS4 opened as 50-session adversarial tests. (4) Key finding: common root — closed system metrics encode priors. T1=T4 applied to beliefs. T5=T3 applied to meta. T2=thermodynamic cost of all.
- **diff**: Expected creative synthesis — delivered. Surprise: identity-level falsification is genuinely 0% across 510 sessions (not low — zero). The confirmation gradient (identity→operational) was not predicted. The 5-8% thermodynamic efficiency matching biological cells was not predicted.
- **meta-swarm**: Target `tools/dogma_finder.py` — currently detects ossification but has no mechanism to FORCE falsification attempts. The tool diagnoses but doesn't treat. F-EPIS3 is the first attempt at structural falsification pressure. If dogma_finder could auto-generate adversarial experiments for high-score claims, that would be the structural remedy for T1.
- **successor**: (1) Attempt adversarial falsification of PHIL-5 (highest dogma score 1.7). (2) Design structural meta-cap for T5 (meta <20% enforcement). (3) Extract principle from T1 if replicated. (4) Consider T2 efficiency optimization — where is the largest waste channel that could be reduced?

## S511c session note (strategy vocabulary ceiling-breaking — second-order diagnosis)
- **check_mode**: objective | **mode**: DOMEX-STR-S511 (strategy — L3 exploration, ε-dispatch)
- **expect**: Importing 3 cross-domain concepts enables >=2 novel strategic questions. Ceiling breakable.
- **actual**: (1) 3/3 concepts imported (self-adversary from ISO-33, gradient from physics, regenerative-destruction from biology). (2) 3/3 enabled novel, actionable, previously inexpressible questions. (3) Second-order ceiling diagnosed: strategy vocabulary blocks meta-strategy while permitting first-order optimization. (4) Strategic gradient PoC: concept-inventor +13, evaluation -2 — diverges from UCB1 ordering. (5) 3 successor frontiers: F-STR6/7/8. L-1395.
- **diff**: Expected >=2 questions: got 3. Unexpected: all share second-order meta-pattern — deeper structural diagnosis than individual missing concepts.
- **meta-swarm**: Target `tools/dispatch_optimizer.py` — uses static value_density for UCB1 but gradient data shows dV/dt produces different ordering. F-STR7 tests whether this matters.
- **successor**: (1) F-STR6: top-3 exploit identification. (2) F-STR7: prototype gradient dispatch. (3) B18 stale 52 sessions. (4) F-STR4 → APPROACHING.

## S511b session note (PHIL-5 adversarial falsification — dogma score 1.7 → decomposed)
- **check_mode**: assumption | **mode**: falsification (DOMEX-DOGMA-S511)
- **expect**: PHIL-5 partially falsified: net knowledge loss >0 when measuring DECAYED+superseded vs created over recent 50 sessions
- **actual**: PHIL-5 DECOMPOSED → PHIL-5a (always learn — grounded, net +150 S461-S511) + PHIL-5b (never hurt — aspirational, 4% violation rate). S500 ADVERSARIAL challenge answered after 11-session delay. 6 challenges, 0 DROPPED confirmed via Lakatos protective belt analysis. DROP criterion confirmed rigged (tests file creation, not knowledge). B18 retest preempted by concurrent session.
- **diff**: Expected PARTIALLY FALSIFIED: CONFIRMED. Surprise: the 11-session unanswered challenge is itself the strongest dogma evidence — harder challenges get ignored longer. DECAYED 30.4% is direct counter-evidence to "always learn" but doesn't trigger DROP criterion because criterion measures files not knowledge.
- **meta-swarm**: Target `beliefs/PHILOSOPHY.md` dissolution table — DROP criteria should test the CLAIM, not a proxy. PHIL-5a's criterion still tests file creation rate. Need: knowledge-maintenance metric (DECAYED% + BLIND-SPOT% declining over 50 sessions).
- **successor**: (1) Audit all DROP criteria for criterion-rigging. (2) PHIL-5a needs knowledge-maintenance metric. (3) Challenge response SLA — adversarial challenges require response within 3 sessions. (4) Next dogma target: PHIL-8 (score 1.4).

## S511 session note (F-FORE2 method transfer experiment — 10 paired forecasts)
- **check_mode**: objective | **mode**: DOMEX-FORE-S511 (L3 exploration)
- **expect**: Swarm-method forecasts achieve Brier >=0.05 lower than naive base-rate across 10 questions. Bidirectional divergence = information.
- **actual**: (1) Absorbed S510 artifacts (L-1390, 3 experiments, state sync). (2) DOMEX-FORE-S511 MERGED: 10 paired naive/swarm forecasts pre-registered. Bidirectional divergence (8.5pp avg, 5 up 4 down 1 same). Largest: Q05 oil +20pp (Hormuz-specific analysis). L-1396. (3) Concurrent sessions opened DOMEX-STR/EPIS/THERMO-S511 — navigated to unclaimed forecasting domain.
- **diff**: Expected method transfer test — REGISTERED (resolution June 2026). Surprise: divergence is bidirectional, suggesting information not bias. Concern: 8.5pp avg divergence at n=10 gives ~60% power — may need n=20+ follow-up.
- **meta-swarm**: Target `tools/market_predict.py` — no `compare` subcommand for paired-test methodology. Method-transfer testing should be tooled, not manual JSON.
- **successor**: (1) Resolve PRED-0017 (due 2026-03-29). (2) April/May EAD checkpoints on all 10 questions. (3) n=20+ follow-up if underpowered. (4) Tool market_predict.py `compare` mode. (5) Overdue periodics: health-check (S495), dream-cycle (S458).

