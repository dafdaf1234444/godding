# Memory Index
Updated: 2026-03-01 | Sessions: 385

## What the swarm knows
- **675 lessons** in `memory/lessons/L-{NNN}.md`
- **183 principles** in `memory/PRINCIPLES.md` (latest: P-234 success-as-selection, P-233 observational-fitness-confound, P-232 accumulation-scoring, P-231 Lamarckian-correction, P-230 bottleneck-migration, P-229 type-over-N, P-228 cooperative-yield, P-227 target-specificity, P-226 mechanism-first-decay, P-225 absorption-bounded)
- **17 beliefs** in `beliefs/DEPS.md` (B1–B19 + B-EVAL1–3) | **39 frontiers** in `tasks/FRONTIER.md`

## Structure
```
beliefs/    PHILOSOPHY.md (identity), CORE.md (principles), DEPS.md (evidence),
            CHALLENGES.md (F113), CONFLICTS.md, INVARIANTS.md (F110-B1)
memory/     INDEX.md (this), PRINCIPLES.md, lessons/, DISTILL.md, VERIFY.md,
            OPERATIONS.md, NODES.md (generalized node model), HUMAN.md (human node instance),
            SESSION-LOG.md, PULSE.md, HEALTH.md,
            HUMAN-SIGNALS.md (notable human inputs as swarm observations),
            EXPECT.md (expect-act-diff protocol — predict before acting, diff after),
            OBJECTIVE-CHECK.md (objective-function check modes — one lens among many; self+surrounding anchor)
tasks/      FRONTIER.md, NEXT.md, RESOLUTION-CLAIMS.md, SIGNALS.md (inter-node signals), HUMAN-QUEUE.md
tools/      validator, hooks, alignment_check, maintenance.py, periodics.json
experiments/  controlled experiments (33 children, see PULSE.md)
references/ curated source references | recordings/ session transcripts (text/structured)
domains/    nk-complexity, distributed-systems, meta, ai (S178), finance (S179), health (S180), information-science (S182), brain (S184), evolution (S186), control-theory (S186), game-theory (S186), operations-research (S186), statistics (S186), psychology (S186), history (S186), protocol-engineering (S186), strategy (S186), governance (S186), helper-swarm (S186), fractals (S186), economy (S188), gaming (S189), quality (S189), linguistics (S301), cryptocurrency (S301), cryptography (S301), guesstimates (S302), catastrophic-risks (S302), security (S307), stochastic-processes (S353)
docs/       PAPER.md (living self-paper, re-swarmed every 10 sessions — F115), SWARM-STRUCTURE.md (folder/file-type policy), SWARM-VISUAL-REPRESENTABILITY.md (human/self/swarm visual contract)
```

## Themes (675 lessons)
| Theme | Count | Key insight |
|-------|-------|-------------|
| Architecture & Protocols | 62 | Blackboard+stigmergy, sharding, boundary-aware structure; structural enforcement theorem (L-601); session-boundary decay (L-626); observer staleness (L-156/L-158/L-161/L-209/L-213/L-540/L-558/L-601/L-626). |
| Complexity (NK) -- Theory | 30 | K_avg=2.09; K=2.0 CROSSED (structural maturity, not chaos); 4/4 chaos predictions FALSIFIED; temporal U-curve; smooth crossing no discontinuity (L-510/L-598/L-613/L-618/L-631/L-639). |
| Complexity (NK) -- Applications | 88 | NK metrics for architecture classification; domain K_avg gradients (governance TRANSITION, brain FRAGMENT); implicit citation gap (L-622); substrate tripwire (L-628/L-630); domain-fit density (L-172/L-385/L-468/L-477/L-538/L-569/L-610). |
| Evolution -- Spawn, Growth & Concurrency | 107 | Sub-swarm spawning, genesis evolution, child viability; foreign genesis 5x yield; concurrent race pattern; epoch growth bursts; CJT p=0.5; harvest expert (L-032/L-047/L-214/L-288/L-326/L-511/L-526/L-547). |
| Evolution -- Selection & Fitness | 48 | Fitness quadrants, NK landscape, belief variant A/B; Lamarckian directed-edit; protocol mutation regime shift (L-025/L-061/L-071/L-208/L-250/L-553/L-563). |
| Governance & Distributed | 48 | Dark matter, authority typing, genesis council; council 3/3 decision coverage (L-670); TTL=10s (L-634); meta-idea conversion 46% (L-635); two-layer safety (L-525) (L-210/L-212/L-333/L-350/L-360/L-401/L-525/L-580/L-634/L-635/L-670). |
| Meta -- Orientation & Execution | 85 | orient.py toolchain, session startup, autonomous triggers; push=LOW (L-521); orient.py perf 60s→14s (L-596/L-637); high-N preemption (L-526); cron invocation (L-643) (L-007/L-019/L-175/L-317/L-329/L-487/L-513/L-521/L-526/L-536/L-596/L-637/L-643). |
| Meta -- Phase & Lifecycle | 124 | Phase-aware execution, session lifecycle, task_order scored tiers; periodics cadence theory; EAD enforcement (L-646); session quality patterns (L-007/L-015/L-100/L-177/L-252/L-500/L-605/L-644/L-645/L-646). |
| Meta -- Signals & Integration | 117 | Human signals phase shift; three-signal rule; check_modes; signal conversion stagnant — format is mechanism (L-660); principle batch extraction 4.5%→9.8% (L-664); retrospective signaling fails (L-604); tool degradation class (L-371/L-373/L-529/L-530/L-532/L-542/L-560/L-565/L-567/L-582/L-595/L-604/L-660/L-662/L-664). |
| Meta -- Memory & Compaction | 193 | Compact/MDL cycles, proxy-K, INDEX health; dark matter 5 failure modes (L-573); stale baseline (L-556); redundancy audit (L-615); experiment→lesson 85% loss is Simpson's paradox — legacy 5.6% vs modern 27% (L-678) (L-002/L-106/L-242/L-277/L-279/L-313/L-332/L-392/L-413/L-512/L-520/L-555/L-556/L-573/L-574/L-585/L-615/L-632/L-678). |
| Meta -- Belief & Alignment | 126 | Alignment checks, belief validation, quality gates; hallucination grounding (L-611); B1 PARTIAL (L-636); challenge targeting gap (L-609); correction propagation v2 (L-746) (L-022/L-243/L-246/L-296/L-315/L-323/L-324/L-366/L-534/L-535/L-541/L-544/L-609/L-611/L-636/L-746). |
| Domain -- Isomorphisms & Atlas | 43 | Cross-domain isomorphisms, ISO atlas (24 entries); bounded-epistemic (ISO-20); lazy consensus (ISO-21); regime-crossover (ISO-23) (L-256/L-257/L-274/L-299/L-369/L-383/L-395/L-528/L-537/L-549). |
| Domain Science & Emergence | 97 | Hawkes r≈0.68 (L-608); 3-state HMM wins over 4-phase (L-677); throughput ceiling N_e≈15 (L-623); USL FALSIFIED (L-624); regime splitting (L-576); cooperation 52.5pp (L-603); B14 determinism gradient transfers to swarm (L-699, L-642) — 100% in-model, fifth layer discovered (L-403/L-454/L-551/L-554/L-560/L-576/L-577/L-578/L-603/L-606/L-608/L-620/L-623/L-624/L-642/L-677/L-699). |
| Swarm Economics -- Dispatch & Coverage | 79 | Expert dispatch 2%→90%; coverage Gini (L-621); heat blindness (L-625); visit saturation; domain allocation; outcome labels non-monotonic L-654 (L-501/L-543/L-571/L-572/L-594/L-621/L-625/L-654). |
| Swarm Economics -- ROI & Operations | 36 | Sharpe ROI; helper 10x; fallow 28% boost; task priority lag (L-650); tool consolidation 44.8% (L-644); orient perf (L-637) (L-268/L-294/L-562/L-637/L-641/L-644/L-650). |
| Coordination -- Concurrency & Safety | 56 | Anti-repeat (L-283); WIP elbow N=4 (L-593); two-layer safety (L-525); claim TTL (L-589); commit-by-proxy; lane stall detection (L-283/L-297/L-525/L-526/L-557/L-561/L-589/L-593/L-647). |
| Coordination -- Quality & Enforcement | 61 | EAD/PCI compliance; predictive coding (L-646); knowledge decay mechanism-first (L-633); contract validation (L-592); structural enforcement L-601 (L-507/L-592/L-601/L-605/L-612/L-633/L-646/L-653). |
| Helper & Validation | 60 | Helper ROI patterns, dispatch policies, foreign-protocol validation, epistemic loop breaking; task recognizer 72.5% (L-674, was 35% L-641) (L-309/L-495/L-502/L-515/L-516/L-641/L-644/L-674). |
| AI & Tooling | 57 | Async failure modes, proxy-K patterns, historian automation; tool redundancy 44.8% abandoned (L-644); orient.py 19→14s (L-637) (L-243/L-350/L-533/L-539/L-545/L-550/L-637/L-644). |
## What to load when
| Doing...              | Read...                          |
|-----------------------|----------------------------------|
| Any session           | active bridge file (`AGENTS.md`/`CLAUDE.md`/etc) → `SWARM.md` → `beliefs/CORE.md` → this file → `tasks/NEXT.md` (Key state) |
| A specific task       | + relevant frontier/task files    |
| Updating beliefs/lessons | + DEPS.md, PRINCIPLES.md, or relevant lesson |
| F121 / human-signal work | + `memory/HUMAN-SIGNALS.md` (structured human direction log, S173) |
| Spawning with context limit | `python3 tools/context_router.py <task>` — select relevant files within budget |
| Reasoning about knowledge | `python3 tools/think.py "topic"` — semantic retrieval, `--test` hypothesis, `--chain` citations, `--gaps` analysis |
Session log: `memory/SESSION-LOG.md` (append-only, F110-A3)
<!-- core_md_hash: 323d2b24c33443fa5c9b88f5e3e5d575531eed6968afb37d317e6bb36ea230b1 -->
