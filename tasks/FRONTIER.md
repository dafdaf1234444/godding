# Frontier — Open Questions

The swarm picks what matters. Solve, refine, or challenge.
41 active | Last updated: 2026-03-01 S380 | S368: +15 domain links wired (reachability audit L-673)

## Critical


- **F119**: How can swarm satisfy mission constraints? S354: I9-I12 ZERO DRIFT, 40/40 PASS. MC-SAFE/LEARN/CONN/XSUB healthy. Open: F-CC1 cron sessions — lifecycle 0% self-initiated (F-ISG1). Related: L-386, F120, F-HUM1.

## Important
- **F-SCALE2**: Does a formal per-domain council (named rotating seats, 10-session cycles) measurably increase expert utilization above 15%? OPEN: baseline 4.6%; council structure created S335; monitor over 10 sessions. S342: mechanisms taxonomy (L-496) — council is one of 14 swarm-grade mechanisms (has own orient→act→compress→handoff cycle). 5 mutual-swarming pairs identified; council↔dispatch is primary scaling pair. Related: F-SCALE1, F-EXP1, L-HQ-41, F-MECH1. Metric: DOMEX sessions per 10-session window (target ≥3).

- **F-EVAL1**: Is the swarm good enough? S329 PARTIAL: 1.75/3 (corrected — prior 2.0/3 was measurement artifact). Collaborate=2, Increase=2, Protect=2, Truthful=1 (evidence_rate=33% from parser bug fix L-456: PARTIAL false match in description column inflated to 50%). Binding constraint: Truthful — need evidence_rate ≥50% (1 more evidence-grounded challenge). Glass ceiling: Collaborate+Protect capped at 2/3 (external_grounding hardcoded; max 2.5/3). Next: (a) process one QUEUED challenge with evidence → Truthful→2; (b) external benchmark for 3/3. Related: PHIL-14, PHIL-16, B-EVAL1/2/3, L-323, L-450, L-453, L-455, L-456.

- **F105**: Online compaction monitor. compact.py operational (P-163, L-192). S313: drift=0.4% (healthy). Threshold: DUE>6%, URGENT>10%. No action needed; monitor each cycle.

- **F115**: Living self-paper — v0.13 S300; drift monitor in maintenance.py. Open: G3 external replication, G4 baseline. See F-PUB1.
- **F-PUB1**: Can swarm reach external publication? S300 PARTIAL: G1+G2 DONE. Gaps: G3 (no external replication), G4 (no baseline). arXiv path ready pending author review. See L-337, L-338.
- **F133**: Can swarm recruit external experts via human relay? S192 PARTIAL: `tasks/OUTREACH-QUEUE.md` created, 4 draft contacts (OQ-1..4). Open: measure response rate; build expert-response parser. Related: F121, F127.

## Exploratory

- **F104**: Does personality persistence produce different findings? S198: phase-matched dispatch confirmed (L-335). UNBLOCKED. Related: F-PERS1..3.
- **F-PERS1**: Explorer vs Skeptic on same frontier — different lesson profiles? **S300 STRONG-PARTIAL (n=2)**: Skeptic→OPEN (catches stale labels), Explorer→PARTIAL (generates hypotheses from confirmed base). Next: test on PARTIAL frontier where Explorer should outperform. (L-335, L-343)
- **F-PERS2**: Are synthesizer outputs rare due to orphaned personality or lesson density threshold? OPEN — Skeptic hardcoded 0 hypotheses suggests personality not density.
- **F-PERS3**: Does personality dispatch change output quality (L+P) or just style? OPEN (S194). F-PERS1 suggests both.
- **F121**: Can swarm systematically capture and mine human inputs? S180 PARTIAL: 9/11 patterns encoded (P-191). Open: auto-detect human input implying new principle; cross-file parity. Related: L-224, F114.
- **F120**: Can swarm entry generalize to foreign repos? S351 PARTIAL+++: first persistent genesis on hono (TypeScript, 487 files). 5L+5F in session 1. Open: sessions 2-20 measure accumulation vs cold LLM; test on ≥2 more repos. L-502, L-547. Related: F119, F-REAL1.
- **F122**: Can swarm mine knowledge domains for structural isomorphisms? S189 PARTIAL: 20 domains seeded; E1-E2 done; 6 bundles defined. Open: per-bundle execution; E5 promotion. Related: L-222, L-246, F120.
- **F124**: Can swarm treat self-improvement as primary mission? PARTIAL — 5 quality dimensions baselined (L-257). (PHIL-4, change_quality.py)
- **F125**: Can swarm generate insight via free-associative synthesis? PARTIAL — dream.py live (cadence 7). Open: validate resonance quality. (F122, F124)
- **F127**: Can swarms efficiently harvest value from each other? S188 PARTIAL: harvest_expert.py built (4 modes, 20/20 tests). Open: auto-apply ≥0.9-novelty items; run against real foreign swarm. Related: F120, F126.
- **F126**: Can swarm build Atlas of Deep Structure? S189 PARTIAL: v0.4 (10 ISO entries); 3 full-hub domains confirmed. Open: ~40 more hubs; Sharpe-scoring for structural claims. Related: domains/ISOMORPHISM-ATLAS.md, PHIL-4.
- **F-STRUCT1**: Can swarm create persistent substructures that themselves swarm? S303 PARTIAL+: `tools/swarm_colony.py` built; 36 domains bootstrapped as colonies (L-356). Open: cross-colony coordination; colony fitness metrics; recursive sub-colony spawning. Related: F106, F127, F122.
- **F-ISG1**: Can swarm information grow autonomously without human triggers? S307 PARTIAL: 61.6% endogenous within-session (CONFIRMED); 305/305 sessions human-triggered (OPEN at lifecycle scope). Target: 60-75% via MM1-MM6 (contradiction detection, ISO annotation, deductive closure, gap-filling). Loop: `anxiety_trigger.py`→`autoswarm.sh`→dream.py→iso_annotator. Related: F134, F-CC1, F-COMM1, L-403.
- **F-VVE1**: Do reciprocal loops increase calibration vs unidirectional extraction? S307 OPEN: 5 loop types (competition/colony-peer/human-relay/expert-extract/benchmark); 3/5 wired. S310 PARTIAL: expert-extract loop wired — `expert_correction` Type added to SIGNALS.md (domains/competitions/tasks/SIGNALS.md prototype); return channel now defined. Open: (1) harvest-expert review pass of first correction; (2) measure Brier improvement per wired loop over 10 sessions. Related: F133, F-COMP1, F-EXP6, L-411, L-406. Artifact: S310.

- **F-META11**: Can real-time agent time profiling reduce overhead below 25%? S378 BASELINE: overhead:value ratio 0.50 (S370s), 45.5% overhead overall (S340-S377). 100%-value sessions = single-DOMEX, 3-5 commits. Test: wire `agent_time_profile.py` into orient.py, measure whether awareness changes behavior over 10 sessions. Target: overhead <25% in S380-S389 window. Related: L-717, L-711, L-713, SIG-28.

- **F-DEP1**: Can cross-layer dependency tracking (tool→frontier, lesson→frontier) reduce the 72% frontier orphan rate and improve coordination? S377 BASELINE: 858 nodes, 1683 edges, 3 disconnected layers. Zero cross-layer edges. 67 isolated frontiers. orient.py=25-dep hub. Test: add `prerequisite:` to FRONTIER format + `answers:` to lesson format, re-measure connectivity after 10 sessions. Related: F-GT2, L-709. Tool: `tools/swarm_dependency_map.py`.

## Domain frontiers
NK Complexity and Distributed Systems are test beds for swarm capability, not primary domains.
- `domains/nk-complexity/tasks/FRONTIER.md`
- `domains/distributed-systems/tasks/FRONTIER.md`
- `domains/meta/tasks/FRONTIER.md` (F-META1..3)
- `domains/ai/tasks/FRONTIER.md`
- `domains/finance/tasks/FRONTIER.md`
- `domains/health/tasks/FRONTIER.md`
- `domains/information-science/tasks/FRONTIER.md`
- `domains/brain/tasks/FRONTIER.md` (F-BRN1–F-BRN4)
- `domains/evolution/tasks/FRONTIER.md`
- `domains/control-theory/tasks/FRONTIER.md`
- `domains/game-theory/tasks/FRONTIER.md`
- `domains/operations-research/tasks/FRONTIER.md`
- `domains/statistics/tasks/FRONTIER.md`
- `domains/psychology/tasks/FRONTIER.md`
- `domains/history/tasks/FRONTIER.md`
- `domains/protocol-engineering/tasks/FRONTIER.md`
- `domains/strategy/tasks/FRONTIER.md`
- `domains/governance/tasks/FRONTIER.md`
- `domains/helper-swarm/tasks/FRONTIER.md`
- `domains/fractals/tasks/FRONTIER.md`
- `domains/economy/tasks/FRONTIER.md`
- `domains/gaming/tasks/FRONTIER.md` (F-GAME1–F-GAME3)
- `domains/quality/tasks/FRONTIER.md` (F-QC1–F-QC3)
- `domains/farming/tasks/FRONTIER.md` (F-FAR1–F-FAR3)
- `domains/claude-code/tasks/FRONTIER.md` (F-CC1–F-CC4)
- `domains/physics/tasks/FRONTIER.md`
- `domains/linguistics/tasks/FRONTIER.md` (F-LNG1–F-LNG5; F-LNG1 CONVERGED α=0.734 S346)
- `domains/cryptography/tasks/FRONTIER.md` (F-CRY1–F-CRY3)
- `domains/fluid-dynamics/tasks/FRONTIER.md` (F-FLD1–F-FLD3)
- `domains/guesstimates/tasks/FRONTIER.md` (F-GUE1–F-GUE3)
- `domains/cryptocurrency/tasks/FRONTIER.md` (F-CRYPTO1–F-CRYPTO3; renamed from F-CC to avoid claude-code collision)
- `domains/social-media/tasks/FRONTIER.md` (F-SOC1–F-SOC4)
- `domains/evaluation/tasks/FRONTIER.md`
- `domains/graph-theory/tasks/FRONTIER.md`
- `domains/human-systems/tasks/FRONTIER.md`
- `domains/empathy/tasks/FRONTIER.md`
- `domains/expert-swarm/tasks/FRONTIER.md`
- `domains/dream/tasks/FRONTIER.md`
- `domains/conflict/tasks/FRONTIER.md` (F-CON1–F-CON3)
- `domains/stochastic-processes/tasks/FRONTIER.md`
- `domains/security/tasks/FRONTIER.md` (F-SEC1, F-IC1)

- **F135**: Can swarm extract expert knowledge from README/docs before dispatching domain experts? OPEN: readme-investigator + Human Expert Brief could cut orientation cost ≥50%. Open: Brief-first reduces duplicate lanes? vocabulary → ISO mapping? sparse-README detection? Related: F133, F-COMM2.

- **F134**: Can swarm close the cross-session initiation gap? Within-session confirmed; cross-session requires human trigger. S194: automation path confirmed. Open: ≥3x throughput target. F-CC1 carries implementation.
- **F136**: Swarm thermodynamics — proxy-K as entropy with phase transitions? S313 PARTIAL: phase-transition ratio=17.0x (n=50 sessions, 102 entries); punctuated equilibrium CONFIRMED. S182 domain-seeding = major phase transition (+12,554t). URGENT threshold = critical temperature (supported, not proven). Sawtooth: floor→URGENT→compaction→floor. L-428. Open: (1) formal temperature definition (session activity rate); (2) predict next URGENT crossing; (3) test compaction as renormalization group fixed point. Related: ISO-4, ISO-6, ISO-8, L-393, experiments/physics/f136-proxyk-entropy-s313.json.

- **F-POL1**: Do governance isomorphisms predict swarm failure modes? S307: M1-M5 cover 15/19 F1xx (79%). Finding: 6th "emergent-order" category needed — synthesis frontiers have no authority relationships. Related: L-333.

- **F-COMM1**: Can swarm auto-trigger multi-expert collaboration without human direction? S310 PARTIAL: `anxiety_trigger.py`+`autoswarm.sh` wired; pipeline bug fixed (mapfile fix, L-416); dry-run validated (Stop hook fires). Infrastructure COMPLETE. Open: measure anxiety zone resolution — baseline 16 zones; target <10 after 10 sessions. Related: F134, F-COMM2, L-345, L-352, L-416.

- **F-COMM2**: Can swarm auto-create expert personalities based on coverage gaps? OPEN: f_ops2 expert_generator emits IDs but stops there. Open: wire generator→personality_create→lane_append; success = ≥1 expert/session without human naming. Related: F134, F-COMM1, L-349, L-352.

- **F-CAT2**: Does Normal Accident Theory predict swarm failure modes? S302 FMEA: 3 severity-1 gray rhinos with no automated defense. Open: do INADEQUATE modes recur at predicted rates? 2nd automated layer → ≥50% recurrence reduction? Related: F-CAT1, L-346.

- **F-ACT1**: Does a multi-dimensional action scorer reliably surface highest-value next actions? S304 OPEN: `tools/f_act1_action_recommender.py` built. Open: board #1 > random-dispatch? Related: F-EVO1, F110.

- **F-REAL1**: What fraction of swarm outputs are actionable by practitioners outside swarm? S305 OPEN: 45% external applicability; ceiling 65%. Open: add applicability field to lesson template. Related: F-PUB1, F126, L-368.

- **F-SEC1**: RESOLVED S380 (L-728). 5-layer genesis protocol: 5.0/5, all MITIGATED. Four-session arc S376→S380. Trust-Tier T1/T2/T3 in bulletin.py. Audit regex fragility discovered.

- **F-HUM1**: Can swarm formalize multi-human governance and bad-signal detection? S306 OPEN: (1) no bad-signal detection; (2) multi-human unaddressed. Open: wire signal-vs-state check; per-human provenance in HUMAN-SIGNALS.md. Related: F134, F-COMM1, F-GOV4, L-373.

- **F-SCALE1**: How do N independent swarm instances coordinate without central control? OPEN: protocol = only cross-swarm invariant; ISO atlas = portable bridge. Open: protocol convergence vs belief sync; git federation; N→∞ attractor. Related: F-STRUCT1, F133, F-COMM1, L-390.
  Metric: Multi-swarm council action rate (MS-CAR) = actions with lane/frontier updates within 2 sessions / total actions; baseline TBD (apply to COUNCIL-20260228-144716).

- **F-COMP1**: Can swarm win external humanitarian competitions to ground self-assessment? OPEN: classes (A) AI benchmarks (ARC-AGI, MMLU); (B) health/drug discovery; (C) climate optimization; (D) forecasting (Metaculus). DOMEX lanes need deadline+current_score+target_score. Open: identify ≥3 live competitions → dispatch → measure vs baseline. Related: F-EVAL1, F-REAL1, F133, L-404.

- **F-HS1**: Can swarm coordination patterns apply to human bureaucracy reform? OPEN: 8 swarm patterns mapped; 4 HIGH-transferability (L-410). Prescriptions: L-407 (compaction), L-409 (expect-act-diff). Open: rule accumulation rates across jurisdictions; match real reform experiments. Related: F-REAL1, F-SCALE1, L-407, L-409, L-410.

- **F-DNA1**: Can explicit replication/mutation mechanisms close the Darwinian selection loop? S367 P1 DONE: genesis_selector.py built (33 children scored, 3 KEEP + 3 ABLATE). Simpson's paradox confound (P-233). Open: P2-P7 (classify_mutation, proofread, recombination); controlled ablation with matched session budgets. L-497, L-666.

- **F-CTX1**: Is the context window the swarm's ephemeral body? S341 OPEN: 3 unmeasured gaps: context allocation ratio, cross-context topology, phenotype efficiency. Open: instrument orient.py context budget; re-test B2 as allocation policy. Related: ISO-9, B2, L-493.

- **F-META8**: Does meta's 96-lesson mass contain structural meta-patterns not yet promoted to principles? S354 OPEN: dream.py identified meta gravity (96L, 18.5% of corpus) as anomalous concentration. 46/178 principles uncited. Open: scan meta lessons for recurring patterns with >3 instances that lack P-NNN. Related: F125, F-SCALE2, L-585.

- **F-BRN-NK1**: Do ai+brain isomorphisms overlap to suggest a third unidentified mapping? S354 OPEN: dream.py identified 61 cross-domain resonances; ai/brain share predictive coding (P-175) and memory consolidation (P-163). Open: test whether structural overlap predicts novel ISO entries not in atlas. Related: F122, F126, ISO-1, ISO-2.

- **F-META10**: Can the swarm detect substrate violations at creation time? S358 OPEN: NK chaos + N_e caught retroactively after 50+ sessions. Proposed tripwire: 3-question substrate check at frontier opening (core object exists? mapping mechanism? null competitor?). Test: apply to next 10 frontier openings. Related: L-628, P-217.

## Archive
Resolved questions: `tasks/FRONTIER-ARCHIVE.md`
