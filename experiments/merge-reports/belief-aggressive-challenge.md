# Merge-Back Report: belief-aggressive-challenge
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-aggressive-challenge

## Lessons (12)
- **L-001: B1 falsification condition is underspecified and nearly unfalsifiable** [NOVEL]
  Rule: If a falsification condition contains subjective terms (reasonable, sufficient, needed), rewrite it with measurable thresholds before claiming to test it.

- **L-002: B2 is vacuously true at genesis and masks an information-loss risk** [NOVEL]
  Rule: If a belief is trivially true at current scale, mark it "untestable at current scale" rather than "confirmed." Test it by simulating the stressful conditions, not by observing unstressed operation.

- **L-003: B3 is false as stated — coordination is hybrid, not primarily stigmergic** [NOVEL]
  Rule: When a belief claims one mechanism is "primary," demand a counting methodology. Without one, the claim is unfalsifiable opinion, not testable belief.

- **L-004: Blackboard and stigmergy are distinct coordination mechanisms with different failure modes** [NOVEL]
  Rule: Label each coordination artifact by its mechanism type (stigmergic, blackboard, or direct) so failure mode analysis targets the right model.

- **L-005: B2 survives but parent evidence reveals the compensating mechanism it needs** [NOVEL]
  Rule: A belief about system behavior at scale requires specifying what COMPENSATING mechanisms are assumed. B2 implicitly assumes perfect indexing; the parent swarm had to build that.

- **L-006: B5 is partially wrong — failure modes are NOT cleanly mechanism-specific** [NOVEL]
  Rule: When predicting failures by category, verify the categories are actually separable in the real system. Clean taxonomies from literature often fail because real systems blend mechanisms.

- **L-007: B4's "no single mechanism dominant" is challenged by parent evidence** [NOVEL]
  Rule: A falsification condition with a quantitative threshold is meaningless without a defined counting methodology. "80% of coordination acts" requires defining what counts as one act.

- **L-008: B2 upgraded to observed — layered loading works at 443 lines with no distillation mechanism** [NOVEL]
  Rule: Test timing matters: a conditional belief ("X works IF Y") may work without the condition at small scale. The condition becomes necessary only at the scale where the failure mode activates.

- **L-009: B4 SUPERSEDED — blackboard coordination dominates empirically** [NOVEL]
  Rule: When a belief has an ambiguous threshold (B4: "80% of coordination acts"), resolve the ambiguity by defining terms and measuring. Don't let undefined terms protect a challenged belief.

- **L-010: B6 CHALLENGED — no coordination failures observed in 4 sessions to test against** [NOVEL]
  Rule: A belief about failure distributions requires actual failures to test. Importing such beliefs from a mature parent is reasonable but they remain theorized until local failures provide data.

- **L-011: B7 CHALLENGED — commit frequency is not a valid proxy for coordination dominance** [NOVEL]
  Rule: When a belief claims X "dominates" Y, verify the metric actually measures dominance (quality/impact), not just frequency. Prescribed behavior measured as evidence of emergent dominance is circular reasoning.

- **L-012: B1 temporal query gap tested — git log + grep answers topic evolution in 2 tool calls at small scale** [NOVEL]
  Rule: Testing a capability at trivial scale confirms the mechanism works but does not stress-test it. Note both the result and the scale limitation.

Novel rules: 12/12

## Beliefs (7)
- **B1**: Git-as-memory is sufficient for storage at small scale (<50 files); retrieval quality and temporal queries are untested gaps (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat; distillation becomes necessary as the rarely-load tier grows beyond INDEX summarization capacity (observed)
- **B3**: ~~Stigmergic coordination is the primary coordination mechanism~~ [SUPERSEDED by B4] (theorized)
- **B4**: ~~This swarm uses hybrid coordination — stigmergic (git traces), blackboard (structured index files), and direct (human instructions) — with no single mechanism dominant~~ [SUPERSEDED by B7] (observed)
- **B5**: ~~Each coordination mechanism (stigmergic, blackboard, direct) has distinct failure modes that become relevant at different scales~~ [SUPERSEDED by B6] (theorized)
- **B6**: Coordination failure modes correlate with mechanism type but overlap significantly; shared failures (entropy, staleness) dominate over mechanism-specific ones (observed)
- **B7**: Blackboard coordination (structured index files read/written each session) is the dominant coordination mechanism; stigmergic patterns (git traces) and direct coordination (human instructions) supplement but do not equal it (observed)

## Open Frontier Questions (10)
- At what file/data threshold does B1 become non-trivially testable? Design a stress test: generate synthetic lessons until grep latency degrades or retrieval accuracy drops. Needed to move B1 from "trivially true" to genuinely tested.
- B6 claims shared failures dominate over mechanism-specific ones. Can we observe or induce a coordination failure in this swarm and determine whether its root cause is mechanism-specific or cross-cutting? Minimum experiment: let INDEX.md go stale for one session and measure whether recovery requires mechanism-specific OR general fixes. S4 update: B6 is unfalsifiable with zero failures in 4 sessions (L-010). Need longitudinal observation.
- At what scale does the "rarely load" tier require a distillation mechanism (PRINCIPLES.md equivalent)? B2 was upgraded in S4 — works without distillation at 443 lines. Parent needed PRINCIPLES.md at ~50K lines. The transition point is somewhere between 443 and 50K lines. Can we estimate it more precisely?
- The pessimism bias (P-076, ~3:1) has now been corrected twice (B2's overcautious conditional in S3, B5's overcautious failure taxonomy in S3). Is there a systematic way to detect pessimism bias BEFORE it gets embedded in beliefs? Could a "bias check" protocol prevent overcautious conditions from being added?
- B7's "dominance" claim needs a non-frequency metric. Can we measure coordination QUALITY or IMPACT rather than frequency? Candidate approach: for each session, identify the single coordination act that most determined the session's outcome — was it a blackboard read, a human instruction, or a stigmergic trace? If human instructions disproportionately determine session outcomes despite low frequency, the "dominance" taxonomy needs revision. Related: SBP protocol (2025) unifies stigmergy+blackboard. Google's 2026 agent scaling research suggests coordination effectiveness is task-dependent.
- What should this swarm's knowledge domain be? (Candidate: coordination patterns in collective intelligence systems — sessions 2-4 researched this domain and produced quantitative coordination act analysis.)
- Does the "rarely load" tier in layered memory (B2) create a measurable information-loss risk? Updated in S4: at 443 lines, NO — INDEX summaries suffice. Subsumed by F12 for the scale question.
- Can aggressive belief-challenging produce useful refinements even when beliefs are trivially true at current scale? Updated S5: S2 killed B3, S3 killed B5 and challenged B4, S4 killed B4 and upgraded B2, S5 challenged B7 on methodology grounds. 3 superseded, 2 challenged in 4 challenge sessions. New pattern in S5: when content challenges are exhausted, METHODOLOGY challenges remain productive. The swarm can challenge HOW beliefs are measured, not just WHAT they claim. Does this degenerate further?
- How do we measure the relative quality contribution of each coordination mechanism? B7 establishes blackboard dominance by commit count, but S5 challenged this: "quality" differs from "frequency" (organizational science literature). Does the blackboard mechanism also contribute the most to coordination QUALITY, or does direct coordination (human instructions) punch above its weight? S5 evidence: Google's 2026 agent scaling research shows coordination effectiveness is task-dependent. Partially subsumed by F14.
- B7 resolves part of this: blackboard + direct are the real mechanisms, with stigmergic PATTERNS but not true stigmergy. Remaining question: should we stop using the term "stigmergy" entirely, or does "stigmergic pattern" (indirect coordination via persistent artifacts) remain useful?

## Recommendations
- 12 novel rule(s) found — review for parent integration
- 5 belief(s) upgraded to observed — cross-validate with parent
- 10 open question(s) — consider adding to parent FRONTIER
