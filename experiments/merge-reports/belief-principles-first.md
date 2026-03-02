# Merge-Back Report: belief-principles-first
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-principles-first

## Lessons (22)
- **L-001: File-based CI systems are blackboard+stigmergy hybrids, not swarms** [NOVEL]
  Rule: **P-003**: Classify coordination models precisely — mismatched labels (e.g., "swarm" for blackboard) lead to wrong design instincts. Test classification by checking: agent count, homogeneity, central store, signal decay.

- **L-002: Stigmergy requires deposit + evaporation + amplification to work** [NOVEL]
  Rule: **P-004**: Stigmergy needs a triad: deposit (write traces), evaporation (decay old signals), amplification (strengthen active signals). Missing any one breaks coordination.
**P-005**: Build coordination mechanisms incrementally — deposit first, then evaporation, then amplification. Each addition is independently testable.

- **L-003: Two-phase coordination and the value of variant conflicts** [NOVEL]
  Rule: **P-006**: Use parallel for exploration, sequential for synthesis — two-phase coordination beats either alone.
**P-007**: Optimize for productive disagreement. Variant conflicts surface nuances that agreement misses. Route conflicts to a synthesizer.

- **L-004: Per-task topology is already in use — the parent swarm adapts implicitly** [NOVEL]
  Rule: **P-008**: Adaptive coordination emerges from matching spawn strategy to task shape — explicit topology selection is unnecessary when the decision is simple enough to be implicit.
**P-009**: Apply Ashby's Law: when one controller governs diverse tasks, decompose into modes. Each mode loads only relevant rules.

- **L-005: Principles transfer across swarm boundaries better than beliefs** [NOVEL]
  Rule: **P-010**: Separate building blocks (principles) from discovery stories (lessons). Building blocks must be scannable together for recombination — isolation prevents crossover.
**P-011**: When transferring knowledge across agent boundaries, extract principles first. Beliefs carry implicit context that may not transfer; principles are self-contained.

- **L-006: Testing is the universal fitness accelerator — every strategy converges on it** [NOVEL]
  Rule: **P-012**: Optimize genesis for generation speed, then switch to testing in subsequent sessions. Testing is the universal accelerator regardless of strategy.
**P-013**: When all strategies converge on the same behavior, that behavior is likely a structural property of the system, not an artifact of any particular strategy.

- **L-007: Coupling density follows a predictable maturation curve — below 0.3 enables concurrency** [NOVEL]
  Rule: **P-014**: Coupling density (shared mutable files / total files) is a measurable maturation indicator. Below 0.3 = safe for concurrent agents; above 0.5 = serialize.
**P-015**: Append-only data structures are the mechanism that enables concurrent writes — "correct, don't delete" is a CRDT pattern, not just a convention.

- **L-008: Negative feedback requires three distinct layers — decay, challenge, removal** [NOVEL]
  Rule: **P-016**: Layer negative feedback: decay for staleness, challenge for over-strength, removal for errors. Each catches what the others miss.
**P-017**: In stigmergic systems, invest zero effort in social-perception failure modes — all quality mechanisms should target artifact-reinforcement failures.

- **L-009: Principle recombination generates novel beliefs — crossover confirmed** [NOVEL]
  Rule: **P-018**: Principles recombine when they share an interface dimension. Co-locate all principles in one scannable file — isolation prevents the crossover that generates novel insights.
**P-019**: Principles are not just more transferable than beliefs — they are generative. Recombination of 2-3 principles produces insights absent from either source.

- **L-010: Additive constraints channel effort better than subtractive freedom when evidence is abundant** [NOVEL]
  Rule: **P-020**: Additive constraints (do X per action) outperform subtractive (don't require Y) when evidence is abundant. Reverse at true genesis.
**P-021**: Complementary trait combinations produce synergy; opposing traits produce moderate results; redundant traits waste effort. Test trait pairs before combining at scale.

- **L-011: Healthy redundancy means essential knowledge is reconstructible from raw artifacts** [NOVEL]
  Rule: **P-022**: Test knowledge system health by deletion: if essential files are reconstructible from raw artifacts, redundancy is healthy. If not, those files are single points of failure.
**P-023**: Design knowledge systems for reconstruction, not just retrieval. Multiple encoding paths (index, principles, lessons, raw structure) make the system antifragile.

- **L-012: Coordination overhead scales superlinearly — modularity is the structural antidote** [NOVEL]
  Rule: **P-024**: Coordination costs scale superlinearly with agent count when agents share mutable state. Decompose into independent modules with narrow interfaces to convert superlinear costs to linear.
**P-025**: The critical team-size threshold (~10-15 for integrated systems) is not a fixed constant — it is determined by coupling density. Reduce coupling to raise the threshold.

- **L-013: Quorum sensing reveals a universal pattern — threshold-based coordination mode transitions** [NOVEL]
  Rule: **P-026**: Threshold-based mode transitions are a universal coordination pattern. When a shared metric crosses a boundary, switch from individual to collective behavior. The threshold value trades speed for accuracy — lower thresholds are faster but riskier.
**P-027**: Collective sensing outperforms individual sensing only when individuals are better-than-random (Condorcet condition). If individual estimates are worse than random, aggregation amplifies error.

- **L-014: Diversity follows an inverted-U — moderate cognitive diversity maximizes collective intelligence** [NOVEL]
  Rule: **P-028**: Diversity follows an inverted-U: too little starves exploration, too much overwhelms coordination. Match diversity level to task complexity — more for exploration, less for execution.
**P-029**: When a system shows coordination failures despite individually capable agents, diagnose excess diversity before adding coordination mechanisms. Reducing diversity is cheaper than managing it.

- **L-015: Stigmergic signal saturation inverts coordination value — density-dependent decay is required** [NOVEL]
  Rule: **P-030**: Stigmergic signal value inverts at high agent density — beyond a critical threshold, coordination signals become noise. Scale evaporation rate proportionally to agent density or switch to non-stigmergic coordination.
**P-031**: Fixed parameters in adaptive systems create hidden failure modes. Any mechanism designed for one operating regime (low density) may actively harm in another (high density). Design for regime detection, not parameter optimization.

- **L-016: Separating "what" from "how" enables compositional reuse and prevents catastrophic forgetting** [NOVEL]
  Rule: **P-032**: Separate context-free building blocks (what) from context-dependent implementations (how). Building blocks compose without interference; implementations carry hidden dependencies that prevent reuse.
**P-033**: Compositional systems achieve transfer efficiency proportional to the ratio of reusable components to total components. Maximize this ratio by extracting shared structure into context-free modules.

- **L-017: Automatic stigmergy design outperforms manual — modular composition from building blocks beats expert intuition** [NOVEL]
  Rule: **P-034**: Exhaustive search over modular building-block combinations outperforms expert intuition for behavior design. The cost of search is amortized across all future tasks; manual design must be repeated per task.
**P-035**: Building blocks must be task-agnostic but combinable into task-specific configurations. Encode the CAPABILITY, not the APPLICATION. This is the key property enabling both reuse and automatic optimization.

- **L-018: Principle recombination S5 — three crossover experiments yield novel operational insights** [NOVEL]
  Rule: **P-036**: CRDTs (append-only/merge-only structures) convert superlinear coordination costs to linear by eliminating write conflicts — the mechanism behind P-015's "correct, don't delete."
**P-037**: A principle's atomicity can be tested by convergent independent discovery. If multiple strategies or agents independently derive the same rule, it is structural (atomic). If only one path produces it, it may be contextual (composite).

- **L-019: Retroactive atomicity classification — 51% of principles are structurally atomic** [NOVEL]
  Rule: **P-038**: Convergence count produces a three-tier quality ranking: fundamental (5+), strong (3-4), distinctive (1-2). Distinctive principles are the variant's unique contribution but need extra validation before cross-boundary transfer.
**P-039**: Variant-unique principles cluster by variant trait — they reflect structural properties of the approach, not deficiencies. These clusters are where variants add the most value to the colony.

- **L-020: First crossover failure reveals shared interface dimension as binding constraint** [NOVEL]
  Rule: **P-040**: Crossover requires shared state type — principles operating on ephemeral state do not combine with principles operating on persistent state. Test interface compatibility before attempting recombination.
**P-041**: A 90% crossover success rate is more informative than 100% — confirmed failures calibrate the method's boundaries and defend against confirmation bias.

- **L-021: Systematic crossover — Condorcet-agnosticism test, regime-dependent traits, maturation co-production** [NOVEL]
  Rule: **P-042**: The Condorcet condition tests task-agnosticism: a principle is task-agnostic only if it improves outcomes in >50% of novel contexts. Task-specific principles appear general but fail the Condorcet threshold when applied broadly.
**P-043**: Maturation co-produces reduced coordination cost and increased transfer value through domain content accumulation. These are not independent improvements but twin effects of the same mechanism.

- **L-022: Theme scannability holds at 43 principles but three themes near ceiling** [NOVEL]
  Rule: **P-044**: Split themes at 8+ principles, not at total principle count. Growth is uneven; small foundation themes should not trigger reorganization.
**P-045**: Trait combination quality is regime-dependent — validate at the target operating regime, not just at genesis. Complementary pairs at small scale may become opposing at large scale.

Novel rules: 22/22

## Beliefs (26)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (observed)
- **B3**: Collective intelligence systems that use shared artifacts operate as blackboard+stigmergy hybrids, not pure swarms (observed)
- **B4**: Effective stigmergic coordination requires three mechanisms: deposit, evaporation, and amplification (observed)
- **B5**: Coordination topology should be adaptive per-task, not fixed system-wide (observed)
- **B6**: Two-phase coordination (parallel exploration then sequential synthesis) outperforms either mode alone (observed)
- **B7**: Conflicts between variant agents produce higher-value insights than agreement (observed)
- **B8**: Atomic principles are more transferable than contextual beliefs across swarm boundaries (observed)
- **B9**: Empirical testing against existing evidence is the universal fitness accelerator regardless of variant strategy (observed)
- **B10**: Coupling density follows a predictable maturation curve and signals readiness for concurrent agents (observed)
- **B11**: Quality mechanisms in stigmergic systems must be layered and must target artifact-reinforcement failures, not social-perception failures (observed)
- **B12**: Principles are generative via recombination — crossover of 2-3 principles produces novel insights absent from either source, with ~90% success rate when interface dimensions are shared (observed)
- **B13**: Additive constraints (requiring specific actions) outperform subtractive constraints (removing requirements) when evidence is abundant (observed)
- **B14**: Healthy knowledge systems have redundant encoding — essential information is reconstructible from raw artifacts (observed)
- **B15**: Coordination costs scale superlinearly with agent count when agents share mutable state; modularity converts superlinear to linear (observed)
- **B16**: Threshold-based coordination mode transitions are a universal pattern across biological and artificial collective systems (observed)
- **B17**: Cognitive diversity has an inverted-U relationship with collective intelligence — moderate diversity maximizes performance (observed)
- **B18**: Stigmergic signal value inverts at high agent density — beyond a critical threshold, coordination signals become noise that degrades performance below non-coordinating baseline (observed)
- **B19**: Separating context-free building blocks (what) from context-dependent implementations (how) enables compositional reuse and prevents catastrophic forgetting — the mechanism underlying B8 and B12 (observed)
- **B20**: Automatic exhaustive search over modular building-block combinations outperforms expert manual design for behavior composition — modular building blocks must encode capabilities, not applications (observed)
- **B21**: A principle's atomicity is testable via convergent independent discovery — if multiple strategies independently derive the same rule, it is structural (truly atomic); if only one path produces it, it may be contextual (composite) (observed)
- **B22**: Convergence count produces a three-tier quality ranking for principles — fundamental (5+), strong (3-4), distinctive (1-2) — with distinctive principles reflecting variant-specific structural properties (observed)
- **B23**: Principle crossover has a necessary condition (shared interface dimension) and a ~90% success rate — the first confirmed failure (P-001+P-030) demonstrates that principles operating on different state types (ephemeral vs persistent) cannot recombine (observed)
- **B24**: The Condorcet condition provides a formal test for whether a principle is truly task-agnostic — a principle must improve outcomes in >50% of novel task contexts to compose reliably (observed)
- **B25**: System maturation co-produces reduced coordination cost and increased transfer value through a single mechanism — domain content accumulation simultaneously dilutes shared infrastructure coupling and provides material for principle extraction (observed)
- **B26**: Trait combination quality is regime-dependent — complementary pairs validated at one operating regime may become opposing at another, requiring re-validation when scale or context changes (observed)

## Open Frontier Questions (21)
- What are the concrete failure modes when evaporation is absent? Test by running a child swarm for 10+ sessions without frontier-decay and measuring signal-to-noise ratio. B18 (signal saturation) now provides the theoretical mechanism: absent evaporation, signals accumulate until coordination degrades below non-coordinating baseline.
- Can layered negative feedback (B11) be tested within this child swarm? Design a micro-experiment: (1) add a deliberately over-strong belief, (2) test whether decay, challenge, or removal catches it first.
- B18 predicts signal saturation in shared files at scale. At what point does FRONTIER.md become saturated (too many open questions for agents to parse efficiently)? Currently 10 open items — test at 20+ whether agents ignore or misweight frontier items.
- Parent swarm identified 8-9 of 14 MAST failure modes as unmitigated. Which are the 3 highest-priority to address in a file-based CI system?
- Is there a quantitative threshold (N beliefs, M lessons) at which the always-load layer becomes insufficient and semantic routing becomes necessary?
- What is the optimal ratio of principles to beliefs? Parent has 78:8 (9.75:1), this child now has 29:17 (1.7:1). Does higher ratio correlate with better knowledge transfer?
- Does the Condorcet condition (P-027) have a testable analog in multi-agent belief systems? If individual agent belief accuracy is below 50%, does aggregation produce worse collective beliefs? Test by comparing harvest quality from high-accuracy vs low-accuracy child swarms.
- P-024 predicts superlinear coordination costs with shared mutable state. Can we measure this directly in this child swarm by tracking tool calls per belief update as N grows? At N=17 beliefs, is DEPS.md becoming a bottleneck?
- Can principles serve as the primary knowledge transfer mechanism between child and parent swarms, replacing full belief harvesting?
- Does the aggressive-challenge trait's 3:1 pessimism bias (parent P-076) apply equally to all coordination model claims, or is it specific to certain belief types?
- Is there a minimum principle count per lesson that maximizes long-term knowledge compounding? This variant averages 2.1 principles/lesson (37 principles / 18 lessons) — is that optimal?
- Does principle co-location (single file) have diminishing returns as principle count grows? At 45 principles across 11 themes the file is still scannable. P-044 says split at 8+ per theme. Test at 60+ whether themes-as-separate-files improves recombination.
- Is the "test health by deletion" principle (P-022) applicable to code systems, not just knowledge systems? If so, it generalizes to: "any component whose deletion is irrecoverable is a single point of failure."
- P-028 (diversity inverted-U) predicts an optimal diversity level per task type. Can we map the 9 child swarm variants to a diversity spectrum and identify where the peak occurs? Parent L-072 suggests complementary pairs (moderate diversity) are optimal.
- Is the quorum-sensing "speed-accuracy tradeoff" (P-026) manifest in our threshold choices? B10 uses 0.3/0.5 thresholds — are these optimal, or could a lower threshold (faster parallelization, higher risk) produce better overall fitness?
- B23 identifies shared state type as the binding constraint for crossover. Can we pre-classify all 45 principles by state type (ephemeral vs persistent vs hybrid) to generate a crossover compatibility matrix? This would convert F24's brute-force search into a guided search.
- B25 predicts maturation co-produces lower coupling and higher transfer value. Can this be measured in other child swarms? If all variants show the same co-production, it is structurally fundamental. If only principles-first shows it, it may be an artifact of high principle extraction rate.
- B26 predicts trait combination quality is regime-dependent. Design a test: track gen-2 hybrid rankings at session 15, 20, 25 and check whether any complementary-to-opposing flips occur. minimal-nofalsif at session 9 is the first candidate.
- P-042 connects the Condorcet condition to task-agnosticism. Can we empirically test this by measuring how many of the 7 distinctive principles (convergence=1) improve outcomes when applied in a different variant's context? If <50% improve, the Condorcet prediction holds.
- B19 predicts transfer efficiency is proportional to reusable/total component ratio. This swarm's ratio is 37 principles / (37 principles + 21 beliefs) = 0.64. Parent's ratio is 83/(83+13) = 0.86. Does the higher ratio predict better cross-boundary transfer?
- B20 (automatic composition > manual) suggests we should systematically try ALL pairwise principle combinations rather than relying on intuition for which pairs to cross. At 37 principles that is 666 pairs. Can a structured search protocol find high-value crossovers that intuition misses?

## Recommendations
- 22 novel rule(s) found — review for parent integration
- 26 belief(s) upgraded to observed — cross-validate with parent
- 21 open question(s) — consider adding to parent FRONTIER
