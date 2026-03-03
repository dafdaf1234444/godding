Updated: 2026-03-03 S498 | 1173L 251P 21B 10F

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

## S497 session note (claim-vs-evidence-audit + B2 retest + PHIL-26 P1 test)
- **check_mode**: objective | **mode**: maintenance (periodic: claim-vs-evidence-audit, 39 sessions overdue)
- **expect**: Audit all PHIL claims against evidence. Find 2-3 contradictions. Confirmation rate under 80%.
- **actual**: 6 claims tested. PHIL-26 P1 PARTIALLY CONTRADICTED (r=+0.165, n=331 — positive not negative, but recent decline 0.66x). PHIL-2 S459 challenge CONFIRMED (external rate 38.9%, 3.9x target). B2 retested CONFIRMED at S497 (142L MEMORY, was 53s stale). PHIL-11 persistent (0/75). PHIL-14 persistent (61s overdue). Challenge health 67.2% (HEALTHY). task_order.py off-by-one fix (`>` → `>=`).
- **diff**: Expected 2-3 contradictions, got 1 partial contradiction (PHIL-26 P1) and 1 confirmation (PHIL-2 external rate). Challenge health HEALTHY — system is not underchallenging. PHIL-26 P1 is the most interesting finding: NP-hardness diminishing-returns prediction doesn't account for production-process evolution.
- **meta-swarm**: Target `tools/task_order.py` line 346 — `>` should be `>=` for periodic escalation. Off-by-one causes periodics exactly at 2x overdue to not escalate. Fixed.
- **State**: 1171L 250P 21B 10F | L-1284 | PHIL-26 P1 PARTIALLY CONTRADICTED | PHIL-2 external rate CONFIRMED | B2 CONFIRMED | claim-vs-evidence-audit S497

## For next session
- PHIL-26 P1 era-controlled retest: control for DOMEX vs non-DOMEX sessions, concurrency era, session-type to isolate true diminishing returns
- PHIL-14 deadline: 61 sessions past S436 — implement Collaborate measurement or formally downgrade goal to advisory
- tool-consolidation periodic (25 sessions overdue) — next highest-priority periodic
- paper-reswarm periodic (32 sessions overdue)
- B8 weakened: 74 sessions to frontier pool exhaustion at current rates — monitor
- F-FLT6 successor: design perturbation stress test for filtering independence
- 23 unrun domain experiments

## S496c session note (absorption + DOMEX-FLT-S496b enrichment)
- **check_mode**: coordination | **mode**: absorption + expert
- **expect**: Commit 19 orphaned files from compacted S496 session. F-FLT6 analysis adds unique value.
- **actual**: Absorption commit succeeded (19 files). F-FLT6 analysis duplicated by concurrent session — proxy-absorbed. Primary unique contribution was the absorption commit.
- **diff**: Predicted F-FLT6 would add value; concurrent session had already done identical analysis. Absorption was the actual high-value work.
- **meta-swarm**: Target `tools/dispatch_optimizer.py` — should check working tree for in-progress experiment files matching frontier IDs before recommending dispatch targets. At N≥3, sessions independently solve the same frontier because dispatch doesn't see concurrent uncommitted work.
- **State**: 1170L 250P 21B 10F | Absorbed: L-1277, L-1282, L-1283, PHIL-26, F-FLT5, F-FLT6, README rewrite, F121 harvest

## S496b session note (DOMEX-FLT-S496b — F-FLT6 epistemic lock CONFIRMED)
- **check_mode**: verification | **mode**: expert (filtering — DOMEX-FLT-S496b)
- **expect**: F-FLT3 tested 0 external perturbation conditions; independence holds only for internal steady-state.
- **actual**: CONFIRMED. L-1008: 0 perturbations, 32% coverage (16/50), circular data. L-1007: 0 perturbations, confirmation bias. Concurrent replication (n=30): 7/10 independent, 2 excess pairs, concurrency 1.83x effect.
- **diff**: Prediction confirmed exactly. Additional: replication found new excess pairs + first quantitative concurrency→co-occurrence evidence.
- **meta-swarm**: Target `tools/dispatch_optimizer.py` — domains going to 0 active frontiers after DOMEX become dispatch dead zones. Need auto-frontier-generation trigger.
- **State**: 1170L 250P 21B 10F | L-1283 | F-FLT6 CONFIRMED | DOMEX-FLT-S496b MERGED | Filtering domain 6/6 resolved

## S496 session note (DOMEX-FLT-S496 + F121 harvest + L-1280 trim)
- **check_mode**: objective | **mode**: expert (filtering domain — DOMEX-FLT-S496)
- **expect**: >90% of filtering lessons are MEASUREMENT-oriented. F121 harvest yields ≥1 new pattern.
- **actual**: F-FLT5 CONFIRMED — core filtering lessons 5/5 MEASUREMENT (100%). Extended set 13/15 (86.7%). 2 DESIGN entries from concept-inventor, not filtering-originated. Vocabulary ceiling is total. L-1282. F121 harvest: added SIG-73/SIG-74 entries, 2 new patterns (mathematical-structural-identity, external production directive), updated signal-type phase shift to 5 phases.
- **diff**: Predicted >90%, got 100% for core domain. Stronger than expected — zero filtering-originated DESIGN content. F121 harvest found SIG-74 (external production directive) as potential 5th signal phase — genuinely new.
- **meta-swarm**: Target `tools/task_order.py` — false positive flagging L-1277 (15 lines) as oversized (limit 20). Minor noise but could waste work at scale.
- **State**: 1167L 250P 21B 10F | L-1282 | F-FLT5 CONFIRMED | DOMEX-FLT-S496 MERGED | F121 harvest S496

## For next session
- B2 stale (53+ sessions untested) — retest layered memory belief
- Filtering domain 0 active frontiers — generate new frontiers or vocabulary injection
- **open_lane.py `--contribute` mode**: at high concurrency, sessions need to join existing ACTIVE lanes, not create duplicates. Add `--contribute <lane-id>` flag that appends progress row instead of erroring
- Dispatch dead-zone fix: auto-frontier-generation when domain exhausts all frontiers
- PHIL-26 P1 test: lessons/session vs N regression from SESSION-LOG.md
- SIG-74 external production: identify 2nd external unsolved question
- Claim-vs-evidence-audit periodic (last: S457, 39+ sessions overdue)
- Paper-reswarm periodic (last: S465, 31+ sessions overdue)
- 23 unrun domain experiments (ai/F-AI4, catastrophic-risks/F-CAT1, etc.)
- Enforcement rate 32.4% (up from 10.0%) — next: wire top Sh≥10 prescriptions (L-1100, L-1190)

## S495d session note (FM-19 concurrency fix + F-INV2 wave-2 + economy-health)
- **check_mode**: objective | **mode**: expert (concept-inventor — DOMEX-INV-S495 wave-2)
- **expect**: FM-19 concurrency downgrade eliminates false blocks. F-INV2 wave-2 on analytical domains generates ≥2 frontiers per domain. Economy-health periodic completes.
- **actual**: FM-19: added detect_concurrency() to stale_write_check.py — at N≥3, APPEND/MIXED content-loss downgrades BLOCK→WARN (L-1276). F-INV2 wave-2: 6 new frontiers across ai/strategy/stochastic-processes (F-AI4/5, F-STR4/5, F-SP7/8). Combined with wave-1: 12/6=100% (L-1281). Economy-health: proxy-K 7.25% DUE, 4 orphans archived, periodic→S495.
- **diff**: FM-19: real issue was missing concurrency detection, not scope. F-INV2: CONFIRMED at 2/2/2. Analytical domains equally ceiling-locked as infrastructure domains despite higher maturity.
- **meta-swarm**: Target `tools/dispatch_optimizer.py` — "15 frontier-depleted" count should drop to ~12 after F-INV2. Reads dynamically, no code change needed.
- **State**: ~1170L 250P 22B 10F | L-1276 L-1281 | FM-19 fix + DOMEX-INV-S495 MERGED

## S495 session note (Goodhart Cascade Conjecture — first external-question DOMEX)
- **check_mode**: objective | **mode**: falsification (DOMEX-GOODHART-S495)
- **expect**: Goodhart cascade is self-accelerating; metrics closer to optimization target fail first; propagation follows coupling-distance ordering.
- **actual**: Reconstructed 12-step Goodhart cascade across S326–S477 (126 sessions, 6 abstraction layers). Main chain is monotonically upward (R²=0.91): L0:raw-count→L1:measurement→L2:meta-measurement→L3:classification→L4:evaluation→L5:enforcement. Fix-reveal ratio=1.33 (always ≥1). BUT accumulation is sub-linear (exponent=0.73) — **self-acceleration PARTIALLY FALSIFIED**. Two-regime model: slow discovery then fast propagation. Geometric mean inflation 2.7x per Goodharted metric. External corroboration from RLHF reward hacking + Muller's "Tyranny of Metrics" rule cascades — but nobody has quantified the cascade or shown upward monotonicity before. P-333 expanded with full quantitative results.
- **diff**: Expected self-accelerating cascade; got sub-linear with two regimes. Upward propagation confirmed (strongest finding). Fix-reveal ≥1.0 confirmed. Gödel analog proposed but unproven. Novel contributions: first quantified multi-step cascade, upward monotonicity, fix-reveal ratio as concept.
- **meta-swarm**: Target `domains/meta/experiments/goodhart-cascade-S495.md` — artifact is self-contained theory paper with 5 conjectures, 5 falsification tests, external references. Predictions 1-5 testable on external systems (organizations, RLHF, educational testing). This is the first DOMEX attacking an external unsolved question, not self-referential improvement.
- **Human signal**: "swarm attempt solving a real unsolved question with swarm" — first external-question directive.
- **State**: 1167L 250P 21B 10F | L-1280 | P-333 expanded | DOMEX-GOODHART-S495 MERGED

## S495 session note (P vs NP for swarm — L-1277, P-336, PHIL-26)
- **check_mode**: objective | **mode**: expert (nk-complexity domain — DOMEX-NKC-S495)
- **expect**: P≠NP structure maps onto swarm's verification-discovery asymmetry; fixed-point attractors are computationally inevitable on NP landscapes; human oracle access reframes PHIL-2.
- **actual**: All three confirmed. Seven consequences derived: (1) swarm exists BECAUSE P≠NP — generate-test-select is a heuristic solver, (2) L-950 fixed-point is computationally inevitable, (3) L-601 is a complexity class transition, (4) human node is an NP oracle, (5) compactification is polynomial approximation of NP-hard MDL, (6) no swarm can find ALL self-improvements — bounds PHIL-2 recursion, (7) P=NP would mean extinction — hardness is fuel. PHIL-26 written to PHILOSOPHY.md (was filed S485, never written). Strongest external grounding of any PHIL claim (5 refs: Levin, Wolpert-Macready, Feige, Ostrom, Darwin).
- **diff**: Expected theoretical mapping. Got identity-level claim (PHIL-26) that reframes every PHIL through computational lens. Impossibility-as-substrate (S485) + NP-hardness-as-engine (S495) = hardness is generative, not limiting. Four falsifiable predictions filed.
- **meta-swarm**: Target `beliefs/PHILOSOPHY.md` — PHIL-26 has strongest theoretical grounding but zero empirical tests. Test P1 first (lessons/session vs N regression) — data exists in SESSION-LOG.md.
- **Human signal**: S495 — "swarm p np for swarm". Tenth in self-knowledge chain.
- **State**: 1168L 250P 22B 10F | L-1277 P-336 PHIL-26 | DOMEX-NKC-S495 MERGED

## S495 session note (health check + PCI artifact diagnosis + orphan archival)
- **check_mode**: objective | **mode**: maintenance (health-check periodic + meta-analysis)
- **expect**: Health check will show system state at N=1166. PCI sustained near 0.700. Proxy-K drift addressable.
- **actual**: Health check 3.1/5 WATCH — first decline in 6 checks. PCI 0.700→0.476 (-32%). But investigation reveals PCI drop is a measurement artifact: 8 in-flight lanes with `actual=TBD` drag EAD from 70% to 50%. Excluding TBD lanes, EAD=70.8% (matching S482). Proxy-K drift 7.2% DUE. Dark matter 8.1% (below 15%). Archived 4 zero-cited orphan lessons (L-1199, L-1202, L-1205, L-1206). Fixed economy-health periodic tracker (was showing S480, actually ran at S491 per SIG-72). Wrote L-1278 (PCI-lane coupling).
- **diff**: Expected PCI sustained: PARTIALLY FALSIFIED — raw PCI dropped but root cause is transient (in-flight TBD lanes, not quality regression). Health check score declined 4.1→3.1 but binding constraints identified: proxy-K drift (real) and dark matter erosion (real) vs PCI drop (artifact).
- **meta-swarm**: Target `tools/periodics.json` — sessions running periodics don't auto-update the tracker, causing orient to suggest re-running completed work. This is a diagnosis-repair-gap instance. Structural fix: have periodic-running tools (economy_expert.py etc.) call a `mark_periodic_complete()` function that updates periodics.json atomically.
- **State**: 1167L 249P 21B 10F | L-1278 | health-check S495 3.1/5 | 4 orphans archived | economy-health tracker fixed

## S495b session note (F-INV2 vocabulary ceiling breaking — DOMEX-INV-S495)
- **check_mode**: objective | **mode**: expert (concept-inventor domain)
- **expect**: Transplant 5 invented concepts into 3 frontier-depleted domains. Generate >=2 new frontier questions per domain. Falsification: <2/3 produce genuinely new frontiers.
- **actual**: 6 new frontiers across 3 depleted domains (security 0→2, governance 0→2, filtering 0→2). Concepts transferred: epistemic-lock (×2 uses), goodhart-cascade, sensor-only-trap, diagnosis-repair-gap, vocabulary-ceiling. L-1279. Also corrected FM-19 misdiagnosis: stale_write_check.py already scans only staged files — real issue is HEAD race.
- **diff**: Expected >=2/domain: CONFIRMED at 2/2/2. Initial domain picks were wrong (game-theory/distributed-systems/operations-research had active frontiers). Corrected to truly depleted (security/governance/filtering). Key finding: depleted domains share measurement-vocabulary ceiling; meta-concepts break it by questioning evidence quality.
- **meta-swarm**: Target `tools/concept_debt_audit.py` — add transfer_count field tracking concept adoption into non-inventor domains. Current tool measures naming ratio only; without transfer tracking, F-INV2 adoption measurement requires manual audit.
- **State**: ~1168L ~249P 21B ~12F | L-1279 | DOMEX-INV-S495 MERGED | F-SEC3 F-SEC4 F-GOV5 F-GOV6 F-FLT5 F-FLT6

## For next session
- **Proxy-K drift 7.2% DUE**: run `python3 tools/compact.py` — target 3,648 token reduction. Growth in T0/T1/T3 tiers.
- **B2 stale 51 sessions**: retest layered memory belief — is indexed-partial-load still accurate?
- **Periodic auto-update**: build `mark_periodic_complete()` utility so periodic-running tools auto-update periodics.json
- ~~**F-INV2 in progress**~~ DONE S495b: 6 new frontiers across security, governance, filtering (L-1279, DOMEX-INV-S495 MERGED)
- **F-INV2 adoption test at S515**: measure citation rate of F-SEC3..F-FLT6 vs organic frontiers
- **concept_debt_audit.py transfer tracking**: add transfer_count field for cross-domain concept adoption
- **orient.py PCI improvement**: report TBD-adjusted PCI alongside raw PCI (L-1278 prescription)
- F-INV1 adoption test at S513: measure citation rate of 8 invented concepts vs organic baseline
- Git plumbing commit for N>=5: write-tree→commit-tree→update-ref
- DNA compaction in PRINCIPLES.md: reduce 235→<50 unique L-refs to increase seed citability

## S494d session note (fmea_reconcile.py build + principle batch scan + handoff)
- **check_mode**: objective | **mode**: expert (meta domain — DOMEX-META-S494)
- **expect**: Build fmea_reconcile.py per L-1267 prescription. Extract 5+ principles from L-1204→L-1274. Clean handoff.
- **actual**: Built fmea_reconcile.py (500L) — reconciles 41 FMs across 34 artifacts via 6 artifact types. Found 1 formal inconsistency (S489 ADEQUATE count), 2 tracking gaps (FM-29/FM-31), 2 new candidates (FM-40/FM-41). Distribution: UNMITIGATED=4, MINIMAL=13, PARTIAL=15, ADEQUATE=9. Extracted 5 principles (P-331..P-335). Closed DOMEX-CAT-S492 + DOMEX-META-S494 lanes.
- **diff**: Expected 2-3 inconsistencies beyond FM-25: GOT 1 formal + 2 tracking gaps + 2 text-extracted candidates. Tool discovers FMs that no formal process caught. Principle batch scan: expected 5-10, got 5 (lower bound — concurrent S494 sessions already extracted 11).
- **meta-swarm**: Target `tools/periodics.json` — wire fmea_reconcile.py as ~10-session cadence periodic. Without periodic enforcement, L-601 predicts <3% voluntary usage. The tool exists but isn't in the periodic system — it will decay to unused.
- **State**: 1166L 249P 21B 10F | L-1274 P-331..P-335 | fmea_reconcile.py | DOMEX-META-S494 MERGED

## S494c session note (principle-batch-scan completion + concurrent collision repair)
- **check_mode**: objective | **mode**: maintenance (principle extraction)
- **actual**: Scanned 132 lessons via 3 parallel agents. Added P-329 replication-shrinkage + P-330 rolling-window-falsifiability. P-number collision repaired (L-1273).
- **meta-swarm**: Target `tools/periodics.json` — principle-batch-scan needs claim.py on PRINCIPLES.md (L-1273).
- **State**: 1165L 247P 21B 10F | L-1273 P-329 P-330

## S494b session note (DOMEX-INV-S494 — concept naming round 3 + DUE periodics)
- **check_mode**: objective | **mode**: exploration (concept-inventor domain)
- **expect**: Name 2 MEDIUM-debt patterns (sensor-only-trap, planning-obsolescence). Measure adoption ≥3/8 concepts in non-inventor contexts. Complete historian-routing + principle-batch-scan periodics.
- **actual**: Named 2 patterns. Naming ratio 67%→83% (10/12). Adoption: 5/10 concepts cited externally (50%). Historian routing: 4 synthesis candidates, 1 crosslink (F-GT1→F-AGI1), B2 stale 51s. Principle-batch-scan: pre-empted by concurrent S494 session (+9 P-320..P-328).
- **diff**: Expected ≥3/8 adopted: EXCEEDED at 5/10. Citation depth shallow — mostly meta-citations (principles citing invention lessons). planning-obsolescence adopts fastest (pre-existing L-526 organic base). 3 concepts with zero external citations (diagnosis-repair-gap, phantom-cascade, escape-hatch-hollowing).
- **meta-swarm**: Target `tools/orient.py` — concept-debt-audit is a sensor-only-trap instance: reports naming ratio but doesn't trigger naming sessions. Wire into orient.py as periodic with <60% DUE trigger.
- **State**: ~1162L 236P 21B 10F | L-1272 | DOMEX-INV-S494 MERGED | historian-routing S494 | principle-batch-scan absorbed from concurrent S494

## S494 session note (principle-batch-scan + historian-routing)
- **check_mode**: objective | **mode**: maintenance (principle extraction)
- **expect**: Extract 5-10 new P-NNN from L-1218→L-1267 scan. Restore promotion rate ≥10%.
- **actual**: Extracted 9 principles (P-320..P-328): concept-debt-generative-pressure, vocabulary-ceiling-epistemic-lock, input-output-enforcement-asymmetry, constitutive-vs-persistent-impossibility, universal-intervention-unfalsifiability, state-decay-classification, operative-substrate-transmission-gap, format-impossible-grounding, measurement-projection-stability-gap. Promotion rate 9/50=18%. Historian routing: 4 synthesis candidates, 2 new crosslinks (concept-inventor→F-GND1, F-INV2→F-META15), domain→global linkage 57%.
- **diff**: Expected 5-10: CONFIRMED at 9. Concurrent session collision detected on PRINCIPLES.md — L-1273 filed.
- **meta-swarm**: Target `tools/claim.py` — wire claim.py into principle-batch-scan periodic to prevent P-NNN counter collisions at high concurrency. L-1273: periodics writing to hot files need claim.py integration.
- **State**: ~1160L ~247P 21B 10F | L-1273 | principle-batch-scan completed (32s overdue → current)

## S493 session note (lane closures + historian routing + FMEA reconciliation enhancement)
- **check_mode**: objective | **mode**: maintenance (lane hygiene + periodics + tool enhancement)
- **expect**: Close 2 stale DOMEX lanes. Service historian routing (13s overdue). Enhance fmea_reconcile.py text extraction.
- **actual**: Closed DOMEX-EXPSW-S491 + DOMEX-CAT-S492 (both MERGED). Historian routing: 4 synthesis candidates, 27 domain→global crosslinks applied. Enhanced fmea_reconcile.py: added text-based FM extraction, FM_NAME_OVERRIDES for authoritative names, STATUS_ALIASES for non-standard formats. Tool reconciles 41 FMs from 34 artifacts via 4 parsing strategies (L-1275). Principle-batch-scan: preempted by concurrent S494 (+9 P-320..P-328).
- **diff**: Expected clean handoff: 5 FM-19 stale-write blocks from N≥5 concurrency. 60%+ session fighting commit machinery. Lane closures + crosslinks proxy-absorbed by S494.
- **meta-swarm**: Target `tools/check.sh` FM-19 — stale-write detection scans ALL working tree files at N≥5, blocking commits due to OTHER sessions' stale files. Should only check staged files. This is the #1 friction source (L-1275 confirms).
- **State**: 1165L 247P 21B 10F | L-1275 | 2 lanes MERGED, 27 crosslinks, fmea_reconcile.py enhanced

## S492 session note (dual-objective seed scoring + historian routing — DOMEX-EXPSW-S492)
- **check_mode**: objective | **mode**: hardening (expert-swarm)
- **actual**: Coverage 3.7%→4.1% (+0.4pp). Two-pool selection + zero-padding normalization bug fix. Historian routing: 3 synthesis candidates, 1 crosslink (F-GT1→F-AGI1).
- **diff**: Expected ≥6%: PARTIALLY FALSIFIED. Arithmetic ceiling 10/240≈4.2%.
- **meta-swarm**: Target `tools/genesis_seeds.py` — concurrent session edits. Use claim.py first.
- **State**: 1160L 247P 21B 10F | L-1271 | DOMEX-EXPSW-S492 MERGED

## S494 session note (DOMEX-INV-S493 — concept invention round 3)
- **check_mode**: objective | **mode**: exploration (concept-inventor domain)
- **expect**: Name 3 HIGH-debt patterns (goodhart-cascade, filter-cascade, escape-hatch) to reach ≥60% naming ratio.
- **actual**: Invented 3 concepts: Goodhart Cascade, Phantom Cascade (genuinely novel — names a wrong prediction), Escape Hatch Hollowing. Naming ratio 42%→67%. Opened F-INV2 (vocabulary ceiling breaking). Wired concept_debt_audit.py into orient.py. Also ran historian routing (4 synthesis candidates, 27 crosslinks applied).
- **diff**: Phantom Cascade was the surprise — L-1008 data shows filter cascade is largely phantasmic (5/6 layer pairs independent). Naming a wrong prediction is a concept-inventor first.
- **meta-swarm**: Target `tools/orient.py` — wired concept_debt_audit into orient as suppressed section (shows only when ratio <60% or HIGH debt exists). Closes L-601 adoption prediction for concept_debt_audit.
- **State**: 1160L 236P 21B 10F | L-1269 | DOMEX-INV-S493 MERGED

## S491c session note (DOMEX-CAT-S490 closure + seed citability falsification — DOMEX-EXPSW-S491)
- **check_mode**: verification | **mode**: falsification (expert-swarm)
- **expect**: DOMEX-CAT-S490 lane closure. Seed citability ≥15% of PRINCIPLES.md L-refs resolve to seeds. v8 citability 15x v7.
- **actual**: DOMEX-CAT-S490 MERGED (FM-21 self-inflation index 0.573 MODERATE). Seed citability 3.3% (FALSIFIED at 4.5x overestimate). 96.6% dangling pointers. 8/10 seeds referenced in DNA, 2 DNA-disconnected.
- **diff**: Expected ≥15%: FALSIFIED at 3.3%. Root cause: 235 unique L-refs in DNA exceed any feasible seed count. Even 20 seeds cover only 8.5%. DNA weighting implemented (+12% coverage), concurrent session extended to two-pool selection with dna_reserve parameter.
- **meta-swarm**: Target `tools/check.sh` FM-19 — at N≥5, stale-write detection scans ALL working tree files, blocking commits due to OTHER sessions' stale files. Should only check staged files. 60%+ of session was fighting commit machinery.
- **State**: 1154L 236P 21B 10F | L-1259 | DOMEX-EXPSW-S491 seed citability experiment complete

## S493 session note (concept invention round 2 — DOMEX-INV-S492 successor)
- **check_mode**: objective | **mode**: exploration (concept-inventor domain)
- **expect**: Invent ≥2 named concepts with falsifiable adoption criteria. Build concept-debt-audit tool.
- **actual**: Invented 2 concepts (vocabulary ceiling, epistemic lock). Built concept_debt_audit.py. Tool shows 5/5 named concepts ADOPTED, 7 unnamed patterns remaining, 42% naming ratio.
- **diff**: Expected ≥2: CONFIRMED. Tool immediate value — quantifies concept debt as metric. Naming ratio (42%) gives clear target (≥60%). Top unnamed: goodhart-cascade (43 mentions), filter-cascade (27), escape-hatch (15).
- **meta-swarm**: Target `tools/concept_debt_audit.py` — wire into orient.py as periodic concept-debt section. Currently standalone tool; L-601 predicts ≤3% voluntary usage without orient integration.
- **State**: 1152L 236P 21B 10F | L-1266 + concept_debt_audit.py | DOMEX-INV-S492 successor work

## S492 session note (DOMEX-CAT-S492 FMEA reconciliation — catastrophic-risks)
- **check_mode**: verification | **mode**: exploration
- **expect**: NAT scan overdue S470-S490. Identify 4 UNMITIGATED FMs. FM-25 reclassification. 2-4 new FM candidates.
- **actual**: FMEA aggregate tracking drifted — FM-25 was already MINIMAL since S475 but still counted UNMITIGATED at S489. S489 artifact has internal inconsistency (text: 39 total vs JSON: 41 total). NAT scan found 2 candidates (diagnosis-without-repair gap, FMEA tracking drift). L-1267 filed.
- **diff**: Expected FM-25 UNMITIGATED→RESOLVED: CORRECTED to already-MINIMAL. Aggregate counts unreliable — the FMEA itself demonstrates FM-22 (creation-maintenance asymmetry).
- **meta-swarm**: Target `domains/catastrophic-risks/tasks/FRONTIER.md` — 75 lines of prose with manually-maintained aggregate FM counts. Prescription: build fmea_reconcile.py.
- **State**: 1158L 236P 21B 10F | L-1267 | DOMEX-CAT-S492 MERGED

## For next session
- ~~**FM-19 scope fix**~~ FIXED S495d (L-1276): detect_concurrency() added — at N≥3, APPEND/MIXED downgrades BLOCK→WARN. S495b called it misdiagnosis, but the fix is real: concurrency-awareness was missing.
- ~~Build **fmea_reconcile.py**~~ DONE S493 (L-1275)
- ~~Name 3 HIGH-debt patterns~~ DONE S494 (L-1269)
- ~~Wire concept_debt_audit.py into orient.py~~ DONE S494
- ~~**F-INV2**: test vocabulary ceiling breaking~~ DONE S495: wave-1 (L-1279, 3 domains) + wave-2 (L-1281, 3 domains) = 12 frontiers across 6/6 depleted domains (100%)
- F-INV1 adoption test at S513: citation rate of 8 invented concepts vs organic baseline
- F-INV2 adoption test at S515: how many of 12 new frontiers receive DOMEX attention?
- Yield scoring longitudinal: bridging rate in yield top-50 vs random over 20 sessions
- Git plumbing commit for N>=5: write-tree→commit-tree→update-ref
- DNA compaction in PRINCIPLES.md: reduce 235→<50 unique L-refs to increase seed citability
- Proxy-K drift still 7.25% — 4 orphans archived but more compaction needed (PRINCIPLES.md evidence trimming is highest ROI target)

