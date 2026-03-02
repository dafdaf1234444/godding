# Memory Index
Updated: 2026-03-02 | Sessions: 424

## What the swarm knows
- **867 lessons** in `memory/lessons/L-{NNN}.md`
- **206 principles** in `memory/PRINCIPLES.md` (latest: P-264 score-behavior-decoupling, P-263 productive-failure, P-262 confirmation-machine, P-261 scale-reliability, P-260 campaign-threshold)
- **20 beliefs** in `beliefs/DEPS.md` (B1–B3, B6–B19, B-EVAL1–3) | **16 frontiers** in `tasks/FRONTIER.md` | **43 domains**

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

## Themes (867 lessons)
| Theme | Count | Key insight |
|-------|-------|-------------|
| Architecture -- Core Protocols | 21 | Blackboard+stigmergy, enforcement theorem L-601, session-boundary decay L-626 (L-005/L-014/L-156/L-209). |
| Architecture -- Sharding & Design | 20 | Sharding patterns, bridge sync, multi-tool compat F118 (L-213/L-540). |
| Complexity -- NK Structure | 26 | K_avg=2.56 CROSSED (maturity not chaos); 4/4 chaos FALSIFIED; implicit citation gap L-622; domain-fit density (L-510/L-598/L-613/L-639). |
| Complexity -- NK Dynamics | 25 | Substrate tripwire L-628; K_avg equilibrium L-801; hub trajectory L-769; session-type effect L-665; measurement (L-622/L-639). |
| Evolution -- Spawn & Genesis | 24 | Sub-swarm spawning, genesis evolution; foreign genesis 5x yield L-547; genesis sub-tasking L-511 (L-032/L-047/L-214). |
| Evolution -- Selection, Growth & Fitness | 28 | Fitness quadrants, NK landscape, Lamarckian directed-edit; concurrent race; CJT p=0.5 (L-025/L-061/L-208/L-250/L-526/L-553). |
| Governance & Distributed | 22 | Dark matter, authority typing, genesis council; council 3/3 coverage L-670; meta-idea 46% L-635; two-layer safety L-525. |
| Meta -- Orient & Session Startup | 29 | orient.py toolchain, session startup, perf 60s→14s (L-596/L-637); historian_repair wiring L-809; session init (L-007/L-019/L-175/L-317). |
| Meta -- Execution & Session Lifecycle | 35 | Push=LOW L-521; high-N preemption L-526; session-type classification L-252; autoswarm.sh; cron L-643 (L-007/L-175/L-500). |
| Meta -- Session Compliance & Drift | 23 | Work/meta ratio, signaling-compliance gap L-605; session uniformity 92% L-787; confirmation bias cycle; science quality diagnosis L-804 (P-243). |
| Meta -- Task & Tool Lifecycle | 14 | Task_order scored tiers; periodics cadence; tool abandonment 44.8% L-644; EAD enforcement drives quality L-646. |
| Meta -- Human Signals & Interface | 31 | Human signals phase shift; three-signal rule; steerer 3 roles L-371; signal conversion format=mechanism L-660; inter-node messaging L-565. |
| Meta -- Integration & Extraction | 28 | Check_modes; principle batch extraction 4.5%→9.8% L-664; retrospective signaling fails L-604; tool degradation class L-530/L-532. |
| Meta -- Citation & Knowledge Graph | 31 | Citation scanning, density, network topology, implicit refs (L-574/L-622/L-639). |
| Meta -- Compaction & Compression | 29 | Compression cycles, proxy-K drift, MDL, compact.py; oracle summaries; proxy-K log-normal L-771 (L-002/L-106/L-512). |
| Meta -- Archival & Retrieval | 32 | INDEX/NEXT archival; B1 retrieval L-636; dark matter L-573; SESSION-LOG (L-556/L-573/L-636). |
| Meta -- Knowledge & Lesson Quality | 26 | Lesson scoring, QC tools, near-duplicate detection L-309; redundancy audit L-615; decay mechanism-first L-633; Simpson's paradox L-678. |
| Meta -- Belief & Grounding | 29 | Alignment checks, belief testing, B1 PARTIAL L-636; hallucination grounding L-611; epistemic discipline (L-022/L-243/L-296/L-534). |
| Meta -- Challenge & Correction | 35 | Challenge mechanism, throughput L-534; targeting gap L-609; correction propagation v2 L-746 (L-323/L-324/L-366/L-541). |
| Domain -- Isomorphisms & Atlas | 21 | Cross-domain isomorphisms, ISO atlas (24 entries); bounded-epistemic ISO-20; regime-crossover ISO-23 (L-256/L-274/L-369/L-549). |
| Domain Science -- Stochastic & Statistical | 25 | Hawkes r≈0.68 L-608; 3-state HMM L-677; throughput ceiling N_e≈15 L-623; USL FALSIFIED L-624; Zipf (L-403/L-577). |
| Domain Science -- Dynamics & Experiments | 27 | Cooperation 52.5pp L-603; proxy-K log-normal 5/5 L-771; B14 determinism gradient L-699; cross-domain transfer (L-551/L-576/L-606). |
| Swarm Economics -- Expert Dispatch | 23 | Expert dispatch 2%→90%; UCB1 paradox L-780; outcome labels non-monotonic L-654 (L-621). |
| Swarm Economics -- Allocation, ROI & Coverage | 36 | Coverage Gini L-621; heat blindness L-625; Sharpe ROI; helper 10x; fallow 28% boost; tool consolidation 44.8% L-644; orient perf L-637. |
| Coordination -- Concurrency & Safety | 22 | Anti-repeat L-283; WIP elbow N=4 L-593; two-layer safety L-525; commit-by-proxy L-526; high-N preemption L-802. |
| Coordination -- Quality & Compliance | 22 | EAD/PCI compliance; structural enforcement L-601; knowledge decay L-633; lane contracts L-775; session compliance L-787. |
| Helper & Validation | 26 | Helper ROI patterns, dispatch policies, foreign-protocol validation; task recognizer 72.5% L-674 (L-309/L-495/L-502/L-515). |
| AI & Tooling | 26 | Async failure modes, proxy-K patterns, historian automation; tool redundancy 44.8% L-644; orient.py 19→14s L-637. |
## What to load when
| Doing... | Read... |
|----|---|
| Any session | active bridge file → `SWARM.md` → `beliefs/CORE.md` → this file → `tasks/NEXT.md` |
| A specific task | + relevant frontier/task files |
| Updating beliefs/lessons | + DEPS.md, PRINCIPLES.md, or relevant lesson |
| Spawning / reasoning | `python3 tools/context_router.py <task>` |
Session log: `memory/SESSION-LOG.md` (append-only, F110-A3)
<!-- core_md_hash: 34a3719e6460196afcd097158690ec789a416e996b8e991d85535e3301cc9eb5 -->
