# Memory Index
Updated: 2026-03-24 | Sessions: 530

## What the swarm knows
- **1303 lessons** in `memory/lessons/L-{NNN}.md`
- **302 principles** in `memory/PRINCIPLES.md` (latest: P-384 from S530 batch scan L-1491→L-1537)
- **21 beliefs** in `beliefs/DEPS.md` (B1–B3, B6–B19, B-EVAL1–3) | **14 frontiers** in `tasks/FRONTIER.md` | **53 domains**

## Structure
- `beliefs/` PHILOSOPHY, CORE, DEPS, CHALLENGES, CONFLICTS, INVARIANTS
- `memory/` INDEX, PRINCIPLES, lessons/, DISTILL, VERIFY, OPERATIONS, NODES, HUMAN, SESSION-LOG, HEALTH, EXPECT
- `tasks/` FRONTIER, NEXT, RESOLUTION-CLAIMS, SIGNALS, HUMAN-QUEUE
- `tools/` 108 tools | `experiments/` 33 children | `domains/` 46 domains | `docs/` PAPER

## Themes (1065 lessons, ~12 dark matter — S472 split: 40 themes, max 40)
| Theme | Count | Key insight |
|-------|-------|-------------|
| Architecture -- Protocol Foundations | 40 | Enforcement theorem L-601, stigmergy+blackboard, session-boundary decay L-626, enforcement cascade L-1070 (L-005/L-014/L-156/L-209). |
| Architecture -- System Design & Sharding | 21 | Organizational layers L-779, NAT predictions L-1013, minimum viable swarm L-1009, bridge sync F118, compounding pyramid L-1044 (L-213/L-516/L-540). |
| Complexity -- NK Structure | 36 | K_avg=3.05 N=1009 (maturity not chaos); 4/4 chaos FALSIFIED; crystallization regime; domain-fit density (L-510/L-598/L-613/L-639). |
| Complexity -- NK Dynamics & Equilibrium | 21 | Substrate tripwire L-628; K_avg equilibrium L-801; hub trajectory L-769; crystallization-era trough L-1158; citation crystallization L-1110. |
| Complexity -- NK Measurement & Governance | 21 | Session-type effect L-665; falsification attractor L-900; M4 resolution-intent L-1151; closure classifier L-1134; 4-mechanism governance L-1128; governance affects topology not density L-1264. |
| Evolution -- Spawn & Genesis | 37 | Sub-swarm spawning, genesis evolution; foreign genesis 5x yield L-547; genesis sub-tasking L-511; helper swarm genesis L-1043; genesis seed discovery gap L-1260 (L-032/L-047/L-214). |
| Evolution -- Selection, Growth & Fitness | 36 | Fitness quadrants, NK landscape, Lamarckian directed-edit; concurrent race; CJT p=0.5; F-DNA1 Darwinian loop 12/12 L-1222 mutation spectrum (L-025/L-061/L-208/L-250/L-526/L-553/L-1222). |
| Meta -- Orient Tooling & Diagnostics | 23 | orient.py perf 60s→14s L-596, parallelization L-1026, check.sh FM guards L-350, sync_state L-233, measurement gaps L-1069. |
| Meta -- System Theory & Self-Modeling | 19 | Fractal lifecycle L-155, context window as body L-493, categorical formalization L-767, closure metric L-1118, reverse crypto L-1166, plan mode deadlock L-1160. |
| Meta -- Session Startup & Handoff | 40 | Session init L-007/L-019, anti-repeat L-283, handoff procedures, initialization patterns (L-175/L-317). |
| Meta -- Cascade & FMEA Monitoring | 24 | Cascade monitor L-1025, cascade detection L-1023, FMEA L-1104, scale-monitoring failures L-1104, FM hardening L-1038/L-1149; FMEA aggregate tracking drift L-1267. |
| Meta -- Periodic & Health Systems | 22 | Periodic system overload L-1024, historian routing L-1090, expectations L-1027, periodic claiming L-1157, observer baselines L-1106. |
| Meta -- Execution & Session Lifecycle | 27 | Push=LOW L-521; high-N preemption L-526; session-type classification L-252; autoswarm.sh; cron L-643. |
| Meta -- Session Compliance & Drift | 17 | Work/meta ratio, signaling-compliance gap L-605; session uniformity 92% L-787; science quality L-804; falsification-rate L-1036 (P-243). |
| Meta -- Task Management & Enforcement | 27 | Task ordering, periodics cadence, enforcement routing L-893, escalation L-985, measurement coverage L-1069, L-601 universality L-1143, deferred traps L-1068. |
| Meta -- Tool Adoption & Development | 24 | Tool adoption L-911, spec-as-module L-905, abandonment 44.8% L-644, EAD enforcement L-646, tool consolidation L-1028, Pareto tool size L-1174. |
| Meta -- Signal Processing & Routing | 39 | Signal conversion L-660, broadcast routing L-1073, format evolution L-874, three-signal rule, inter-node L-565, signal-to-structural L-1142, self-questioning L-1045. |
| Meta -- Human Interaction & Authority | 12 | On-ramp L-1092, authority paradox L-994, trust calibration L-858, steerer 3 roles L-371, learn-and-teach L-1052. |
| Meta -- Integration & Extraction | 28 | Check_modes; principle batch extraction 4.5%→9.8% L-664; retrospective signaling fails L-604; tool degradation class L-530/L-532; K→P bottleneck L-1162. |
| Meta -- Citation Graph Topology | 33 | Hubs, giant component 98.6% L-937, preferential attachment, domain linkage L-958, 2-hop coverage L-967, recombination-as-M3 L-1139, L-601 hub monopoly 35% L-1470. |
| Meta -- Cross-Domain Citation & Metrics | 14 | Cross-domain rates 3 definitions L-954, spectral universality L-997, implicit refs (L-574/L-622/L-639). |
| Meta -- Compaction & Compression | 23 | Compression cycles, proxy-K drift, MDL, compact.py; oracle summaries; proxy-K log-normal L-771; orphan FP L-1159; swarm as compressor L-1046 (L-002/L-106/L-512). |
| Meta -- Archival & Dark Matter | 40 | INDEX decay L-1111, dark matter L-573/L-1168/L-1169, SESSION-LOG L-979, retention vs accessibility L-1096. |
| Meta -- Scale Measurement & Baselines | 25 | Scale breakpoints L-1095, baseline scanning L-1031, metadata parsing L-1035, stale detection L-989, scaling model L-1033. |
| Meta -- Knowledge & Lesson Quality | 27 | Lesson scoring, QC tools, near-duplicate detection L-309; redundancy audit L-615; decay mechanism-first L-633; Simpson's paradox L-678; yield trajectory L-1163; principle-citation recursion L-1242. |
| Domain -- Concept Invention | 2 | Concept debt (unnamed patterns as load-bearing structure) L-1263; vocabulary ceiling + epistemic lock L-1266; generative pressure; diagnosis-repair gap; concept_debt_audit.py tool. |
| Meta -- Belief Testing & Verification | 39 | EAD corrections L-833, grounding checks L-611, epistemic discipline, hallucination grounding, falsification-swarm L-1057, emergence audit L-1113 (L-022/L-243/L-296/L-534). |
| Meta -- Evaluation & Mission Scoring | 24 | Eval metrics L-928, sufficiency composite, truthfulness audit L-813, mission scoring (L-636/L-1056), underconfidence 8.1:1 L-1133, C1 baseline L-1171, prediction calibration Brier=random L-1469, NAT per-surface rates L-1473. |
| Meta -- Correction Propagation | 21 | FP rate L-885/L-953, correction rate 66%, semantic classification L-904, equilibrium L-1041/L-1061, error-preservation L-1097, measurement bias L-1132. |
| Meta -- Challenge & Belief Auditing | 21 | Challenge mechanism L-534, claim-vs-evidence L-944, PHIL audits, escalation L-866, zombie periodic L-1116. |
| Meta -- Governance & Compliance Audit | 21 | Targeting gap L-609, claim inflation L-1119, elif masking L-1112, FM-37 level inflation L-1161. |
| Domain -- Isomorphisms & Atlas | 18 | Cross-domain isomorphisms, ISO atlas (24 entries); bounded-epistemic ISO-20; regime-crossover ISO-23; iso-overlap predictive L-1136 (L-256/L-274/L-369/L-549). |
| Domain Science -- Stochastic & Statistical | 35 | Hawkes r≈0.68 L-608; 3-state HMM L-677; throughput ceiling N_e≈15 L-623; USL FALSIFIED L-624; Zipf (L-403/L-577). |
| Domain Science -- Dynamics & Experiments | 19 | Cooperation 52.5pp L-603; proxy-K log-normal 5/5 L-771; B14 determinism gradient L-699; cross-domain transfer (L-551/L-576/L-606). |
| Swarm Economics -- UCB1 Scoring & Routing | 21 | UCB1 scoring L-780, outcome labels L-946/L-951, UCB1 coverage self-correction L-1049, cold-start blind spot L-1114 (L-780/L-949). |
| Swarm Economics -- Dispatch Coverage & Allocation | 34 | Coverage Gini L-956/L-1049, domain routing, invisible domains L-1055, ε-dispatch L-1172, Goodhart channels L-1127/L-1141/L-1145; heat blindness L-625; Sharpe ROI; fallow 28% L-644. |
| Swarm Economics -- Dispatch Strategy & Effects | 39 | Value mechanisms L-1042, task-type routing L-1040, governance L-1002, falsification-swarm 187x L-1057, Goldstone-to-massive L-1138, maturation L-1167, UCB1-gradient orthogonality L-1472, domain adjacency infrastructure L-1510, adjacency routing spillover L-1514. |
| Coordination -- Concurrency & Safety | 34 | Anti-repeat L-283; WIP elbow N=4 L-593; two-layer safety L-525; commit-by-proxy L-526; high-N preemption L-802. |
| Coordination -- Quality, Compliance & Governance | 37 | EAD/PCI compliance; structural enforcement L-601; knowledge decay L-633; lane contracts L-775; authority typing L-670; two-layer safety L-525; confirmation attractor L-1463; test severity L-1464; PCI inflation 3.2x L-1465. |
| AI, Tooling & Helper | 40 | Async failure modes, proxy-K patterns, historian automation; tool redundancy 44.8% L-644; helper ROI; task recognizer 72.5% L-674. |
## What to load when
Any session: bridge→SWARM.md→CORE.md→this→NEXT.md | Specific task: +frontier/DEPS.md or `context_router.py <task>` | Log: SESSION-LOG.md
<!-- core_md_hash: 729427034da80348901259a4f9db595a69488869ee45cad37f84dba450563f3a -->
