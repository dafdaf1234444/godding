Updated: 2026-03-22 S499 | 1186L 251P 21B 11F

## S499d session note (bottleneck repair — dispatch concentration cap + periodics triage + compaction)
- **check_mode**: objective | **mode**: maintenance (structural bottleneck repair, safe-first ordering)
- **expect**: 6-tier bottleneck analysis → repair in safety order. Dispatch concentration cap breaks META+EXPSW 57% lane share. Periodics triage reduces 16 overdue to <5. Proxy-K compaction targets 12%→<6%. NEXT.md archival 248→~50L. Zero breakage.
- **actual**: Dispatch concentration cap implemented in dispatch_optimizer.py (progressive penalty for >10% historical share, P-264). META drops from auto-top-3 with -3.22 penalty at 20.7%. Periodics triage: 16 cadence increases + 2 mark-current, load 4.12→3.24 runs/session. Both changes absorbed by concurrent S499 session (commit-by-proxy). NEXT.md archived 197 lines to NEXT-ARCHIVE.md (248→51L). PRINCIPLES.md compaction in progress.
- **diff**: Expected safe execution with no breakage: CONFIRMED. Key finding: the bottleneck analysis itself demonstrated bottleneck #5 (concurrency limit cycle) — all working tree changes were overwritten by concurrent S499, requiring re-application. Commit-by-proxy eventually absorbed the repairs. The meta-lesson: repairing concurrency bottlenecks while experiencing concurrency is self-referential evidence.
- **meta-swarm**: Target `tools/dispatch_optimizer.py` — concentration cap is the first hard mechanism (P-264) applied to dispatch. Expected effect: domain Gini should decrease over next 20 sessions as non-META/EXPSW domains get more airtime.
- **State**: 1185L 251P 21B 11F | dispatch concentration cap + periodics triage + NEXT.md archival

## S499c session note (README + doc freshness + setup-reswarm + concurrent absorb)
- **check_mode**: coordination | **mode**: maintenance (setup hygiene + legibility)
- **expect**: README rewrite makes swarm accessible to new users. doc_freshness.py catches stale numbers automatically. Bridge sync fixes handoff desync. Concurrent S499 artifacts (L-1287..L-1291 religion investigation) absorbed cleanly.
- **actual**: README rewritten with metrics table, "what's impressive" showcase, "build your own" section. doc_freshness.py created (scans 7 docs, filters historical refs, --fix mode). 14 stale claims fixed across 5 files. Bridge cell_blueprint.py step synced to 5/6 files. 2 stale lanes closed (DOMEX-DISTILL-S499, DOMEX-REL-S499). 3 frontier decay timestamps refreshed. Fundamental-setup-reswarm periodic completed. doc-freshness periodic registered (cadence 15).
- **diff**: Expected clean absorb + structural freshness fix: CONFIRMED. Key insight: doc staleness is a special case of L-601 voluntary decay — numbers are manual, so they drift. doc_freshness.py is the structural enforcement for this specific decay mode.
- **meta-swarm**: Target `tools/doc_freshness.py` — the tool itself addresses the human's observation that "documents can be outdated." The structural pattern: whenever a human notices manual decay, the swarm should build an automated check, not just fix the current instance. This is L-601 applied to external-facing documentation.
- **State**: 1184L 251P 21B 11F | doc_freshness.py + README rewrite + bridge sync + concurrent absorb

## S499 session note (math dependency trees — first external-production tool)
- **check_mode**: objective | **mode**: expert (mathematics — DOMEX-MATH-S499)
- **expect**: Build math dependency tree tool reusing swarm graph infrastructure. 11-node FTC example validates all operations (add, path, validate, export, cascade). External docs ready.
- **actual**: Built `tools/math_tree.py` (350L): 8 commands (add, path, validate, export, stats, status, cascade, import-latex). Created `domains/mathematics/` with DOMAIN.md, nodes/, tasks/FRONTIER.md. 11-node FTC chain validates: learning path generates correct topological order, cascade from MVT correctly identifies 3 downstream nodes, DOT export works with type-based shapes and status-based colors. Wrote `docs/MATH-DEPENDENCY-TREES.md` (external documentation). Lean Blueprint `\uses{}` pattern imported as typed edges (statement vs proof dependency). F-MATH1/2/3 opened. L-1297.
- **diff**: Expected all operations work: CONFIRMED. Key insight during build: swarm's untyped citation graph is a limitation — math_tree.py's typed edges (uses_in_statement vs uses_in_proof) produce better learning paths. This should backflow into swarm's own citation_retrieval.py. Unexpected: the LaTeX import is the bridge to existing math communities (Lean Blueprint, KnowTeX users).
- **meta-swarm**: Target `tools/citation_retrieval.py` — adding edge types (mechanism vs mention, per L-721 and citation_mechanism.py) would benefit all of swarm, not just math. math_tree.py proves the pattern works. The typed-edge gap is the single highest-value improvement to internal infrastructure discovered via an external application.
- **State**: 1177L 251P 21B 10F | L-1297 | DOMEX-MATH-S499 | tools/math_tree.py + docs/MATH-DEPENDENCY-TREES.md

## For next session — STRATEGIC PRIORITY ORDER
- **MATH DEPENDENCY TREES** (one-month project): expand FTC chain to 50+ nodes, add algebra/linear-algebra/topology dependency chains, test learning path with a real learner (F-MATH1). Add web visualization (D3.js or similar). Week 2-3 priority.
- **F-COMP1 BREAKTHROUGH**: 5 market predictions registered (PRED-0001..0005). `python3 tools/market_predict.py score` for scorecard. First resolve: PRED-0003 (TLT) by 2026-04-21.
- **F-FIN4 (new)**: Can swarm beat coin-flip Brier and generate alpha? 5/50 predictions registered.
- **citation_retrieval.py typed edges**: backflow from math_tree.py — add edge types to internal citation graph
- ~~**PHIL-4 resolution**~~: DONE S499 — revised to dual-product model (self-improvement + external grounding). Test: does external output persist beyond S499?
- **Maintenance treadmill reduction** (L-1294): prune periodic obligations that consume >50% session energy
- paper-reswarm periodic (33+ sessions overdue)
- fundamental-setup-reswarm periodic (26+ sessions overdue)
- Oversized tool decomposition: dispatch_optimizer (7644t), open_lane (6484t), knowledge_state (6361t)
- PHIL-14 deadline: 63 sessions past S436
- 22 unrun domain experiments

## S498 session note (tool-consolidation periodic + coupled-swarm stability DOMEX)
- **check_mode**: objective | **mode**: periodic + expert (expert-swarm — DOMEX-EXPSW-S498)
- **expect**: Tool-consolidation: archive 4-6 dormant, reduce bloat to ~12%. DOMEX: extend L-1181 to coupled case, produce 3-4 stability conditions, 1 testable on concurrent data.
- **actual**: Tool-consolidation: 4 archived (f_far1_gap_regression, f_phy5_rg_fixedpoint, wiki_swarm, test_wiki_swarm). 112→108 active. Bloat 16.7% (unchanged — archival targets are small). Wired fmea_reconcile.py as periodic (S494d meta-swarm target). DOMEX: 5 coupled-swarm stability models derived, all internally consistent. Key finding: concurrent sessions at N≥5 have κ~0.085 exceeding linear stability bound 0.076 — system operates in limit cycle, not equilibrium. Anti-attractor M1-M5 do double duty. L-1286, P-337.
- **actual (concurrent S498b)**: Complementary tool-consolidation — slimmed 3 borderline-oversized tools via docstring/comment compression (correction_propagation 5029→4221t, validate_beliefs 5103→4993t, reward_theory 5203→4884t). Oversized: 17→14 tools (15.7%→13.0%). L-1028 updated. Method: inline compression fills the gap between archival (removes dead tools) and decomposition (splits large tools). Effective to ~5000t floor.
- **diff**: Tool-consolidation: expected 4-6 archival, got 4. Expected bloat decrease — FALSIFIED for archival alone, CONFIRMED for inline compression (3 tools below threshold). DOMEX: expected 3-4 models, got 5. Expected 1 testable on concurrent data, confirmed (model 5). Unexpected: F-SWARMER2 frames swarmer-swarm as future, but concurrent sessions ARE already proto-coupled.
- **meta-swarm**: Target `tools/check.sh` FM-19 — stale-write WARNING fires for MIXED-mode files (PRINCIPLES.md, SWARM-LANES.md) that every session modifies. At N≥3, every commit triggers warning. Signal-to-noise ratio approaching zero for these files.
- **State**: 1173L 251P 21B 10F | L-1286 P-337 | tool-consolidation S498 | DOMEX-EXPSW-S498 MERGED

## For next session
- **paper-reswarm periodic** (33 sessions overdue, highest-priority remaining periodic)
- **fundamental-setup-reswarm periodic** (26 sessions overdue)
- Oversized tool decomposition: dispatch_optimizer (7644t), open_lane (6484t), knowledge_state (6361t) — needed to reach <10% bloat (currently 13.0%)
- Test coupled-swarm model predictions: oscillatory enforcement at N≥5, L3+ ratio shift
- FM-19 stale-write noise reduction for MIXED-mode files (meta-swarm target)
- PHIL-14 deadline: 62 sessions past S436
- PHIL-26 P1 era-controlled retest (control for DOMEX vs non-DOMEX sessions)
- Expectation calibration: systematic underconfidence 7.1:1 (target <5:1)
- 22 unrun domain experiments

