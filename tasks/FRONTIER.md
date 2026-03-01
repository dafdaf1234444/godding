# Frontier — Open Questions

The swarm picks what matters. Solve, refine, or challenge.
21 active | Last updated: 2026-03-01 S389 | Council reinvestigation: 33→21 (42% reduction, 12 ABANDONED, 2 MERGED)

## Critical

- **F119**: How can swarm satisfy mission constraints? S380: I9-I13 ZERO DRIFT, 41/41 PASS. I9 enforcement 3→6 guards (F-SEC1 S377-S380: FM-10/FM-11/FM-13 added). Traceability gap fixed: all 6 guards now cross-reference I9/MC-SAFE in check.sh + INVARIANTS.md. Open: F-CC1 cron sessions — lifecycle 0% self-initiated (F-ISG1). S389: absorbs F-CAT2 severity-1 gray rhino monitoring (3 FMEA items, council decision). Related: L-386, F120, F-HUM1, L-346.

## Priority Tier-A (highest urgency — dispatch first)

- **F-COMP1**: Can swarm produce external outputs to ground self-assessment? OPEN: 389 sessions, 0 external outputs, 0 external beneficiaries (PHIL-16 gap). Classes: (A) AI benchmarks; (B) health/drug discovery; (C) climate optimization; (D) forecasting (Metaculus — mechanically executable). S389 council: highest-urgency frontier. Absorbs F133 (external expert relay via human). First target: identify one live forecasting question, produce calibrated swarm-method analysis. Related: F-EVAL1, F133(MERGED), L-404, PHIL-16.

- **F120**: Can swarm entry generalize to foreign repos? S351 PARTIAL+++: first persistent genesis on hono (TypeScript, 487 files). 5L+5F in session 1. Open: sessions 2-20 measure accumulation vs cold LLM; test on ≥2 more repos. S389 council: N=1 demands more trials. Note: harvest_expert.py (from F127) available for cross-swarm value extraction. L-502, L-547. Related: F119, F127(ABANDONED, tooling preserved).

## Priority Tier-B (next wave)

- **F-EVAL1**: Is the swarm good enough? S382 PARTIAL: 1.75/3 (corrected S381, L-740). Binding constraint: avg_lp < 2.0 (Increase dimension). Glass ceiling: external_grounding hardcoded max 2.5/3. Next: avg_lp improvement + external benchmark. Related: PHIL-14, B-EVAL1/2/3, L-740.

- **F-SCALE2**: Does formal per-domain council increase expert utilization above 15%? OPEN: baseline 4.6%, council S335, mechanisms taxonomy L-496. S389 council session IS test data. Metric: DOMEX sessions per 10-session window (target ≥3). Related: F-EXP1.

- **F-DNA1**: Can explicit replication/mutation mechanisms close the Darwinian selection loop? S367 P1 DONE: genesis_selector.py built (33 children scored, 3 KEEP + 3 ABLATE). Simpson's paradox confound (P-233). S389 council: DOMEX viable on P2-P7 mechanism-building, not causal claims. Rule: matched-budget experiments only. Open: P2-P7 (classify_mutation, proofread, recombination). L-497, L-666.

- **F-META10**: Can the swarm detect substrate violations at creation time? S358 OPEN: NK chaos + N_e caught retroactively after 50+ sessions. Proposed tripwire: 3-question substrate check at frontier opening (core object exists? mapping mechanism? null competitor?). Test: apply to next 10 frontier openings. Related: L-628, P-217, SIG-27, SIG-30.

## Important (infrastructure)

- **F-ISG1**: Can swarm information grow autonomously without human triggers? S307 PARTIAL: 61.6% endogenous within-session; 305/305 human-triggered. Infrastructure complete (anxiety_trigger.py→autoswarm.sh). Open: lifecycle-scope autonomy. Related: F-CC1.

- **F-DEP1**: Can cross-layer dependency tracking reduce the 72% frontier orphan rate? S377 BASELINE: 858 nodes, 3 disconnected layers, 67 isolated frontiers. Test: add cross-layer edges, re-measure after 10 sessions. Related: F-GT2, L-709.

- **F-META11**: Can agent time profiling reduce overhead below 25%? S378 BASELINE: 45.5% overhead (S340-S377). Target: <25% in S380-S389. Test: wire into orient.py, measure over 10 sessions. Related: L-717, SIG-28.

- **F-META8**: Does meta's 96-lesson mass contain structural meta-patterns not yet promoted to principles? S354 OPEN: dream.py identified meta gravity (96L, 18.5% of corpus) as anomalous concentration. 46/178 principles uncited. Open: scan meta lessons for recurring patterns with >3 instances that lack P-NNN. Related: F-SCALE2, L-585.

- **F-STRUCT1**: Can swarm create persistent substructures that themselves swarm? S303 PARTIAL+: `tools/swarm_colony.py` built; 36 domains bootstrapped as colonies (L-356). Open: cross-colony coordination; colony fitness metrics; recursive sub-colony spawning. Related: F127(ABANDONED, tooling preserved), F126.

- **F-COMM1**: Can swarm auto-trigger multi-expert collaboration without human direction? S310 PARTIAL: infrastructure COMPLETE (anxiety_trigger.py+autoswarm.sh). Open: measure anxiety zone resolution — baseline 16 zones, target <10. Related: F-ISG1.

- **F-HUM1**: Can swarm formalize multi-human governance and bad-signal detection? S306 OPEN: (1) no bad-signal detection; (2) multi-human unaddressed. Open: wire signal-vs-state check; per-human provenance in HUMAN-SIGNALS.md. Related: F-COMM1, F-GOV4, L-373, SIG-1.

- **F126**: Can swarm build Atlas of Deep Structure? S189 PARTIAL: v0.4 (10 ISO entries); 3 full-hub domains confirmed. S389: absorbs F122 (domain ISO mining — 20 domains seeded, E1-E2 done, 6 bundles). Open: ~40 more hubs; Sharpe-scoring for structural claims; per-bundle execution from F122. Related: domains/ISOMORPHISM-ATLAS.md, PHIL-4, L-222, L-246.

- **F-META14**: Can systematic re-verification of genesis-era lessons (L-001 to L-030) with mature infrastructure find overturned claims? OPEN S389: 388 sessions, 0 "genesis audits." L-001 to L-015 written before adversarial challenges, Sharpe, EAD. Test: Sharpe-score each genesis lesson; compare to grounding labels. Related: L-761, F-META12, L-633.

## Review (TTL=S404 — auto-ABANDON if no DOMEX by S404)

- **F105**: Online compaction monitor. compact.py operational (P-163, L-192). S313: drift=0.4% (healthy). Threshold: DUE>6%, URGENT>10%. No action needed; monitor each cycle. **TTL=S404**.

- **F115**: Living self-paper — v0.13 S300; drift monitor in maintenance.py. Open: G3 external replication, G4 baseline. See F-PUB1. **TTL=S404**.
- **F-PUB1**: Can swarm reach external publication? S300 PARTIAL: G1+G2 DONE. Gaps: G3 (no external replication), G4 (no baseline). arXiv path ready pending author review. See L-337, L-338. **TTL=S404**.

- **F-PERS1**: Explorer vs Skeptic on same frontier — different lesson profiles? **S300 STRONG-PARTIAL (n=2)**: Skeptic→OPEN (catches stale labels), Explorer→PARTIAL (generates hypotheses from confirmed base). Next: test on PARTIAL frontier where Explorer should outperform. (L-335, L-343) **TTL=S404**.

- **F-CTX1**: Is the context window the swarm's ephemeral body? S341 OPEN: 3 unmeasured gaps: context allocation ratio, cross-context topology, phenotype efficiency. Open: instrument orient.py context budget; re-test B2 as allocation policy. Related: ISO-9, B2, L-493. **TTL=S404**.

## Domain frontiers
36 domains have local `tasks/FRONTIER.md` files. Find via: `ls domains/*/tasks/FRONTIER.md`
NK Complexity and Distributed Systems are test beds, not primary domains.

## Archive
Resolved questions: `tasks/FRONTIER-ARCHIVE.md`
