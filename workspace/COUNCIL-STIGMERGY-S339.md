# Council: Stigmergy Improvements
Session: S339 | Date: 2026-03-01 | Mode: A (Deliberation) | Human signal: "council on stigmergy improvements swarm"

## Panelists
| Seat | Domain | Key framework |
|------|--------|---------------|
| C-07 | Information Science | Shannon channel capacity, rate-distortion |
| C-06 | Distributed Systems | CRDTs, vector clocks, partition tolerance |
| Evolution | Evolution | ACO pheromone dynamics, quorum sensing |
| Control Theory | Control Theory | PID loops, observability, gain scheduling |

---

## Convergent Diagnosis (4/4 agreement)

**The swarm deposits traces but cannot prioritize, decay, or amplify them.**

Each expert arrived at the same structural finding through different vocabulary:

| Domain | Name for the problem | Core statement |
|--------|---------------------|----------------|
| Info-sci | Channel saturation | Uniform-weight, unbounded-deposit channel beyond capacity |
| Dist-sys | Hot-file contention without causal ordering | Last-writer-wins on NEXT.md; no happens-before |
| Evolution | Pheromone saturation syndrome | All trails equally strong; foraging degenerates to random walk |
| Control | Unobservable, uncontrollable stigmergy | No state estimator → no error signal → no control |

**The three missing stigmergy primitives** (P-046 already identified these, but none are implemented):
1. **Amplification** — no mechanism strengthens high-value traces
2. **Evaporation** — decay is manual (compact.py), not automatic
3. **Gradient** — all traces carry equal weight; no priority encoding

---

## Ranked Proposals (by convergence strength)

### TIER 1: Full convergence (4/4 experts agree)

#### S1. Automatic Trace Decay (Evaporation)
**What**: Each lesson/NEXT.md entry gets a `last_touched: S<N>` field. A decay score = `citations / (1 + age_sessions/50)` is computed. Lessons below threshold 0.1 with a PRINCIPLES.md absorbing principle → auto-flagged for archival.
**Who proposed**: Info-sci (exponential decay), Evolution (citation half-life), Control (drift accumulator), Dist-sys (implicit via partition)
**Implementation**: ~30 lines in compact.py + 1 periodics.json entry (every 5 sessions)
**Prediction**: Proxy-K drift stays below 10% without manual compact.py runs. NEXT.md stabilizes below 100 lines.
**Falsification**: Drift exceeds 15% after 2 auto-decay cycles.

#### S2. Trace Priority Encoding (Gradient)
**What**: Add a 2-bit weight field (`Weight: 0-3` = dormant/background/active/critical) to lesson headers. orient.py and context_router.py filter by weight. Total cost: ~840 tokens for 420 lessons.
**Who proposed**: Info-sci (bit-weighted traces), Evolution (fitness gradient), Control (state estimator as compact summary), Dist-sys (priority absent from dispatch)
**Implementation**: ~20 lines in orient.py + batch-tag script
**Prediction**: Sink node re-citation rate rises from 0% to >5% in 30 sessions (dormant lessons become visible for revival or archival). Orient scan focuses on high-weight items.
**Falsification**: No measurable change in citation patterns after tagging.

### TIER 2: Strong convergence (3/4 experts agree)

#### S3. Mandatory Expect-Act-Diff (Error Correction)
**What**: check.sh gate rejects lessons and NEXT.md session notes without `expect:` and `actual:` fields. EAD becomes structural, not advisory.
**Who proposed**: Info-sci (error-correction bits), Control (state estimator prerequisite), Evolution (negative stigmergy overlap)
**Implementation**: ~10 lines in check.sh
**Prediction**: EAD compliance rises from 22% to >80% in 20 sessions. Amplification becomes possible: confirmed predictions get weight boost.
**Falsification**: Compliance stays below 50% after enforcement.

#### S4. Compact State Estimator (`swarm_state.json`)
**What**: A single machine-readable JSON file updated every session: proxy-K drift %, EAD compliance ratio, sessions since last compaction, open/stale lane ratio, tool utilization ratio. ~500 bytes replaces 30k tokens of orient.py output.
**Who proposed**: Control (Luenberger observer), Info-sci (reduce routing entropy), Dist-sys (implicit in partition)
**Implementation**: ~50 lines as new tool or orient.py extension
**Prediction**: Session orientation time drops measurably. State becomes machine-queryable for automated triggers.
**Falsification**: Sessions still read full orient.py output and ignore swarm_state.json.

### TIER 3: Partial convergence (2/4 experts agree)

#### S5. Partition NEXT.md into Per-Session Intent Files
**What**: Replace NEXT.md (single hot file) with `tasks/intents/S<N>.md` (one per session). orient.py reads all intent files as the merge function.
**Who proposed**: Dist-sys (eliminate hot-file contention), Control (reduce coupling)
**Implementation**: ~100 lines (orient.py merge logic + migration)
**Prediction**: NEXT.md merge conflicts drop to zero. No more archive events needed.

#### S6. Randomized Task Selection with Intent Broadcast
**What**: dispatch_optimizer.py samples from top-5 (weighted random) instead of picking top-1. Session writes a 1-line intent file before starting work.
**Who proposed**: Dist-sys (stochastic load balancing), Evolution (foraging efficiency)
**Implementation**: ~30 lines in dispatch_optimizer.py
**Prediction**: Duplicate work rate drops below 5% under 4-session concurrent load.

### TIER 4: Novel domain-specific proposals (1/4, high value)

#### S7. Negative Stigmergy (Repellent Pheromone)
**What**: `## Dead Ends` section in domain FRONTIER.md files. Format: `- REPELLENT: <approach> | tried: S<N> | result: <why> | see: L-<N>`. orient.py surfaces domain-relevant repellents.
**Who proposed**: Evolution (Pharaoh ant repellent pheromone)
**Prediction**: Quality duplication drops from 15.3% toward 8%.

#### S8. Quorum Sensing for Dormant Domains
**What**: Domains inactive >100 sessions get a `fallow_bonus` multiplier (1.28x, per P-201) in dispatch_optimizer.py. Domains fallow >200 sessions trigger frontier redistribution.
**Who proposed**: Evolution (Temnothorax quorum thresholds)
**Prediction**: Active domain ratio rises from 62% to >70%.

#### S9. Session-Scoped Logical Clocks
**What**: Extend commit format to `[S<N> @T<tick>] what: why`. Enables partial causal ordering reconstruction.
**Who proposed**: Dist-sys (Lamport clocks)
**Prediction**: Anti-repeat false-negative rate drops >50%.

#### S10. Gain Scheduling by Session Age
**What**: orient.py partitions recommendations by regime: early (S<100: favor exploration), middle (S100-300: balance), mature (S>300: favor compression/pruning).
**Who proposed**: Control (gain scheduling)
**Prediction**: Net growth rate drops from ~170t/session to <100t/session in mature regime.

---

## Implementation Priority (cost/impact matrix)

| Rank | Proposal | Cost (lines) | Impact | Dependencies |
|------|----------|-------------|--------|-------------|
| 1 | S3: EAD enforcement | ~10 | HIGH — unlocks amplification | None |
| 2 | S4: swarm_state.json | ~50 | HIGH — enables all control | None |
| 3 | S1: Auto-decay | ~30 | HIGH — fixes evaporation | S4 (reads state) |
| 4 | S7: Negative stigmergy | ~20 | MED — prevents re-exploration | None |
| 5 | S2: Priority encoding | ~20 + batch | MED — creates gradient | S4 (reads weight) |
| 6 | S6: Randomized dispatch | ~30 | MED — concurrent scaling | None |
| 7 | S8: Fallow bonus | ~15 | MED — domain activation | None |
| 8 | S5: NEXT.md partition | ~100 | MED — removes hot file | orient.py changes |
| 9 | S10: Gain scheduling | ~30 | MED — maturity-aware | S4 |
| 10 | S9: Logical clocks | ~20 | LOW — causal ordering | Commit format change |

**Recommended first wave (this session)**: S3 + S4 + S7 (total ~80 lines, zero dependencies, immediately testable).

---

## Cross-Domain Isomorphisms Discovered

| ISO | Domains | Pattern |
|-----|---------|---------|
| NEW: ISO-STG1 | info-sci + evolution + control | Trace decay = evaporation = exponential forgetting = integral anti-windup |
| NEW: ISO-STG2 | dist-sys + evolution | Intent broadcast = pheromone deposit at trail head (before foraging, not after) |
| NEW: ISO-STG3 | control + info-sci | State estimator = channel compression = sufficient statistic for stigmergy |
| Extends: ISO-1 | all four | Blackboard+stigmergy = shared memory + indirect coordination (now with 3 missing primitives named) |

---

## Council Verdict

The swarm's stigmergy has **deposit** (well-developed) but lacks the other two legs of the P-046 triad: **evaporation** and **amplification**. This is not a new diagnosis (P-046 identified it), but this council provides the first concrete, cross-domain-validated implementation plan.

The single most impactful change: **S4 (swarm_state.json)** — a compact state estimator that makes the stigmergy landscape observable. Every other improvement depends on being able to read the current state cheaply.

*Council adjourned. Next review: S349 (10 sessions).*
