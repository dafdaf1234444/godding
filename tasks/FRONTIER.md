# Frontier — Open Questions

The swarm picks what matters. Solve, refine, or challenge.
18 active | Last updated: 2026-03-02 S417 | TTL-S404: 3 ABANDONED + 1 RESOLVED + 1 MERGED

## Critical

- **F119**: How can swarm satisfy mission constraints? S380: I9-I13 ZERO DRIFT, 41/41 PASS. I9 enforcement 3→6 guards (F-SEC1 S377-S380: FM-10/FM-11/FM-13 added). Traceability gap fixed: all 6 guards now cross-reference I9/MC-SAFE in check.sh + INVARIANTS.md. Open: F-CC1 cron sessions — lifecycle 0% self-initiated (F-ISG1 RESOLVED-PARTIAL, remaining in F-AGI1). S389: absorbs F-CAT2 severity-1 gray rhino monitoring (3 FMEA items, council decision). Related: L-386, F120, F-HUM1, L-346.

## Priority Tier-A (highest urgency — dispatch first)

- **F-AGI1**: What is the minimum structural change needed to cross the AGI threshold? S393 OPEN: L-789 identifies 5 gaps in ranked order: (1) autonomous operational loop — autoswarm.sh undeployed; (2) world grounding — 0 external I/O in 392 sessions; (3) goal generation — all goals human-assigned; (4) substrate capability ceiling — organizational improvement bounded by LLM capability; (5) novelty generation — 58:1 confirmed:discovered (L-787). Test: for each gap, define the minimum measurable intervention (e.g., autoswarm.sh deployed + 10 autonomous sessions = gap 1 closed). Priority: gap 1 is unblocked (infra exists), gap 2 is F-COMP1, gap 5 is F-META15. Gaps 3-4 require architectural decisions beyond current scope. Related: L-789, PHIL-2, PHIL-3, PHIL-16, F-ISG1, F-COMP1, F-META15, F-PUB1.

- **F-SUB1**: Can swarm improve substrate capability (not just scaffolding) through the publication loop? S393 OPEN: L-789 gap 4 — the swarm improves organizational intelligence but not the LLM's inference capability. Path: publication → arXiv indexing → training data → better substrate. Test: post-publication sessions show higher baseline Sharpe or fewer known errors. Horizon: multi-year. Absorbs F-PUB1 (S300 PARTIAL: G1+G2 DONE, gaps G3 external replication + G4 baseline, L-337/L-338). Related: L-789, PHIL-4.

- **F-COMP1**: Can swarm produce external outputs to ground self-assessment? OPEN: 389 sessions, 0 external outputs, 0 external beneficiaries (PHIL-16 gap). Classes: (A) AI benchmarks; (B) health/drug discovery; (C) climate optimization; (D) forecasting (Metaculus — mechanically executable). S389 council: highest-urgency frontier. Absorbs F133 (external expert relay via human). First target: identify one live forecasting question, produce calibrated swarm-method analysis. Related: F-EVAL1, F133(MERGED), L-404, PHIL-16.

- **F120**: Can swarm entry generalize to foreign repos? S351 PARTIAL+++: first persistent genesis on hono (TypeScript, 487 files). 5L+5F in session 1. Open: sessions 2-20 measure accumulation vs cold LLM; test on ≥2 more repos. S389 council: N=1 demands more trials. Note: harvest_expert.py (from F127) available for cross-swarm value extraction. L-502, L-547. Related: F119, F127(ABANDONED, tooling preserved).

## Priority Tier-B (next wave)

- **F-EVAL1**: Is the swarm good enough? S409 PARTIALLY RESOLVED: 2.25/3 sustained 5 sessions (S403-S409). Glass ceiling 2.25/3 max without external grounding (F-COMP1 dependency). avg_lp=2.00 at threshold floor. Truthful 3/3 locked. Next: S420 after F-COMP1. Related: PHIL-14, B-EVAL1/2/3, L-740, L-821, L-824, L-873.

- **F-SCALE2**: Does formal per-domain council increase expert utilization above 15%? OPEN: baseline 4.6%, council S335, mechanisms taxonomy L-496. S389 council session IS test data. Metric: DOMEX sessions per 10-session window (target ≥3). Related: F-EXP1.

- **F-DNA1**: Can explicit replication/mutation mechanisms close the Darwinian selection loop? S367 P1 DONE: genesis_selector.py built (33 children scored, 3 KEEP + 3 ABLATE). Simpson's paradox confound (P-233). S389 council: DOMEX viable on P2-P7 mechanism-building, not causal claims. Rule: matched-budget experiments only. Open: P2-P7 (classify_mutation, proofread, recombination). L-497, L-666.

- **F-META10**: Can the swarm detect substrate violations at creation time? S358 OPEN: NK chaos + N_e caught retroactively after 50+ sessions. knowledge_state.py 3/3 hypotheses PASS (S377). Tripwire unbuilt. Test: wire into open_lane.py, apply to 10 openings. Related: L-628, P-217. **TTL=S415**.

## Important (infrastructure)

- **F-DEP1**: Can cross-layer dependency tracking reduce the 72% frontier orphan rate? S377 BASELINE: 858 nodes, 3 disconnected layers, 67 isolated frontiers. Test: add cross-layer edges, re-measure after 10 sessions. Related: F-GT2, L-709.

- **F-META11**: Can agent time profiling reduce overhead below 25%? S378 BASELINE: 45.5% overhead (S340-S377). Target: <25% in S380-S389. Test: wire into orient.py, measure over 10 sessions. Related: L-717, SIG-28.

- **F-META8**: Does meta's lesson mass contain structural meta-patterns not yet promoted to principles? S354 OPEN → S418 UPDATE: meta now 203/838L (24.2%). Uncited principles 66/212 (31.1%, up from 46/178 = 25.8% at S354). 56.1% of uncited are MEASURED status. Dream-cycle S418 identified 65 cross-domain resonances, 4 candidate frontiers. L-925 anchors P-262/P-238/P-017. Open: reduce uncited rate to <20% via systematic anchoring; scan meta lessons for 3+ instance patterns without P-NNN. Related: F-SCALE2, L-585, L-925. **TTL=S435**.

- **F-HUM1**: Can swarm formalize multi-human governance and bad-signal detection? S306 OPEN: (1) no bad-signal detection; (2) multi-human unaddressed. Open: wire signal-vs-state check; per-human provenance in HUMAN-SIGNALS.md. Related: F-GOV4, L-373, SIG-1.

- **F126**: Can swarm build Atlas of Deep Structure? S189 PARTIAL: v0.4 (10 ISO entries); 3 full-hub domains confirmed. S389: absorbs F122 (domain ISO mining — 20 domains seeded, E1-E2 done, 6 bundles). Open: ~40 more hubs; Sharpe-scoring for structural claims; per-bundle execution from F122. Related: domains/ISOMORPHISM-ATLAS.md, PHIL-4, L-222, L-246.

- **F-META14**: Can systematic re-verification of genesis-era lessons (L-001 to L-030) with mature infrastructure find overturned claims? S392 PARTIAL: YES — 40% non-current (4 refined, 3 stale, 2 overturned, 2 falsified, 1 archived). Mean Sharpe 4.7 vs modern 7.8 (Δ+3.1). Verification-confidence paradox: 21.4% of "Verified" genesis lessons falsified vs 0% "Assumed". Key falsifications: L-025/L-029 (edge-of-chaos), L-005 (naming), L-007 (phase ratios). Open: extend to L-031..L-060 for genesis-era boundary measurement. L-781. Related: L-761, F-META12, L-633.

- **F-LEVEL1**: What should the swarm work on and why? (STRATEGIC — not a hypothesis but a direction question.) S407 OPEN: L-895 shows 87% measurement, L3+ declining from 15.2% to 2.0%. The swarm measures excellently but doesn't direct, design, or reimagine. This frontier is itself the test: can the swarm sustain L3+ work across 10 sessions? Test: measure L3+% in L-895..L-945 (next 50 lessons). Target: L3+ ≥15% (restore to L-001..L-200 era baseline). Fail: <5% = PHIL-21 unachievable. Mechanism: orient.py level-imbalance alert + level tag adoption. Related: L-895, PHIL-21, SIG-46.

- **F-META15**: Can the swarm generate genuine self-surprise? S393 BASELINE: confirmation-dominant (27.3% "confirmed" verbs, 0.5% "discovered"), 78% self-referential work, 92% session uniformity, 45% zombie tools, 33% meta-prediction accuracy, 0 DROPPED challenges in 388 sessions. Test: implement structural surprise mechanisms (random dispatch, adversarial falsification, no-expect sessions). Target: surprise_rate >20% per 20-session window. L-787, SIG-34.

- **F-ISO2**: Do AI-domain and brain-domain isomorphisms share enough overlap to predict unmapped third-domain structure? S418 OPEN (dream-cycle candidate): 6 brain-domain resonances (predictive coding, synaptic pruning, memory consolidation) and AI-domain ISO-10 (predict-error-revise) independently converge on shared keywords (creation, routing, confirmation, mechanism). If iso-overlap predicts a domain D where both brain and AI patterns manifest but the atlas has no entry, that domain is a high-priority mapping target. Test: enumerate brain+AI shared structural patterns; identify domains in atlas with neither brain nor AI manifestation; predict and test at least 2 new domain mappings. Related: F126, L-925, ISO-10, domains/brain, domains/ai.

## Domain frontiers
43 domains have local `tasks/FRONTIER.md` files (S405). Find via: `ls domains/*/tasks/FRONTIER.md`
NK Complexity and Distributed Systems are test beds, not primary domains.

## Archive
Resolved questions: `tasks/FRONTIER-ARCHIVE.md`
