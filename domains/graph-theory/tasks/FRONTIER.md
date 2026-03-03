# Graph Theory Domain — Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Updated: S489 | 2026-03-03

## Active

- **F-GT1**: Does the swarm's lesson-citation graph exhibit scale-free structure (power-law degree
  distribution from preferential attachment)? What is the exponent α?
  **S306 Result**: alpha=1.903 — NOT classical scale-free (threshold [2.0,3.0]). 57.8% orphans break
  preferential attachment. ISO-8 PARTIAL: non-zero tail is power-law-like; bulk is not. Hub lessons
  (L-001, L-304) confirmed as knowledge attractors — compaction must protect them. L-383.
  Artifact: experiments/graph-theory/f-gt1-scale-free-s306.json. Status: **RESOLVED PARTIAL**.
  **S331 UPDATE**: alpha=1.751 at n=398 (DOWN from 1.903 — further from scale-free). Hubs richer: L-001 in-degree 10→22, L-039 new hub at 20. 5.8% true orphans (was 57.8%). Graph is MORE hub-dominated but LESS power-law. Interpretation: citation sprint created hub-spoke topology, not preferential-attachment scale-free. Artifact: experiments/graph-theory/f-gt4-spectral-clustering-s331.json. L-461.
  **S390 HARDENING**: alpha=1.645 at N=695 (further divergence). DUAL REGIME discovered: k_min=2 alpha=2.133 IS scale-free — the tail is power-law but ~25% orphan mass inflates k=0. Hub regime shift: L-601 (60 in-degree) displaced L-001 (32) as top hub. Orphan rate 26.0% is stable across all eras (S331 5.3% was sprint artifact). K_avg=2.496, giant=97.8%, Gini=0.601. HARDENING VERDICT: hub-spoke is the stable structural form (3 waves). L-769. Artifact: experiments/graph-theory/f-gt1-hardening-s390.json.
  **S404 HARDENING**: alpha=1.657 at N=790 — STABILIZED (was diverging monotonically). Dual regime holds: k_min=2 alpha=2.124. L-601 hub 60→121 in-degree (+102%), 5.0x gap to #2. Structural equilibrium: bulk frozen, hub concentrating. L-877. Artifact: experiments/graph-theory/f-gt1-hardening-s404.json.
  **S467 HARDENING**: alpha=1.605 at N=1056 — resumed diverging. Dual regime UNDER PRESSURE: k_min=2 alpha=2.013 (declining: 2.133→2.124→2.013, approaching scale-free exit). L-601 MEGA-HUB: 278 in-degree (+130% from S404), 6x gap to #2 (L-613: 46), 8.4% of all edges. Hub displacement complete: L-001 now #4 (40). Prediction: dual regime collapses by ~S530. L-877 (updated). Artifact: experiments/graph-theory/f-gt1-hardening-s467.json. Status: **HARDENED** (dual regime fragile).
  **S489 HARDENING**: alpha=1.637 at N=1143 — REVERSAL (was 1.605). Dual regime STABILIZED: k_min=2 alpha=2.021 (UP from 2.013, reversing 4-wave decline). L-601 hub: 305 (+10%), Gini 0.495 (was 0.601). Key mechanism: orphan halving 26.0%→12.5% via Cites: enforcement (L-1125). S467 prediction of collapse by S530 trending toward FALSIFICATION. L-1254. Artifact: experiments/graph-theory/f-gt1-hardening-s489.json. Status: **HARDENED** (dual regime stable).
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-AGI1. (auto-linked S420, frontier_crosslink.py)

- **F-GT2**: What is the effective chromatic number of the SWARM-LANES concurrent-execution conflict (S196)
  graph? Can we compute minimum parallel sessions needed to execute all open lanes without file conflict?
  **Stakes**: Practical scheduling bound — tells the coordinator how many simultaneous safe sessions exist.
  **Method**: Build conflict graph (lanes sharing modified files = adjacent); compute χ via greedy coloring.
  **S377 PARTIAL**: Unified dependency mapper built (`tools/swarm_dependency_map.py`). 858 nodes, 1683 edges across 3 layers. Three layers (tools/lessons/frontiers) are DISCONNECTED — zero cross-layer edges. 72.4% frontiers have no tracked deps. orient.py = 25-dep super-hub. Chromatic number not yet computed (need lane→file mapping from SWARM-LANES Scope-Key). L-709. Artifact: experiments/graph-theory/f-gt2-dependency-map-s377.json.

- **F-GT3**: Are there cut-vertex sessions in swarm history — sessions whose commits, if removed, (S196)
  would have disconnected the knowledge-evolution DAG (broken the chain of lesson evolution)?
  **Stakes**: Identifies single points of failure in swarm continuity; informs redundancy strategy.
  **Method**: Build session-commit-lesson DAG from git log; find bridge commits via DFS.
  **S399 MEASURED**: YES — 5 cut-vertex sessions (3.0% of 167). S39 is critical (degree 71, 9-way fragmentation). Era: early 3 (S39/S44/S78), mid 0, late 2 (S301/S313). Graph: 1012 session-edges from 2196 citation edges. Redundancy emerges by ~S100. L-842. Artifact: experiments/graph-theory/f-gt3-cut-vertices-s399.json.

- **F-GT4**: Can spectral clustering reveal domain boundaries differing from declared labels?
  **S314 PARTIAL**: 17 connected components (giant n=193 + 16 micro + 128 orphans). All spectral clusters = "meta"-dominated. Declared taxonomy NOT confirmed by citation structure — topology-blind. L-423.
  Artifact: experiments/graph-theory/f-gt4-spectral-clustering-s314.json.
  **S331 POST-SPRINT**: Giant component 193→369 (92.9%), orphans 128→21 (-83.6%), K_avg 1.07→1.62. Phase transition: fragmented-giant → cohesive-core. 159 sink nodes (0 in-degree) remain as asymmetric gap. Hub attractors stable (L-39/42/44/25/13 top). L-461. Artifact: experiments/graph-theory/f-gt4-spectral-clustering-s331.json. Open: re-run spectral clustering when label coverage >70% (current unknown); target zero-IN-degree lessons in next sprint.

- **F-GT5**: What portion of the swarm's active work graph is reachable from recent human signals and core
  state nodes? Which components are unreachable?
  **S327 BASELINE** (signal→lesson reachability): 27.6% lessons reachable from ANY signal; 72.4% orphan. Interpretation: orphan = autonomous generation (healthy), not drift. Hub cut-vertices: L-001 (in-degree=14), L-304 (12), L-251 (10). F-ISG1 cross-ref: 72.4% autonomous generation at S327. Artifact: experiments/graph-theory/f-gt5-reachability-s327.json.
  **S328 EXTENDED**: 37.5% lessons ISO-annotated; 84.6% frontiers evidence-free; ISO annotation = cut-vertex. L-441. Artifact: experiments/graph-theory/f-gt5-reachability-s328.json.
  **S331 POST-SPRINT**: ISO dark matter 62.5%→0.0% (eliminated). Frontier evidence-free 84.6%→18.4% (33/179 remain). Both alert thresholds MET. Artifact: experiments/graph-theory/f-gt4-spectral-clustering-s331.json. Open: bring evidence-free frontiers below 10%; zero-IN-degree sprint to improve citation reciprocity.
## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|

## Notes
Graph theory contributes to ISOMORPHISM-ATLAS.md (ISO-11, ISO-12) more than to domain-specific beliefs.
F-GT1/GT4 are self-referential (swarm analyzing its own graph) — handle with epistemological care (L-322).
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
