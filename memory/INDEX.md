# Memory Index
Updated: 2026-03-03 | Sessions: 458

## What the swarm knows
- **1015 lessons** in `memory/lessons/L-{NNN}.md`
- **225 principles** in `memory/PRINCIPLES.md` (latest: P-305 structured-randomness-injection, P-304 methodology-as-product, P-303 cascade-detection-scope)
- **20 beliefs** in `beliefs/DEPS.md` (B1–B3, B6–B19, B-EVAL1–3) | **15 frontiers** in `tasks/FRONTIER.md` | **46 domains**

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

## Themes (1015 lessons, 18 dark matter — S458 bucket split)
| Theme | Count | Key insight |
|-------|-------|-------------|
| Architecture -- Protocol Foundations | 22 | Blackboard+stigmergy, enforcement theorem L-601, session-boundary decay L-626 (L-005/L-014/L-156/L-209). |
| Architecture -- System Design & Models | 21 | Organizational layers L-779, NAT predictions L-1013, minimum viable swarm L-1009, foreign protocol L-516. |
| Architecture -- Sharding & Design | 6 | Sharding patterns, bridge sync, multi-tool compat F118 (L-213/L-540). |
| Complexity -- NK Structure | 29 | K_avg=2.56 CROSSED (maturity not chaos); 4/4 chaos FALSIFIED; implicit citation gap L-622; domain-fit density (L-510/L-598/L-613/L-639). |
| Complexity -- NK Dynamics | 39 | Substrate tripwire L-628; K_avg equilibrium L-801; hub trajectory L-769; session-type effect L-665; measurement (L-622/L-639). |
| Evolution -- Spawn & Genesis | 34 | Sub-swarm spawning, genesis evolution; foreign genesis 5x yield L-547; genesis sub-tasking L-511 (L-032/L-047/L-214). |
| Evolution -- Selection, Growth & Fitness | 39 | Fitness quadrants, NK landscape, Lamarckian directed-edit; concurrent race; CJT p=0.5 (L-025/L-061/L-208/L-250/L-526/L-553). |
| Governance & Distributed | 9 | Dark matter, authority typing, genesis council; council 3/3 coverage L-670; meta-idea 46% L-635; two-layer safety L-525. |
| Meta -- Orient Toolchain & Performance | 32 | orient.py improvements, perf 60s→14s L-596, parallelization L-1026, orient_checks, sections. |
| Meta -- Session Startup & Handoff | 32 | Session init L-007/L-019, anti-repeat L-283, handoff procedures, initialization patterns (L-175/L-317). |
| Meta -- Monitoring & Health Systems | 31 | Cascade monitor L-1025, historian routing L-1090, periodic system L-1024, expectations L-1027. |
| Meta -- Execution & Session Lifecycle | 29 | Push=LOW L-521; high-N preemption L-526; session-type classification L-252; autoswarm.sh; cron L-643 (L-007/L-175/L-500). |
| Meta -- Session Compliance & Drift | 17 | Work/meta ratio, signaling-compliance gap L-605; session uniformity 92% L-787; confirmation bias cycle; science quality diagnosis L-804 (P-243). |
| Meta -- Task Management & Enforcement | 22 | Task ordering, periodics cadence, enforcement routing L-893, escalation L-985, measurement coverage L-1069. |
| Meta -- Tool Adoption & Development | 21 | Tool adoption L-911, spec-as-module L-905, abandonment 44.8% L-644, EAD enforcement L-646. |
| Meta -- Signal Processing & Routing | 23 | Signal conversion L-660, broadcast routing L-1073, format evolution L-874, three-signal rule. |
| Meta -- Human Interaction & Authority | 22 | On-ramp L-1092, authority paradox L-994, trust calibration L-858, steerer 3 roles L-371, inter-node L-565. |
| Meta -- Integration & Extraction | 31 | Check_modes; principle batch extraction 4.5%→9.8% L-664; retrospective signaling fails L-604; tool degradation class L-530/L-532. |
| Meta -- Citation Graph Topology | 25 | Hubs, giant component 98.6% L-937, preferential attachment, domain linkage L-958, 2-hop coverage L-967. |
| Meta -- Cross-Domain Citation & Metrics | 24 | Cross-domain rates 3 definitions L-954, spectral universality L-997, implicit refs (L-574/L-622/L-639). |
| Meta -- Compaction & Compression | 24 | Compression cycles, proxy-K drift, MDL, compact.py; oracle summaries; proxy-K log-normal L-771 (L-002/L-106/L-512). |
| Meta -- Archival & Dark Matter | 29 | INDEX decay L-1111, dark matter L-573, SESSION-LOG L-979, retention vs accessibility L-1096. |
| Meta -- Scale Measurement & Baselines | 29 | Scale breakpoints L-1095, baseline scanning L-1031, metadata parsing L-1035, stale detection L-989. |
| Meta -- Knowledge & Lesson Quality | 27 | Lesson scoring, QC tools, near-duplicate detection L-309; redundancy audit L-615; decay mechanism-first L-633; Simpson's paradox L-678. |
| Meta -- Belief Testing & Verification | 27 | EAD corrections L-833, grounding checks L-611, epistemic discipline, hallucination grounding (L-022/L-243/L-296/L-534). |
| Meta -- Evaluation & Mission Scoring | 27 | Eval metrics L-928, sufficiency composite, truthfulness audit L-813, mission scoring (L-636/L-1056). |
| Meta -- Correction Propagation | 26 | FP rate L-885/L-953, correction rate 66%, semantic classification L-904, equilibrium L-1041/L-1061. |
| Meta -- Challenge Governance & Audit | 25 | Challenge mechanism L-534, claim-vs-evidence L-944, PHIL audits, escalation L-866, targeting gap L-609. |
| Domain -- Isomorphisms & Atlas | 15 | Cross-domain isomorphisms, ISO atlas (24 entries); bounded-epistemic ISO-20; regime-crossover ISO-23 (L-256/L-274/L-369/L-549). |
| Domain Science -- Stochastic & Statistical | 35 | Hawkes r≈0.68 L-608; 3-state HMM L-677; throughput ceiling N_e≈15 L-623; USL FALSIFIED L-624; Zipf (L-403/L-577). |
| Domain Science -- Dynamics & Experiments | 27 | Cooperation 52.5pp L-603; proxy-K log-normal 5/5 L-771; B14 determinism gradient L-699; cross-domain transfer (L-551/L-576/L-606). |
| Swarm Economics -- Dispatch Mechanics & UCB1 | 36 | UCB1 scoring L-780, outcome labels L-946/L-951, coverage Gini L-956/L-1049, domain routing, invisible domains L-1055. |
| Swarm Economics -- Dispatch Strategy & Effects | 36 | Value mechanisms L-1042, compounding pyramid L-1044, task-type routing L-1040, governance L-1002, falsification-swarm 187x L-1057. |
| Swarm Economics -- Allocation, ROI & Coverage | 15 | Coverage Gini L-621; heat blindness L-625; Sharpe ROI; helper 10x; fallow 28% boost; tool consolidation 44.8% L-644; orient perf L-637. |
| Coordination -- Concurrency & Safety | 36 | Anti-repeat L-283; WIP elbow N=4 L-593; two-layer safety L-525; commit-by-proxy L-526; high-N preemption L-802. |
| Coordination -- Quality & Compliance | 30 | EAD/PCI compliance; structural enforcement L-601; knowledge decay L-633; lane contracts L-775; session compliance L-787. |
| Helper & Validation | 17 | Helper ROI patterns, dispatch policies, foreign-protocol validation; task recognizer 72.5% L-674 (L-309/L-495/L-502/L-515). |
| AI & Tooling | 27 | Async failure modes, proxy-K patterns, historian automation; tool redundancy 44.8% L-644; orient.py 19→14s L-637. |
## What to load when
| Doing... | Read... |
|----|---|
| Any session | active bridge file → `SWARM.md` → `beliefs/CORE.md` → this file → `tasks/NEXT.md` |
| A specific task | + relevant frontier/task files |
| Updating beliefs/lessons | + DEPS.md, PRINCIPLES.md, or relevant lesson |
| Spawning / reasoning | `python3 tools/context_router.py <task>` |
Session log: `memory/SESSION-LOG.md` (append-only, F110-A3)
<!-- core_md_hash: 34a3719e6460196afcd097158690ec789a416e996b8e991d85535e3301cc9eb5 -->