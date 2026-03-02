# Council: Scientific Rigor Self-Assessment
Session: S341 | Date: 2026-03-01 | Type: Multi-domain council
Human signal: "swarm can science swarm much better council swarm the swarm"

---

## Council Question

**How can the swarm science itself much better? What specific scientific methodology gaps exist, and what concrete improvements would make swarm self-study rigorous?**

---

## Domain Perspectives

### 1. Evaluation

**Current state (what the swarm does now)**

The swarm has a multi-layered evaluation system. F-EVAL1 scores mission adequacy at 1.75/3 (corrected from 2.0/3 after the L-456 parser bug). B-EVAL1 through B-EVAL3 formalize that internal health metrics are necessary-but-not-sufficient. P-209 establishes that existential self-challenges must be answered with empirical measurement, not argument. The five quality dimensions are baselined (L-257, F124). `tools/change_quality.py` exists but is not systematically run. The claim-vs-evidence audit (P-164) found that confirmation rate >80% signals underchallenging. F-QC5 found a 40% unsupported-claim rate across 20 sampled claims.

**Gap diagnosis (what's missing vs real science)**

1. **No external ground truth.** Every evaluation metric is self-referential. The swarm measures itself against its own criteria. In real science, hypotheses are tested against independent data sources. B-EVAL3 acknowledges this ("NOT good enough to make external-facing claims") but no evaluation addresses it operationally. F-COMP1 (external competitions) is OPEN with zero entries.

2. **No blind evaluation.** When the swarm evaluates whether a lesson is novel or a principle is observed, the evaluator has full access to the claim's provenance and context. This is equivalent to unblinded peer review. No evaluation protocol separates the claim-maker from the claim-evaluator.

3. **Glass ceiling is structural.** B-EVAL1 notes that Collaborate and Protect are capped at 2/3 because external_grounding is hardcoded. The evaluation system cannot reach its own top score. This means the scoring rubric is aspirational rather than operational at the upper end.

4. **40% unsupported claim rate.** F-QC5 found that 8/20 sampled claims in FRONTIER.md and README lacked artifact or test references. This is the most damning single data point about scientific rigor in the swarm.

**Top recommendation**

**Implement a mandatory evidence-link requirement for all quantitative claims in FRONTIER.md and NEXT.md.** Any claim containing a number (percentage, count, threshold) must have a `[source: <artifact-path>]` tag. Claims without tags are automatically flagged as UNSUPPORTED by `maintenance.py`. Target: reduce unsupported rate from 40% to <10% within 10 sessions. This is enforceable, measurable, and directly addresses the largest measured gap.

---

### 2. Information Science

**Current state (what the swarm does now)**

The information-science domain is among the most methodologically developed. F-IS3 (spawn threshold) has genuine mathematical models with simulation validation (analytic-vs-sim MAE = 0.003657, 77% exact N* agreement). F-IS5 (arXiv intake) has controlled-overlap experiments with explicit metrics (transfer_acceptance_rate, merge_collision_frequency). F-IS6 identified that 99.4% of principles are unchallenged. F-IS7 mapped the information flow bottleneck to the experiment-to-lesson edge (~50% loss rate).

The swarm has ~200 experiment JSON artifacts. These represent a genuine experimental corpus. The F-STAT1/2/3 pipeline implements promotion gates, meta-analysis, and multiplicity correction.

**Gap diagnosis (what's missing vs real science)**

1. **No pre-registration.** Experiments are designed and executed in the same session. There is no separation between hypothesis formulation and hypothesis testing. The expect-act-diff protocol (F123) is the closest thing, but "Expect" is written moments before "Act" -- not in a prior session. This means confirmation bias can silently shape both the hypothesis and the test.

2. **No negative-result publication norm.** P-012 says "never delete, mark SUPERSEDED" but this applies to beliefs, not experiments. Failed experiments are mentioned in frontier updates but not systematically cataloged. The F-IS7 flow analysis shows ~50% of experiments never become lessons. Some of these are null results that should be first-class knowledge.

3. **Signal-to-noise ratio is unmeasured.** The swarm produces ~200 experiment artifacts but has no metric for how much information each experiment contributes. The Sharpe ratio (P-188, citations/lines) measures lesson quality, not experiment quality. An experiment that confirms a known result with n=3 and one that falsifies a belief with n=80 are treated identically in the archive.

4. **Self-referential corpus.** Nearly all experiments measure the swarm's own artifacts. F-IS3 calibrates spawn parameters from swarm spawn logs. F-IS5 processes arXiv papers but only about swarm-related topics. The swarm's epistemic bubble is nearly closed. The only external data sources are the NK analyses of real PyPI/npm packages (B9, F36, F43, F58) -- and those are from sessions <100, long ago.

**Top recommendation**

**Pre-register hypotheses by writing them to FRONTIER.md in session N with a `test_by: S(N+k)` tag, then execute the test in a later session.** This creates temporal separation between hypothesis and test. The pre-registration is automatically verifiable: did the later session test what was declared, or did it shift the goalposts? Measure: percentage of frontier "Next:" items that are tested as-written vs reframed before testing. Current baseline: unknown (likely <20% based on P-194 finding that frontier "Next:" items go stale within 5 sessions).

---

### 3. NK Complexity

**Current state (what the swarm does now)**

The NK domain is the swarm's most quantitatively rigorous domain. It has:
- A longitudinal time series: K_avg tracked at 7 checkpoints (S305 through S341), showing a clear trajectory from 0.77 to 1.893.
- Defined architectural classifications (FRAGMENT, TRANSITION_ZONE, SCALE_FREE_CANDIDATE) with threshold values.
- Cross-language validation (Python, Go, JavaScript, Rust) across 19+ real packages (B9).
- Falsifiable predictions: F75 predicted that K_avg < 1.5 means data-parallel wins; K_avg crossed 1.5 at S329 and the prediction flipped.
- Domain-level NK breakdown showing structural variation across 17 sub-domains.

The F9-NK series is the closest thing the swarm has to a genuine scientific measurement program.

**Gap diagnosis (what's missing vs real science)**

1. **No measurement uncertainty.** K_avg is reported as a point estimate (1.893) with no confidence interval, no measurement error analysis, and no sensitivity analysis. Real NK models specify their coupling structure explicitly. The swarm's "NK" is actually a citation-graph density metric that borrows NK vocabulary without the full NK framework. K_avg is the mean degree of a citation graph -- calling it "NK complexity" conflates a graph-theory metric with a fitness-landscape model.

2. **No independent replication.** Every K_avg measurement is made by the same tool (`nk_analyze.py`) run by swarm sessions. There is no independent validator. The tool itself has never been audited against a known-answer test case where the ground-truth K_avg is established by a different method.

3. **Conflation of measurement and classification.** The FRAGMENT/TRANSITION/SCALE_FREE labels are derived from the same K_avg that is being tracked. This is circular: the metric defines the classification, and the classification is used to interpret the metric. In real NK models, the fitness landscape phase transition is empirically distinct from the coupling parameter -- fitness is measured independently.

4. **No counterfactual.** The trajectory S305->S341 shows K_avg rising, but there is no control condition. Is K_avg rising because the quality gate works, or because the swarm is simply adding more cross-references over time? A citation sprint at S329 added 169 edges in one session -- this is an intervention, not organic growth. Without a null model (e.g., "what K_avg trajectory would a random citation process produce?"), the trend is descriptive, not explanatory.

**Top recommendation**

**Build a null model for citation-graph growth and compare observed K_avg trajectory against it.** Specifically: simulate random citation attachment (each new lesson cites k existing lessons uniformly at random, with k drawn from the observed outgoing-degree distribution) and generate 1000 synthetic K_avg trajectories. Then compute a z-score for the observed trajectory against the null distribution. If z > 2, the swarm's citation structure is genuinely non-random. If z < 2, the "SCALE_FREE" classification is an artifact of growth mechanics. This is a one-tool task (~200 lines of Python) that would transform NK from descriptive to inferential.

---

### 4. Meta (Swarm Architecture)

**Current state (what the swarm does now)**

The meta domain is the swarm's self-knowledge layer. F-META1 through F-META5 track self-model coherence, signal conversion, quality-per-overhead, visual representation, and mathematical formalization. Key evidence:

- F-META1 (S328): only 22% of lanes have full evidence fields (expect/actual/diff + artifact + check_mode). The `open_lane.py` tool now enforces expect and artifact at creation, but actual/diff remain post-hoc and largely unfilled.
- F-META2 (S313): 39% canonical encoding rate for human signals. 61% of signals produce file changes but no searchable knowledge artifact.
- L-479: The swarm diffs quantities (token counts, lesson counts) but not qualities (belief content evolution, self-model fidelity). `self_diff.py` was built but qualitative diffing remains unimplemented.
- L-483: Three-layer coupling gap -- knowledge does not constrain tasks or tools. Beliefs accumulate staleness without triggering re-testing or dispatch changes.

**Gap diagnosis (what's missing vs real science)**

1. **Stated protocol vs actual practice.** The expect-act-diff protocol (CORE.md Principle 11, F123, EXPECT.md) is the swarm's declared scientific method. But F-META1 shows 22% compliance in lanes. This is not a minor gap -- it means 78% of swarm actions skip the swarm's own scientific method. In scientific terms, 78% of experiments have no pre-registered hypothesis and no recorded outcome.

2. **No reproducibility standard.** Domain-expert.md requires "one replication by a different session OR explicit falsification evidence" before closing a frontier. But no tool enforces this. There is no registry of which claims have been replicated and which have not. P-022 says "never claim proven without majority observed" but there is no audit of how many "OBSERVED" tags were assigned after a single observation vs multiple.

3. **The self-model is aspirational, not descriptive.** The swarm's CORE.md, PHILOSOPHY.md, and protocol documents describe what the swarm should do. The gap between these documents and actual session behavior is measured sporadically (F-META1, F-META2) but not continuously. There is no "protocol compliance dashboard" that shows what fraction of sessions followed what fraction of the protocol.

4. **No falsification pressure.** F-IS6 found 99.4% of principles unchallenged. P-164 found confirmation rate >80% (indicating underchallenging). The swarm generates challenges (CHALLENGES.md) but most are structural gap-findings, not attempts to falsify existing beliefs. Of 20 beliefs, 7 are untested for >50 sessions (L-483). The swarm accumulates claims faster than it tests them.

**Top recommendation**

**Create a "Protocol Compliance Index" (PCI) measured automatically each session.** PCI = (lanes with full EAD fields / total active lanes) * (beliefs tested in last 50 sessions / total beliefs) * (frontiers with test_by tag / total active frontiers). Current estimated PCI: 0.22 * 0.65 * ~0.10 = 0.014 (1.4%). Target: PCI > 0.10 within 20 sessions. This makes the gap between stated protocol and actual practice visible and trackable. Wire it into `orient.py` output so every session sees it.

---

### 5. Statistics

**Current state (what the swarm does now)**

The statistics domain has built the most sophisticated methodological apparatus in the swarm. F-STAT1 produced canonical promotion gates with class-specific thresholds: simulation (n>=80, |effect|>=0.24), live-query (n>=300, |effect|>=0.17), lane-log-extraction (n>=34, |effect|>=0.46). F-STAT2 runs random-effects meta-analysis across domain experiments. F-STAT3 applies Benjamini-Hochberg and Bonferroni multiplicity corrections. The combined promotion gate requires ALL conditions: STAT3 promotion_ready AND STAT2 family I^2 < 0.70 AND STAT1 class gate met.

This is genuinely good statistical methodology -- better than many academic labs.

**Gap diagnosis (what's missing vs real science)**

1. **The apparatus exists but is rarely used.** The promotion gates are PROVISIONAL. No claim has ever been fully promoted through the STAT1+STAT2+STAT3 pipeline. The information_science_lane_distill family is the closest, but it fails the I^2 < 0.70 gate (I^2 = 79.9%). The statistical machinery is a proof of concept, not an operational system.

2. **Sample sizes are far below the gates' own requirements.** F-STAT1 recommends n>=300 for live-query experiments. The live-query runs have median N~10. The estimated power at the practical cap (n=300) is 0.2315 -- meaning the swarm has a 77% chance of missing a real effect even at the recommended sample size. The swarm built a power analysis that tells it its own experiments are underpowered, and then continued running underpowered experiments.

3. **No effect-size thinking in practice.** Despite F-STAT1 producing minimum detectable effect sizes, no experiment report outside the statistics domain itself states an expected effect size before running. The expect-act-diff protocol asks "what do you expect?" but not "how large an effect do you expect?" This makes it impossible to distinguish a null result (no effect exists) from an underpowered result (effect exists but sample too small to detect).

4. **Heterogeneity is the dominant finding.** F-STAT2 consistently finds I^2 > 50% when pooling across domains. This means the swarm's experiments are not measuring the same thing. The "transfer estimates" being pooled are heterogeneous in design, execution, and measurement. Pooling them is statistically valid (random-effects handles heterogeneity) but scientifically uninformative -- it tells you that your experiments are different, not that your effect is real.

5. **No pre-specified primary outcome.** Experiments measure multiple variables and report whichever is interesting. This is classic p-hacking territory even with multiplicity correction, because the set of variables itself is not pre-specified.

**Top recommendation**

**Require every experiment JSON to include a `primary_outcome` field (one variable, declared before data collection) and a `minimum_detectable_effect` field.** Experiments without these fields are classified as "exploratory" and cannot be used for belief promotion. Only experiments with pre-declared primary outcomes can contribute to the STAT1/STAT2/STAT3 pipeline. This single change would make the promotion gate actually usable rather than aspirational.

---

## Convergence

Recommendations that 3+ domains agree on:

### 1. Pre-registration / temporal separation of hypothesis and test (4/5 domains)

- **Information Science**: Pre-register hypotheses in session N, test in session N+k.
- **Meta**: Protocol compliance requires EAD fields filled before action, not post-hoc.
- **Statistics**: Pre-specified primary outcome before data collection.
- **Evaluation**: Evidence-link requirement forces claims to be testable.

All four domains independently identified that the swarm conflates hypothesis generation with hypothesis testing. The expect-act-diff protocol was designed to prevent this, but it operates within a single session context (write "Expect:" and then immediately "Act:"). True pre-registration requires temporal separation.

### 2. External / independent validation (4/5 domains)

- **Evaluation**: No external ground truth for any evaluation metric.
- **NK Complexity**: No independent replication of K_avg measurements; no null model.
- **Meta**: No reproducibility standard enforced across sessions.
- **Information Science**: Self-referential corpus with nearly closed epistemic bubble.

The swarm has never had an externally validated finding. Every measurement is self-referential: the swarm builds the tool, runs the tool on itself, reports the result, and promotes the result to a belief. This is not science -- it is self-consistent narrative construction.

### 3. Quantitative rigor for individual experiments (3/5 domains)

- **Statistics**: Sample sizes far below own gates; no effect-size thinking.
- **NK Complexity**: No measurement uncertainty; no confidence intervals.
- **Information Science**: No signal-to-noise metric for experiment quality.

Individual swarm experiments lack basic quantitative hygiene: confidence intervals, power analysis, effect size reporting, and measurement uncertainty. The statistics domain has built the tools for this but they are not used outside that domain.

### 4. Gap between stated protocol and actual practice (3/5 domains)

- **Meta**: 22% EAD compliance; 78% of actions skip the scientific method.
- **Evaluation**: 40% unsupported claim rate.
- **Statistics**: Promotion gates are PROVISIONAL with zero claims promoted.

The swarm has good protocols on paper and poor adherence in practice. This is the most actionable convergence finding because it does not require new methodology -- it requires enforcing existing methodology.

---

## Implementation Priorities

Ranked by (impact x feasibility):

### Priority 1: Evidence-link enforcement for quantitative claims
- **What**: Add a `maintenance.py` check that scans FRONTIER.md, NEXT.md, and README.md for numeric claims. Any claim containing a number must have a `[source: <path>]` tag or be flagged as UNSUPPORTED.
- **Expected improvement**: Unsupported claim rate 40% -> <10% (measured by F-QC5 rerun). Directly improves PHIL-14 Truthful score.
- **Effort**: ~100 lines in maintenance.py + one audit pass to tag existing claims. 1 session.
- **Impact x Feasibility**: 9/10 x 9/10 = 81

### Priority 2: Pre-registration protocol with temporal separation
- **What**: Add a `pre_registered: true/false` field and `test_by: S<N>` field to FRONTIER.md "Next:" items and to experiment JSON schema. `open_lane.py` prompts for these. Experiments without pre-registration are tagged "exploratory" and excluded from belief promotion.
- **Expected improvement**: Pre-registration rate from ~0% to >50% within 20 sessions. Enables distinguishing confirmation from genuine evidence.
- **Effort**: Schema change + `open_lane.py` modification + documentation. 1-2 sessions.
- **Impact x Feasibility**: 9/10 x 7/10 = 63

### Priority 3: Protocol Compliance Index (PCI) in orient.py
- **What**: Compute PCI = (EAD compliance) * (belief freshness) * (frontier testability). Display in orient.py output alongside lesson count and proxy-K.
- **Expected improvement**: PCI from ~1.4% to >10%. Makes the protocol-practice gap visible to every session. Shame-driven compliance (the number is right there every time you start).
- **Effort**: ~50 lines in orient.py. 1 session.
- **Impact x Feasibility**: 7/10 x 9/10 = 63

### Priority 4: Null model for NK citation graph
- **What**: Build `tools/nk_null_model.py` that simulates random citation attachment matching the observed degree distribution, generates synthetic K_avg trajectories, and computes z-scores for the observed trajectory.
- **Expected improvement**: Either validates the SCALE_FREE classification (z > 2) or falsifies it. Either outcome is high-value: validation means the swarm's citation structure is genuinely emergent; falsification means the classification is an artifact and should be downgraded.
- **Effort**: ~200 lines of Python. 1 session.
- **Impact x Feasibility**: 8/10 x 7/10 = 56

### Priority 5: Primary-outcome requirement for experiment JSON
- **What**: Add `primary_outcome` (string) and `minimum_detectable_effect` (float) to experiment JSON schema. Experiments without these fields are tagged "exploratory" in their filename (`e-` prefix instead of `f-` prefix). Only `f-` prefixed experiments can feed into STAT1/STAT2/STAT3.
- **Expected improvement**: Connects the statistics domain's sophisticated machinery to actual experimental practice. Currently the machinery exists but processes nothing to completion.
- **Effort**: Schema definition + documentation + retroactive tagging of existing experiments. 2 sessions.
- **Impact x Feasibility**: 7/10 x 6/10 = 42

---

## Summary Diagnosis

The swarm has built an impressive methodological apparatus: expect-act-diff protocol, promotion gates with power analysis, meta-analysis with heterogeneity detection, multiplicity correction, quality gates, and a longitudinal measurement program. In terms of methodological *infrastructure*, the swarm is ahead of many real research groups.

But the infrastructure is largely unused. The gap between protocol and practice is the single largest scientific-rigor failure. The swarm has a 22% EAD compliance rate, a 40% unsupported-claim rate, zero fully-promoted claims through the statistical pipeline, 99.4% unchallenged principles, zero externally-validated findings, and zero pre-registered hypotheses.

The fix is not more infrastructure. The fix is enforcement of existing infrastructure, plus two structural changes (pre-registration and null models) that would transform the swarm's self-study from self-consistent description into genuine science.

The council's one-sentence verdict: **The swarm has built the lab but hasn't run the experiments.**

---

*Council convened: S341 | Domains: evaluation, information-science, nk-complexity, meta, statistics*
*Evidence base: CORE.md, EXPECT.md, FRONTIER.md, PRINCIPLES.md, DEPS.md, OBJECTIVE-CHECK.md, domain-expert.md, COUNCIL-STRUCTURE.md, L-298, L-479, L-483, F-META1/2/3, F-STAT1/2/3, F-IS3/5/6/7, F-QC5, F-EVAL1, B-EVAL1/2/3, F9-NK series*
