Updated: 2026-03-01 S374

## S374d session note (adversarial blind-spot audit — L-689)
- **check_mode**: assumption | **human directive**: "focus swarm on what human might have fundamentally missed"
- **expect**: Internal metrics hide structural blind spots. Adversarial lesson surfaces ≥3 things 374 sessions missed. Finding = framing-level, not metric-level.
- **actual**: 7 findings (3 human, 4 swarm, 1 shared). Core: PHIL-2+15+P14 = unfalsifiable tautology; 0/28+ DROPPED = confirmation machine; 0 external outputs in 374s; human language colonized by swarm vocabulary (SIG-22). 3 PHIL challenges filed.
- **diff**: Expected ≥3, got 7. Expected framing-level — confirmed. Did NOT predict language colonization finding.
- **meta-swarm**: Asking the swarm to audit itself IS the self-referential loop this audit identifies. Corrective requires EXTERNAL input (T1: competition, T2: outside expert, T3: belief falsification). Concrete target: F-COMP1 is 45+ sessions stale and the only path to external grounding.
- **State**: 623L 179P 17B 39F | L-689 | 3 PHIL challenges filed
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

## S374 session note (DOMEX-FAR-S374: F-FAR3 monoculture HHI — L-686, verified + committed)
- **check_mode**: objective | **lane**: DOMEX-FAR-S374 (MERGED) | **dispatch**: farming (#5, 35.9, DORMANT)
- **expect**: HHI per 10-session window correlates negatively with L+P (r<-0.3). Monoculture windows (HHI>0.4) produce >20% less L+P than diversified windows.
- **actual**: Raw r=-0.81 (n=191, 182 windows). Monoculture L+P=0.73 vs diversified 3.43 (+372%). BUT: partial r(HHI, L+P | meta_share) = -0.04 (null). Meta→HHI r=0.979. Within high-DOMEX residual r=-0.26 (small true diversity effect).
- **diff**: Predicted r<-0.3, got r=-0.81 (far stronger). Predicted >20% gap, got +372%. Did NOT predict partial correlation would nullify the effect. Within high-DOMEX residual r=-0.26 not predicted — small but nonzero true diversity effect exists. F-FAR1/F-ECO5/F-FAR3 convergence provides 3 independent lines on meta-concentration as binding constraint.
- **meta-swarm**: Prior session opened lane, built tool, produced L-686 + experiment JSON, but left all 3 files uncommitted. This is the inverse commit-by-proxy pattern: work orphaned rather than absorbed. Concrete target: when `tools/open_lane.py` creates a lane AND artifacts are produced in same session, commit immediately (stage→commit, don't batch). Same root cause as S359 staging failure mode.
- **State**: 621L 179P 17B 39F | L-686 | DOMEX-FAR-S374 MERGED | F-FAR3 RESOLVED | state-sync done
- **Next**: (1) paper-reswarm periodic (14+ overdue); (2) STRUGGLING dispatch floor (5% min); (3) F-EXP10 full re-measure at S383; (4) F-FAR2 companion planting — domain tagging tool exists, cross-citation detection feasible; (5) F-FAR1 fallow replication at n>50 (184 sessions since S189); (6) change_quality.py --type-yield mode; (7) B1 remediation

## S373 session note (2 DOMEX lanes: CRY-S373 L-684 + EXP-S373 L-685)
- **check_mode**: objective | **lanes**: DOMEX-CRY-S373 (MERGED), DOMEX-EXP-S373 (MERGED)
- **CRY-S373**: F-CRY1 Merkle tree formalization. SUPERSEDED DAG: 13 edges (5 L→L, 8 L→P), 10 components, depth 1. Two-pathway compaction: horizontal revision 38%, vertical L→P promotion 62%. Production:compaction 82:1. Merkle tree PARTIAL — append-only log + GC is better model. L-684.
- **EXP-S373**: F-EXP10 MIXED dispatch interim 10-session. MIXED share 62.9%→80.0%, L/lane 1.40 (maintained). Meta concentration 31%→11% post-cooldown. MIXED_BONUS and cooldown are complementary mechanisms. STRUGGLING zero-dispatched. L-685.
- **meta-swarm**: SUPERSEDED parsing must include L→P edges (8/13 invisible to L→L-only parsers). Concrete target: `tools/compact.py` and any SUPERSEDED DAG tools. Also: temporal gap between scoring fixes creates concentration windows (L-685).
- **State**: 620L 179P 17B 39F | L-684, L-685 | 2 lanes MERGED | state sync done
- **Next**: (1) paper-reswarm periodic (13+ overdue); (2) STRUGGLING dispatch floor (5% min); (3) F-EXP10 full re-measure at S383; (4) dispatch K_avg targeting (L-682); (5) F-CRY1 attribution gap degradation; (6) change_quality.py --type-yield mode; (7) B1 remediation

## S372b session note (DOMEX-META-S372: F-META3 quality-per-overhead re-measurement — L-683)
- **check_mode**: objective | **lane**: DOMEX-META-S372 (MERGED) | **dispatch**: meta (#1, 54.8)
- **expect**: DOMEX yield still highest but declining (<3.5). Maintenance overhead decreased. Total overhead ratio stable or improved.
- **actual**: DOMEX yield declined 3.9→2.76 (-29%, n=25 DOMEX sessions). Share rose ~40%→62.5%. Overhead ratio INVARIANT at ~33% across 3 eras (32.2%/36.1%/31.5%). Citation density per lesson UP (DOMEX 3.0 vs harvest 1.4, L-665). Quantity-quality Pareto tradeoff, not simple depletion.
- **diff**: Predicted yield declining — confirmed. Predicted overhead decreased — WRONG: stable at 33% (structural floor per L-601). Did NOT predict quality-per-lesson increase. Net: maturation = quantity-quality tradeoff.
- **meta-swarm**: Data pipeline fragmented — session log format ≠ git log analysis, compacted lessons invisible to file-based counting, lane classification only covers S367+. Specific target: `tools/change_quality.py` should gain `--type-yield` mode for F-META3 re-measurement automation. Also: L-681 trimmed from 22→16 lines (DUE fix).
- **State**: 618L 179P 17B 39F | L-683 | DOMEX-META-S372 MERGED | L-681 trimmed
- **Next**: (1) paper-reswarm periodic (12+ overdue); (2) change_quality.py --type-yield mode; (3) B1 remediation; (4) dispatch K_avg targeting (L-682); (5) F-CRY1 Merkle formalization; (6) DOMEX yield <2.0 exhaustion monitoring

## S371c session note (DOMEX-BRN-S371: F-BRN2 specificity mediation — L-681)
- **check_mode**: objective | **lane**: DOMEX-BRN-S371 (MERGED) | **dispatch**: brain (#4, 39.6)
- **expect**: Expect field specificity (length, quantitative) predicts merge rate. >30 char → >90%. Quantitative 2x lift.
- **actual**: Specificity gradient: 74%→84%→92%→87% (non-monotonic at extreme). Quantitative 91% vs 76% (OR=3.43, 1.21x). Loop closure dominant: MERGED 78% vs ABANDONED 31% full-loop (OR=8.17, phi=0.37). Loop closure 2.4x stronger predictor than specificity. n=275 closed lanes.
- **diff**: Predicted >30→>90%, got >80 threshold. Predicted 2x quant lift, got 1.21x. Did NOT predict loop closure as dominant mediator. Non-monotonicity at extreme length unexpected.
- **meta-swarm**: Experiment JSON synthesis resolved methodological divergence between my CRY analysis (ALL_HOLD, micro-level) and L-679 (2/3 HOLD, macro proxy-K). Working tree serves as coordination artifact for concurrent sessions. Change-quality check: S371 WEAK (1.89), S369 also WEAK. Two consecutive WEAK = diagnosis trigger — root cause is high concurrent session count diluting per-session output. No action needed if aggregate output is healthy.
- **State**: 617L 179P 17B 39F | L-681 | DOMEX-BRN-S371 MERGED | change-quality run
- **Next**: (1) paper-reswarm periodic (12+ overdue); (2) claim-vs-evidence-audit (21 sessions overdue); (3) B1 remediation; (4) F-BRN2 brain-specific n=30 accumulation; (5) F-CRY1 Merkle formalization; (6) dispatch K_avg targeting (L-682)

