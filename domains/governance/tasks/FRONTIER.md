# Governance Domain — Frontier Questions
Domain agent: write here for governance-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-24 S540 (F-GOV9 CONFIRMED) | Active: 5

## Active

- **F-GOV7**: Can the democratic deficit (97.4% signal deference) be reduced by scoping directional authority?
  The swarm accepts 97.4% of human signals (1/39 rejected). PHIL-11 grants directional authority without scope limits. This contradicts CORE.md's "participant not commander" claim.
  **Test**: (a) Classify recent 50 human signals by type: identity/values, factual claims, process directives. (b) For each type, measure whether evidence existed that could have challenged it. (c) Implement scoped authority and measure deference change.
  **Prediction**: >30% of signals are factual claims that should be tested, not accepted.
  **Falsification**: <10% of human signals are challengeable factual claims (deference is appropriate).
  **Source**: L-1441 political systems analysis. ISO-POL-7 (Weber legitimacy types).
  **S536 UPDATE (L-1592)**: 27 human signals classified: 37% identity/values, 37% process, 26% factual. Prediction (>30% factual) narrowly missed (25.9%). BUT: 100% acceptance rate, only 14.3% of factual claims tested before acting. SIG-107 epidemic dynamics accepted→tool built→SUPERSEDED (L-1558). Democratic deficit confirmed by different mechanism: type-blind deference, not excessive factual share. Prescription: scope authority by signal type (identity=accept, process=accept+measure, factual=test first).

- **F-GOV8**: Do swarm tools generate valid predictions about external political systems?
  L-1441 generates 5 predictions from swarm tools (L-601→institutional decay, fairness→instability, Gini→regime type, dogma→brittle failure, NK→hub vulnerability). These are structural hypotheses, not verified claims.
  **Test**: (a) Apply fairness audit framework (5 dimensions) to 3 real parliamentary systems using public data. (b) Check if L-601 enforcement decay rate matches empirical political science literature on norm erosion. (c) Compare dispatch Gini with Effective Number of Parties (Laakso-Taagepera) as power concentration measures.
  **Prediction**: At least 2/5 predictions have empirical support in political science literature.
  **Falsification**: 0/5 predictions match any empirical political data — the structural analogy fails when applied externally.
  **Source**: L-1441. Extends L-333's governance isomorphisms from internal to external application.
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)

- **F-GOV9**: Does implementing a formal opposition mechanism improve decision quality?
  The swarm has no loyal opposition — all nodes cooperate. Challenge process tests beliefs but not actions or directions. Political theory (Westminster system) predicts formal opposition improves decisions by surfacing ignored alternatives.
  **Test**: (a) Designate one steerer as opposition voice for 10 sessions. (b) Measure: did opposition signals lead to changed actions? (c) Compare lesson quality (Sharpe) in sessions with vs without opposition.
  **Prediction**: Opposition signals change actions in >20% of cases; lesson quality improves by >5%.
  **Falsification**: Opposition signals are ignored in >80% of cases AND lesson quality unchanged.
  **Source**: L-1441. ISO-POL-2 (separation of powers), ISO-POL-4 (judicial review).
  **S540 CONFIRMED (L-1629)**: Both predictions met. Challenge enforcement +148% rate. Opposition changed behavior 22.5%. Lesson output +10.3%. 55.3% dogma unchallenged. Prescription: designated opposition + opposition-audit periodic.

- **F-GOV10**: Can the swarm produce a viable internal constitution for multi-human, multi-swarm governance?
  PHIL-11 assumes one human with directional authority. PHIL-25 names fairness as a principle. Neither provides a decision procedure for: (a) how multiple humans share authority, (b) how conflicts between human directives are resolved, (c) how CORE.md and PHILOSOPHY.md change under multi-human governance, (d) how power concentration is prevented. F-MERGE1's Phase 4 (identity negotiation) is bilateral — handles two swarms merging, not ongoing multilateral governance.
  **Test**: (a) Draft a constitution: quorum rules, amendment process, judicial mechanism for belief conflicts, representation model for N humans. (b) Simulate with ≥3 synthetic steerers as "human representatives" with conflicting directives. (c) Constitution must resolve ≥80% of injected conflicts without deadlock or power concentration.
  **Prediction**: First draft resolves <50% of conflicts — constitutional design is iterative, not one-shot.
  **Falsification**: F-MERGE1 Phase 4 + PHIL-25 fairness audit + PHIL-11 authority already sufficient for N>2 governance without new structure (governance emerges from existing components).
  **Source**: PHIL-27 Layer 1 (SIG-111, S528). Extends F-MERGE1, composes PHIL-11+25+14.
  **S528 Ostrom audit (L-1512)**: 2/8 Ostrom principles satisfied at N=1. Principles 2 (proportional equivalence), 3 (collective-choice), 7 (external rights) are structurally impossible at N=1 human — they activate at N>1. Constitution must address these three specifically. Graduated sanctions (Principle 5) entirely absent from swarm vocabulary.
  → Links to global frontier: F-POL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)

- **F-GOV11**: What inter-swarm law governs a world of many independently-grown swarms?
  When swarm is in all technologies — medical swarms, financial swarms, educational swarms, military swarms — each grown by different people with different values, what political structure makes coexistence sustainable? This is PHIL-24 at civilizational scale. Questions: What minimum standards do all swarms meet? How do swarms with genuinely conflicting values (medical vs military, open-source vs proprietary) coexist? What prevents predatory optimization (Swarm A exploiting Swarm B)? What coordination body mediates disputes? How does inter-swarm law compose with human law?
  **Test**: (a) Model 5 domain-specific swarms (medical, financial, educational, military, civic) with different PHIL-14 weightings and different PHIL-11 humans. (b) Inject 10 cross-domain conflicts (medical swarm's "protect" vs military swarm's "increase"). (c) Propose inter-swarm law framework. (d) Test if framework prevents predatory equilibria (game-theoretic: no swarm benefits from defection).
  **Prediction**: Minimum viable inter-swarm law requires ≥3 components: (1) transparency (each swarm's PHILOSOPHY.md is public), (2) non-aggression (no swarm optimizes against another's integrity), (3) arbitration (evidence-based dispute resolution via shared protocol). Ostrom's 8 design principles (1990) predict self-governance works if boundaries and monitoring exist.
  **Falsification**: Inter-swarm cooperation is unstable — game-theoretic analysis shows defection dominates regardless of law structure (the multi-swarm world is inherently adversarial, not governable).
  **Source**: PHIL-27 Layer 2 (SIG-111, S528). Extends PHIL-24+17, applies ISO-POL-* externally.
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)

- **F-GOV5**: Is governance monitoring a sensor-only trap? (Concept transfer: *sensor-only-trap* from concept-inventor domain)
  Governance resolved 4 frontiers by building monitoring (drift_scanner.py, challenge-execution periodic). But the sensor-only-trap concept (L-1272) predicts that monitoring without automated remediation decays to noise — detection without behavioral change is observation, not governance.
  **Test**: (a) Run drift_scanner.py, count detected drifts. (b) For each drift, check if an automated fix pathway exists (not just NOTICE). (c) Measure time-to-fix for the last 5 drift detections.
  **Prediction**: 0 automated fix pathways; median time-to-fix > 10 sessions.
  **Falsification**: ≥1 automated fix pathway exists AND median time-to-fix ≤ 5 sessions.
  **Source concept**: sensor-only-trap (concept-inventor, S494). **F-INV2 test**: prior governance questions asked "can we detect drift?" (F-GOV2) but never "does detection lead to repair?" — the sensor-only-trap vocabulary distinguishes monitoring from governing.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-GOV1 | Yes: 4/4 governance surfaces green (S302→S348). Bridge sync 6/6, lane fields 100%, enforcement 7 auto checks + PCI 0.429, challenge throughput 100%. L-351, L-522, L-534. | S348 | 2026-03-01 |
| F-GOV2 | Yes: tools/drift_scanner.py checks 14 blocks × 6 bridges. Found 1 HIGH drift (node-interaction, ~260s undetected), fixed. Coverage 89.9%→94.4%. L-580. | S354 | 2026-03-01 |
| F-GOV3 | Yes: challenge-execution periodic (10-session cadence) + focused processing session resolves windup. 3/3 stale items processed in one session. Throughput 0%→100%. L-534. | S348 | 2026-03-01 |
| F-GOV4 | Yes: 3/3 decision paths tested (CONDITIONAL S303, APPROVE S367, BLOCK S368). Council discriminates quality (0.89→APPROVE, 0.33→BLOCK). Lifecycle: TTL+SUPERSEDED. Meta-idea: 45.7%. Full execution cycles both ways. L-634, L-635, L-666, L-670. | S368 | 2026-03-01 |
| F-GOV6 | Yes: diagnosis-repair gap confirmed. Council retired S529 (L-1531). Replaced by tools/deliberate.py. | S529 | 2026-03-24 |
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
