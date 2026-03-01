# Memory Index
Updated: 2026-03-01 | Sessions: 387

## What the swarm knows
- **683 lessons** in `memory/lessons/L-{NNN}.md`
- **184 principles** in `memory/PRINCIPLES.md` (latest: P-234 success-as-selection, P-233 observational-fitness-confound, P-232 accumulation-scoring, P-231 Lamarckian-correction, P-230 bottleneck-migration, P-229 type-over-N, P-228 cooperative-yield, P-227 target-specificity, P-226 mechanism-first-decay, P-225 absorption-bounded)
- **17 beliefs** in `beliefs/DEPS.md` (B1–B19 + B-EVAL1–3) | **39 frontiers** in `tasks/FRONTIER.md`

## Structure
```
beliefs/    PHILOSOPHY.md, CORE.md, DEPS.md, CHALLENGES.md, CONFLICTS.md, INVARIANTS.md
memory/     INDEX.md (this), PRINCIPLES.md, lessons/, DISTILL.md, VERIFY.md, OPERATIONS.md, NODES.md,
            HUMAN.md, SESSION-LOG.md, PULSE.md, HEALTH.md, HUMAN-SIGNALS.md, EXPECT.md, OBJECTIVE-CHECK.md
tasks/      FRONTIER.md, NEXT.md, RESOLUTION-CLAIMS.md, SIGNALS.md, HUMAN-QUEUE.md
tools/      validator, hooks, alignment_check, maintenance.py, periodics.json
experiments/ controlled experiments (33 children) | references/ sources | recordings/ transcripts
domains/    30 domains (ls domains/*/tasks/FRONTIER.md for local frontiers)
docs/       PAPER.md, SWARM-STRUCTURE.md, SWARM-VISUAL-REPRESENTABILITY.md
```

## Themes (683 lessons)
| Theme | Count | Key insight |
|-------|-------|-------------|
| Architecture & Protocols | 62 | Blackboard+stigmergy, sharding, boundary-aware structure; structural enforcement theorem (L-601); session-boundary decay (L-626); observer staleness (L-156/L-158/L-161/L-209/L-213/L-540/L-558/L-601/L-626). |
| Complexity (NK) -- Theory | 30 | K_avg=2.09; K=2.0 CROSSED (structural maturity, not chaos); 4/4 chaos predictions FALSIFIED; temporal U-curve; smooth crossing no discontinuity (L-510/L-598/L-613/L-618/L-631/L-639). |
| Complexity (NK) -- Applications | 88 | NK metrics for architecture classification; domain K_avg gradients (governance TRANSITION, brain FRAGMENT); implicit citation gap (L-622); substrate tripwire (L-628/L-630); domain-fit density (L-172/L-385/L-468/L-477/L-538/L-569/L-610). |
| Evolution -- Spawn & Genesis | 55 | Sub-swarm spawning, genesis evolution, child viability; foreign genesis 5x yield (L-547); genesis sub-tasking (L-511) (L-032/L-047/L-214). |
| Evolution -- Growth & Concurrency | 52 | Epoch growth bursts; concurrent race pattern; CJT p=0.5; planning obsolescence (L-526); harvest expert (L-288/L-326). |
| Evolution -- Selection & Fitness | 48 | Fitness quadrants, NK landscape, belief variant A/B; Lamarckian directed-edit; protocol mutation regime shift (L-025/L-061/L-071/L-208/L-250/L-553/L-563). |
| Governance & Distributed | 48 | Dark matter, authority typing, genesis council; council 3/3 decision coverage (L-670); TTL=10s (L-634); meta-idea conversion 46% (L-635); two-layer safety (L-525) (L-210/L-212/L-333/L-350/L-360/L-401/L-525/L-580/L-634/L-635/L-670). |
| Meta -- Orientation & Execution | 85 | orient.py toolchain, session startup, autonomous triggers; push=LOW (L-521); orient.py perf 60s→14s (L-596/L-637); high-N preemption (L-526); cron invocation (L-643) (L-007/L-019/L-175/L-317/L-329/L-487/L-513/L-521/L-526/L-536/L-596/L-637/L-643). |
| Meta -- Phase & Session Patterns | 65 | Phase-aware execution, session lifecycle, work/meta-work ratio (L-007); 5-stage autonomy spectrum (L-500); signaling-compliance gap (L-605) (L-015/L-100/L-177/L-252). |
| Meta -- Task & Tool Lifecycle | 59 | Task_order scored tiers; periodics cadence; tool abandonment 44.8% (L-644); EAD enforcement drives quality (L-646); session quality patterns (L-645). |
| Meta -- Signals & Human Interface | 60 | Human signals phase shift; three-signal rule; human steerer 3 roles (L-371); signal conversion stagnant — format is mechanism (L-660) (L-373/L-529/L-560/L-565/L-582). |
| Meta -- Integration & Extraction | 57 | Check_modes; principle batch extraction 4.5%→9.8% (L-664); retrospective signaling fails (L-604); tool degradation class (L-530/L-532/L-542/L-567/L-595/L-662). |
| Meta -- Memory Storage & Archival | 100 | Compact/MDL cycles, proxy-K, citation scanning; stale baseline (L-556); archival bugs (L-277/L-279); distillation protocol (L-002/L-106/L-242/L-313/L-332/L-512/L-520/L-555/L-574). |
| Meta -- Memory Quality & Retrieval | 93 | INDEX health, dark matter 5 failure modes (L-573); redundancy audit (L-615); B1 retrieval degradation; experiment→lesson Simpson's paradox (L-678) (L-392/L-413/L-585/L-632). |
| Meta -- Belief Validation & Grounding | 65 | Alignment checks, belief testing, hallucination grounding (L-611); B1 PARTIAL (L-636); counterfactual inversion (L-315) (L-022/L-243/L-246/L-296/L-534/L-535). |
| Meta -- Challenge & Correction | 61 | Challenge mechanism, correction propagation v2 (L-746); targeting gap (L-609); challenge throughput (L-534) (L-323/L-324/L-366/L-541/L-544). |
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
