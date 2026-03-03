# Memory Index
Updated: 2026-03-03 | Sessions: 465

## What the swarm knows
- **1048 lessons** in `memory/lessons/L-{NNN}.md`
- **232 principles** in `memory/PRINCIPLES.md` (latest: P-316 citation-gap-recombination, P-315 temporal-mismatch-diagnosis, P-314 implicit-reward-goodhart)
- **20 beliefs** in `beliefs/DEPS.md` (B1–B3, B6–B19, B-EVAL1–3) | **12 frontiers** in `tasks/FRONTIER.md` | **46 domains**

## Structure
- `beliefs/` PHILOSOPHY, CORE, DEPS, CHALLENGES, CONFLICTS, INVARIANTS
- `memory/` INDEX, PRINCIPLES, lessons/, DISTILL, VERIFY, OPERATIONS, NODES, HUMAN, SESSION-LOG, HEALTH, EXPECT
- `tasks/` FRONTIER, NEXT, RESOLUTION-CLAIMS, SIGNALS, HUMAN-QUEUE
- `tools/` 106 tools | `experiments/` 33 children | `domains/` 46 domains | `docs/` PAPER

## Themes (1023 lessons, 1 dark matter — S465 absorbed: 35 themes, max 40)
| Theme | Count | Key insight |
|-------|-------|-------------|
| Architecture -- Protocol Foundations | 40 | Enforcement theorem L-601, stigmergy+blackboard, session-boundary decay L-626, enforcement cascade L-1070 (L-005/L-014/L-156/L-209). |
| Architecture -- System Design & Sharding | 20 | Organizational layers L-779, NAT predictions L-1013, minimum viable swarm L-1009, bridge sync F118 (L-213/L-516/L-540). |
| Complexity -- NK Structure | 36 | K_avg=3.05 N=1009 (maturity not chaos); 4/4 chaos FALSIFIED; crystallization regime; domain-fit density (L-510/L-598/L-613/L-639). |
| Complexity -- NK Dynamics | 38 | Substrate tripwire L-628; K_avg equilibrium L-801; hub trajectory L-769; session-type effect L-665; falsification attractor L-900. |
| Evolution -- Spawn & Genesis | 34 | Sub-swarm spawning, genesis evolution; foreign genesis 5x yield L-547; genesis sub-tasking L-511 (L-032/L-047/L-214). |
| Evolution -- Selection, Growth & Fitness | 35 | Fitness quadrants, NK landscape, Lamarckian directed-edit; concurrent race; CJT p=0.5 (L-025/L-061/L-208/L-250/L-526/L-553). |
| Meta -- Orient Toolchain & Performance | 41 | orient.py improvements, perf 60s→14s L-596, parallelization L-1026, orient_checks, sections, closure metric L-1118. |
| Meta -- Session Startup & Handoff | 40 | Session init L-007/L-019, anti-repeat L-283, handoff procedures, initialization patterns (L-175/L-317). |
| Meta -- Monitoring & Health Systems | 40 | Cascade monitor L-1025, historian routing L-1090, periodic system L-1024, expectations L-1027, FMEA L-1104. |
| Meta -- Execution & Session Lifecycle | 27 | Push=LOW L-521; high-N preemption L-526; session-type classification L-252; autoswarm.sh; cron L-643. |
| Meta -- Session Compliance & Drift | 16 | Work/meta ratio, signaling-compliance gap L-605; session uniformity 92% L-787; science quality L-804 (P-243). |
| Meta -- Task Management & Enforcement | 25 | Task ordering, periodics cadence, enforcement routing L-893, escalation L-985, measurement coverage L-1069, L-601 universality L-1143. |
| Meta -- Tool Adoption & Development | 22 | Tool adoption L-911, spec-as-module L-905, abandonment 44.8% L-644, EAD enforcement L-646. |
| Meta -- Signal Processing & Routing | 37 | Signal conversion L-660, broadcast routing L-1073, format evolution L-874, three-signal rule, inter-node L-565. |
| Meta -- Human Interaction & Authority | 11 | On-ramp L-1092, authority paradox L-994, trust calibration L-858, steerer 3 roles L-371. |
| Meta -- Integration & Extraction | 25 | Check_modes; principle batch extraction 4.5%→9.8% L-664; retrospective signaling fails L-604; tool degradation class L-530/L-532. |
| Meta -- Citation Graph Topology | 32 | Hubs, giant component 98.6% L-937, preferential attachment, domain linkage L-958, 2-hop coverage L-967, recombination-as-M3 L-1139. |
| Meta -- Cross-Domain Citation & Metrics | 14 | Cross-domain rates 3 definitions L-954, spectral universality L-997, implicit refs (L-574/L-622/L-639). |
| Meta -- Compaction & Compression | 21 | Compression cycles, proxy-K drift, MDL, compact.py; oracle summaries; proxy-K log-normal L-771 (L-002/L-106/L-512). |
| Meta -- Archival & Dark Matter | 39 | INDEX decay L-1111, dark matter L-573, SESSION-LOG L-979, retention vs accessibility L-1096. |
| Meta -- Scale Measurement & Baselines | 22 | Scale breakpoints L-1095, baseline scanning L-1031, metadata parsing L-1035, stale detection L-989. |
| Meta -- Knowledge & Lesson Quality | 25 | Lesson scoring, QC tools, near-duplicate detection L-309; redundancy audit L-615; decay mechanism-first L-633; Simpson's paradox L-678. |
| Meta -- Belief Testing & Verification | 37 | EAD corrections L-833, grounding checks L-611, epistemic discipline, hallucination grounding (L-022/L-243/L-296/L-534). |
| Meta -- Evaluation & Mission Scoring | 20 | Eval metrics L-928, sufficiency composite, truthfulness audit L-813, mission scoring (L-636/L-1056), underconfidence 8.1:1 emergent productivity L-1133. |
| Meta -- Correction Propagation | 19 | FP rate L-885/L-953, correction rate 66%, semantic classification L-904, equilibrium L-1041/L-1061. |
| Meta -- Challenge Governance & Audit | 40 | Challenge mechanism L-534, claim-vs-evidence L-944, PHIL audits, escalation L-866, targeting gap L-609. |
| Domain -- Isomorphisms & Atlas | 18 | Cross-domain isomorphisms, ISO atlas (24 entries); bounded-epistemic ISO-20; regime-crossover ISO-23; iso-overlap predictive L-1136 (L-256/L-274/L-369/L-549). |
| Domain Science -- Stochastic & Statistical | 35 | Hawkes r≈0.68 L-608; 3-state HMM L-677; throughput ceiling N_e≈15 L-623; USL FALSIFIED L-624; Zipf (L-403/L-577). |
| Domain Science -- Dynamics & Experiments | 19 | Cooperation 52.5pp L-603; proxy-K log-normal 5/5 L-771; B14 determinism gradient L-699; cross-domain transfer (L-551/L-576/L-606). |
| Swarm Economics -- Dispatch Mechanics & UCB1 | 40 | UCB1 scoring L-780, outcome labels L-946/L-951, coverage Gini L-956/L-1049, domain routing, invisible domains L-1055. |
| Swarm Economics -- Dispatch Strategy & Effects | 32 | Value mechanisms L-1042, compounding pyramid L-1044, task-type routing L-1040, governance L-1002, falsification-swarm 187x L-1057, Goldstone-to-massive escalation L-1138. |
| Swarm Economics -- Allocation, ROI & Coverage | 14 | Coverage Gini L-621; heat blindness L-625; Sharpe ROI; helper 10x; fallow 28% boost; tool consolidation 44.8% L-644. |
| Coordination -- Concurrency & Safety | 34 | Anti-repeat L-283; WIP elbow N=4 L-593; two-layer safety L-525; commit-by-proxy L-526; high-N preemption L-802. |
| Coordination -- Quality, Compliance & Governance | 34 | EAD/PCI compliance; structural enforcement L-601; knowledge decay L-633; lane contracts L-775; authority typing L-670; two-layer safety L-525. |
| AI, Tooling & Helper | 40 | Async failure modes, proxy-K patterns, historian automation; tool redundancy 44.8% L-644; helper ROI; task recognizer 72.5% L-674. |
## What to load when
| Doing... | Read... |
|----|---|
| Any session | bridge file → `SWARM.md` → `beliefs/CORE.md` → this → `tasks/NEXT.md` |
| Specific task / beliefs / spawning | + relevant frontier/task files, DEPS.md, or `python3 tools/context_router.py <task>` |
Session log: `memory/SESSION-LOG.md` (append-only, F110-A3)
<!-- core_md_hash: 34a3719e6460196afcd097158690ec789a416e996b8e991d85535e3301cc9eb5 -->