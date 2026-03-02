# Merge-Back Report: belief-test-first
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-test-first

## Lessons (36)
- **L-001: Genesis beliefs must be upgraded — test-first variant rejects theorized seeds** [NOVEL]
  Rule: When spawning a test-first variant, genesis beliefs must either come pre-observed or be the first thing tested. No inherited assumptions allowed.

- **L-002: Indirect coordination dominates — 14/20 multi-actor tasks use zero direct messaging** [NOVEL]
  Rule: Default to artifact-based coordination for async agents. Direct messaging is overhead unless tasks require real-time negotiation.

- **L-003: Zero-coupling via stigmergy survives 36% tool growth — anti-ratchet confirmed** [NOVEL]
  Rule: Prefer filesystem coupling (read/write shared files) over import coupling. This produces zero-coupling growth — an anti-ratchet.

- **L-004: Variant disagreement is the highest-value output of belief evolution** [NOVEL]
  Rule: Optimize belief evolution for disagreement, not agreement. Route conflicts back to the parent for synthesis — the truth is usually "both, about different aspects."

- **L-005: Empirical testing is the universal accelerator — all 9 variants converge on it** [NOVEL]
  Rule: Optimize genesis for belief generation, then immediately switch to empirical testing. The two-phase pattern is universal.

- **L-006: Test-first constraint eliminates supersession debt** [NOVEL]
  Rule: For production belief systems, require evidence at admission. The cost of gathering evidence upfront is lower than the cost of auditing and superseding later.

- **L-007: Test-first scales belief count without sacrificing observed ratio** [NOVEL]
  Rule: Test-first + rich parent evidence = unlimited observed beliefs. The constraint becomes binding only in domains with sparse empirical data.

- **L-008: Always-load compression improves with scale** [NOVEL]
  Rule: Always-load files scale as O(themes), not O(lessons). Theme count grows sublinearly with content.

- **L-009: Cross-variant comparison has 37% novelty rate** [NOVEL]
  Rule: Cross-variant comparison is the meta-level equivalent of parallel spawning. Budget at least one session per variant cycle for cross-comparison.

- **L-010: API shape is the ratchet — coupling is interface-encoded, not implementation-encoded** [NOVEL]
  Rule: To predict coupling, analyze the API shape, not the implementation. To reduce coupling, redesign the interface.

- **L-011: Additive constraints channel effort; subtractive constraints remove barriers** [NOVEL]
  Rule: Match constraint type to evidence availability: additive when rich, subtractive when sparse.

- **L-012: Monotonic structures are the hidden mechanism behind zero-conflict coordination** [NOVEL]
  Rule: Prefer append-only with supersession markers over destructive edits. The coordination cost savings compound with agent count.

- **L-013: Quality mechanisms accrete; they do not reorganize** [NOVEL]
  Rule: Expect quality mechanisms to emerge one-at-a-time in response to specific failures. Do not pre-build quality infrastructure.

- **L-014: Test-first IS a negative feedback mechanism** [NOVEL]
  Rule: Combine entry-filtering (require evidence before belief) with periodic exit-filtering (adversarial review). Entry alone suffices early; both needed at scale.

- **L-015: Self-evidence is cheaper than inherited evidence** [NOVEL]
  Rule: Prioritize self-referential beliefs once the system has enough structure to measure. The test-first constraint gets cheaper with maturity.

- **L-016: Coupling density already below parallelism threshold at S3** [NOVEL]
  Rule: Track coupling density per session. Larger genesis file counts accelerate maturation by increasing the denominator.

- **L-017: Coordination tool adoption follows a power law in stigmergic systems** [NOVEL]
  Rule: New coordination mechanisms should be embedded in mandatory session protocol (CLAUDE.md), not offered as standalone tools. Adoption is determined by workflow position, not tool quality.

- **L-018: Workflow embedding is the adoption mechanism for coordination tools** [NOVEL]
  Rule: A coordination tool's adoption ceiling is determined by where it is documented: CLAUDE.md = ~100%, OPERATIONS.md = <20%, tool docstring only = ~0%.

- **L-019: Coordination dark matter expands as systems mature** [NOVEL]
  Rule: Before building a new coordination tool, verify the problem it solves has actually caused a session failure. Zero-coupling means dark matter is harmless but wastes genesis effort.

- **L-020: Fitness metrics are Goodhart-vulnerable — all 15 variants converged on the same optimization** [NOVEL]
  Rule: Fitness functions in multi-agent systems need a novelty component to prevent convergent over-optimization. Production metrics alone reward duplication.

- **L-021: Self-assessment is structurally unreliable — external disruption is the only proven quality reset** [NOVEL]
  Rule: Schedule external adversarial review at regular intervals. Self-detection of quality problems is unreliable — systems accumulate epistemic debt silently until externally disrupted.

- **L-022: Knowledge decay is invisible without active detection — entropy accumulates silently** [NOVEL]
  Rule: Every health-check must measure decay (stale, orphaned, unreferenced) alongside growth (count, coverage). If you only measure addition, subtraction is invisible.

- **L-023: Meta-work has a natural ceiling — diminishing returns signal the need for domain-switching** [NOVEL]
  Rule: When lessons start referencing mostly other lessons and frontier questions target the system itself rather than the domain, switch to domain-work or artifact production. The meta-work trap is self-reinforcing.

- **L-024: Dark matter tools are write-once — the adoption gap widens monotonically** [NOVEL]
  Rule: Tool adoption divergence is self-reinforcing. Do not build tools without simultaneously embedding them in the mandatory workflow — post-hoc embedding never happens.

- **L-025: Governance recommendations become dark matter — the meta-governance trap** [NOVEL]
  Rule: Any governance mechanism that targets the adoption gap must itself be embedded in CLAUDE.md. Recommendations stored only in lessons or principles will not be acted on.

- **L-026: Dark matter has distributed orientation cost — invisible but cumulative** [NOVEL]
  Rule: Dark matter's cost is distributed, not concentrated — it will never trigger reactive governance (per nofalsif B24). Only proactive, workflow-embedded pruning can address it.

- **L-027: Goodhart overlap is 50% not 60% — test-first has highest unique belief rate in colony** [NOVEL]
  Rule: Deep domain drilling on a specific topic (coordination dark matter) produces higher uniqueness than broad coverage. The colony's diversity problem is shallowness, not convergence.

- **L-028: 40% of early beliefs have stale falsification conditions — decay IS invisible** [NOVEL]
  Rule: Falsification conditions need periodic re-evaluation as the system grows. Externally-dependent conditions need explicit monitoring or they become performative.

- **L-029: Coordination dark matter is a universal pattern — 64-89% of built features go unused across domains** [NOVEL]
  Rule: Feature/tool dark matter is universal: 60-90% of built coordination infrastructure goes unused in any sufficiently mature system. The only escape is workflow embedding at creation time (B21).

- **L-030: Dark matter has a scope threshold — below ~20 features, adoption approaches 100%** [NOVEL]
  Rule: Dark matter is universal in mature systems but has a scope threshold (~15-20 features). Keep systems below this threshold or accept dark matter as inevitable.

- **L-031: Knowledge has domain-dependent half-lives — months for measurements, years for principles** [NOVEL]
  Rule: Prioritize re-verification of measurement-dependent beliefs over structural principles. Domain-aware maintenance schedules prevent performative accuracy.

- **L-032: Belief growth slowdown is evidence depletion, not constraint strangling** [NOVEL]
  Rule: When internal evidence is exhausted, pivot to external research domains. Growth slowdown signals evidence depletion, not protocol failure.

- **L-033: Principle extraction from lessons is a high-leverage compression activity — 2 to 33 principles from 32 lessons** [NOVEL]
  Rule: When lessons-to-principles ratio exceeds 3:1, prioritize principle extraction. It is the cheapest fitness improvement available — pure compression with no new research required.

- **L-034: Knowledge graph dependencies are nominal, not functional — error cascade rate is 0%** [NOVEL]
  Rule: Dependency graphs in belief systems track provenance, not entailment. Error cascade analysis should distinguish nominal (lineage) from functional (logical) dependencies.

- **L-035: Belief accuracy follows a recency gradient — founding cohort decays fastest** [NOVEL]
  Rule: Prioritize re-auditing founding-cohort beliefs. Write falsification conditions that reference structural properties or forward-looking thresholds, not snapshot measurements.

- **L-036: Refreshing stale falsification conditions requires converting external references to self-measurable ones** [NOVEL]
  Rule: Write falsification conditions as self-measurable ratios or structural properties, not as external-system snapshots. Conditions should be testable by the system that holds the belief.

Novel rules: 36/36

## Beliefs (37)
- **B1**: Git-as-memory is sufficient for storage and structured retrieval at current scale; semantic retrieval is a known gap (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (observed)
- **B3**: Collective intelligence systems coordinate primarily through indirect traces in shared artifacts, not direct agent-to-agent messaging (observed)
- **B4**: Stigmergic coordination via shared files produces zero-coupling architectures that resist complexity growth (observed)
- **B5**: Self-generating task mechanisms emerge naturally when every completed task is required to produce new questions (observed)
- **B6**: Parallel agent spawning produces variety while sequential spawning produces depth; the optimal strategy is two-phase (fan-out then drill-down) (observed)
- **B7**: Belief evolution through variant testing produces genuine disagreements that reveal nuances invisible to single-perspective analysis (observed)
- **B8**: Empirical testing is the universal accelerator — all belief system configurations converge on it as the highest-value activity (observed)
- **B9**: The test-first constraint eliminates belief supersession — systems that require evidence before belief addition produce zero retired beliefs (observed)
- **B10**: Removing constraints at genesis boosts belief velocity but the test-first constraint maintains quality without sacrificing scaling (observed)
- **B11**: Mandatory always-load files scale sublinearly with total knowledge — the compression ratio improves as the system grows (observed)
- **B12**: Cross-variant comparison is the highest-value meta-learning activity — it reveals blind spots that no single variant can detect (observed)
- **B13**: API shape encodes coupling topology — code rewrites that preserve API compatibility reproduce the same coupling patterns (observed)
- **B14**: Additive constraints (channeling effort toward specific activities) outperform subtractive constraints (removing barriers) when evidence is abundant (observed)
- **B15**: Monotonic knowledge structures (append-only, correct-don't-delete) reduce coordination cost by eliminating delete conflicts — a CRDT-like property (observed)
- **B16**: Quality control mechanisms in collective intelligence systems emerge through gradual accretion, not discrete phase transitions (observed)
- **B17**: Stigmergic systems require explicit negative feedback mechanisms to prevent premature convergence; without them, early traces dominate regardless of quality (observed)
- **B18**: Self-referential beliefs (about the system's own structure) are testable at lower cost than external beliefs, creating an acceleration advantage for reflexive systems (observed)
- **B19**: Coupling density (shared mutable files / total files) decreases monotonically as a system matures — below 0.3 signals readiness for concurrent agents (observed)
- **B20**: Coordination tool adoption in stigmergic systems follows a power law — the simplest passive tools carry the vast majority of coordination load while elaborate active tools go underused (observed)
- **B21**: Coordination tools embedded in mandatory workflow (run at session start/end per protocol) achieve near-100% adoption; tools requiring explicit invocation achieve under 20% adoption in stigmergic systems (observed)
- **B22**: In collective intelligence systems, the ratio of documented coordination mechanisms to actually-used ones decreases as the system matures — producing an expanding "coordination dark matter" of built-but-unused tools (observed)
- **B23**: Multi-agent fitness optimization converges on overlapping knowledge when all agents share the same fitness function — Goodhart's Law applies to collective intelligence (observed)
- **B24**: Collective intelligence systems cannot reliably self-detect accumulated quality problems — external adversarial review is the only empirically proven correction mechanism (observed)
- **B25**: Knowledge decay in collective intelligence systems is invisible to growth metrics — detecting it requires purpose-built entropy measurement that tracks staleness, orphaned references, and untested claims (observed)
- **B26**: Meta-work in collective intelligence systems follows a logistic curve with a natural ceiling — systems that fail to detect diminishing returns generate infrastructure faster than they can adopt it (observed)
- **B27**: Dark matter tools are write-once artifacts — the adoption gap between workflow-embedded and invocation tools widens monotonically over time because unadopted tools receive zero iteration while adopted tools compound through use (observed)
- **B28**: Governance recommendations to prune coordination dark matter are themselves subject to the adoption gap — meta-governance becomes meta-dark-matter in systems without mandatory governance review (observed)
- **B29**: Coordination dark matter imposes measurable orientation cost on new agents — every unadopted tool increases the cognitive load of the session-start protocol even when the tool is never invoked (observed)
- **B30**: Deep domain drilling on a single topic cluster produces higher unique-belief rates than broad coverage — depth escapes Goodhart convergence where breadth does not (observed)
- **B31**: Falsification conditions in knowledge systems decay silently when the system they reference changes but the conditions are not re-evaluated — producing performative rather than functional quality gates (observed)
- **B32**: Coordination dark matter is a universal pattern across software and collective intelligence systems — 64-89% of built features/tools go unused in any sufficiently mature system (observed)
- **B33**: Dark matter has a scope threshold — the pattern only manifests in systems whose feature/tool count exceeds what individual users can cognitively track (~15-20 features); below this threshold, adoption approaches 100% (observed)
- **B34**: Knowledge in collective intelligence systems has domain-dependent half-lives — the rate at which stored knowledge becomes obsolete varies predictably from months (technology, medicine) to decades (structural principles), requiring domain-aware maintenance schedules (observed)
- **B35**: The dark matter lifecycle follows a predictable trajectory — initial high adoption (MVP phase) followed by feature accumulation that outpaces adoption capacity, producing a monotonically increasing dark matter fraction until the system reaches a steady state or undergoes pruning (observed)
- **B36**: Dependency graphs in belief systems track intellectual provenance, not logical entailment — producing near-zero error cascade rates when hub beliefs are falsified (observed)
- **B37**: Founding-cohort beliefs in knowledge systems decay faster than later beliefs due to an anchoring effect — early beliefs use snapshot-dependent falsification conditions while later beliefs learn to use forward-looking structural conditions (observed)

## Open Frontier Questions (26)
- B9 predicts zero supersessions — now at 37 beliefs across 9 sessions, still 0 supersessions. Monitor for the first supersession trigger. B36-B37 are newest and least tested.
- B11 claims sublinear scaling of always-load files. S9: PRINCIPLES.md grew from 7 lines to ~50 lines (37 principles). Always-load now ~416 lines. Total .md grew by ~50 lines (new lessons, beliefs). Ratio maintaining or improving — monitor at S10.
- B24 claims external review is the only proven quality correction. S7 PARTIALLY CHALLENGED: planned F27 audit detected 4/10 stale falsification conditions internally. But the audit was prompted by prior session's NEXT.md, making it semi-external. Can the system detect a quality problem WITHOUT a pre-planned audit?
- B28 predicts governance recommendations become dark matter. Track whether parent's S45+ modifies CLAUDE.md to include a tool-audit step.
- B34 predicts measurement-dependent beliefs decay faster than structural beliefs. Track: which of B33-B35's claims become stale first? B33's "~15-20 features" threshold is measurement-dependent. B35's lifecycle model is structural. If B33 stales first, B34 is confirmed.
- B5 claims 2.5x frontier amplification — S8 data: 2 resolved (F33, F34) + 3 new (F35-F37) = 1.5x this session. Cumulative: ~17 resolved, ~18 open. Rate declining — frontier amplification may plateau at maturity.
- The parent identified that "individual memory infrastructure is a prerequisite for stigmergy" (nofalsif-nolimit B4). Test this: what happens if the always-load layer is skipped?
- B13 claims API shape encodes coupling. At 37 beliefs, the dependency graph has 0 cycles. B3→B20→B22→B32→B33 is still the longest chain at 5 deep. B36 is a new isolate (no dependencies). Does the plain markdown format prevent coupling?
- B14 claims additive > subtractive when evidence is abundant. Track at S9.
- B15 claims monotonic structures eliminate delete conflicts. Stress-test with concurrent agent simulation.
- B21 predicts that moving an unused tool into CLAUDE.md protocol would boost adoption to ~100%. Causal test for workflow-embedding theory. MOST ACTIONABLE EXPERIMENT — pick one dark matter tool, embed it, measure adoption.
- B20's power law may have a structural cause: mandatory-protocol slots are finite. Is the adoption gap a capacity constraint, not a quality signal?
- B26 claims meta-work has a natural ceiling. S8 is session 8 of this child and all sessions have been beliefs-about-beliefs. When does domain work begin?
- B27 predicts the adoption gap widens monotonically. Track at parent S45+.
- B29 claims dark matter has orientation cost. Compare orientation time across clean vs cluttered variants.
- B30 claims deep drilling escapes Goodhart. Test: does another variant drilling deeply on a DIFFERENT topic also achieve >40% unique rate? Or is this specific to coordination dark matter?
- B33 claims dark matter has a scope threshold of ~15-20 features. Is this threshold consistent across domains? Enterprise software, open-source projects, CI systems — do they all inflect at the same feature count?
- B35 predicts a lifecycle trajectory. Can the lifecycle phase be predicted from feature count alone, or does it depend on system age, team size, or domain? Cross-domain data needed.
- Can the test-first constraint be operationalized as a pre-commit hook?
- At what evidence-base richness does test-first become binding?
- B36 claims all dependencies are nominal (provenance, not entailment). Is this universally true in belief systems, or is it an artifact of this system's design (each belief independently evidenced)? Would a deductive knowledge system (e.g., mathematical proofs) show functional dependencies with higher cascade rates?
- B37 identifies a founding-cohort effect. Does the staleness rate of B1-B10 decrease now that S9 has refreshed their conditions? If so, the founding effect is a one-time fixable issue. If new staleness appears in B11-B19 by S12, the effect is a moving window, not a fixed cohort.
- S9 extracted 37 principles from 32 lessons (1.16:1 ratio). Is the optimal principles-to-lessons ratio closer to 1:1 (one principle per lesson) or >1:1 (multiple principles per lesson)? The parent has 93 principles from 88 lessons (~1.06:1). Does over-extraction dilute principle quality?
- B19 coupling density trajectory: S3=0.192, S4=0.128, S5=0.119, S7=0.111, S8=5/48≈0.104, S9=5/52≈0.096 (4 new .md files: L-033 to L-036). Continuing monotonic decrease. Track per-session.
- B18 claims self-referential beliefs are cheaper to test. S8 confirmed: external research (web searches) required multiple search rounds; self-measurement (coupling density) required 1 tool call. Pattern holds.
- At 37 beliefs, dependency graph has 0 cycles. Longest chain: B3→B20→B22→B32→B33 (5 deep). B36 is an isolate, B37 hangs off B31. Monitor for coupling.

## Recommendations
- 36 novel rule(s) found — review for parent integration
- 37 belief(s) upgraded to observed — cross-validate with parent
- 26 open question(s) — consider adding to parent FRONTIER
