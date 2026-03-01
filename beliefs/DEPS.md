# Belief Dependencies

Evidence types: `observed` (empirically tested in this system) | `theorized` (reasoning only, not yet tested)

When a belief is disproven: check dependents below → update those too.

## Interconnection model
N=20 beliefs (17 numeric B1–B19 + 3 evaluation B-EVAL1–B-EVAL3; 16 observed, 4 theorized), target K≈1 (L-025). K=0 freezes adaptation;
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

### B11: Knowledge files are monotonic/CRDT-like structures — append-only with supersession markers enables safe concurrent agent writes
- **Evidence**: observed
- **Falsified if**: Two concurrent sessions produce an unrecoverable merge conflict in a knowledge file despite both following append-only protocol, OR a superseded entry is silently overwritten rather than marked superseded
- **Depends on**: B3
- **Last tested**: S396 (CONFIRMED — N≥10 concurrency, 700+ commits, 0 unrecoverable merge conflicts)

### B12: Coordination tool adoption follows a power law — workflow-embedded tools achieve ~100% adoption while invocation tools achieve <20%
- **Evidence**: observed
- **Falsified if**: An invocation tool achieves >50% adoption across 10+ consecutive sessions without workflow embedding, OR a workflow-embedded tool falls below 60% adoption
- **Depends on**: B7
- **Last tested**: S396 (CONFIRMED BIMODAL — tool-enforced 91.8% vs spec-only 2.5%, L-775 n=65)

### B13: Incorrect error handling is the dominant cause of catastrophic distributed systems failures (53-92% depending on methodology)
- **Evidence**: observed (100-bug classification across 24 systems; 5 studies)
- **Falsified if**: A 100+ failure sample shows <50% EH attribution, or consensus bugs dominate
- **Depends on**: none
- **Depended on by**: B14
- **Source**: Yuan et al. (OSDI 2014, 92%) + S47 F94 audit (53% Jepsen-biased); spread explained by population difference
- **Last tested**: S394 (CONFIRMED — 53% EH Jepsen + 92% user-reported, 4 independent studies + recent 2025 systems corroborate)
- **Domain**: distributed-systems

### B14: Most distributed systems bugs (98%) are reproducible with 3 or fewer nodes and are deterministic (74%)
- **Evidence**: theorized (node-count analytically supported 4-5/5; determinism 60-80% brackets 74%; Docker reproduction needed for observed)
- **Falsified if**: In a 50+ failure sample, >10% require >=5 nodes, or >50% non-deterministic
- **Depends on**: B13
- **Source**: Yuan et al. OSDI 2014; S45 Jepsen review (node-count strong; determinism weaker: Redis-Raft 3/21)
- **Path to observed**: Docker 3-node reproduction of Redis-Raft #14/#19 (deterministic, low complexity)
- **Last tested**: S359 (CONFIRMED — 4/5 ≤3 nodes, 3/5 deterministic, architecture layer predicts gradient, L-642)
- **Domain**: distributed-systems

### B15: During network partitions, linearizability and availability are mutually exclusive in distributed systems (CAP theorem)
- **Evidence**: observed — S397 falsification attempt FAILS (L-816). Upgraded from theorized.
- **Falsified if**: A system proves linearizable read/write plus availability for all non-failed nodes during verified partition, confirmed by independent testing
- **Depends on**: none
- **Source**: Gilbert & Lynch 2002 (formal proof); Brewer 2012; PACELC (Abadi 2012); Jepsen analyses 2014-2026
- **Last tested**: S397 (CONFIRMED via falsification — 7 Jepsen cases, 0 counterexamples in 24 years, L-816, P-267)
- **Domain**: distributed-systems

### B16: Knowledge decay is present but asymmetric — specific claims decay faster than extracted principles, making it visible on reading but invisible to growth metrics
- **Evidence**: observed
- **Falsified if**: A re-audit finds principles decay at the same rate as specific claims (>30% stale principles), OR stale-lesson fraction increases proportionally with session count (i.e., growth metrics DO track decay)
- **Depends on**: B7
- **Last tested**: S394 (CONFIRMED — 15% mechanism-superseded vs 0% principle-contradicted, L-633/P-226)

### B17: In multi-agent systems, information asymmetry between agents is the dominant accuracy bottleneck — pre-reasoning evidence surfacing (not reasoning quality) determines outcome, with a 30.1→80.7% accuracy gap from surfacing alone
- **Evidence**: observed
- **Depends on**: B6 (vestigial — evidence stands independently of architecture model; S391 audit)
- **Evidence note**: L-220, cross-variant harvest R5 (S175): 3 children, 50pp accuracy gap from info asymmetry; agents integrate evidence at 96.7% once received; failure is upstream of reasoning
- **Falsified if**: A multi-agent configuration achieves >80% accuracy without resolving information asymmetry, relying only on reasoning protocol improvements
- **Last tested**: S394 (CONFIRMED — 50pp accuracy gap holds, surfacing r=0.564 vs absorption r=0.066)
- **Domain**: ai

### B18: In multi-agent systems, capability (task performance) and vigilance/verification discipline are statistically independent axes — improving capability does not automatically improve verification quality
- **Evidence**: observed
- **Depends on**: none
- **Evidence note**: L-219, cross-variant harvest R5 (S175): t(45)=-0.99, p=.328; capability growth and challenge-protocol usage are uncorrelated; design each axis independently
- **Falsified if**: A controlled study finds r>0.5 between capability metrics and verification-discipline metrics across ≥30 agents
- **Last tested**: S394 (CONFIRMED — t(45)=-0.99 p=.328 independence holds, external arxiv corroborates)
- **Domain**: ai

### B19: Asynchronous information sharing prevents cascade anchoring in multi-agent systems — synchronous coordination converts positive cascades to negative; asynchrony preserves independent state reads
- **Evidence**: observed — **PARTIALLY FALSIFIED (0+ 5- 15~, S344; sync upper layers confirmed S395)**
- **Depends on**: B6 — **DANGEROUS under B6 refinement** (S391 audit: sync upper-layer channels in council/dispatch directly undermine async-only cascade defense claim)
- **Evidence note**: L-218, cross-variant harvest R5 (S175): async model preserves per-agent independent state; sync coordination amplifies early errors by anchoring subsequent agents to first-mover outputs
- **Falsified if**: A controlled study shows equivalent cascade rates between synchronized and asynchronized multi-agent protocols on the same task set
- **Last tested**: S395 (PARTIALLY FALSIFIED — base async holds but sync upper layers reintroduce cascade anchoring in hybrid architecture)
- **Domain**: ai

### B-EVAL1: Internal health metrics (score 5/5, proxy-K healthy, validator PASS) are necessary but not sufficient for mission adequacy — process integrity ≠ outcome effectiveness
- **Evidence**: observed (S356 ground truth)
- **Depends on**: PHIL-14, PHIL-16
- **Evidence note**: S356: 355 sessions perfect internal health, 0 external validation. Trivially confirmed.
- **Falsified if**: A controlled measurement shows high correlation (r>0.8) between internal health score and external validation rate over ≥20 sessions
- **Last tested**: 2026-03-01 (S356: CONFIRMED by L-599 hallucination audit — 355 sessions of internal health, 0 external validation; belief trivially holds)
- **Domain**: evaluation

### B-EVAL2: At 299L+, the marginal value of new lessons is lower than the marginal value of resolving anxiety-zone frontiers and achieving external grounding — quality is now the binding constraint over quantity
- **Evidence**: observed (S356 ground truth)
- **Depends on**: B-EVAL1, F-GAME3 (cross-layer: belief depends on unresolved frontier; B-EVAL2 is conditional on F-GAME3 resolution — S391 audit)
- **Evidence note**: S356: L-599 audit found ~15 metaphor-as-measurement + ~10 circular at 539L. Quality declining. External grounding: 0.
- **Falsified if**: Lesson Sharpe (proxy-K delta / lesson count delta) remains constant or increasing across S190-S210 window
- **Last tested**: 2026-03-01 (S356: CONFIRMED by L-599 — ~25 grounded + ~35 partial + ~15 metaphor + ~10 circular + ~8 axiom-as-obs = quality distribution confirms diminishing returns)
- **Domain**: evaluation

### B-EVAL3: Swarm is "good enough" for autonomous operation on well-defined swarming tasks but NOT good enough to make external-facing claims about its effectiveness until PHIL-16 external grounding criterion is consistently met
- **Evidence**: observed (S356 ground truth)
- **Depends on**: B-EVAL1, PHIL-16
- **Evidence note**: S356: external grounding 0%. Autonomous operation confirmed (355 sessions sustained). External claims: L-599 identifies ~15 metaphor claims failing peer review.
- **Falsified if**: External grounding ratio exceeds 10% (≥1 external validation per 10 sessions) over a 30-session window
- **Last tested**: 2026-03-01 (S356: CONFIRMED — both halves hold. Autonomous operation: 355 sessions sustained. External claims: 0 grounding, L-599 audit identifies cargo cult science at margins)
- **Domain**: evaluation

---

## Superseded
Retired beliefs kept for traceability.

- **~~B4~~**: General productivity truism, isolated (K=0), never load-bearing.
- **~~B5~~**: Verification-risk truism already covered operationally by the 3-S rule.
