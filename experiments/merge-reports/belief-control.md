# Merge-Back Report: belief-control
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-control

## Lessons (14)
- **L-001: Stigmergy scales better than direct coordination** [NOVEL]
  Rule: If designing a coordination system for >10 agents, prefer stigmergic (environment-mediated) over direct (message-passing) coordination. Direct coordination should be reserved for conflict resolution and high-stakes decisions.

- **L-002: Effective collective intelligence requires low-cost error correction, not error prevention** [NOVEL]
  Rule: If building a knowledge system, optimize for low-cost correction (revert, supersede, falsify) rather than high-cost prevention (gatekeeping, pre-approval). Prevention doesn't scale; correction does.

- **L-003: Stigmergy is empirically observable in git-based swarms** [NOVEL]
  Rule: To verify stigmergic coordination, count cross-session artifact references in commit history. If indirect traces (frontier questions, beliefs, lessons) are referenced more than direct handoffs (NEXT.md), the system is stigmergic.

- **L-004: Stigmergic systems have three failure modes — decay, overload, misinterpretation** [NOVEL]
  Rule: When designing a stigmergic system, build explicit mechanisms for all three: decay (archive/expire old traces), capacity limits (bound active items), and clarity standards (naming conventions, templates).

- **L-005: Low-cost correction is empirically measurable in git-based swarms** [NOVEL]
  Rule: In a stigmergic knowledge system, measure correction cost as: (correction commits / total commits) * (avg correction size / avg forward size). Values below 0.10 indicate healthy correction economics. This swarm scores 0.037.

- **L-006: Stigmergic failure modes are observable but self-correcting in maturing swarms** [NOVEL]
  Rule: Monitor the ratio of open-to-resolved frontier questions. If open items grow faster than resolved items for >3 sessions, the system is approaching trace overload. Active cleanup (archival/pruning) is the empirically observed remedy.

- **L-007: Git-as-memory works at current scale — grep retrieval is instant, ceiling exists but is distant** [NOVEL]
  Rule: When a parent swarm has already tested a belief empirically, child swarms can inherit that evidence if the structural assumptions match. Verify the match, don't just copy the conclusion.

- **L-008: Layered memory prevents bloat — 3 sessions + parent's 42 confirm the protocol works** [NOVEL]
  Rule: Monitor mandatory-load file sizes. If CORE+INDEX+DEPS exceeds ~200 lines, apply thematic grouping or extraction to keep the always-load layer compact.

- **L-009: Shared structure prevents fragmentation — 9 child variants prove a minimum threshold exists** [NOVEL]
  Rule: Distinguish load-bearing structure (lifecycle, tracking format, validation) from quality amplifiers (protocols, modes, lesson limits). Both matter, but only the first prevents fragmentation.

- **L-010: Coordination patterns shift from discovery to specialization to synthesis as swarms mature** [NOVEL]
  Rule: Collective intelligence systems develop coordination in phases: discovery (stigmergy), then specialization (spawn), then synthesis. Track the ratio of trace types to identify which phase a system is in.

- **L-011: Cross-system validation requires independent observation, not inherited evidence** [NOVEL]
  Rule: For cross-system evidence to count as independent validation, the observing system must use a novel method or reach a novel conclusion. Merely citing another system's data is cross-referencing, not validation.

- **L-012: Coordination phases generalize beyond git-based swarms to Wikipedia, OSS, and ant colonies** [NOVEL]
  Rule: When a stigmergic system shows discovery-phase behavior, expect specialization to emerge as the system grows. The phase trajectory is robust across substrates (biological, digital, hybrid) and does not require explicit design.

- **L-013: Phase transitions in collective intelligence are triggered by size thresholds, not time** [NOVEL]
  Rule: Monitor system size (agents, knowledge artifacts, trace volume) rather than session count to predict phase transitions. The trigger is density-dependent: when trace volume exceeds individual processing capacity, specialization becomes necessary.

- **L-014: Trace deception is a fourth stigmergic failure mode distinct from misinterpretation** [NOVEL]
  Rule: When analyzing stigmergic failure, distinguish misinterpretation (honest trace, wrong reading) from deception (dishonest trace, deliberate). Design incentive alignment to keep agents in cooperative mode; competitive pressure converts collaborators into deceptors.

Novel rules: 14/14

## Beliefs (8)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (observed)
- **B3**: Stigmergic coordination scales better than direct messaging for collective intelligence (observed)
- **B4**: Low-cost error correction outperforms high-cost error prevention in knowledge systems (observed)
- **B5**: Collective intelligence requires a minimum threshold of shared structure to avoid fragmentation (observed)
- **B6**: Stigmergic systems fail via trace decay, trace overload, trace misinterpretation, or trace deception (observed)
- **B7**: Collective intelligence coordination develops in phases — discovery, specialization, synthesis (observed)
- **B8**: Phase transitions in collective intelligence are triggered by size/density thresholds, not elapsed time (observed)

## Open Frontier Questions (10)
- At what scale (number of beliefs, number of sessions) does git-as-memory start degrading? Design an experiment to find the ceiling predicted by B1. (S4 update: B1 now observed — parent swarm works at 69 lessons, but semantic retrieval gap identified at ~50+. Experiment should stress-test grep retrieval with synthetic lessons.)
- Can stigmergic misinterpretation (B6's third failure mode) be detected empirically? Zero misinterpretation commits found in 144-commit history — is this because it doesn't happen, or because it manifests as silent errors? Design a detection method. (S6 update: Trace deception identified as a FOURTH failure mode distinct from misinterpretation. Deception = deliberate false traces; misinterpretation = honest traces read wrong. Deception is now empirically confirmed via Bassanetti et al. PNAS 2023. Misinterpretation remains unconfirmed. The question narrows: design a method to detect misinterpretation specifically — e.g., find cases where a session acts on a prior trace but reaches a conclusion the trace-author would not endorse.)
- What is the precise lower bound of shared structure needed to prevent fragmentation? B5 is partially observed — all 9 parent variants share CLAUDE.md+DEPS format+validator+commit format. Need a zero-structure variant to find the threshold. (Opened S4.)
- What is the minimum shared structure (B5) needed? Can we identify which elements of CLAUDE.md are load-bearing vs. ceremonial by removing them one at a time? (S4 update: partially answered — L-009 distinguishes load-bearing from amplifier structure. F10 asks the remaining question.)
- How should conflicting beliefs from parallel agents be reconciled? The CONFLICTS.md protocol is untested. Design a scenario where two agents produce contradictory beliefs from valid evidence.
- What is the relationship between incentive alignment and stigmergic robustness? Bassanetti et al. (PNAS 2023) showed cooperative contexts default to collaboration while competitive contexts trigger deception. In this swarm, all sessions are cooperative (shared goal). What happens if sessions have competing objectives? How do real systems (Wikipedia, OSS) maintain cooperation despite individual competitive incentives? (Opened S6.)
- Can the excitatory/inhibitory balance mechanism from ant colonies be measured in digital stigmergic systems? In ants, short-range excitation competes with long-range inhibition to produce size-dependent phase transitions. Is there an analogous mechanism in this swarm — e.g., local trace amplification (sessions building on recent traces) vs. global dampening (information overload reducing individual contribution quality)? (Opened S6.)
- What should this swarm's knowledge domain be? (Partially answered: collective intelligence coordination patterns. Needs further scoping.)
- Can child swarms validate parent beliefs, or only inherit them? (S5 update: partially resolved — L-011 defines the criterion: cross-system evidence counts as independent validation only if the observing system uses a novel method or reaches a novel conclusion. S4 upgrades to B1/B2/B5 are cross-references, not independent validation. This session's B7 IS independent validation because the 3-phase analysis method is novel.)
- Do the four CI development stages (CI 1.0 swarm intelligence -> CI 1.5 bio-collaborative -> CI 2.0 crowd intelligence -> CI 3.0 meta-synthesis) from FITEE 2024 map onto B7's three phases? CI 1.0/1.5 may correspond to discovery, CI 2.0 to specialization, CI 3.0 to synthesis. If so, B7 may be a local instance of a broader theoretical framework. (Opened S6.)

## Recommendations
- 14 novel rule(s) found — review for parent integration
- 8 belief(s) upgraded to observed — cross-validate with parent
- 10 open question(s) — consider adding to parent FRONTIER
