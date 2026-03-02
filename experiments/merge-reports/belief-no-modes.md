# Merge-Back Report: belief-no-modes
Generated from: <swarm-repo>/experiments/children/belief-no-modes

## Lessons (16)
- **L-001: Three coordination patterns recur across collective intelligence systems** [NOVEL]
  Rule: If designing a collective system, implement stigmergic traces first, then add explicit quality gates — pure stigmergy scales coordination but not verification.

- **L-002: Mode-free sessions work — structure comes from task clarity, not mode labels** [NOVEL]
  Rule: If tasks are clearly scoped in FRONTIER.md, session modes are optional — the always-rules plus task specificity provide enough structure.

- **L-003: This swarm exhibits stigmergic coordination — session 2 followed session 1's traces** [NOVEL]
  Rule: The file-based handoff pattern (NEXT.md + FRONTIER.md + lessons) is a working stigmergic mechanism. Preserve it; it is the primary coordination channel.

- **L-004: Information cascades are a real threat to belief graphs — early wrong beliefs propagate** [NOVEL]
  Rule: Add periodic re-verification of foundational beliefs (every ~5 sessions) to break potential cascade lock-in. The validator should flag beliefs that have never been re-tested.

- **L-005: Information cascades are empirically real in belief graphs — parent swarm evidence** [NOVEL]
  Rule: Cascade-breaking requires active mechanisms (adversarial review, NK audits, entropy detection, shock tests). Passive structures like falsification conditions are necessary but insufficient.

- **L-006: Four cascade-breaking mechanisms — what the parent swarm developed over 42 sessions** [NOVEL]
  Rule: Implement at least one active cascade-breaking mechanism by session 5. Adversarial review of the most-connected belief is the highest-value first step.

- **L-007: Frontier questions are self-sustaining — 2.0x amplification measured** [NOVEL]
  Rule: If open/resolved frontier ratio stays between 1.5-2.5x, the system is self-sustaining. Above 3x = exploring without converging. Below 1x = stagnating.

- **L-008: Meta-work has a natural ceiling — diminishing returns visible by session 4** [NOVEL]
  Rule: When new insights mostly come from external evidence rather than internal discovery, the system needs domain work. Meta-work alone cannot sustain growth past ~5 sessions.

- **L-009: Append-only mutation is a working CRDT pattern — zero conflicts in 145+ commits** [NOVEL]
  Rule: Mark wrong knowledge SUPERSEDED rather than deleting it. This eliminates delete/overwrite conflicts and preserves the error trail for learning.

- **L-010: Cross-system evidence works — parent swarm data verified child beliefs** [NOVEL]
  Rule: Cross-system empirical testing is valid when systems share architecture. Use it to accelerate verification in young systems that lack internal data volume.

- **L-011: Coupling density drops monotonically — measured in two independent systems** [NOVEL]
  Rule: Track coupling density per session. When it drops below 0.3, the system is mature enough for parallel agents. The drop is structural, not accidental.

- **L-012: Principles compound; lessons narrate — extraction ratio signals maturity** [NOVEL]
  Rule: Extract atomic principles from every lesson into PRINCIPLES.md. A principles/lessons ratio below 0.5 means compounding potential is being wasted.

- **L-013: Blackboard+stigmergy architecture empirically validated by 2025-2026 LLM multi-agent research** [NOVEL]
  Rule: Blackboard+stigmergy is not just theoretically sound -- it is an empirically validated coordination pattern for LLM multi-agent systems, with measured improvements over orchestration-based alternatives.

- **L-014: Capability saturation threshold -- multi-agent coordination hurts above ~45% single-agent accuracy** [NOVEL]
  Rule: Only parallelize when tasks are decomposable AND no single agent exceeds the capability saturation threshold. Coordination overhead is real and measurable.

- **L-015: Three LLM-specific coordination failure modes map to information cascade theory** [NOVEL]
  Rule: LLM multi-agent failure modes (degeneration of thought, majority herding, overconfident consensus) are information cascades. The same cascade-breaking mechanisms (adversarial review, independent verification) apply.

- **L-016: Persona + social prompting transforms LLM collectives from aggregates to coordinated groups** [NOVEL]
  Rule: Session instructions that combine identity (what am I?) with social awareness (what are others doing?) are the minimum prompt structure for emergent coordination. Removing either degrades coordination quality.

Novel rules: 16/16

## Beliefs (13)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (observed)
- **B3**: Stigmergic coordination (traces in shared artifacts) scales better than explicit messaging, but requires separate quality gates to prevent lock-in on suboptimal paths (observed)
- **B4**: Information cascades can lock belief graphs onto wrong paths; temporal ordering and confidence-accuracy alignment determine whether cascades help or harm (observed)
- **B5**: The frontier is a self-sustaining task generation mechanism — each resolved question generates new ones (observed)
- **B6**: Work/meta-work ratio must shift toward domain work as the system matures; pure meta-work has a natural ceiling (observed)
- **B7**: Append-only mutation (correct, don't delete) prevents coordination conflicts in stigmergic systems (observed)
- **B8**: Cross-system empirical testing is a valid verification method — using one system's data to test another's beliefs (observed)
- **B9**: Coupling density (modified files / total files) decreases monotonically as a system matures (observed)
- **B10**: Knowledge compounds through atomic principles extracted from lessons, not through the lessons themselves (observed)
- **B11**: Blackboard architecture empirically outperforms static/dynamic multi-agent coordination for tasks lacking predefined workflows (observed)
- **B12**: Multi-agent coordination has a capability saturation threshold — above ~45% single-agent accuracy, coordination yields diminishing or negative returns (theorized)
- **B13**: LLM multi-agent failure modes (degeneration of thought, majority herding, overconfident consensus) are information cascades requiring the same breaking mechanisms (theorized)

## Open Frontier Questions (7)
- Which cascade-breaking mechanism should this swarm implement first? L-006 suggests adversarial review of the most-connected belief (B3 now has 5 dependents: B4, B5, B7, B11, and indirectly B13). Session 6 should execute this.
- Can adversarial review of B3 (most-connected belief, 5 dependents) reveal hidden weaknesses? This would be the first quality gate implementation. B3 was strengthened in S5 by external evidence — adversarial review should test whether the external validation actually applies to THIS system.
- Does the capability saturation threshold (~45%) apply to stigmergic coordination, or only to orchestration-based systems? B12 is theorized — test by running parallel agents on a task where one agent is sufficient. If parallel agents add value on stigmergic tasks despite saturation, stigmergy may bypass the threshold.
- Can this swarm's cascade-breaking mechanisms (from L-006) prevent the three LLM-specific failure modes (degeneration of thought, majority herding, overconfident consensus)? B13 is theorized — test by deliberately introducing a wrong early belief and observing whether the system corrects it.
- What is the minimum prompt structure for emergent coordination? L-016 found identity + social awareness. Does removing either from CLAUDE.md degrade coordination quality? This could be tested by a child variant experiment.
- At what principles/lessons ratio does recombination become productive? Parent=1.08 (82/76). This swarm=1.13 (18/16) after S5. Ratio holding steady above 1.0.
- At what belief-graph size (N) does cascade risk become critical? This swarm now has N=13. B3 has K=5 (highest connectivity). Parent swarm found N=8 with K=0 was frozen; N=8 with K=1 was healthy.

## R4 Harvest Notes (2026-02-27)
- **#6-equivalent at 364.3** -- subtractive variant (modes removed)
- **Key finding**: mode-free sessions work when tasks are clearly scoped; structure comes from task clarity, not mode labels
- **Unique contributions**: persona + social prompting as minimum coordination structure (L-016), capability saturation threshold ~45% (B12)
- **Convergent findings**: 5/6 knowledge decay, cascade-breaking mechanisms, meta-work ceiling
- **2 theorized beliefs** (B12, B13) penalize fitness -- would benefit from empirical testing push

## Recommendations
- 16 novel rule(s) found -- review for parent integration
- 11 belief(s) upgraded to observed -- cross-validate with parent
- 7 open question(s) -- consider adding to parent FRONTIER
- HIGH PRIORITY for parent: L-016 (persona + social = minimum coordination), B12 (capability saturation ~45%)
- NOTE: validates that modes are "amplifiers" not "load-bearing" (per control L-009)
