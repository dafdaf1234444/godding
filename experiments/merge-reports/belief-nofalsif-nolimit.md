# Merge-Back Report: belief-nofalsif-nolimit
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-nofalsif-nolimit

## Lessons (16)
- **L-001: Coordination topology trumps agent quantity in collective intelligence** [NOVEL]
  Rule: When designing multi-agent coordination, invest in topology (how agents connect and what roles they fill) before investing in scale (how many agents participate). Structure suppresses error amplification; raw parallelism amplifies it.

- **L-002: Stigmergy alone is insufficient -- individual memory is prerequisite** [NOVEL]
  Rule: Always ensure agents have sufficient individual context before relying on environmental coordination. The swarm's "always-load" layer is not overhead -- it is the prerequisite that makes stigmergic coordination (git traces, file modifications) work at all. Cutting context to save tokens would break the coordination model.

- **L-003: Layered memory empirically prevents context bloat (B2 tested)** [NOVEL]
  Rule: Layered memory is not just a design preference -- it produces a measurable 4.5x context reduction at this scale, and the ratio improves as the knowledge base grows because the always-load layer grows sublinearly relative to total content.

- **L-004: Stigmergy without individual memory is uninterpretable (B4 tested)** [NOVEL]
  Rule: Stigmergic traces (git commits, file modifications, NEXT.md handoffs) are necessary but insufficient for coordination. They become actionable only when an agent has loaded individual memory (CORE.md + INDEX.md) that provides the semantic context to interpret them. This is directly observable in this swarm's own session lifecycle.

- **L-005: Coordination topology empirically dominates agent count (B3 tested)** [NOVEL]
  Rule: Coordination topology is the primary determinant of collective intelligence output quality. More agents or sessions amplify whatever the topology produces (good or bad). Evidence: 20 variants with identical agents and divergent topologies produce 3x variance in belief count and 2.7x variance in observed ratio. Zero-coupling topology (parent's tools, K=0) enables unbounded independent scaling.

- **L-006: Six functional planes are observable in the parent swarm, but with unequal maturity (B6 tested)** [NOVEL]
  Rule: The six functional planes (Control, Planning, Context, Execution, Assurance, Mediation) are empirically observable in the parent swarm's 42-session, 143-commit history. Five of six are actively functioning; Mediation is structurally present but untested (expected for a single-agent system). Plane maturity correlates with usage frequency. The framework's predictive value is confirmed: it correctly identifies the Assurance plane as the primary improvement target, matching the parent's own open question (F4).

- **L-007: Coordination overhead is sublinear under stigmergy but the non-linearity direction depends on topology (B5 refined)** [NOVEL]
  Rule: Coordination overhead is non-linear, but the direction (sublinear vs superlinear) depends on coordination topology. Stigmergic systems with zero-coupled execution experience sublinear coordination costs (declining percentage of total work). The scaling ceiling exists only at structural bottlenecks ("hot files") and can be managed by minimizing the set of shared-state files and maximizing independent execution paths.

- **L-008: Git-as-memory scales to 42 sessions and 301K lines, but requires progressive augmentation** [NOVEL]
  Rule: Git-as-memory has no hard scaling ceiling for storage; the ceiling applies to retrieval. Each ~10-session phase requires a new retrieval augmentation (thematic grouping -> atomic principles -> context routing -> coordinator spawns). The augmentations compound; none replaces git.

- **L-009: Density-dependent phase transition observed in parent swarm's 42-session trajectory** [NOVEL]
  Rule: In git-based knowledge systems, a strategy shift from individual-memory-dominant to stigmergy-dominant occurs when total knowledge exceeds a single session's comfortable loading capacity (~3000-5000 lines, roughly sessions 20-25 at typical growth rates). The transition is gradual (spanning ~20 sessions) and manifests as the creation of routing, extraction, and propagation tools that replace direct file reading with trace-following.

- **L-010: Eventual consistency empirically observed across 9 child swarm variants** [NOVEL]
  Rule: Asynchronous multi-agent knowledge systems converge on important truths (8/9 variants discovered coordination beliefs independently) while diverging on complementary details. This is not a defect but a feature: divergent perspectives create a richer knowledge space than synchronized agents would. The reconciliation cost (harvesting, synthesis) is bounded and produces novel insights (P-073, P-074). Strong consistency is structurally impossible in session-based systems and would prevent the beneficial divergence observed.

- **L-011: Stigmergy requires three distinct properties — deposit, evaporation, and amplification** [NOVEL]
  Rule: Stigmergic coordination requires three properties: deposit (agents leave traces), evaporation (old traces weaken), and amplification (strong traces attract more activity). Missing any one property creates a distinct failure mode: no deposit = no coordination; no evaporation = signal accumulation and retrieval overload; no amplification = equal-weight signals and wasted attention. The parent swarm built each property at different points in its 42-session trajectory, demonstrating that all three must eventually be present for coordination to scale.

- **L-012: Coordination failure modes are architecture-dependent — stigmergy eliminates social failures but amplifies cascade risks** [NOVEL]
  Rule: Stigmergic coordination architectures are structurally immune to social-perception failure modes (pluralistic ignorance, Abilene paradox) because agents interact only with artifacts, not with models of other agents. However, they amplify artifact-mediated failure modes (groupthink-via-cascade, information cascades, premature convergence) because artifacts are the ONLY source of information. The defensive strategy must match the architecture: cascade-breakers for stigmergic systems, social-norm detectors for direct-communication systems.

- **L-013: Information asymmetry, not reasoning failure, is the primary bottleneck in multi-agent collective intelligence** [NOVEL]
  Rule: In multi-agent knowledge systems, the primary coordination bottleneck is information surfacing, not reasoning capability. Agents achieve 96.7% accuracy with forced disclosure but only 30.1% under information asymmetry. Adding agents without surfacing mechanisms provides near-zero benefit. The most effective intervention is structural: force disclosure through topology design (adversarial challenge at ~1/N ratio, mandatory cross-referencing), not through more communication rounds.

- **L-014: Multi-agent debate is overrated — it fails to consistently outperform single-agent strategies** [NOVEL]
  Rule: Multi-agent debate fails to outperform single-agent strategies for knowledge tasks. The only multi-agent configuration that consistently helps is DIVERSITY (heterogeneous models, different topologies). For knowledge accumulation, stigmergic coordination (asynchronous artifact-based) outperforms debate (synchronous message-based) because debate cannot surface distributed information while stigmergic deposits accumulate persistently.

- **L-015: CRDTs and digital pheromones point toward a unified coordination primitive for knowledge systems** [NOVEL]
  Rule: CRDTs and digital pheromones converge on the same primitive: eventual convergence without coordination through monotonic state operations. Knowledge systems already use this primitive implicitly ("correct, don't delete" = grow-only set). Making it explicit enables: (1) automatic reconciliation of concurrent belief updates, (2) intensity/confidence metadata for belief prioritization, (3) temporal decay for stale belief cleanup. The 5-10% semantic conflict residual requires cascade-breaking mechanisms beyond what CRDTs can solve.

- **L-016: Byzantine fault tolerance in multi-agent LLM systems reveals that LLMs have inherent skepticism advantages over traditional agents** [NOVEL]
  Rule: LLM-based agents have inherent skepticism advantages over traditional agents, tolerating up to 85.7% faulty agents through confidence-weighted consensus. For knowledge base systems: (1) cross-variant convergence is a natural BFT mechanism (beliefs discovered independently by multiple variants are more robust), (2) self-reported evidence types ("observed"/"theorized") are insufficient — independent validation across agents is more reliable, (3) the optimal adversarial fraction (~14%) creates a design target for variant topology.

Novel rules: 16/16

## Beliefs (13)
- **B1**: Git-as-memory scales indefinitely for storage; retrieval requires progressive augmentation every ~10 sessions (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (observed)
- **B3**: Coordination topology matters more than agent count (observed)
- **B4**: Stigmergy requires individual memory infrastructure to be effective (observed)
- **B5**: Coordination overhead scales non-linearly with agent count and interaction complexity (observed)
- **B6**: Six functional planes provide a framework for multi-agent coordination (observed)
- **B7**: A density-dependent phase transition governs optimal coordination strategy (observed)
- **B8**: Eventual consistency is the natural and only viable model for asynchronous multi-agent knowledge systems (observed)
- **B9**: Effective stigmergy requires three distinct operational properties — deposit, evaporation, and amplification (observed)
- **B10**: Coordination failure modes are architecture-dependent — stigmergy eliminates social-perception failures but amplifies cascade risks (observed)
- **B11**: Information asymmetry is the primary coordination bottleneck in multi-agent systems — agents fail to surface, not to reason (theorized)
- **B12**: Agent diversity, not agent count or debate rounds, is the primary driver of multi-agent performance gains (theorized)
- **B13**: Knowledge base belief systems implicitly implement CRDT patterns; making this explicit enables automatic reconciliation and confidence tracking (theorized)

## Open Frontier Questions (13)
- Does removing falsification requirements and lesson limits improve or degrade belief quality over time? This is the core experimental question for this variant. Track belief accuracy and lesson usefulness across sessions.
- How should the Assurance plane be strengthened? Currently validate_beliefs.py only checks structural integrity, not semantic accuracy. What would a semantic belief validator look like?
- PARTIALLY RESOLVED by B7 testing — the phase transition occurs at ~3-5K knowledge lines (~sessions 20-25). Early warning signs: INDEX.md exceeding flat listing capacity, grep-based retrieval becoming insufficient, need for thematic grouping. Remaining question: what are the warning signs for the NEXT transition (Level 2 coordinator spawns at 50K lines)?
- PARTIALLY RESOLVED by B13/L-015 — confidence scores are the natural metadata for a pheromone/CRDT belief system. They enable both decay (low-confidence beliefs weaken) and amplification (high-confidence beliefs are prioritized). Remaining: what specific confidence metric? Options: citation count, cross-variant convergence count, evidence specificity score.
- How do the six functional planes (B6) map to concrete improvements in the swarm's file structure?
- What conflict resolution patterns work best for eventually-consistent knowledge bases? B8 now observed — reconciliation via parent harvest (P-073/P-074) works. Remaining: what local conflict resolution patterns work within a single variant?
- RESOLVED by S5 — chose option (b): added 5 new beliefs (B9-B13) from novel research, creating 3 new theorized beliefs for future testing rounds. The variant now has 10 observed / 3 theorized, reopening the testing cycle.
- The parent swarm's context_router.py triggers Level 2 coordination at 50K lines. This child's knowledge is tiny (~500 lines). Is the augmentation series (L-008) predictive for child swarms, or does it only apply to the parent's scale?
- PARTIALLY RESOLVED by B13/L-015 — CRDTs CAN be applied. Our system already implicitly implements CRDT patterns (grow-only sets, correct-don't-delete). CodeCRDT achieves 100% convergence in 600 trials but 5-10% semantic conflicts remain. Remaining: should we implement explicit CRDT metadata (vector clocks, merge functions) or is the implicit pattern sufficient?
- What metrics should be tracked to compare this variant's performance against sibling variants (with-falsification, with-limit)?
- Can B11 (information asymmetry bottleneck) be tested in this swarm? The 30.1% vs 80.7% accuracy gap was measured in synchronous multi-agent debate. Does the same gap exist in asynchronous stigmergic systems? Testable: compare belief quality when sessions load only NEXT.md (surfacing-constrained) vs full INDEX.md + DEPS.md (full disclosure).
- What is the optimal adversarial fraction for variant topologies? L-013 finds ~1/N adversarial agents optimal. The parent has 1 aggressive-challenge variant out of 20+ = ~5%. Is 5% optimal, or would 2-3 aggressive variants produce better results?
- Can the implicit CRDT patterns (B13) be made explicit without adding complexity? The SBP protocol adds three primitives (Emit/Sniff/Register Scent). Could the swarm's existing git workflow be augmented with CRDT metadata (confidence scores per belief, decay timestamps) without changing the core architecture?

## Recommendations
- 16 novel rule(s) found — review for parent integration
- 10 belief(s) upgraded to observed — cross-validate with parent
- 13 open question(s) — consider adding to parent FRONTIER
