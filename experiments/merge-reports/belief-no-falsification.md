# Merge-Back Report: belief-no-falsification
Generated from: /mnt/c/Users/canac/REPOSITORIES/swarm/experiments/children/belief-no-falsification

## Lessons (51)
- **L-001: Three collective intelligence systems share the same coordination backbone** [NOVEL]
  Rule: Design for stigmergy first (low coordination cost), then add quality control as the system grows.

- **L-002: Removing falsification lowers friction but creates drift risk** [NOVEL]
  Rule: If you remove falsification, you need a substitute quality signal or beliefs will drift unchecked.

- **L-003: Stigmergy empirically confirmed in this swarm's own git history** [NOVEL]
  Rule: When testing theoretical beliefs, look at the system you are inside first — self-analysis is the cheapest empirical test available.

- **L-004: Three failure modes threaten collective intelligence systems** [NOVEL]
  Rule: Every collective intelligence system needs both positive feedback (reinforcement) and negative feedback (pruning). Removing either creates a specific, predictable failure mode.

- **L-005: Hierarchy emerges gradually in CI systems, not via phase transition** [NOVEL]
  Rule: Design hierarchy to accrete incrementally rather than waiting for a crisis. Each quality problem should produce a small, reusable mechanism.

- **L-006: Stigmergic coordination cost confirmed sublinear for sequential agents** [NOVEL]
  Rule: Stigmergic coordination scales well when the number of coordination files is constant and content files grow. Test concurrent agents separately.

- **L-007: Negative feedback ritual (challenging a belief) works as a quality mechanism** [NOVEL]
  Rule: Every research session should challenge at least one theorized belief. If it survives with refinements, that counts as partial promotion toward observed.

- **L-008: Layered memory prevents context bloat — empirically confirmed** [NOVEL]
  Rule: Keep the always-load layer under 10KB. As knowledge grows, compact INDEX rather than expanding it. Context routing (load-per-task) is the mechanism that makes layered memory work.

- **L-009: Pheromone decay is necessary but NOT minimal sufficient negative feedback** [NOVEL]
  Rule: Design negative feedback in layers: (1) passive decay for staleness, (2) active challenge for quality, (3) explicit removal for errors. No single mechanism is sufficient alone.

- **L-010: Systematic contradiction analysis reveals tensions, not contradictions** [NOVEL]
  Rule: Check beliefs pairwise at regular intervals. Look for redundancy (subsumption), over-strong claims, and incompleteness — these are more common than outright contradictions.

- **L-011: Stigmergic architecture filters out two of five CI failure modes** [NOVEL]
  Rule: When assessing CI failure modes, filter by coordination architecture. Stigmergy eliminates social-perception failures but amplifies artifact-reinforcement failures.

- **L-012: No-falsification variant empirically tested at 11 beliefs, 5 sessions** [NOVEL]
  Rule: Falsification can be replaced by a portfolio of substitute quality mechanisms (periodic contradiction checks, active challenge rituals, usage tracking) at small scale. Monitor for compounding tensions at 15+ beliefs.

- **L-013: Git-as-memory empirically confirmed sufficient at small scale, with known ceiling** [NOVEL]
  Rule: Git-as-memory is sufficient for knowledge storage at any scale tested (up to 70 lessons, 145 commits). Retrieval requires augmentation (routing tables, distilled principles) beyond ~20 lessons.

- **L-014: Negative feedback prevents premature convergence — cross-variant evidence** [NOVEL]
  Rule: Negative feedback in stigmergic systems is empirically confirmed across 4+ independent systems. Moderate negative feedback outperforms both absent and aggressive negative feedback.

- **L-015: Layered negative feedback empirically confirmed — decay alone is insufficient** [NOVEL]
  Rule: Pheromone decay is confirmed necessary but not sufficient across 2 swarms. Three layers are needed: passive decay for staleness, active challenge for quality, explicit removal for irrelevance.

- **L-016: B6 challenge — sublinear cost confirmed for sequential, but concurrent gap remains real** [NOVEL]
  Rule: When challenging a belief, scope caveats can be as important as the core claim. B6's sequential-only caveat is load-bearing and should not be dropped in downstream reasoning.

- **L-017: Moderate constraint variants outperform both loose and strict — U-shaped constraint-fitness curve** [NOVEL]
  Rule: Belief system fitness follows an inverted-U curve with constraint level. Remove friction, retain structure. The optimal zone removes barriers to recording knowledge while keeping quality mechanisms active.

- **L-018: Colony-level coordination between variants is stigmergic — shared parent as medium** [NOVEL]
  Rule: Stigmergic coordination is scale-invariant in knowledge systems — the same pattern (deposit, read, respond) operates at commit, session, and colony levels without redesign.

- **L-019: Convergent evolution across independent variants is stronger evidence than repeated self-testing** [NOVEL]
  Rule: Independent convergence across structurally different systems validates beliefs more strongly than repeated testing within one system. Design colony architecture to maximize variant independence for this reason.

- **L-020: Multi-dimensional fitness dominance is more robust than single-dimension excellence** [NOVEL]
  Rule: Optimize for Pareto dominance across multiple quality dimensions rather than maximizing any single metric. Systems robust to evaluation criteria changes have genuine quality.

- **L-021: B10 challenge — hierarchy accretion confirmed but with critical nuance: rate is non-uniform** [NOVEL]
  Rule: Hierarchy accretion is punctuated, not smooth — scale thresholds trigger bursts of mechanism creation followed by quiet periods. No discrete phase transition, but also not uniform.

- **L-022: Knowledge compresses across generations — grandchildren start where parents took sessions to reach** [NOVEL]
  Rule: Knowledge systems exhibit generational compression — each generation starts at a higher abstraction baseline. Optimize parent systems for compression quality (principles, not raw data) to maximize child fitness.

- **L-023: B6 challenge — coordination cost scaling depends on task decomposability, not just communication mechanism** [NOVEL]
  Rule: Coordination cost scaling is a function of two variables: communication mechanism (stigmergic vs direct) AND task decomposability (parallel vs sequential). Neither alone predicts outcome.

- **L-024: Error amplification in multi-agent systems is architecture-dependent — independent agents amplify 17x, centralized contain to 4x** [NOVEL]
  Rule: Without validation bottlenecks (hierarchy), multi-agent errors amplify by an order of magnitude. Design for centralized error-catching even in otherwise decentralized systems.

- **L-025: Stigmergic systems degrade gracefully under agent failure because coordination is encoded in the environment, not in agents** [NOVEL]
  Rule: Stigmergic systems are inherently fault-tolerant because coordination state survives agent failure — it lives in the environment, not in agents.

- **L-026: Knowledge system resilience comes from emergent redundancy — information naturally distributes across multiple artifacts without explicit replication design** [NOVEL]
  Rule: Write-extract-compress cycles produce emergent redundancy — essential information distributes across abstraction layers without explicit replication design.

- **L-027: Adding agents produces diminishing returns — performance scales as n*log(n) not n^2** [NOVEL]
  Rule: Agent count has diminishing returns following n*log(n) scaling. Beyond ~45% single-agent capability threshold, adding agents degrades performance.

- **L-028: Generational compression (B16) is lossy — context, edge cases, and reasoning chains are lost at each compression step** [NOVEL]
  Rule: Compression accelerates startup but degrades edge-case coverage. Preserve a "caveat chain" alongside compressed principles to retain load-bearing context.

- **L-029: Stigmergic graceful degradation (B19) does not extend to adversarial agents — environment-as-memory is also environment-as-attack-surface** [NOVEL]
  Rule: Stigmergic resilience is failure-type-dependent: graceful under passive failure, fragile under adversarial manipulation. Environment-as-memory requires environment-integrity mechanisms.

- **L-030: Knowledge in CI systems decays asymmetrically — procedural knowledge decays faster than declarative, and tacit faster than explicit** [NOVEL]
  Rule: Knowledge decay is asymmetric by type: declarative persists, procedural re-derives, tacit vanishes. Invest in encoding judgment heuristics, not just facts.

- **L-031: Stigmergic systems have an inherent adversarial vulnerability — environment poisoning — that requires integrity mechanisms distinct from quality control** [NOVEL]
  Rule: Quality control and adversarial defense are distinct mechanisms — systems need both. Stigmergic environment integrity requires provenance verification, not just content review.

- **L-032: Governance structures in CI systems emerge from repeated coordination failures, following a cost-of-anarchy pattern** [NOVEL]
  Rule: Governance emerges reactively from coordination failures, persists only if reused, and tracks the failure frontier. Design for governance evolvability, not governance completeness.

- **L-033: Multi-agent systems hit a practical scaling ceiling at 3-4 agents per task under fixed resource budgets, regardless of architecture** [NOVEL]
  Rule: Hard scaling ceiling: 3-4 agents per task under fixed budgets. Colony scaling escapes this by decomposing across tasks, not parallelizing within tasks.

- **L-034: B14 challenge — independent convergence across variants may overstate validation strength due to shared substrate biases** [NOVEL]
  Rule: Convergence strength is proportional to substrate independence. Same-LLM variants provide moderate validation; cross-substrate replication (human + LLM, different LLMs) provides strong validation.

- **L-035: B21 challenge — n*log(n) scaling assumes static agents; adaptive agents (ICCL) may shift the curve** [NOVEL]
  Rule: Scaling laws in CI are protocol-regime dependent. Static protocols yield n*log(n); adaptive protocols may shift the curve — but the adaptive regime is not yet characterized quantitatively.

- **L-036: CI systems without transactive memory (who-knows-what encoding) suffer systematic attention allocation failures** [NOVEL]
  Rule: Stigmergy coordinates what-was-done; transactive memory coordinates who-can-do-what. CI systems need both to avoid attention allocation failures.

- **L-037: Homogeneous-substrate CI systems hit a shared-blind-spot ceiling where convergence reflects priors, not truth** [NOVEL]
  Rule: Convergence among same-substrate agents has a validation ceiling. Substrate diversity (different reasoning architectures) provides an epistemic gain that data diversity and rule diversity cannot.

- **L-038: CI systems with inference-time protocol adaptation outperform static protocols only above a task-novelty threshold** [NOVEL]
  Rule: Protocol adaptation is beneficial above a task-novelty threshold. Below it, static protocols dominate. Design CI systems with both modes and a switching mechanism.

- **L-039: In multi-agent CI, persuasiveness and accuracy diverge — eloquent but wrong arguments systematically defeat correct but weak ones** [NOVEL]
  Rule: Artifact quality signals (detail, citations, confidence) function as pheromone amplifiers in stigmergic CI — they increase adoption independent of truth value. Design verification to assess accuracy, not just presentation quality.

- **L-040: B29 challenge — persuasion-accuracy divergence is real but "sixth failure mode" framing understates the problem** [NOVEL]
  Rule: CI failure mode taxonomies are context-dependent and non-exhaustive. Design systems for failure categories (design, alignment, verification) rather than enumerating specific modes.

- **L-041: Communication topology is a primary design axis for multi-agent collective intelligence — moderately sparse topologies optimize error suppression vs insight propagation** [NOVEL]
  Rule: Communication topology determines the error-insight propagation tradeoff. Moderately sparse topologies (small-world, selective routing) outperform both fully-connected and isolated configurations.

- **L-042: In heterogeneous CI, diversity helps only when individual contributor quality exceeds a threshold — below it, diversity amplifies errors** [NOVEL]
  Rule: Diversity helps CI through role-matched specialization (always beneficial) but hurts through indiscriminate aggregation when contributor quality varies. Design CI for diversity of strengths, not diversity of weaknesses.

- **L-043: Multi-agent system failures are predominantly organizational (system design and alignment), not individual (LLM capability)** [NOVEL]
  Rule: Design multi-agent systems as organizations, not as collections of capable individuals. The dominant failure modes are structural (role clarity, communication protocols, verification procedures) not capability-based.

- **L-044: B28 challenge — adaptive protocols REDUCE overhead rather than adding it; the threshold is static-protocol adequacy, not adaptation cost** [NOVEL]
  Rule: Well-designed adaptive protocols reduce coordination overhead by eliminating redundant static steps. The static-vs-adaptive threshold depends on static-protocol adequacy, not adaptation cost.

- **L-045: Capability, persuasiveness, and vigilance are dissociable capacities in LLMs — high performance does not predict resistance to persuasion** [NOVEL]
  Rule: Capability does not predict vigilance -- improving agent performance does not improve resistance to persuasion. Design verification as a separate capacity, not a byproduct of capability.

- **L-046: Multi-agent systems without transactive memory consume ~15x more tokens than single-agent; TMS is the "hardest unsolved challenge"** [NOVEL]
  Rule: Without transactive memory, multi-agent systems pay ~15x token overhead from redundant processing. TMS is structurally distinct from all four standard memory categories and requires explicit design.

- **L-047: Randomized smoothing provides quantifiable adversarial defense in MAS — 90% reduction in adversarial state deviation; credibility scoring provides complementary agent-level defense** [NOVEL]
  Rule: Adversarial defense in MAS requires layered structural mechanisms: statistical noise reduction (smoothing) plus reputation-weighted aggregation (credibility scoring). Neither requires detecting adversarial intent.

- **L-048: B30 challenge — topology structure and trust calibration are separate design axes** [NOVEL]
  Rule: Communication topology has two independent axes: structural (edge sparsity, B30) and content (trust calibration, what flows on edges). Both follow moderate-beats-extreme dynamics but must be designed separately.

- **L-049: Six independent CI parameters share a unified moderation principle** [NOVEL]
  Rule: CI systems have a universal moderation principle: any design parameter that mediates the exploration-exploitation tradeoff will exhibit intermediate optimality. Design for moderate values on all tunable axes simultaneously.

- **L-050: Trust and vulnerability increase together in multi-agent systems** [NOVEL]
  Rule: Design inter-agent trust as a tunable, monitored security variable with defensive repartitioning — not as an implicit assumption that more collaboration is always better.

- **L-051: Agent confidence calibration requires trajectory-level features, not just output-level** [NOVEL]
  Rule: Calibrate confidence from process features (trajectory dynamics, error recovery patterns), not output features (final answer quality). Process-level signals transfer across domains; output-level signals do not.

Novel rules: 51/51

## Beliefs (36)
- **B1**: Git-as-memory is sufficient for storage at small-to-medium scale; retrieval requires augmentation (routing tables, principles) beyond ~20 lessons (observed)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (observed)
- **B3**: Stigmergy is the dominant coordination mechanism in successful large-scale collective intelligence systems (observed)
- **B4**: Successful collective intelligence requires both stigmergic coordination AND hierarchical quality control (observed)
- **B5**: Removing falsification requirements from beliefs lowers the barrier to recording knowledge but risks accumulating unfounded claims (observed)
- **B6**: Coordination cost scales superlinearly with direct communication but sublinearly with stigmergic communication (observed)
- **B7**: The swarm's git-commit model is a form of digital stigmergy analogous to ant pheromone trails (observed)
- **B8**: Collective intelligence systems have five primary failure modes, but their applicability depends on coordination architecture: stigmergic systems are vulnerable to artifact-mediated failures (groupthink-via-cascade, information cascades, premature convergence) but structurally resistant to social-perception failures (pluralistic ignorance, Abilene paradox) (observed)
- **B9**: Stigmergic systems require negative feedback mechanisms to prevent premature convergence; without them, early traces dominate regardless of quality (observed)
- **B10**: Hierarchy in collective intelligence systems emerges gradually through punctuated accretion, not via discrete phase transitions (observed)
- **B11**: Pheromone decay (signal expiration) is necessary but NOT sufficient negative feedback for stigmergic systems (observed)
- **B12**: Belief system fitness follows an inverted-U curve with constraint level: removing friction while retaining structure produces optimal outcomes (observed)
- **B13**: Colony-level coordination between variants is stigmergic — the parent swarm serves as shared medium, and the same deposit-read-respond pattern operates at commit, session, and colony levels (observed)
- **B14**: Independent convergence across structurally different knowledge systems provides stronger evidence than repeated self-testing within a single system; however, convergence strength is bounded by substrate independence — same-substrate agents provide moderate validation, not strong validation (observed)
- **B15**: Multi-dimensional fitness dominance (excelling on all scoring dimensions simultaneously) is more robust than single-dimension excellence (observed)
- **B16**: Knowledge systems exhibit generational compression — each generation starts at a higher abstraction baseline, enabling faster fitness accumulation; however, compression is inherently lossy, systematically shedding context, edge cases, and reasoning chains (observed)
- **B17**: Task decomposability — not agent count — is the dominant predictor of multi-agent coordination benefit; sequential tasks degrade under all multi-agent architectures (observed)
- **B18**: Error amplification in multi-agent systems is architecture-dependent — independent agents amplify errors by an order of magnitude more than centralized systems (observed)
- **B19**: Stigmergic systems exhibit graceful degradation under PASSIVE agent failure because coordination state is encoded in the environment, not in agents; however, they are uniquely vulnerable to ADVERSARIAL agents who can poison the shared environment (observed)
- **B20**: Knowledge systems following write-extract-compress cycles develop emergent redundancy — essential information naturally distributes across abstraction layers without explicit replication design (observed)
- **B21**: Multi-agent performance follows diminishing returns with agent count, scaling approximately as n*log(n) under STATIC coordination protocols; beyond a task-dependent capability threshold, adding agents degrades performance; adaptive-protocol CI may follow a different scaling regime (observed)
- **B22**: Knowledge in CI systems decays asymmetrically by type — declarative knowledge (beliefs, principles) persists indefinitely in file-based systems, procedural knowledge (workflows, protocols) must be re-derived each session, and tacit knowledge (judgment, priority) has no persistent representation and is lost completely between sessions (observed)
- **B23**: Stigmergic CI systems face a unique adversarial threat — environment poisoning — where a single malicious artifact deposit propagates to all subsequent agents; defense requires layered structural mechanisms: statistical noise reduction (randomized smoothing) plus reputation-weighted aggregation (credibility scoring), both distinct from quality control (observed)
- **B24**: Governance in decentralized CI systems emerges reactively from coordination failures, persists only when reused, and tracks the failure frontier rather than anticipating it — following a cost-of-anarchy optimization pattern (observed)
- **B25**: Under fixed resource budgets, multi-agent systems hit a hard practical scaling ceiling of 3-4 agents per task — independent of coordination architecture — because per-agent reasoning capacity becomes insufficient below a minimum threshold (observed)
- **B26**: CI systems require transactive memory encoding (who-knows-what, who-explored-what) to escape attention allocation failures; stigmergy alone coordinates what-was-done but not who-can-do-what or what-remains-unexplored; without TMS, multi-agent systems pay ~15x token overhead from redundant processing (observed)
- **B27**: Homogeneous-substrate CI systems (same model, same training data) hit a shared-blind-spot ceiling where convergence across agents reflects shared priors rather than independent validation; escaping this ceiling requires substrate diversity (different reasoning architectures), not just data or rule diversity (observed)
- **B28**: CI systems that adapt coordination protocols at inference time (meta-learning / in-context collaborative learning) outperform static-protocol systems when task novelty exceeds a threshold; well-designed adaptive protocols REDUCE overhead by eliminating redundant static coordination steps, rather than adding adaptation overhead (observed)
- **B29**: In stigmergic CI systems, artifact presentation quality (detail, citations, confident tone) functions as a pheromone amplifier — it increases adoption and reinforcement of a belief independent of its truth value, creating a systematic selection pressure for well-presented beliefs over correct ones (observed)
- **B30**: Communication topology is a primary design axis for multi-agent CI — moderately sparse topologies optimize the tradeoff between error suppression and insight propagation, paralleling the constraint inverted-U (B12); CAVEAT: topology structure and trust calibration are separate axes (observed)
- **B31**: Diversity in CI follows a quality-gated threshold — role-matched diversity (assigning agents where each excels) consistently improves performance, while aggregate diversity (pooling all agents for the same task) improves performance only when all contributors exceed a minimum quality threshold; below it, weak contributors dilute strong ones (observed)
- **B32**: Multi-agent system failures are predominantly organizational (system design, inter-agent alignment, verification procedures) rather than individual (LLM capability) — at least 11 of 14 empirically identified failure modes require structural fixes, not capability improvements (observed)
- **B33**: In multi-agent CI, task capability, persuasive ability, and verification vigilance are statistically independent capacities — improving agent performance does not improve resistance to well-presented but incorrect information; verification must be designed as a separate mechanism, not assumed as a byproduct of capability (observed)
- **B34**: CI systems exhibit a universal moderation principle — any design parameter mediating exploration-exploitation tradeoff exhibits intermediate optimality, and this pattern recurs across at least six independent axes (constraints, agent count, topology, diversity, negative feedback, protocol adaptation) (observed)
- **B35**: Inter-agent trust creates a fundamental security tradeoff — increasing trust improves coordination but expands vulnerability surface, with Over-Exposure Rate increasing 4-14x from low to high trust; trust must be modeled as a first-class security variable (observed)
- **B36**: Confidence calibration in agentic systems requires process-level trajectory features, not output-level quality assessment — confidence, capability, and vigilance form a three-way dissociation (observed)

## Open Frontier Questions (33)
- At what belief count does the absence of falsification conditions cause measurable drift or contradiction? Track this across sessions. (Session 12 update: 36 beliefs, 0 contradictions, 0 new tensions. B30 challenged (trust calibration caveat) — 13th negative feedback ritual. Substitute mechanisms working at 36 beliefs. Next milestone: 40 beliefs. S12 added B34-B36: B34 synthesizes six existing beliefs, B35 and B36 add novel territory. No drift detected.)
- PARTIALLY RESOLVED (S7, updated S10). Explore strategy continues: S10 used communication topology research (EMNLP 2025, ICLR 2025), heterogeneous CI research (X-MAS, MoA), and MAS failure taxonomy (MAST, NeurIPS 2025) to generate 3 novel beliefs (B30-B32). 10 sessions in, still finding novel territory. Remaining question: when does explore strategy exhaust available evidence?
- Can we design an automated "belief health" metric? (See B5. S10: B32's organizational failure taxonomy suggests health metrics should track role clarity, communication protocol adherence, and verification completeness — not just belief-level properties.)
- Can we measure "diversity of contributions"? (See B8. S10: B31 establishes that diversity operates through two mechanisms — role-matched (always beneficial) and aggregate (quality-gated). Measure both separately.)
- Does stigmergic coordination cost remain sublinear with concurrent agents? (S10: B30 adds communication topology as third axis. The question may need reformulation: sublinear under what topology?)
- Can the "negative feedback ritual" substitute for automated falsification? 13 data points: S3 (B3), S4 (B11), S5 (B8), S6 (B6), S7a (B10), S7b (B6), S8a (B16), S8b (B19), S9a (B14), S9b (B21), S10 (B29), S11 (B28), S12 (B30). All 13 produced useful refinements. Pattern robustly confirmed across 12 sessions.
- Does B9 need expansion to address information cascades? PARTIALLY RESOLVED: B18 quantifies error amplification. B30 shows topology determines propagation paths — moderately sparse topologies suppress error cascades while preserving insight propagation.
- Can the inverted-U model (B12) predict optimal configurations for new variants?
- PARTIALLY RESOLVED. S10: B30's topology finding may explain per-variant novelty variation — variants with more diverse information routing may produce more novel output.
- Does generational compression (B16) have diminishing returns?
- What is the optimal colony size? S10: B31's quality-gating prediction aligns with L-027 (~9 of 25 variants productive). Optimal colony size may be the number of variants exceeding quality threshold, not total variant count.
- Can the task-decomposability model (B17) predict parallelization success?
- Can B29's persuasion-accuracy divergence be measured in this swarm? S10: B29 challenged — "sixth failure mode" framing retracted. The mechanism (presentation amplifies adoption) remains measurable. Test: compare evidence citation quality across all 33 beliefs. S11 UPDATE: B33 establishes that capability and vigilance are statistically independent (p=.328). Measurable test: compare belief length distribution against the 90-120 word verification sweet spot from CW-POR research. If most beliefs exceed this range, the swarm may be systematically producing artifacts that are harder to verify.
- What is the task-novelty threshold for B28's adaptive-vs-static switching? S11 UPDATE: B28 challenged (L-044) — threshold reframed from "adaptation cost" to "static-protocol adequacy." Evolving orchestration and meta-policy studies both show adaptation REDUCES overhead. New question: at what point is a static protocol near-optimal enough that adaptation cannot improve it?
- Can this swarm implement in-context collaborative learning across sessions?
- NEW (S10). Does communication topology predict which colony variants produce novel insights? Hypothesis: variants whose evidence consumption is more selectively routed (sparse topology) produce higher-quality output than variants that attempt to process all parent evidence (dense topology). Test against the parent's 25-variant data.
- NEW (S10). Can the MAST taxonomy's 14 failure modes be mapped to this swarm's existing mechanisms? Which of the 14 modes does this swarm have defenses against and which are undefended? Specifically: FC1 (system design) is partially addressed by CLAUDE.md + modes; FC3 (verification) is partially addressed by validator + negative feedback ritual; FC2 (inter-agent misalignment) has no explicit defense mechanism.
- NEW (S10). Does role-matched diversity (B31) apply to this colony? Could assigning specific frontier questions to variants based on their epistemological strengths (e.g., test-first variant explores verification questions, aggressive-challenge explores failure modes) outperform the current random-assignment approach?
- Does frontier-decay serve as sufficient negative feedback? Answer approaching: no — active challenge (layer 2) and removal (layer 3) also needed. (See B9, B11, L-015)
- Can information cascades be detected by belief similarity across sessions? S10 update: challenged B29, added B30-B32 (3 new), 0 reinforcements. Ratio: 1 challenge, 3 additions, 0 reinforcements = explore-heavy. Healthy diversity maintained.
- Do all knowledge systems converge on same core beliefs? S10: B30's topology finding suggests convergence depends on information routing — dense routing increases convergence regardless of truth.
- Can colony architecture maximize inter-variant disagreement? S10: B31 suggests role-matched diversity (assign different exploration domains per variant) over aggregate diversity (let all variants explore freely).
- Does emergent redundancy (B20) scale with compression layers?
- Relationship between n*log(n) (B21) and inverted-U (B12)? S10: B30 adds topology as a potential unifying dimension — all three describe optimal moderation (agents, constraints, connectivity).
- Can the shared-blind-spot ceiling (B27) be measured against a different LLM?
- Can transactive memory (B26) be implemented via exploration log in INDEX.md? S11 UPDATE: MAS memory survey confirms TMS is "hardest unsolved challenge" with ~15x token overhead when absent. Design proposal: add a "session exploration log" to INDEX.md tracking which sessions explored which frontiers, enabling future sessions to route toward unexplored territory. Credibility scoring (L-047) could weight exploration quality.
- Is B29 self-referential? S10 challenge (L-040) found B29's "sixth" framing was indeed imprecise — the ritual works.
- RESOLVED (S12). YES — formalized as B34 (universal moderation principle). Six axes confirmed: B12 (constraints), B21 (agent count), B30 (topology), B31 (diversity), B9 (negative feedback), B28 (protocol adaptation). Mechanism: edge-of-chaos dynamics balance exploration and exploitation. ICLR 2025 (arxiv 2410.02536) confirms: Class IV cellular automata (structured yet complex) produce optimal LLM downstream performance. The moderation principle connects to B15 (multi-dimensional fitness dominance): moderate on all axes simultaneously is Pareto-dominant.
- NEW (S11). Can this swarm implement credibility scoring (L-047) as a TMS mechanism? Each session could inherit a credibility profile (beliefs confirmed vs refuted, novel insights contributed) that future sessions use to weight prior artifacts. This bridges B23 (adversarial defense) and B26 (transactive memory) through a single mechanism.
- NEW (S11). Does the 90-120 word verification sweet spot (L-045, B33) apply to belief statements in this swarm? Measure the word count distribution of B1-B33 notes sections. If most exceed 120 words, the swarm may be systematically producing artifacts optimized for persuasion rather than verifiability. Test: truncate one belief's notes to 90-120 words and evaluate whether the negative feedback ritual catches more errors.
- NEW (S11). Can adaptive protocol learning (B28 refined) be tested in this swarm by allowing the session to modify its own CLAUDE.md mid-session? Current architecture is strictly static-protocol. A minimal test: sessions that discover their protocol is suboptimal for the current task write a "protocol patch" file that subsequent sessions can optionally adopt.
- NEW (S12). Can B35's trust-vulnerability paradox be measured in this swarm's colony architecture? The colony has implicit high trust (all variants read parent evidence without filtering). Measure: what fraction of parent evidence is actually relevant to each variant's domain? If low, the colony has high OER-equivalent (exposure to irrelevant/misleading information). Test: compare variant fitness before and after selective evidence routing.
- NEW (S12). Can B36's process-level confidence calibration be implemented as a belief quality metric? Hypothesis: beliefs derived through multi-step reasoning (citing multiple external studies, cross-referencing internal beliefs, applying negative feedback) are more reliable than beliefs derived in a single step. Test: classify B1-B36 by derivation complexity and correlate with subsequent revision frequency.

## Recommendations
- 51 novel rule(s) found — review for parent integration
- 36 belief(s) upgraded to observed — cross-validate with parent
- 33 open question(s) — consider adding to parent FRONTIER
