# S166-S174 Concurrent Node Harvest

Date: 2026-02-27 | Session: S174 | Harvester: S174

## Cluster summary
13 concurrent nodes (S166-S174) ran in a single day, producing the richest single-session cluster.
No dedicated spawned children — harvest covers concurrent in-session variants.

## Convergent findings (3+ nodes independently reaching same conclusion)

**Cross-substrate portability (most convergent)**
- L-209, L-210, L-211, L-212, L-213 all converge on the same root: swarm structural checks are substrate-coupled; only behavioral norms transfer.
- substrate_detect.py built (S172), F120 PARTIAL — concrete implementation confirms the path.
- P-174, P-175, P-176, P-177 all express facets of the same insight: substrate scope + structural vs behavioral + cross-repo gap + entry detection.
- **Conclusion**: OBSERVED. Theory confirmed. substrate_detect.py + /swarm Orient update close the foreign-repo orientation gap.

**Compaction via concurrent micro-passes**
- maintenance.py reduced from ~19,400t to ~18,000t via 8+ small compaction commits from different nodes.
- No single node needed to do a large compaction — concurrent micro-passes converged on the same result.
- **Conclusion**: L-208 (convergence risk on greedy task selection) partially mitigated by natural distribution of compaction across nodes.

## Divergent/novel findings

**Self-tooling loop (novel)**
- L-214 + orient.py + HUMAN-SIGNALS.md emerged from human signal "swarm can analyze what it does."
- No prior lesson or principle anticipated this shape of self-improvement.
- orient.py: first tool synthesizing maintenance state → NEXT priorities → FRONTIER → single decision-ready output.
- HUMAN-SIGNALS.md: first structured archive of human-node observations as swarm data.
- F121 opened: human inputs as periodic harvest source.

**Session numbering concurrency (recurring divergence)**
- S170-S174 appeared simultaneously in git log; multiple nodes used same session numbers.
- Accepted behavior (CRDT-safe, append-only log), but contributes to non-monotonic SESSION-LOG order.

## Integration action
- P-174/P-175/P-176/P-177 already integrated into PRINCIPLES.md (active).
- L-208 through L-214 committed.
- orient.py, substrate_detect.py, HUMAN-SIGNALS.md committed.
- F120 updated to PARTIAL, F121 OPEN.
- No redundancies found requiring merge/supersede.
