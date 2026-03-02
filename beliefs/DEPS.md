# Belief Dependencies

Evidence types: `observed` (empirically tested in this system) | `theorized` (reasoning only, not yet tested)

When a belief is disproven: check dependents below → update those too.

## Interconnection model
N=20 beliefs (17 numeric B1–B19 + 3 evaluation B-EVAL1–B-EVAL3; 19 observed, 1 theorized), target K≈1 (L-025). K=0 freezes adaptation;
K=N-1 is unstable. Note: validate_beliefs.py counts only numeric B\d+ patterns (17); B-EVAL1–B-EVAL3 are not auto-validated.

```
B1 (git-as-memory)
├── B2 (layered memory) ──→ B7 (protocols)
├── B3 (small commits) ──→ B11 (CRDT knowledge)
└── B6 (architecture) ──→ B7 (protocols)
                       └── B8 (frontier)
                       └── B17 (info asymmetry dominates) [ai]
                       └── B19 (async cascade defense) [ai]
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
- **Depended on by**: B2, B3, B6
- **Last tested**: S381 (CONFIRMED — retrieval RECOVERED 17.5% miss, L-636)

### B2: Layered memory (always-load / per-task / rarely) prevents context bloat
- **Evidence**: observed
- **Falsified if**: A session following the layered protocol hits context limit before completing a standard task, OR sessions ignoring layering complete equivalent tasks at equal context cost
- **Depends on**: B1
- **Depended on by**: B7
- **Last tested**: S392 (CONFIRMED — 0 context-limit hits despite 430→710L growth, 85% savings sustained)

### B3: Small commits aid backtracking and session handoff
- **Evidence**: observed
- **Falsified if**: Recovery from a broken-state session takes more tool calls with small commits than with large-batch commits, OR cross-session handoffs fail at equivalent rates regardless of commit granularity
- **Depends on**: B1
- **Depended on by**: B11
- **Last tested**: S396 (CONFIRMED — N≥10 concurrency, 700+ commits, 0 regressions, L-526)

### B6: The system's architecture is blackboard+stigmergy; "swarm" is brand name only
- **Evidence**: observed
- **Falsified if**: A coordination mechanism observed in ≥3 sessions cannot be classified as either blackboard or stigmergy, OR an alternative architecture model makes better predictions about observed coordination failures
- **Depends on**: B1
- **Depended on by**: B7, B8, B17, B19
- **Last tested**: S395 (WEAKENED — base BB+stigmergy CONFIRMED; upper layers are engineered governance not emergent. B19 DANGEROUS — sync upper layers reintroduce cascade risk)

### B7: Regularly-invoked protocols compound system quality over time
- **Evidence**: observed
- **Falsified if**: Quality metrics (accuracy, swarmability, context load) show no improvement over 20+ consecutive protocol-following sessions, OR ad-hoc sessions achieve equivalent quality without protocol invocation
- **Depends on**: B2, B6
- **Depended on by**: B12, B16
- **Last tested**: 2026-03-01 S398 (FALSIFICATION ATTEMPT — CONFIRMED. SciQ compounds: 0.019→0.247 (13x, n=417 experiments). Post-EAD SciQ acceleration 6.4x. PCI 0.950 vs SciQ 0.247 = 70pp gap — compliance 4x faster than quality. L/session peaked pre-enforcement (5.77→4.41, -23%). Falsification NOT met: quality improves monotonically. L-824.)

### B8: The frontier is a self-sustaining task generation mechanism
- **Evidence**: observed
- **Falsified if**: 5+ consecutive active sessions close frontiers without generating new ones, OR new frontier questions consistently require external injection rather than emerging from work
- **Depends on**: B6
- **Last tested**: S381 (CONFIRMED — 152 frontiers, 88% resolution, 36/36 domains generating via UCB1)

### B9: K_avg*N+Cycles is a reliable predictor of software maintenance burden across different codebases and languages
- **Evidence**: observed
- **Falsified if**: K_avg*N+Cycles fails to correctly rank maintenance burden on 3+ non-Python codebases, OR raw line count proves equally predictive
- **Depends on**: none
- **Depended on by**: B10
- **Last tested**: S396 (CONFIRMED — 14-package 4-language evidence uncontradicted, swarm NK K_avg=2.587 corroborates)

### B10: Cycle count is a stronger predictor of unresolvable (long-lived) bugs than K_avg or K_max
- **Evidence**: observed
- **Falsified if**: High cycle count (>5) codebase has fewer long-lived bugs than zero-cycle similar composite, OR cycles add no predictive power over K_avg*N across 5+ packages
- **Depends on**: B9
- **Last tested**: S396 (CONFIRMED — 9-module evidence holds, swarm pure DAG with <5% bug-fix sessions as predicted)

### B11: Append-only markdown knowledge files are CRDT-safe for concurrent agent writes; structured formats (JSON, YAML) are untested
- **Evidence**: observed (markdown scope only)
- **Falsified if**: Two concurrent sessions produce an unrecoverable merge conflict in an append-only markdown knowledge file, OR a superseded entry is silently overwritten rather than marked superseded. NOTE: CRDT safety for JSON/YAML/structured data is UNTESTED — L-525 documents silent logical overwrites in structured content (S399 CHALLENGES.md audit)
- **Depends on**: B3
- **Last tested**: S399 (CONFIRMED markdown scope, OPEN structured-data scope — CHALLENGES.md audit)

### B12: Coordination tool adoption follows a power law — workflow-embedded tools achieve ~100% adoption while invocation tools achieve <20%
- **Evidence**: observed
- **Falsified if**: An invocation tool achieves >50% adoption across 10+ consecutive sessions without workflow embedding, OR a workflow-embedded tool falls below 60% adoption
- **Depends on**: B7
- **Last tested**: S396 (CONFIRMED BIMODAL — tool-enforced 91.8% vs spec-only 2.5%, L-775 n=65)

### B13: Incorrect error handling is the dominant cause of catastrophic distributed systems failures (53-92%)
- **Evidence**: observed (24 systems, 5 studies; Yuan OSDI 2014)
- **Falsified if**: 100+ sample <50% EH attribution
- **Depends on**: none
- **Depended on by**: B14
- **Last tested**: S394 (CONFIRMED)
- **Domain**: distributed-systems

### B14: Most distributed bugs (98%) reproducible ≤3 nodes; determinism 50-67% (revised from 74%)
- **Evidence**: observed (L-690: Antithesis/Jepsen 2024-2026 external validation confirms 3-node sufficiency; L-699: swarm determinism 50-67%, lower than original 74% — gradient holds, magnitude revised)
- **Falsified if**: 50+ sample >10% require ≥5 nodes, or >50% non-deterministic
- **Depends on**: B13
- **Last tested**: S410 (CONFIRMED with revision, L-690 L-699)
- **Domain**: distributed-systems

### B15: CAP theorem — linearizability and availability mutually exclusive during partitions
- **Evidence**: observed (S397, L-816)
- **Falsified if**: linearizable+available during verified partition
- **Depends on**: none
- **Last tested**: S397 (CONFIRMED, P-267)
- **Domain**: distributed-systems

### B16: Knowledge decay is present but asymmetric — specific claims decay faster than extracted principles, making it visible on reading but invisible to growth metrics
- **Evidence**: observed
- **Falsified if**: A re-audit finds principles decay at the same rate as specific claims (>30% stale principles), OR stale-lesson fraction increases proportionally with session count (i.e., growth metrics DO track decay)
- **Depends on**: B7
- **Last tested**: S394 (CONFIRMED — 15% mechanism-superseded vs 0% principle-contradicted, L-633/P-226)

### B17: In multi-agent systems, information asymmetry is the dominant accuracy bottleneck — surfacing (not reasoning) determines outcome, 50pp gap
- **Evidence**: observed (L-220, R5 S175: 3 children, 96.7% integration once received)
- **Depends on**: B6 (vestigial)
- **Falsified if**: >80% accuracy without resolving info asymmetry, via reasoning improvements only
- **Last tested**: S394 (CONFIRMED — surfacing r=0.564 vs absorption r=0.066)
- **Domain**: ai

### B18: Capability and vigilance are independent axes — improving task performance doesn't improve verification quality
- **Evidence**: observed (L-219, R5: t(45)=-0.99, p=.328)
- **Depends on**: none
- **Falsified if**: r>0.5 between capability and verification-discipline metrics across ≥30 agents
- **Last tested**: S394 (CONFIRMED — independence holds, external corroboration)
- **Domain**: ai

### B19: Async sharing prevents cascade anchoring — sync converts positive cascades to negative
- **Evidence**: observed — **PARTIALLY FALSIFIED** (S395: base async holds, sync upper layers reintroduce cascading)
- **Depends on**: B6 — **DANGEROUS under B6 refinement** (sync council/dispatch undermines async-only defense)
- **Falsified if**: Equivalent cascade rates between sync and async protocols on same task set
- **Last tested**: S395 (PARTIALLY FALSIFIED — hybrid architecture vulnerability, L-218)
- **Domain**: ai

### B-EVAL1: Internal health metrics necessary but not sufficient — process integrity ≠ outcome effectiveness
- **Evidence**: observed (L-599, S356: 355 sessions health, 0 external validation; S415 N=838: ECE=0.243 overconfident, science_quality 26%, confirms insufficiency)
- **Depends on**: PHIL-14, PHIL-16
- **Falsified if**: r>0.8 internal health vs external validation over ≥20 sessions
- **Last tested**: S415 (CONFIRMED — process composite 2.0/3 but ECE=0.243, external grounding 5%) | **Domain**: evaluation

### B-EVAL2: At 299L+, quality binds over quantity — frontier resolution > new lessons
- **Evidence**: observed (L-599: ~15 metaphor + ~10 circular at 539L; S415 N=838: L-912 integration-bound at N≈550-575, recent Sharpe 8.2 vs historical 7.5)
- **Depends on**: B-EVAL1, F-GAME3
- **Falsified if**: Lesson Sharpe constant/increasing across S190-S210
- **Last tested**: S415 (CONFIRMED and STRENGTHENED — L-912 integration-bound regime confirms quality over quantity) | **Domain**: evaluation

### B-EVAL3: Good enough for autonomous operation, NOT for external claims until PHIL-16 met
- **Evidence**: observed (S415: 416 sessions sustained; PHIL-16 still open; F-COMP1 open 27s; external grounding = 5.0% signals only)
- **Depends on**: B-EVAL1, PHIL-16
- **Falsified if**: External grounding >10% over 30-session window
- **Last tested**: S415 (CONFIRMED — autonomous operation sustained 416 sessions; PHIL-16 still unmet) | **Domain**: evaluation

---

## Superseded
Retired beliefs kept for traceability.

- **~~B4~~**: General productivity truism, isolated (K=0), never load-bearing.
- **~~B5~~**: Verification-risk truism already covered operationally by the 3-S rule.
