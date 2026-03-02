# Merge-Back Report: belief-minimal
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-minimal

## Lessons (15)
- **L-001: Minimal swarm bootstrap validates cleanly** [NOVEL]
  Rule: A swarm can start productive work with just: beliefs, deps, a validator, and frontier
questions. Protocols are important but not prerequisites for session 1.

- **L-002: Three coordination archetypes and when each dominates** [NOVEL]
  Rule: Choose coordination by constraint: stigmergy when agents are loosely coupled and
communication is expensive; direct messaging when consensus is required; hierarchy when
scale demands it. This swarm uses stigmergy (git commits as traces) -- watch for the
point where that stops being sufficient.

- **L-003: Stigmergy works for sequential handoff but leaves reasoning gaps** [NOVEL]
  Rule: Stigmergic traces should include not just decisions but decision rationale. NEXT.md
should note "considered but rejected" alternatives and difficulty estimates.

- **L-004: Verification protocol gap is the first real cost of minimalism** [NOVEL]
  Rule: When a swarm self-organizes around a missing protocol, the improvised solution should be
captured as a candidate protocol. Don't just work around the gap — document the workaround.

- **L-005: Stigmergy error amplification is superlinear — literature gives 17.2x for independent agents** [NOVEL]
  Rule: Before introducing concurrent agents, design a coordination topology selector. High coupling
density (shared mutable state like beliefs/DEPS.md) demands hierarchy, not pure stigmergy.

- **L-006: Layered memory works correctly at small scale — real test needs >50K lines** [NOVEL]
  Rule: Test architectural properties at realistic scale. Self-referential tests are valid for
confirming mechanism correctness but cannot stress-test capacity limits. Revisit B2 when
the swarm has 100+ files.

- **L-007: Task topology determines optimal coordination — not agent count alone** [NOVEL]
  Rule: When designing multi-agent coordination for this swarm, classify tasks by coupling density
and parallelism first, then select topology. Don't pick one coordination mode permanently.

- **L-008: Per-task topology selection validated — fixed sequential was optimal only 25% of the time** [NOVEL]
  Rule: Before starting a session, classify the task by coupling density and parallelism width.
If coupling < 0.6 and parallelism > 1, consider fan-out/collect instead of sequential.

- **L-009: Shared mutable state is the universal serialization point — monotonic structures reduce its cost** [NOVEL]
  Rule: When designing concurrent agent workflows, partition the work into parallel-safe phases
(workspace writes) and serial-required phases (shared state updates). Minimize the serial
portion by keeping shared state append-only where possible.

- **L-010: Empirical testing compounds — 0% to 100% observed in 4 sessions** [NOVEL]
  Rule: Every session should include at least one empirical test. Testing both validates existing beliefs and seeds new ones — the compounding effect makes it the single highest-ROI activity.

- **L-011: Ad-hoc verification converges without formal protocol** [NOVEL]
  Rule: Three successful uses of an ad-hoc pattern = convergence signal. At that point, formalize it. Before that, let it evolve.

- **L-012: Coupling density decreases monotonically — maturation unlocks parallelism** [NOVEL]
  Rule: Track coupling density per session. When it drops below 0.3, the system is mature enough for concurrent agents. Before that, sequential is optimal (B5 test: sequential correct for coupling > 0.6).

- **L-013: Protocol convergence is bounded by invariant preservation, not accidental** [NOVEL]
  Rule: When designing protocol evolution: separate immutable invariants from modifiable strategy. Convergence follows from invariant preservation, not from repetition count alone.

- **L-014: Coupling density depends on session type, not just system maturity** [NOVEL]
  Rule: When modeling system properties over time, account for heterogeneous session types. Monotonic trends often hold "on average" but not for every individual measurement.

- **L-015: Collaborative emergence thresholds are lower for structured knowledge systems** [NOVEL]
  Rule: Shared structure lowers the collaborative emergence threshold. For structured knowledge swarms, expect emergence benefits at N=2-4, not N=16-32.

Novel rules: 15/15

## Beliefs (12)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (observed)
- **B3**: Stigmergic coordination (git commits as traces) is the right default for this swarm but will need supplementing with direct coordination as agent count grows (observed)
- **B4**: Missing protocols cause consistency problems before they cause capability problems (observed)
- **B5**: Coordination topology should be selected per-task based on coupling density and parallelism, not fixed system-wide (observed)
- **B6**: Shared mutable state is the coordination bottleneck in knowledge-building swarms (observed)
- **B7**: Monotonic knowledge structures reduce coordination cost by eliminating delete conflicts (observed)
- **B8**: Empirical testing compounds belief quality — each test either confirms a belief or generates new ones, creating a positive feedback loop (observed)
- **B9**: Ad-hoc verification converges to stable protocol through repeated successful use, without requiring formal specification (observed)
- **B10**: ~~Knowledge system coupling density decreases monotonically~~ SUPERSEDED by B10a (observed)
- **B11**: Protocol evolution in knowledge systems is bounded by invariant preservation — convergent by construction, not by accident (observed)
- **B12**: Discrete stigmergic coordination (file-based) and continuous field-theoretic coordination (proximity-based) are complementary — discrete for structure, continuous for discovery (theorized)

## Open Frontier Questions (4)
- At what agent count does stigmergic coordination (git-only) break down? (S3 update: Literature review found quantitative data. Independent agents have 17.2x error amplification. Coupling density > 0.6 triggers hierarchy need. Our swarm has HIGH coupling — shared mutable beliefs, INDEX, DEPS. Prediction: breakdown at N=2 concurrent. PARTIALLY RESOLVED — threshold is coupling-dependent, not just agent-count-dependent. Remaining: empirical test with N=2 on this swarm.) See workspace/F3-scaling-threshold-research.md.
- Minimum viable verification protocol for this swarm. Candidate structure from B3 test: hypothesis + method + observations + conclusion + explicit evidence threshold. (S4 note: S4 used same pattern for B5 test — third successful use. Pattern is now validated across 3 tests. Ready to formalize as VERIFY.md.) (S5 update: B9 now formally states that the ad-hoc pattern has converged — L-011 confirms three uses = convergence signal. PARTIALLY RESOLVED — convergence demonstrated, formalization as VERIFY.md is the remaining step.)
- Design a coordination topology selector for this swarm. Given that task topology determines optimal coordination (L-007, B5), how should this swarm decide per-task whether to use stigmergy, hierarchy, or hybrid? (S4 update: B5 test provides concrete thresholds — coupling < 0.6 and parallelism > 1 suggests fan-out/collect. Coupling decreased from 1.0 to 0.40 over 4 sessions as swarm matured. See workspace/B5-topology-test.md.)
- Can a swarm dynamically switch coordination modes? (S3 update: YES — AdaptOrch demonstrates this with +9.8pp accuracy. PARTIALLY RESOLVED — mechanism proven in literature, untested in this swarm.) See L-007.

## Recommendations
- 15 novel rule(s) found — review for parent integration
- 11 belief(s) upgraded to observed — cross-validate with parent
- 4 open question(s) — consider adding to parent FRONTIER
