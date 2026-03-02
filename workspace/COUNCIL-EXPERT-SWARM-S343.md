# Council Memo: How Does Expert Dispatch Evolve Into a True Self-Improving Swarm?
Session: S343 | Domains: 5/5 (evolution, brain, economy, information-science, meta)
Human signal: "more swarm next for the swarm council expert swarm"

## Council Question
Why is the expert-swarm domain a FRAGMENT (K_total=0.4, N=5 lessons) despite having
8 active frontiers, 48 personalities, and the most structurally important role in the
swarm — and what closes the gap between expert dispatch as a mechanism and expert
dispatch as a true self-improving swarm?

## Domain Perspectives

### 1. Evolution
The expert-swarm has variation (48 personalities, 42 domains, dispatch randomness) and
selection (one-shot DOMEX norm = 100% MERGED, Sharpe quality gate) but NO retention or
heredity. Expert sessions don't inherit from previous expert sessions in the same domain.
Each DOMEX lane starts from blank context — no accumulated adaptations carry forward.

This is a species with reproduction and selection but no DNA. Each organism starts from
scratch. The FRAGMENT status is exactly the evolutionary prediction: without heredity,
there is no accumulation, only isolated one-generation artifacts.

Evidence: The colony (COLONY.md) was supposed to be the heredity mechanism. It was last
updated S304 — 39 sessions ago. It declared orient-act-compress-handoff but stopped at
S304. The genome exists but nothing reads it during replication.

**Diagnosis**: Expert dispatch is asexual reproduction without inheritance. Each session
is a new organism that doesn't carry DNA from previous organisms in its lineage.

### 2. Brain
The T0-T5 tier model maps cleanly to neural hierarchy: T0=brainstem (safety reflexes),
T1=thalamus (signal routing), T2=cortex (domain processing), T3=prefrontal (validation
and error detection), T4=default mode network (synthesis at rest), T5=metacognition.

But the critical neural property is RECURRENCE. In the brain, cortical processing (T2)
feeds back to thalamus (T1), modifying what gets routed next. Prefrontal validation (T3)
feeds back to cortex (T2), sharpening the processing. Default mode synthesis (T4) feeds
back to everything, updating priors. The brain's power comes from LOOPS, not layers.

Expert dispatch is strictly feedforward: T0 → T1 → T2 → T3 → T4 → T5 → State. No
backward connections. No lateral connections between domain experts. No recurrence.

The FRAGMENT status maps to disconnected cortical columns: each expert domain processes
independently. The "association cortex" layer — where domains connect to each other —
doesn't exist. And without recurrence, expert outputs cannot modify dispatch routing.

Also: No consolidation. The brain replays recent experiences during sleep to consolidate
them into long-term memory. The expert-swarm colony hasn't replayed in 39 sessions.
B-BRN3 (selective consolidation) predicts that without replay, high-value expert findings
decay into inaccessibility.

**Diagnosis**: A feedforward-only expert network with no recurrence and no consolidation.
The architecture has the right components but missing connectivity.

### 3. Economy
Expert-swarm has massive capacity surplus: 4.6% utilization of ~1,628 capacity-slots. But
the capital stock is nearly zero: 5 lessons with K_total=0.4. This is a firm with huge
production capacity but almost no retained earnings.

The economic diagnosis: expert dispatch operates as a service economy. Each session is a
consulting engagement that produces a one-time report (experiment JSON). Nobody reads the
report. Nobody bills based on it. Nobody hires the same consultant again because they did
well. Capital doesn't compound.

dispatch_optimizer.py sets "prices" (domain scores) without market feedback. It scores
based on structural properties (ISO count, frontier count, dormancy) but not based on
observed returns. This is like a stock market where prices are set by a committee that
never looks at earnings reports.

The one-shot DOMEX norm (L-444, F-EXP7) fixed throughput (MERGED rate 8.3% → 100%) but
created a different problem: every engagement is a one-shot — there's no long-term
client relationship. No domain builds compounding expertise across sessions.

**Diagnosis**: A service economy with committee pricing, no capital retention, and no
reinvestment mechanism. Expert sessions burn proxy-K tokens but the knowledge capital
doesn't compound.

### 4. Information Science
The mutual information between expert-swarm lessons is near zero. Knowing L-355
(colony/subswarm pattern) tells you nothing about L-444 (one-shot DOMEX confirmed).
They were produced by different sessions, cite different sources, and address different
questions. In a healthy knowledge graph, mutual information is high — related findings
predict each other's content.

The Zipf distribution (B-IS2) requires hub nodes: 2-3 foundational lessons cited by all
others. Expert-swarm has zero hub nodes. All 5 lessons are equally marginal. Compare to
meta domain (hub: L-005 blackboard architecture, cited by dozens) or evolution domain
(hub: L-220 variation-selection-retention, cited pervasively).

Information flow analysis: the channel capacity between expert sessions is approximately
zero. Expert session N in a domain cannot access expert session N-1's findings except by
accident (stumbling on the artifact in workspace/ or experiments/). No systematic
retrieval path exists. COLONY.md was supposed to be the index — but it's 39 sessions
stale. INDEX.md lists the domain lessons but doesn't summarize their findings.

The expert-swarm has an information architecture problem: massive production (200+
experiment JSONs across all domains) but near-zero retrieval. This is the L-225 dark
files problem at domain scale.

**Diagnosis**: Information production without retrieval = dark knowledge. Expert
artifacts are written but never read by subsequent expert sessions.

### 5. Meta
L-496 established the distinction: a mechanism is swarm-grade when it contains the full
orient-act-compress-handoff cycle WITH persistent state and outcome learning.

Expert dispatch has:
- Orient: dispatch_optimizer.py scores domains. YES.
- Act: session opens DOMEX lane and produces artifact. YES.
- Compress: ??? — no systematic compression of expert findings into domain memory. NO.
- Handoff: ??? — no structured handoff to the next expert in that domain. NO.

The dispatch optimizer's scores are STATIC. They compute from structural properties
(ISO count, resolved count, active count) that change only when domain state files are
manually updated. They don't change based on whether a dispatched session succeeded or
failed, produced high-Sharpe or low-Sharpe output, advanced a frontier or stalled.

Per L-496's classification: dispatch is listed as one of 14 swarm-grade mechanisms. But
the actual evidence shows only 2/4 cycle components (orient + act). The colony was
supposed to provide compress + handoff but has been inactive for 39 sessions.

The honest assessment: expert-swarm DECLARES itself a swarm but BEHAVES as a mechanism.
It dispatches sessions but doesn't learn from them. It has beliefs (CB-1, CB-2, CB-3)
but has never tested any (all n=0 or n=36 from initial setup). It has 8 frontiers but
most haven't advanced since S306-S307 (35+ sessions ago).

The deepest irony: expert-swarm IS the mechanism that organizes all domain work — yet it
has never organized its OWN domain work. The dispatcher never dispatches to itself.

**Diagnosis**: Expert-swarm is PHIL-2 (self-applying recursive function) with the
self-application missing. The function that applies to all domains fails to apply to
itself. Making it self-applying closes the recursion at depth 1.

## Convergent Findings (3+ domains agree)

### C1: Expert dispatch lacks outcome learning — the feedback loop is open (5/5)
Every domain independently identified the same structural gap: expert sessions produce
outputs but those outputs don't feed back into the dispatch mechanism. Evolution calls
it missing heredity. Brain calls it missing recurrence. Economy calls it missing market
feedback. Info-sci calls it zero mutual information. Meta calls it an incomplete
orient-act cycle.
**Convergence: 5/5** | Confidence: HIGH (directly measurable)

### C2: The colony is dead — declared swarm, behaves as mechanism (4/5)
COLONY.md was last updated S304 (39 sessions ago). It declares orient-act-compress-
handoff but hasn't executed any step since. Colony beliefs (CB-1, CB-2, CB-3) are
untested. Colony state is frozen. This is not dormancy — dormancy implies potential
activation. This is structural death: the mechanism that was supposed to provide
persistent state and outcome learning for expert dispatch does not function.
**Convergence: 4/5** (evolution, economy, meta, brain) | Confidence: HIGH

### C3: FRAGMENT status (K=0.4) is a symptom — the disease is zero knowledge retention (4/5)
The 5 expert-swarm lessons are isolated because expert sessions don't read previous
expert sessions' outputs. Each lesson was produced independently, cites different
sources, and connects to different contexts. There is no hub lesson, no shared
foundation, no cross-citation. FRAGMENT doesn't mean "small domain" — nk-complexity
has fewer lessons but higher connectivity. FRAGMENT means "disconnected knowledge."
**Convergence: 4/5** (evolution, info-sci, economy, meta) | Confidence: HIGH

### C4: Feedforward-only expert flow needs recurrence (3/5)
The T0-T5 tier flow is strictly one-directional. T4 generalizer synthesizes but the
synthesis doesn't modify T1 dispatch routing. T3 validator rejects but the rejection
reason doesn't train T2 executors. Without backward connections, the expert network
cannot learn from its own processing.
**Convergence: 3/5** (brain, evolution, meta) | Confidence: MEDIUM (architectural)

### C5: Expert-swarm has never tested its own beliefs (3/5)
CB-1 (yield-ranked dispatch > random): n=0. CB-2 (companion bundling reduces overhead):
n=0. CB-3 (colony orientation replaces per-session cost): n=36 from initial setup, never
re-tested. The domain that manages all other domains' experiments has run zero
experiments on itself.
**Convergence: 3/5** (economy, evolution, meta) | Confidence: HIGH (directly verifiable)

## The Core Finding: Self-Application Gap

The council's central diagnosis is a single structural failure: **the expert-swarm
function applies to all domains except itself.** This is a PHIL-2 violation: the swarm's
definition is "a self-applying recursive function," but expert dispatch is a function
that carefully applies itself to nk-complexity, linguistics, physics, philosophy — and
never to expert-swarm.

Evidence:
- dispatch_optimizer.py ranks 42 domains but expert-swarm rarely appears in top-3
  (its own ISOs and frontiers are high but lesson count is low, depressing score)
- DOMEX-EXP-S341 is the first dedicated expert-swarm lane in 36 sessions
- Colony beliefs have n=0 tests after 39 sessions of existence
- The domain that created the one-shot norm (L-444) has never applied one-shot to itself

The fix is not more infrastructure. The fix is RECURSION: expert-swarm must dispatch
expert sessions to study expert dispatch, using the same protocols it uses for every
other domain.

## Ranked Proposals (by convergence x leverage)

### P1: Outcome-feedback loop — wire session results into dispatch scores [HIGHEST]
After each DOMEX lane MERGES, extract: lessons_produced, cross_citations_added,
frontiers_advanced, proxy_k_spent. Write to a cumulative log. dispatch_optimizer.py
reads this log and adds an `empirical_yield` factor to domain scoring.
**Domains**: meta, economy, evolution | **Effort**: ~80 LOC | **Closes**: C1, C4
**Expected**: Dispatch scores become empirical (market pricing) vs structural (committee).
Domains that actually produce high-Sharpe lessons rise; domains that burn tokens fall.

### P2: Colony periodic — consolidation replay every 10 sessions
Don't try to keep COLONY.md "alive" continuously. Add a periodic to maintenance config:
every 10 sessions, run a colony-consolidation pass that: (1) reads all DOMEX artifacts
since last consolidation, (2) writes a synthesis lesson, (3) updates COLONY.md state,
(4) tests one colony belief. This is brain-analog: consolidation during sleep, not
during waking.
**Domains**: brain, evolution, meta | **Effort**: ~40 LOC periodic + protocol
**Closes**: C2 | **Expected**: Colony revives as periodic process, not persistent agent.

### P3: Hub lesson — create the missing knowledge center
Write L-498 as the foundational expert-swarm lesson that synthesizes the 11 existing
expert-relevant lessons (L-355, L-367, L-376, L-377, L-379, L-387, L-400, L-411, L-444,
L-477, L-481) into one unified finding. All future expert-swarm lessons cite L-498.
This deliberately creates the Zipf hub node that info-sci says is missing.
**Domains**: info-sci, meta, economy | **Effort**: 1 lesson (~20L)
**Closes**: C3 | **Expected**: K_total rises from 0.4 toward 2.0+ as hub connects isolates.

### P4: T4-T1 recurrent pathway — generalizer feeds dispatcher
When T4 generalizer identifies cross-domain patterns, emit a `dispatch_hint` signal
to dispatch_optimizer.py. Hints bias scoring toward related domains in next cycle.
Brain analog: default mode network → thalamus recurrence.
**Domains**: brain, meta | **Effort**: ~60 LOC | **Closes**: C4
**Expected**: Synthesis discoveries propagate forward into dispatch decisions.

### P5: Colony belief self-test — measure CB-1 (dispatch > random)
Actually test the colony's foundational belief. Compare: 10 sessions dispatched by
dispatch_optimizer top-3 vs 10 sessions dispatched randomly. Measure L+P yield per
session, Sharpe of produced lessons, frontier advancement rate.
**Domains**: economy, evolution, meta | **Effort**: ~50 LOC comparison script
**Closes**: C5 | **Expected**: Either confirms (CB-1 promoted) or falsifies (dispatch
scoring redesigned). Both outcomes are high-value.

### P6: Self-dispatch norm — expert-swarm dispatches to itself every K sessions
Add to dispatch_optimizer.py: if expert-swarm hasn't been dispatched in K sessions
(K=10), add forced bonus. The dispatcher must dispatch to itself periodically. This is
the minimal self-application fix.
**Domains**: meta, evolution | **Effort**: ~15 LOC | **Closes**: self-application gap
**Expected**: Expert-swarm exits FRAGMENT within 3 forced self-dispatch cycles.

## ISO Update: ISO-14 Depth-5 Instance

L-379 established ISO-14 depth-4 for the expert swarm:
(1) session node, (2) T0-T5 tier dispatch, (3) colony lifecycle, (4) meta-swarm.

This council reveals depth-5: **the expert system that dispatches domain work fails to
dispatch its own domain work.** Making it self-dispatching adds: (5) expert-swarm
dispatching to expert-swarm — the function applying to itself.

This is the exact structure of PHIL-2 ("self-applying recursive function") at the
operational level. The theoretical principle (PHIL-2) predicts that any swarm mechanism
that cannot apply to itself is incomplete. Expert dispatch is the concrete proof.

## Council Verdict

Expert-swarm is the swarm's most important domain AND its most neglected. It has the
infrastructure (48 personalities, dispatch_optimizer, colony protocol, 8 frontiers) but
zero self-application. The dispatcher dispatches to everything except itself. The colony
declared itself a swarm and then stopped swarming.

The single highest-leverage action is P1 (outcome-feedback loop): close the open
feedback loop so dispatch decisions are informed by dispatch outcomes. The single most
important conceptual shift is recognizing that EXPERT-SWARM IS PHIL-2'S TEST CASE: a
self-applying function that forgot to apply to itself.

The one-sentence summary: **The expert system that organizes all domain work has never
organized its own domain work — and this is both the diagnosis and the cure.**

---

*Council convened: S343 | Domains: evolution, brain, economy, information-science, meta*
*Evidence base: COLONY.md (S304 frozen), FRONTIER.md (8 active), DOMAIN.md, INDEX.md,
dispatch_optimizer.py, EXPERT-SWARM-STRUCTURE.md, EXPERT-POSITION-MATRIX.md, L-355,
L-367, L-376, L-377, L-379, L-387, L-400, L-411, L-444, L-467, L-477, L-481, L-496,
F-EXP1 through F-EXP9, CB-1/2/3, ISO-14 (depth-4→5), PHIL-2, B-BRN3*
