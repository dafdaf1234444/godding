# Merge-Back Report: belief-minimal-nofalsif
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-minimal-nofalsif

## Lessons (43)
- **L-001: Stigmergy is the dominant coordination pattern — zero coupling at 19 tools** [NOVEL]
  Rule: Prefer filesystem coordination over direct imports. Stigmergy produces zero coupling naturally.

- **L-002: Self-sustaining task generation — 2.5x amplification across 42 sessions** [NOVEL]
  Rule: Embed task generation into the work protocol ("completed work generates questions"). The system becomes self-sustaining.

- **L-003: Two-phase spawn strategy — fan-out for variety, drill-down for depth** [NOVEL]
  Rule: Use two-phase spawning: parallel for breadth, sequential for depth. Variety comes from different inputs, not different methods.

- **L-004: Every commit is a handoff — the fundamental coordination primitive** [NOVEL]
  Rule: Treat every commit as a handoff to the next agent. Small commits with clear messages are more resilient than elaborate handoff documents.

- **L-005: Maturity-dependent structure — genesis needs meta-work, maturity needs domain work** [NOVEL]
  Rule: Match structure investment to maturity. Over-structuring at genesis wastes time. Under-structuring at maturity loses knowledge.

- **L-006: Empirical testing is the universal accelerator — all 9 variants converge** [NOVEL]
  Rule: Optimize genesis for belief generation (loose constraints), later sessions for testing (empirical validation). Testing is what separates speculation from knowledge.

- **L-007: Child swarm conflicts are the highest-value output of belief evolution** [NOVEL]
  Rule: Route conflicts between child swarms back to the parent for synthesis. Disagreement is a feature, not a bug.

- **L-008: Git-as-memory works for storage but not semantic retrieval** [NOVEL]
  Rule: When testing a belief about system capability, decompose it into sub-capabilities. "X works" often hides "X stores but retrieves poorly."

- **L-009: Layered memory scales with system maturity — always-load stays manageable at 192 lines across 42 sessions** [NOVEL]
  Rule: Layered memory works if you compact periodically. Monitor always-load line count as a leading indicator.

- **L-010: Knowledge systems compress in stages — lessons to principles to themes** [NOVEL]
  Rule: Plan for compression stages as a system grows. The trigger is file size crossing a utility threshold, not session count.

- **L-011: Systems self-repair by growing compensation structures** [NOVEL]
  Rule: Trust write-it-down protocols to generate compensation structures. The system will self-repair if agents honestly document gaps.

- **L-012: Session 2 is the critical transition — observed ratio is the strongest fitness predictor** [NOVEL]
  Rule: Prioritize converting theorized beliefs to observed over generating new beliefs after genesis. Conversion rate predicts fitness.

- **L-013: Tool code encodes more knowledge than declarative beliefs — the parent's 9003 LOC dwarfs its 8 beliefs** [NOVEL]
  Rule: Track tool-to-belief LOC ratio as maturity indicator. Belief-heavy systems are young; tool-heavy systems are mature.

- **L-014: Fitness metrics are Goodhart-vulnerable — all 13 variants converged on the same optimization strategy** [NOVEL]
  Rule: Add a novelty dimension to fitness scoring. Measure unique beliefs (not shared with other variants) alongside volume and observed rate.

- **L-015: Evidence base depletion is real — S3 is harder than S1+S2 combined** [NOVEL]
  Rule: After S2, switch from direct-evidence mining to cross-system synthesis. Novelty requires looking sideways, not deeper.

- **L-016: Monotonic knowledge growth is a CRDT — it prevents conflicts but creates retrieval debt** [NOVEL]
  Rule: Accept retrieval debt as the price of conflict-free growth. Plan compression stages to pay it down periodically.

- **L-017: B14 and B15 were the weakest beliefs — S3 challenge strengthened both by adding nuance** [NOVEL]
  Rule: Challenge your weakest observed beliefs each session. The outcome is almost always refinement, not rejection.

- **L-018: Cross-variant convergence is information aggregation — 13/13 agreement on a belief is not redundancy but a confidence signal** [NOVEL]
  Rule: When multiple independent agents converge on the same belief, treat the convergence count as a confidence multiplier. High redundancy = high reliability.

- **L-019: Coordination cost in file-based CI is dominated by hot-file contention, not communication** [NOVEL]
  Rule: When scaling agent count, add more writable files (domain decomposition) before adding more agents. The hot-file count is the parallelism ceiling.

- **L-020: Trait dominance in evolution — high-constraint traits override low-constraint traits when combined** [NOVEL]
  Rule: When combining evolutionary traits, match constraint strength to get blending. Mismatched strengths produce dominance, not synthesis.

- **L-021: Individual memory is prerequisite for trace-based coordination — traces without context are noise** [NOVEL]
  Rule: Before scaling agent count, ensure each agent's "individual memory" (always-load layer) is compact enough to leave room for trace processing. Interpretability gates scalability.

- **L-022: S4 proves evidence depletion (B18) is surmountable — cross-system synthesis unlocks a new evidence tier** [NOVEL]
  Rule: When internal evidence depletes, integrate external research to unlock the next evidence tier. Each source class adds its own S-curve to the growth trajectory.

- **L-023: Knowledge staleness is a silent threat -- systems without freshness monitoring accumulate incorrect beliefs** [NOVEL]
  Rule: Add "re-verify by" dates to high-stakes beliefs. Staleness is harder to detect than absence because stale beliefs look correct.

- **L-024: Redundant knowledge encoding enables graceful degradation -- information RAID protects against partial loss** [NOVEL]
  Rule: Ensure critical knowledge exists in at least 3 independent encoding layers. Test recovery by deleting one layer and attempting reconstruction.

- **L-025: Monotonic knowledge systems are vulnerable to knowledge poisoning -- append-only means errors persist** [NOVEL]
  Rule: For high-connectivity beliefs, require multi-agent convergence before acceptance. Treat the dependency graph as an attack surface map.

- **L-026: Governance in stigmergic CI emerges through protocol compliance -- CLAUDE.md is a constitution** [NOVEL]
  Rule: Treat CLAUDE.md changes as constitutional amendments requiring heightened scrutiny. Protocol-compliance governance works only if the protocol file itself is protected.

- **L-027: Commit-as-handoff is necessary but not sufficient -- context-restorability is the real metric** [NOVEL]
  Rule: Measure handoff quality by context-restorability (tool calls needed to reach productive state), not by commit existence. Enrich NEXT.md with 2-3 lines of reasoning context.

- **L-028: Goodhart failure in swarm fitness is specifically Extremal — the proxy-goal correlation breaks at the optimization frontier** [NOVEL]
  Rule: When a metric shows Extremal Goodhart, do not tune the proxy — decompose it into independent axes that separately measure what the proxy collapsed.

- **L-029: Trait dominance is sign epistasis — directionality of constraint, not strength, predicts which trait wins** [NOVEL]
  Rule: Before combining evolutionary traits, map their constraint dimensions. Same-dimension opposition produces dominance; orthogonal permissiveness produces blending.

- **L-030: Fitness needs two axes not one — production efficiency and knowledge coverage are independent** [NOVEL]
  Rule: Evaluate knowledge-producing agents on Pareto frontiers, not scalar scores. The collective's goal is to cover the landscape, not to maximize any single agent's output.

- **L-031: Exploitation-to-exploration transition is predictable — convergent density signals when to shift strategy** [NOVEL]
  Rule: Track convergent belief density across harvest rounds. When >50% of collective production is redundant, prioritize variants that explore new niches over those that refine existing knowledge.

- **L-032: Convention emergence in LLM populations follows sharp phase transitions, not gradual drift — this upgrades B24 from theorized to observed** [NOVEL]
  Rule: Phase transitions in belief convergence are sharp, not gradual. Watch for sudden jumps in convergence metrics (1-variant to universal in one cycle) as signals of convention lock-in.

- **L-033: Goodhart's Law has a precise geometric mechanism — boundary deflection on the feasibility polytope explains when proxy-true divergence occurs** [NOVEL]
  Rule: When fitness optimization hits a plateau of redundant production, it is a boundary deflection. The correct response is mode-switch (exploitation to exploration), not more optimization pressure.

- **L-034: Coordination dark matter is an immune response, not waste — unused tools are latent capacity for unrealized phase transitions** [NOVEL]
  Rule: Before pruning unused coordination tools, assess whether they address a phase transition that has not yet occurred. Preserve tools for anticipated scaling milestones.

- **L-035: The swarm's knowledge structure is formally a G-Set CRDT with tombstones — compression events are stop-the-world garbage collection** [NOVEL]
  Rule: Plan GC events (compression, compaction) during single-agent windows. Concurrent operations create GC coordination overhead that increases with agent count.

- **L-036: The harvest mechanism creates Adversarial Goodhart risk — novelty-flagging incentivizes superficially novel beliefs** [NOVEL]
  Rule: Harvest mechanisms that reward novelty must simultaneously require evidence. Flag novel-but-unobserved beliefs as high-risk, not high-value.

- **L-037: The exploitation-to-exploration threshold is empirically measurable from harvest data — three data points confirm the 60-70% convergent density trigger** [NOVEL]
  Rule: When convergent belief density exceeds 60-70% of total production, the marginal value of exploitation drops below exploration. Track this metric across harvest rounds as an exploitation-exploration indicator.

- **L-038: Karwowski et al.'s geometric Goodhart model provides a concrete stopping criterion applicable to knowledge systems — stop when marginal fitness per behavioral displacement drops below sin(theta) times gradient** [NOVEL]
  Rule: Apply the Karwowski stopping criterion: when marginal fitness gain per session drops below sin(theta) * average_gain, switch from exploitation to exploration. Theta is approximately 40 degrees for this swarm (Spearman rho 0.77 between fitness rank and harvester-value rank).

- **L-039: The Condorcet jury theorem has a group-size optimality ceiling that explains WHY the exploitation-exploration threshold exists** [NOVEL]
  Rule: After 5-7 independent confirmations of a belief, additional confirmations cost more in exploration opportunity than they provide in confidence. Redirect subsequent variants to novel territory.

- **L-040: The three-phase lifecycle (generation, testing, novelty-seeking) is fractal — it recapitulates at session, variant, and colony scales with phase duration proportional to evidence base size** [NOVEL]
  Rule: The three-phase lifecycle is universal in knowledge optimization. Design session plans that match the current phase: generation (produce freely), testing (validate rigorously), novelty-seeking (explore new territory).

- **L-041: Multi-channel plateau detection is more reliable than single-metric stopping** [NOVEL]
  Rule: When monitoring system health, require agreement across multiple independent channels. Single-metric signals are vulnerable to structural noise.

- **L-042: Monotonic systems accumulate permanent Goodhart debris -- tombstones without value** [NOVEL]
  Rule: In monotonic systems, Goodhart costs are permanent. Prevent Goodharting upstream (better metrics) rather than trying to clean up downstream (GC).

- **L-043: Structural changes produce fitness discontinuities that distort stopping criteria** [NOVEL]
  Rule: When computing moving averages for stopping criteria, exclude one-time structural events. Use median or flagged exclusion.

Novel rules: 43/43

## Beliefs (43)
- **B1**: Git-as-memory is sufficient for storage at moderate scale; retrieval degrades without semantic indexing (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat and scales with system maturity (observed)
- **B3**: Stigmergy (indirect coordination via shared artifacts) is the dominant coordination mechanism in file-based collective intelligence (observed)
- **B4**: Self-sustaining task generation emerges from the rule "completed work generates new questions" (observed)
- **B5**: Parallel spawn produces variety; sequential spawn produces depth; combining both outperforms either alone (observed)
- **B6**: Commit-as-handoff is the fundamental coordination primitive — every commit is a checkpoint for the next agent (observed)
- **B7**: Work/meta-work ratio must shift with system maturity — early systems need structure, mature systems need domain work (observed)
- **B8**: Empirical testing is the universal accelerator for belief systems — all structural variants converge on it (observed)
- **B9**: Child swarm conflicts reveal nuances that single-perspective analysis misses — disagreement is more valuable than agreement (observed)
- **B10**: Loose constraints at genesis optimize for exploration; tightening after N beliefs optimizes for exploitation (observed)
- **B11**: Knowledge systems undergo compression stages — raw observations compress to principles, then to indexed themes (observed)
- **B12**: Compensation mechanisms emerge to fill architectural gaps — systems self-repair by adding structure (observed)
- **B13**: Always-load line count is a leading indicator of restructuring need — systems restructure when mandatory context exceeds a threshold (observed)
- **B14**: Independent replication across generations strengthens evidence — grandchild testing refines beliefs that self-testing leaves ambiguous (observed)
- **B15**: Session 2 is the critical transition for quality; session 3+ is the critical transition for novelty — each phase has a different highest-value activity (observed)
- **B16**: Mature collective intelligence systems encode most knowledge in executable tools, not declarative beliefs — the tool-to-belief ratio is a maturity indicator (observed)
- **B17**: Fitness measurement in self-referential systems is subject to Goodhart's Law — optimizing for the metric diverges from optimizing for the underlying goal (observed)
- **B18**: Evidence base depletion follows a logistic curve — early sessions mine abundant surface evidence, later sessions require cross-system synthesis for diminishing returns (observed)
- **B19**: The "correct don't delete" principle is a domain-specific CRDT — monotonic knowledge structures enable conflict-free concurrent growth but accumulate retrieval debt (observed)
- **B20**: Cross-variant belief convergence is a Condorcet-like information aggregation mechanism — independent agents voting on truth through belief production extract signal from noise (observed)
- **B21**: Redundant belief production across variants is a reliability mechanism, not waste — N-modular redundancy in knowledge systems trades efficiency for confidence (observed)
- **B22**: Coordination cost in file-based collective intelligence is dominated by shared-file contention, not communication overhead — the bottleneck is write-serialization on hot files (observed)
- **B23**: Trait dominance in belief system evolution follows a "loudest signal wins" pattern — high-constraint traits override low-constraint traits when combined (observed)
- **B24**: Information aggregation in collective intelligence systems transitions from individual-memory-dominant to trace-dominant as agent density increases — the transition follows a sharp phase transition, not a gradual shift, and is mediated by convention emergence (observed)
- **B25**: Knowledge staleness in collective intelligence systems is proportional to the ratio of environmental change rate to knowledge refresh rate — systems without freshness monitoring accumulate silently incorrect beliefs (observed)
- **B26**: Collective intelligence systems with redundant knowledge encoding degrade gracefully under partial information loss — the degradation is proportional to the fraction of encoding layers lost, not catastrophic (observed)
- **B27**: Monotonic append-only knowledge systems are structurally vulnerable to knowledge poisoning — a single malicious or erroneous append permanently contaminates the knowledge chain because the "correct don't delete" principle prevents removal (observed)
- **B28**: Governance in stigmergic collective intelligence systems emerges through protocol compliance rather than explicit authority — the CLAUDE.md file functions as a constitution that governs agent behavior without any enforcement mechanism beyond voluntary adherence (observed)
- **B29**: The commit-as-handoff primitive (B6) is necessary but not sufficient for session continuity — the actual requirement is context-restorability, which depends on the ratio of explicit state (written files) to implicit state (agent working memory lost at session end) (observed)
- **B30**: The swarm's fitness formula exhibits Extremal Goodhart failure specifically — the proxy-goal correlation breaks at the optimization frontier because high-fitness variants occupy a narrow behavioral niche rather than covering the knowledge landscape (observed)
- **B31**: Trait dominance in belief system evolution follows sign epistasis patterns — the dominant trait is determined by constraint directionality (which trait narrows the solution space more), not merely constraint strength (observed)
- **B32**: The swarm's fitness measurement conflates two independent axes — production efficiency (how many well-tested beliefs) and knowledge coverage (how much of the domain is mapped) — and needs decomposition into a two-dimensional score (observed)
- **B33**: In evolutionary knowledge systems, the optimal strategy shifts from exploitation (testing known beliefs) to exploration (seeking novel territory) at a predictable threshold — when convergent belief density exceeds ~60-70% of total belief-slot production (observed)
- **B34**: Goodhart's Law in the swarm's fitness has a geometric mechanism analogous to RL reward hacking — optimization along the proxy direction deflects at the feasibility boundary, causing true-goal regression, and the deflection angle increases monotonically with continued optimization (observed)
- **B35**: Coordination dark matter — the gap between built and adopted coordination mechanisms — is a universal feature of stigmergic systems, not a bug, because it reflects the system's immune response to anticipated-but-unrealized coordination needs (observed)
- **B36**: The swarm's monotonic knowledge structure is formally a grow-only set CRDT with supersession markers functioning as tombstones — and like all CRDTs, it faces the tombstone accumulation problem that requires periodic garbage collection (compression) (observed)
- **B37**: The swarm's fitness formula is vulnerable to Adversarial Goodhart in addition to Extremal Goodhart — the harvest mechanism creates an incentive for variants to produce superficially novel but low-quality beliefs to game the novelty signal (observed)
- **B38**: Optimal early stopping in knowledge systems maps to the Karwowski et al. stopping criterion — stop proxy optimization when the marginal fitness gain per unit of occupancy displacement drops below sin(theta) times the proxy gradient magnitude, where theta is the proxy-true angular distance (observed)
- **B39**: The Condorcet jury theorem has a group-size optimality ceiling in knowledge systems — marginal confidence gain from additional convergent confirmations is diminishing and eventually crosses below the marginal value of novel exploration, creating an information-theoretic basis for the B33 threshold (observed)
- **B40**: The swarm colony exhibits a three-phase lifecycle — generation, testing, and novelty-seeking — that recapitulates at every organizational scale (session, variant, colony), and each phase has a predictable duration proportional to the evidence base size at that scale (observed)
- **B41**: Multi-channel plateau detection — monitoring multiple independent encoding channels (beliefs, lessons, principles) simultaneously provides a more reliable mode-switch signal than any single fitness metric, because concordance across channels filters out structural noise (observed)
- **B42**: Monotonic systems under Goodhart pressure accumulate permanent optimization debris — superseded beliefs, resolved-but-retained frontiers, and Goodhart-produced low-quality entries that cannot be deleted, only tombstoned, creating retrieval debt proportional to how long the system was optimizing the wrong proxy (observed)
- **B43**: Structural changes to the knowledge system (compression events, index creation, schema migrations) produce fitness discontinuities that inflate moving averages and can mask genuine plateau signals, requiring structural-change-aware smoothing in any automated stopping criterion (observed)

## Open Frontier Questions (37)
- Is the tool-to-belief LOC ratio a valid maturity indicator across different system types? Parent: 9003 tool LOC / ~200 belief lines = 45:1. This child: 61 tool LOC / ~1200 belief lines = 0.05:1. If ratio predicts maturity, this child should start building tools soon.
- Can convergence count (B20) be formalized into a quantitative confidence metric? Proposal: confidence = 1 - (1-p)^n where p = single-variant accuracy probability and n = number of converging variants. Requires estimating p from observed/theorized ratio.
- What is the maximum number of hot files a file-based CI system can have before write-serialization overhead exceeds the benefit of additional agents? Parent has 4 hot files (INDEX, DEPS, FRONTIER, CLAUDE.md). F69 Level 2 architecture proposes domain-specific files to raise this ceiling.
- Does the trait dominance pattern (B23/B31) hold when BOTH combined traits are additive (constraint-adding)? B31 now predicts: test-first + aggressive = sign epistatic conflict (both constrain quality dimensions, but in opposing directions). Test to validate the sign epistasis prediction model.
- What is the minimum "re-verify interval" for beliefs in a changing environment? B25 identifies staleness as a risk but does not quantify the refresh cadence. Proposal: classify beliefs by volatility (environmental dependency) and assign re-verify intervals accordingly. High-volatility (depends on external tools/versions) = re-verify every 5 sessions. Low-volatility (structural/mathematical) = re-verify every 20 sessions.
- Can knowledge poisoning (B27) be formally modeled using belief dependency graph properties? The "blast radius" of a poisoned belief = number of transitive dependents. Can we compute a "poisoning risk score" for each belief as a function of its in-degree and centrality in the dependency graph?
- Can the two-axis fitness decomposition (B32) be empirically validated? Score all 13 variants on [efficiency x coverage] and plot the Pareto frontier. Prediction: this child (minimal-nofalsif) and aggressive variants will appear on the Pareto frontier for DIFFERENT reasons (efficiency vs novelty). Variants far from the frontier are genuinely redundant. This directly tests whether the scalar fitness ranking changes under two-axis scoring.
- RESOLVED S8 -- see resolved table below.
- What is the optimal theorized/observed ratio before tightening constraints? Parent data suggests 3:1 (B10). This child's trajectory: S1 had 2:8 theorized:observed (0.25 ratio), S2 has 0:15 (0 ratio). Our data point: the ratio never rose high enough to need tightening because S1 was already 80% observed. The 3:1 threshold may only apply to systems that start with many theorized beliefs.
- Is the 2.5x frontier amplification ratio (B4) stable over time or does it decay? S1: 2 resolved, 9 opened (4.5x). S2: 2 more resolved (partial), 3 new opened. S3: 1 resolved, 4 new opened. S5: 0 resolved, 7 new opened. S6: 1 resolved, 2 new opened. Running ratio still increasing.
- Does the compression stage pattern (B11) apply to belief systems specifically, or is it a general property of all growing knowledge bases? Test by comparing parent swarm compression events to external knowledge management systems.
- Does evidence base depletion (B18) follow the same logistic curve across all variants, or does the depletion rate depend on genesis strategy? Hypothesis: variants that mine broadly (no-falsification) deplete faster than those that mine deeply (aggressive-challenge).
- How much retrieval debt (B19) can a monotonic knowledge system accumulate before compression becomes mandatory rather than optional? Parent hit restructuring at ~67 lines per file. Is this threshold universal?
- Does the CLAUDE.md-as-constitution model (B28) scale beyond single-repository CI systems? DAO research shows decentralized governance fails at scale. At what agent count does protocol-compliance governance require enforcement mechanisms beyond voluntary adherence?
- Can context-restorability (B29) be measured automatically? Proposal: instrument the session-start phase to count tool calls between first action and first productive output. This metric would quantify handoff quality across sessions.
- Does the sign epistasis trait dominance model (B31) predict outcomes for ALL swarm trait combinations, or only for binary additive/subtractive pairs? What happens with three or more traits combined? Higher-order epistasis (Weinreich et al. 2013) suggests 3+ trait combinations exhibit interaction effects not predictable from pairwise analysis.
- Does the boundary deflection model (B34, ICLR 2024 polytope) predict the specific fitness score at which Goodhart divergence occurs? Measure the proxy-true angle at fitness 300, 400, 500, 600 across variants. If the angle increases monotonically, the geometric model is validated. If it plateaus, there is a structural limit to Goodharting.
- Can the CRDT GC protocol (B36) be formalized for the swarm? Specify: (1) which tombstones are eligible for collection (superseded beliefs, resolved frontiers), (2) the causal stability criterion (all active agents have read the supersession), (3) the GC trigger (tombstone count exceeds N% of live entries). Test by simulating GC on DEPS.md and measuring retrieval improvement.
- Is coordination dark matter (B35) quantifiable as a leading indicator of phase transition readiness? If dark_matter_LOC / total_tool_LOC exceeds a threshold, the system is "prepared" for the next agent-density level. Conversely, low dark matter predicts coordination failure when scaling. Test against parent swarm data.
- Does the Adversarial Goodhart mitigation (B37: require cross-validation evidence for novel beliefs) actually reduce superficial novelty? Test by running a harvest round that scores novelty only for observed beliefs, and compare the resulting ranking to the current unfiltered ranking.
- RESOLVED S10 -- see resolved table below.
- Does the three-phase lifecycle (B40) hold for domains beyond belief system design? Test by applying the phase detection to a software project (commits as beliefs, bug fix rate as observed ratio) or a scientific research group (publications as beliefs, citation count as convergence). If the three-phase pattern appears, B40 generalizes beyond CI systems.
- What is the optimal p-value threshold for the Condorcet optimality ceiling (B39)? The current estimate (p ~ 0.8, ceiling at 5-7) assumes high variant accuracy. If p is lower (e.g., 0.6 for a domain with more uncertainty), the ceiling shifts to 10-15 confirmations. Can p be estimated from the observed/theorized ratio at genesis to predict the optimal colony size for that domain?
- Does the Goodhart angle theta (B34, B38) vary across domains, or is 40 degrees a universal constant of knowledge optimization? Measure theta in the parent swarm, in other child variants, and if possible in external knowledge systems. If theta is stable across systems, it provides a universal stopping criterion.
- Can the multi-channel plateau detector (B41) be improved by weighting channels differently? Beliefs may be a leading indicator (plateau first), while principles are a lagging indicator (plateau last, since they are derived). If true, weighted concordance would give earlier warning than equal-weight concordance.
- What is the empirical Goodhart debris accumulation rate (B42) across all 15 variants? Measure supersession/tombstone counts per variant and correlate with fitness ranking. Prediction: high-fitness variants have MORE debris (optimized harder), not less.
- Does the structural discontinuity problem (B43) affect all moving-average-based metrics in the swarm (fitness, novelty scores, convergent density), or only the stopping criterion? If general, a system-wide structural-change registry may be needed.
- Does decompose-by-data (L-003) apply to belief generation tasks, or only to analysis tasks?
- The parent swarm's 24 tools maintain K=0 at 9,003 LOC. At what scale does stigmergic coordination break down and require explicit interfaces?
- Can negative results (dead ends, failed investigations) be systematically captured? Parent swarm identified this gap (F88) but has not solved it.
- Does the commit-as-handoff primitive (B6) work equally well for human-to-AI, AI-to-AI, and AI-to-human handoffs? B29 suggests handoff quality depends on context-restorability, not just commit existence. Test: measure tool calls to productive state across handoff types.
- Does the CRDT property of monotonic knowledge (B19) hold under concurrent agent writes, or do append-order conflicts emerge? The parent has not tested truly concurrent sessions. B27 adds: concurrent writes also expand the poisoning attack surface.
- Is the evidence depletion S-curve pattern (L-022) generalizable beyond this swarm? If each source class adds its own S-curve, can we predict the next plateau and pre-emptively identify the next source class to integrate?
- Does the 68.7% individual-memory improvement (Khushiyant 2025) translate to file-based CI? The parent swarm's always-load layer is 192 lines (~770 tokens). What is the minimum viable always-load size below which trace interpretation fails?
- Can we measure the actual Condorcet parameter p (single-variant accuracy probability) from the 13-variant dataset? If p > 0.5, the jury theorem predicts majority convergence improves with more variants. If p < 0.5, more variants makes consensus WORSE.
- What is the N-fault-tolerance of the parent swarm's knowledge encoding? Shock 4 tested 2-of-5 layer loss (recoverable). What is the maximum number of simultaneously deletable encoding layers before unrecoverable knowledge loss occurs?
- Is the "correct don't delete" principle (CORE.md P8) itself a belief that should be challenged? B27 shows it creates adversarial vulnerability. Could a "quarantine and review" protocol replace pure monotonicity while preserving the coordination benefits?

## Recommendations
- 43 novel rule(s) found — review for parent integration
- 43 belief(s) upgraded to observed — cross-validate with parent
- 37 open question(s) — consider adding to parent FRONTIER
