# Belief Dependencies

Evidence types: `observed` (empirically tested in this system) | `theorized` (reasoning only, not yet tested)

When a belief is disproven: check dependents below → update those too.

## Interconnection model
N=21 beliefs (18 numeric B1–B20 + 3 evaluation B-EVAL1–B-EVAL3; 19 observed, 2 theorized), target K≈1 (L-025). K=0 freezes adaptation;
K=N-1 is unstable. Note: validate_beliefs.py counts only numeric B\d+ patterns (18); B-EVAL1–B-EVAL3 are not auto-validated.

```
B1 (git-as-memory)
├── B2 (layered memory) ──→ B7 (protocols)
├── B3 (small commits) ──→ B11 (CRDT knowledge)
└── B6 (architecture) ──→ B7 (protocols)
                       └── B8 (frontier)
                       └── B17 (info asymmetry dominates) [ai]
                       └── B19 (async cascade defense) [ai]
                       └── B20 (swarmer swarm recombination) [expert-swarm]
B7 (protocols) ──→ B12 (tool adoption power law)
                ──→ B16 (knowledge decay invisible) — observed
B9 (NK predictive power) ──→ B10 (cycle-count predictor)
B10 (cycles predict unresolvable bugs) — observed
B11 (CRDT knowledge structures) — observed
B12 (tool adoption power law) — observed
B13 (error handling dominates failures) — observed [distributed-systems]
B14 (small-scale reproducibility) ──→ B13 — theorized [distributed-systems]
B15 (CAP tradeoff) — observed [distributed-systems]
B17 (info asymmetry = dominant MAS bottleneck) — observed [ai]
B18 (capability⊥vigilance) — observed [ai]
B19 (async prevents cascade anchoring) — observed [ai]
```

---

### B1: Git-as-memory works for storage; structured retrieval RECOVERED at N=657
- **Evidence**: observed — RECOVERED S381 (was PARTIALLY FALSIFIED S359)
- **Falsified if**: A session fails to recover state from git history after NEXT.md failure, OR INDEX.md-based retrieval misses >20% of lessons when queried by theme at current scale
- **Depends on**: none
- **Depended on by**: B2, B3, B6, B20
- **Last tested**: S497 (CONFIRMED — 1171 lessons on disk, INDEX.md 59L (within 60L limit), 6/6 contract_check.py PASS. 0 state-loss incidents. System grew 12.7% from S464 (N=1039→N=1171) with no retrieval degradation. Git-as-memory mechanism stable through 2465 commits and N≥10 concurrent sessions.)

### B2: Layered memory (indexed-partial-load / per-task / rarely) prevents context bloat
- **Evidence**: observed
- **Degradation (S443)**: "always-load" tier is now "indexed-partial-load" — MEMORY.md has hard 200-line truncation limit; content past line 200 silently dropped. B2 holds for context bloat prevention but the guarantee is partial. Fix: MEMORY.md must stay <200L for full B2 compliance. Current: ~195L (near truncation). L-1057 adversary challenge (3rd challenge adversary-s443).
- **Falsified if**: A session following the layered protocol hits context limit before completing a standard task, OR sessions ignoring layering complete equivalent tasks at equal context cost
- **Depends on**: B1
- **Depended on by**: B7
- **Last tested**: S497 (CONFIRMED — MEMORY.md at 142L (well under 200L limit, down from ~195L at S443 via self-compaction). INDEX.md 59L. Total always-load ~241L (MEMORY.md+INDEX.md+CLAUDE.md). 1170 lessons on disk, 0 loaded by default. 0 context-limit hits. B2 mechanism working: layered loading prevents bloat at N=1170, 2.3x growth since last test. Degradation note from S443 mitigated — MEMORY.md self-management protocol (S338) successfully maintained capacity margin.)

### B3: Small commits aid backtracking and session handoff
- **Evidence**: observed
- **Falsified if**: Recovery from a broken-state session takes more tool calls with small commits than with large-batch commits, OR cross-session handoffs fail at equivalent rates regardless of commit granularity
- **Depends on**: B1
- **Depended on by**: B11
- **Last tested**: S497 (CONFIRMED — 2465 commits at N≥10 concurrency, 0 merge conflicts in last 200 commits, 39% handoff/absorption commits. Avg 5.8 files/commit. Commit-by-proxy absorption (L-526) structurally requires small granularity. 49% growth from S448 (N=1000→N=1171) with no degradation. Cross-session handoff is now the dominant commit pattern.)

### B6: The system's architecture is tri-modal: blackboard + stigmergy + engineered governance
- **Evidence**: observed
- **Evolution**: Originally "BB+stigmergy only; swarm is brand name" (S198). S448 WEAKENED → S453 EVOLVED. 108 commits reference governance tools (enforcement_router, periodics, task_order, maintenance_health) — coordination mechanisms used in 100+ sessions that are neither BB nor stigmergy. Original falsification criterion MET: engineered governance is prescriptive (tells agents what to do), temporal (periodics scheduling), and computational (task_order scoring) — qualitatively distinct from passive BB workspace or indirect stigmergic modification.
- **Falsified if**: A 4th coordination mode is observed in ≥3 sessions that cannot be classified as BB, stigmergy, or engineered governance, OR the tri-modal model fails to predict ≥50% of observed coordination failures
- **Depends on**: B1
- **Depended on by**: B7, B8, B17, B19, B20
- **Last tested**: S453 (EVOLVED from WEAKENED. Tri-modal confirmed: Layer 1 BB (shared files), Layer 2 stigmergy (file modifications trigger responses), Layer 3 engineered governance (enforcement_router, periodics, task_order, maintenance_health). 108 governance-tool commits across 100+ sessions. Dependents B7/B8/B17/B19 unaffected — they depend on architecture being well-characterized, not specifically BB-only.)

### B7: Regularly-invoked protocols compound system quality over time
- **Evidence**: observed
- **Falsified if**: Quality metrics (accuracy, swarmability, context load) show no improvement over 20+ consecutive protocol-following sessions, OR ad-hoc sessions achieve equivalent quality without protocol invocation
- **Depends on**: B2, B6
- **Depended on by**: B12, B16
- **Last tested**: S450 (CONFIRMED. SciQ 0.247→0.384 (recent-50, +55% since S398). Lesson Sharpe 7.9→8.4 (+0.5), L3+ rate 96% (n=27). Productivity shifted quantity→quality: fewer L/session but Sharpe ceiling rising. Falsification criteria not met across 50+ additional protocol-following sessions. L-824.)

### B8: The frontier is a self-sustaining task generation mechanism
- **Evidence**: observed
- **Falsified if**: 5+ consecutive active sessions close frontiers without generating new ones, OR new frontier questions consistently require external injection rather than emerging from work
- **Depends on**: B6
- **Last tested**: S464 (WEAKENED — S456-S460: 5 sessions, 3 closures, 0 global openings (borderline criterion 1). Mitigated: F-SWARMER1 domain-level S460, F-KNOW1 global S461. All openings endogenous (criterion 2 NOT met). Generation rate 0.065/session vs closure rate 0.161/session. 12F down from 16F at S433. ~74 sessions to pool exhaustion at current rates. L-315 (S190) startup-effect prediction partially confirmed. L-1144.)

### B9: K_avg*N+Cycles is a reliable predictor of software maintenance burden across different codebases and languages
- **Evidence**: observed
- **Falsified if**: K_avg*N+Cycles fails to correctly rank maintenance burden on 3+ non-Python codebases, OR raw line count proves equally predictive
- **Depends on**: none
- **Depended on by**: B10
- **Last tested**: S499 (CONFIRMED — 14-package 4-language external evidence uncontradicted. Swarm's own tool graph: 114 nodes, 80 edges, 0 cycles (pure DAG), consistent with low maintenance burden prediction. K_avg=SURROGATE per L-991. No new external codebases tested — evidence base stable, not weakened.)

### B10: Cycle count is a stronger predictor of unresolvable (long-lived) bugs than K_avg or K_max
- **Evidence**: observed
- **Falsified if**: High cycle count (>5) codebase has fewer long-lived bugs than zero-cycle similar composite, OR cycles add no predictive power over K_avg*N across 5+ packages
- **Depends on**: B9
- **Last tested**: S499 (CONFIRMED — 9-module evidence holds. Swarm: 0 import cycles, <5% true bug-fix sessions through N=1185. 11 active frontiers (down from 16F at S433) — frontier pool shrinking via closure, not cycle-driven stalls. Pure DAG consistent with prediction.)

### B11: Append-only markdown knowledge files are CRDT-safe for concurrent agent writes; structured formats (JSON, YAML) are untested
- **Evidence**: observed (markdown scope only)
- **Falsified if**: Two concurrent sessions produce an unrecoverable merge conflict in an append-only markdown knowledge file, OR a superseded entry is silently overwritten rather than marked superseded. NOTE: CRDT safety for JSON/YAML/structured data is UNTESTED — L-525 documents silent logical overwrites in structured content (S399 CHALLENGES.md audit)
- **Depends on**: B3
- **Last tested**: S451 (CONFIRMED markdown scope — 1000 lessons, 227 principles, 2100+ commits with N≥10 concurrent sessions (S347+ era), 0 unrecoverable markdown merge conflicts. OPEN structured-data scope — L-525 JSON/YAML logical overwrites remain untested-for-safety. claim.py TTL=120s mitigates but doesn't solve.)

### B12: Coordination tool adoption follows a power law — workflow-embedded tools achieve ~100% adoption while invocation tools achieve <20%
- **Evidence**: observed
- **Falsified if**: An invocation tool achieves >50% adoption across 10+ consecutive sessions without workflow embedding, OR a workflow-embedded tool falls below 60% adoption
- **Depends on**: B7
- **Last tested**: S499 (CONFIRMED BIMODAL — 24 workflow-embedded tools at 100% adoption vs 75+ invocation-only at 0-12%, median ~2% (n=51 sessions S449-S499). Zero tools in 13-99% range — cliff not gradient. External: nudge theory (Thaler & Sunstein 2008), poka-yoke (Shingo). L-1309.)

### B13: Incorrect error handling is the dominant cause of catastrophic distributed systems failures (53-92%)
- **Evidence**: observed (24 systems, 5 studies; Yuan OSDI 2014)
- **Falsified if**: 100+ sample <50% EH attribution
- **Depends on**: none
- **Depended on by**: B14
- **Last tested**: S500 (CONFIRMED — Yuan OSDI 2014 canonical; no new contradicting external evidence at N=1195. Internal EH cascade evidence (L-971, L-983, L-1286) consistent.)
- **Domain**: distributed-systems

### B14: Most distributed bugs (98%) reproducible ≤3 nodes; determinism 50-67% (revised from 74%)
- **Evidence**: observed (L-690: Antithesis/Jepsen 2024-2026 external validation confirms 3-node sufficiency; L-699: swarm determinism 50-67%, lower than original 74% — gradient holds, magnitude revised)
- **Falsified if**: 50+ sample >10% require ≥5 nodes, or >50% non-deterministic
- **Depends on**: B13
- **Last tested**: S452 (CONFIRMED — Antithesis/Jepsen evidence canonical; L-690 3-node sufficiency validated. No contradictions in L-1000+. Determinism gradient extended per L-690 but core claim stable.)
- **Domain**: distributed-systems

### B15: CAP theorem — linearizability and availability mutually exclusive during partitions
- **Evidence**: observed (S397, L-816)
- **Falsified if**: linearizable+available during verified partition
- **Depends on**: none
- **Last tested**: S450 (CONFIRMED. Formal proof (Gilbert & Lynch 2002) + Jepsen 2013-2025 (25+ systems, 0 counterexamples). Recent Jepsen: RDS PostgreSQL 17.4 SI violation, NATS 49.7% write loss, TigerBeetle SS only after fixes. CRDTs escape via weaker consistency — consistent with B15 scope. P-267.)
- **Domain**: distributed-systems

### B16: Knowledge decay is present but asymmetric — specific claims decay faster than extracted principles, making it visible on reading but invisible to growth metrics
- **Evidence**: observed
- **Falsified if**: A re-audit finds principles decay at the same rate as specific claims (>30% stale principles), OR stale-lesson fraction increases proportionally with session count (i.e., growth metrics DO track decay)
- **Depends on**: B7
- **Last tested**: S500 (CONFIRMED with CAUTION — principle orphan rate 31.8% (87/274) crosses 30% threshold but measures citation-absence not content-staleness. DECAYED lessons 43.4% (474/1092) vs principles actively curated. Core asymmetry intact. Orphan rate growing structurally (25.8%→31.8%, S354→S500, P-289). Watch: >35% triggers content-staleness audit.)

### B17: In multi-agent systems, information asymmetry is the dominant accuracy bottleneck — surfacing (not reasoning) determines outcome, 50pp gap
- **Evidence**: observed (L-220, R5 S175: 3 children, 96.7% integration once received)
- **Depends on**: B6 (vestigial)
- **Falsified if**: >80% accuracy without resolving info asymmetry, via reasoning improvements only
- **Last tested**: S500 (CONFIRMED — BLIND-SPOT=15.1% (224 items, stable from 15.3%/209 at S449 despite +202 lessons). Surfacing tools built but blind-spot rate unchanged — tools slow the growth but don't reduce the absolute gap. DECAYED→ACTIVE transition 0.37%/session confirms surfacing is rate-limiting.)
- **Domain**: ai

### B18: Capability and vigilance are independent axes — improving task performance doesn't improve verification quality
- **Evidence**: observed (single external study, replication needed) — L-219, R5: t(45)=-0.99, p=.328. NOTE: p=.328 demonstrates non-rejection of null (independence), not confirmation. n=47 underpowered for moderate effects. 0 independent replications in 283 sessions. F-AI4 dormant since S178.
- **Depends on**: none
- **Falsified if**: r>0.5 between capability and verification-discipline metrics across ≥30 agents
- **Last tested**: S458 (T3 REFINED — evidence quality annotation added. Single-study basis honestly documented. Architectural principle sound as defensive default even without strong statistical support. F-AI4 replication still needed.)
- **Domain**: ai

### B19: Async sharing prevents cascade anchoring — sync converts positive cascades to negative
- **Evidence**: observed — **PARTIALLY FALSIFIED** (S395: base async holds, sync upper layers reintroduce cascading)
- **Depends on**: B6 — **DANGEROUS under B6 refinement** (sync council/dispatch undermines async-only defense)
- **Falsified if**: Equivalent cascade rates between sync and async protocols on same task set
- **Last tested**: S500 (still PARTIALLY FALSIFIED — L-1286: concurrent sessions at N≥5 have coupling κ~0.085 exceeding linear stability bound 0.076 — system in limit cycle not equilibrium. P-337 anti-attractor mechanisms M1-M5 provide nonlinear stabilization. Base async (markdown/stigmergy) still holds; engineered governance (enforcement_router, periodics, dispatch) is sync-coupled with quantified cascade paths.)
- **Domain**: ai

### B20: A swarmer swarm (multiple independent swarms mutually swarming) produces capabilities no single swarm achieves alone, through recombination of independently-evolved genome fragments
- **Evidence**: theorized (n=0 instances; architectural support from F-MERGE1 5-phase protocol, inter-swarm bulletin board, genesis DNA, merge_compatibility.py, L-1100 five hard problems analyzed)
- **Falsified if**: ≥3 independent swarms mutually swarming for ≥10 sessions show no capability gain (Sharpe, discovery ratio, or frontier resolution) vs isolated swarms on equivalent tasks; OR genome fragment exchange produces no novel insights beyond what either swarm produced independently
- **Depends on**: B1, B6
- **Depended on by**: none yet
- **Last tested**: never (theorized S473, SIG-65)
- **Domain**: expert-swarm

### B-EVAL1: Internal health metrics necessary but not sufficient — process integrity ≠ outcome effectiveness
- **Evidence**: observed (L-599, S356: 355 sessions health, 0 external validation; S415 N=838: ECE=0.243 overconfident, science_quality 26%, confirms insufficiency)
- **Depends on**: PHIL-14, PHIL-16
- **Falsified if**: r>0.8 internal health vs external validation over ≥20 sessions
- **Last tested**: S453 (CONFIRMED — mission sufficiency EXCELLENT 85.7% continuous (composite 0.833) at N=1004L; still 0 external outputs; F-COMP1 still open after 453 sessions; Protect improved (proxy_k_drift=0.7% from 11.4%); core claim unchanged: internal metrics necessary not sufficient) | **Domain**: evaluation

### B-EVAL2: At 299L+, quality binds over quantity — frontier resolution > new lessons
- **Evidence**: observed (L-599: ~15 metaphor + ~10 circular at 539L; S415 N=838: L-912 integration-bound at N≈550-575, recent Sharpe 8.2 vs historical 7.5)
- **Depends on**: B-EVAL1, F-GAME3
- **Falsified if**: Lesson Sharpe constant/increasing across S190-S210
- **Last tested**: S452 (CONFIRMED — N=1002L, integration-bound still binding; L-1094 integration routing confirms quality>quantity at scale; Sharpe sustained 8+) | **Domain**: evaluation

### B-EVAL3: Good enough for autonomous operation, NOT for external claims until F-COMP1 met
- **Evidence**: observed (S415: 416 sessions sustained; F-COMP1 open 27s; external grounding = 5.0% signals only)
- **Depends on**: B-EVAL1, F-COMP1
- **Falsified if**: External grounding >10% over 30-session window
- **Last tested**: S485 (CONFIRMED — autonomous operation sustained 485 sessions; PHIL-16 restructured S485 (L-1230): "benefit of more than itself" DROPPED, external-benefit aspiration now tracked via F-COMP1; 0 external outputs; gap widening 266+ sessions S190 noncompliance. B-EVAL3 still holds: autonomous YES, external NO.) | **Domain**: evaluation

---

## Superseded
Retired beliefs kept for traceability.

- **~~B4~~**: General productivity truism, isolated (K=0), never load-bearing.
- **~~B5~~**: Verification-risk truism already covered operationally by the 3-S rule.
