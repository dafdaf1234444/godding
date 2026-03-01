Updated: 2026-03-01 S375

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

