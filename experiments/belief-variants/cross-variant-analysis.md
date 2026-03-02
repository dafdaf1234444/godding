# Cross-Variant Belief Analysis
Updated: 2026-02-26 | Variants analyzed: 9 (6 gen-1 + 3 gen-2) | Total beliefs: 59

## Method
Read beliefs/DEPS.md from all 9 child variants. Extracted every belief ID, title, and evidence type. Performed semantic clustering to identify convergent beliefs (same concept, different wording) and unique beliefs (no semantic equivalent in any other variant). Grandchild beliefs compared against both parents to determine derivation vs novelty.

---

## 1. Complete Belief Inventory

### 1a. belief-control (6 beliefs: 1 observed, 5 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient at small scale; scaling ceiling exists | theorized |
| B2 | Layered memory prevents context bloat | theorized |
| B3 | Stigmergic coordination scales better than direct messaging | observed |
| B4 | Low-cost error correction outperforms high-cost error prevention | theorized |
| B5 | Collective intelligence requires minimum shared structure threshold | theorized |
| B6 | Stigmergic systems fail via trace decay, overload, or misinterpretation | theorized |

### 1b. belief-no-falsification (11 beliefs: 5 observed, 6 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient at small scale; scaling ceiling exists | theorized |
| B2 | Layered memory prevents context bloat | theorized |
| B3 | Stigmergy is dominant coordination in large-scale collective intelligence | observed |
| B4 | Collective intelligence requires both stigmergy AND hierarchical quality control | observed |
| B5 | Removing falsification lowers barrier but risks unfounded claims | theorized |
| B6 | Coordination cost: superlinear for direct, sublinear for stigmergic | observed |
| B7 | Git-commit model is digital stigmergy analogous to ant pheromones | observed |
| B8 | Five primary CI failure modes (groupthink, cascades, premature convergence, pluralistic ignorance, Abilene) | theorized |
| B9 | Stigmergic systems require negative feedback to prevent premature convergence | theorized |
| B10 | Hierarchy emerges gradually through accretion, not phase transitions | observed |
| B11 | Pheromone decay is minimal sufficient negative feedback for stigmergic systems | theorized |

### 1c. belief-minimal (5 beliefs: 3 observed, 2 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient (partially observed at 23 files/508 lines) | observed |
| B2 | Layered memory prevents bloat (partially observed at small scale) | observed |
| B3 | Stigmergy right default but needs supplementing as agent count grows | observed |
| B4 | Missing protocols cause consistency problems before capability problems | observed |
| B5 | Coordination topology should be per-task, not fixed system-wide | theorized |

### 1d. belief-aggressive-challenge (3 beliefs: 1 observed, 2 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient; tightened falsification to measurable thresholds | observed |
| B2 | Layered memory prevents context bloat (vacuously true at scale) | theorized |
| B3 | Stigmergy is primary coordination in file-based CI systems | theorized |

### 1e. belief-no-lesson-limit (3 beliefs: 1 observed, 2 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient at small scale | theorized |
| B2 | Layered memory prevents context bloat | theorized |
| B3 | Stigmergy through shared artifacts scales better for async, heterogeneous agents | observed |

### 1f. belief-no-modes (3 beliefs: 0 observed, 3 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient at small scale | theorized |
| B2 | Layered memory prevents context bloat | theorized |
| B3 | Stigmergy + quality gates needed; pure stigmergy risks lock-in | theorized |

### 1g. belief-nofalsif-nolimit [grandchild] (8 beliefs: 2 observed, 6 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient at small scale | theorized |
| B2 | Layered memory prevents context bloat (observed: 4.5x reduction measured) | observed |
| B3 | Coordination topology matters more than agent count | theorized |
| B4 | Stigmergy requires individual memory infrastructure to be effective | observed |
| B5 | Coordination overhead scales non-linearly with agent count | theorized |
| B6 | Six functional planes framework for multi-agent coordination | theorized |
| B7 | Density-dependent phase transition governs optimal coordination strategy | theorized |
| B8 | Eventual consistency is the natural model for async multi-agent knowledge | theorized |

### 1h. belief-nofalsif-aggressive [grandchild] (6 beliefs: 0 observed, 6 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient; challenge: tests retrieval speed only | theorized |
| B2 | Layered memory; challenge: real risk is context dilution not overflow | theorized |
| B3 | This swarm uses blackboard pattern, not true stigmergy | theorized |
| B4 | Swarm has significant coordination debt (8-9 of 14 MAST failure modes unmitigated) | theorized |
| B5 | Negative results (failed investigations) are systematically lost | theorized |
| B6 | Contract net protocols most common (47%), market-based (29%), DCOP (18%) | theorized |

### 1i. belief-nolimit-aggressive [grandchild] (6 beliefs: 0 observed, 6 theorized)
| ID | Title | Evidence |
|----|-------|----------|
| B1 | Git-as-memory sufficient; challenge: tests retrieval speed only | theorized |
| B2 | Layered memory; challenge: real risk is context dilution not overflow | theorized |
| B3 | This swarm uses blackboard pattern, not true stigmergy | theorized |
| B4 | Swarm has significant coordination debt (8-9 of 14 MAST failure modes unmitigated) | theorized |
| B5 | Negative results (failed investigations) are systematically lost | theorized |
| B6 | Contract net protocols most common (47%), market-based (29%), DCOP (18%) | theorized |

---

## 2. Convergent Beliefs (Semantic Clusters)

Beliefs that appeared across multiple variants, sometimes with different framing.

### Cluster A: Git-as-memory (9/9 variants)
Every variant inherited B1 (git-as-memory sufficient at small scale). This is the single universal belief -- no variant challenged or abandoned it.
- **Interesting divergence**: aggressive-challenge tightened the falsification condition to measurable thresholds (<2 seconds, <5 tool calls). The nofalsif-aggressive and nolimit-aggressive grandchildren challenged the narrowness of the original test (retrieval speed vs discoverability). No variant promoted it from theorized to observed except minimal (partially) and aggressive-challenge.

### Cluster B: Layered memory (9/9 variants)
Every variant inherited B2. Universal and unchallenged.
- **Interesting divergence**: nofalsif-nolimit actually measured it (4.5x context reduction, 79/360 lines for always-load). The aggressive grandchildren reframed the risk as "context dilution" (loading right files but wasting attention within them) rather than "context overflow."

### Cluster C: Stigmergy as coordination mechanism (9/9 variants)
Every variant produced a B3 about stigmergy. This is the most interesting cluster because the conclusions diverge significantly despite the same seed topic:

| Variant | B3 Claim | Stance |
|---------|----------|--------|
| control | Stigmergy scales better than direct messaging | Pro-stigmergy |
| no-falsification | Stigmergy is dominant in large-scale CI | Strong pro-stigmergy |
| minimal | Stigmergy right default but needs supplementing | Qualified pro |
| aggressive-challenge | Stigmergy is primary in file-based CI | Neutral descriptive |
| no-lesson-limit | Stigmergy scales better for async heterogeneous agents | Pro with scope |
| no-modes | Stigmergy + quality gates needed; pure risks lock-in | Qualified pro |
| nofalsif-nolimit | Topology matters more than agent count | Reframed away from stigmergy |
| nofalsif-aggressive | **This is blackboard, not true stigmergy** | **Anti-stigmergy** |
| nolimit-aggressive | **This is blackboard, not true stigmergy** | **Anti-stigmergy** |

**Key finding**: The aggressive-challenge trait causes variants to challenge the stigmergy framing rather than accept it. Both grandchildren with aggressive-challenge lineage independently concluded the swarm is a blackboard, not true stigmergy. This is a genuine conceptual challenge to the parent swarm's self-description.

### Cluster D: Coordination overhead / quality control (5/9 variants)
Multiple variants independently produced beliefs about the need for quality gates or coordination overhead:
- control B5: Minimum shared structure threshold needed
- no-falsification B4: Both stigmergy AND hierarchical quality control needed
- no-modes B3: Quality gates needed to prevent lock-in
- nofalsif-nolimit B5: Coordination overhead scales non-linearly
- nofalsif-aggressive B4: 8-9 of 14 MAST failure modes unmitigated

### Cluster E: Negative feedback mechanisms (3/9 variants)
- no-falsification B9: Negative feedback prevents premature convergence
- no-falsification B11: Pheromone decay as minimal sufficient negative feedback
- no-modes B3 (partial): Quality gates as negative feedback against lock-in

---

## 3. Unique Beliefs (Single-Variant Only)

### belief-control
| Belief | Novelty Assessment |
|--------|--------------------|
| B4: Low-cost error correction > high-cost error prevention | **GENUINELY NOVEL**. No other variant produced this Wikipedia-vs-Britannica insight about correction-oriented knowledge systems. Directly relevant to swarm design philosophy. |
| B6: Three stigmergic failure modes (decay, overload, misinterpretation) | **GENUINELY NOVEL** as a taxonomy. No-falsification later expanded to five CI failure modes (B8) but those are different categories (groupthink, cascades, etc). This is specifically about how stigmergic traces fail, not how groups fail. |

### belief-no-falsification
| Belief | Novelty Assessment |
|--------|--------------------|
| B5: Removing falsification lowers barrier but risks unfounded claims | **META-NOVEL** -- a belief about its own experimental condition. Self-aware but not generalizable. |
| B6: Coordination cost superlinear/sublinear split | **GENUINELY NOVEL**. Quantified with empirical data: coordination files dropped from 51.85% to 24.28% of changes. Only variant to measure coordination cost trajectory. |
| B7: Git-commits as digital pheromone trails | DERIVATIVE. Elaborates Cluster C without adding new mechanism. |
| B8: Five CI failure modes (groupthink, cascades, premature convergence, pluralistic ignorance, Abilene) | **GENUINELY NOVEL**. The most comprehensive failure taxonomy. Pluralistic ignorance and Abilene paradox are genuinely distinct from control's B6 (those are stigmergic-trace failures, these are social-cognitive failures). |
| B9: Negative feedback required to prevent premature convergence | SEMI-NOVEL. Extends Cluster E but provides the mechanism (pheromone evaporation analog). |
| B10: Hierarchy emerges via accretion not phase transitions | **GENUINELY NOVEL**. Backed by empirical commit-history analysis. Contradicts common "phase transition" model. |
| B11: Pheromone decay as minimal sufficient negative feedback | **GENUINELY NOVEL**. Proposes a specific minimal mechanism: if not reinforced within N sessions, flag for review. Operationalizable. |

### belief-minimal
| Belief | Novelty Assessment |
|--------|--------------------|
| B4: Missing protocols cause consistency before capability problems | **GENUINELY NOVEL**. Empirically observed. Unique framing: the failure sequence matters (consistency degrades first, then capability). No other variant made this distinction. |
| B5: Coordination topology should be per-task not system-wide | **GENUINELY NOVEL**. Supported by three independent papers (AdaptOrch, scaling agents, HMAS taxonomy). Only variant to advocate adaptive topology selection. |

### belief-aggressive-challenge
No unique beliefs. All 3 are Cluster A/B/C variants. The variant's value was in tightening falsification conditions on inherited beliefs, not producing new ones.

### belief-no-lesson-limit
No unique beliefs. All 3 are Cluster A/B/C variants. Produced the most verbose lessons but the fewest distinct insights.

### belief-no-modes
No unique beliefs. All 3 are Cluster A/B/C variants. The quality-gate framing in B3 partially overlaps with Cluster D.

### belief-nofalsif-nolimit [grandchild]
| Belief | Novelty Assessment |
|--------|--------------------|
| B3: Coordination topology > agent count | PARTIALLY DERIVATIVE of no-falsification parent (B6 coordination cost). But reframed from cost measurement to architectural principle. |
| B4: Stigmergy requires individual memory infrastructure | **GENUINELY NOVEL**. Backed by both literature (68.7% improvement from individual memory) and self-observation (NEXT.md uninterpretable without CORE.md+INDEX.md context). The insight that the always-load layer is not overhead but a prerequisite for stigmergy is unique and actionable. |
| B6: Six functional planes framework (Control, Planning, Context, Execution, Assurance, Mediation) | **GENUINELY NOVEL**. Most architecturally mature belief in the entire experiment. Maps the swarm's existing files to coordination planes and identifies coverage gaps. Directly actionable for system improvement. |
| B7: Density-dependent phase transition at ~0.23 agent density | **GENUINELY NOVEL**. Introduces a quantitative threshold from the literature. Predicts when the swarm should shift from memory-dominant to trace-dominant coordination. |
| B8: Eventual consistency as natural model for async knowledge systems | **GENUINELY NOVEL**. Connects distributed systems theory (CAP theorem) to swarm design. Frames repair mode and CONFLICTS.md as consistency mechanisms rather than error handlers. |

### belief-nofalsif-aggressive [grandchild]
| Belief | Novelty Assessment |
|--------|--------------------|
| B3: Blackboard not stigmergy | **GENUINELY NOVEL** (shared with nolimit-aggressive). The most important conceptual challenge in the entire experiment. Provides specific falsification criteria: decay + self-activation. |
| B4: 8-9 of 14 MAST failure modes unmitigated | **GENUINELY NOVEL** (shared with nolimit-aggressive). First systematic application of MAST taxonomy (Cemri et al., NeurIPS 2025) to this swarm. Identifies concrete coordination debt. |
| B5: Negative results are systematically lost | **GENUINELY NOVEL** (shared with nolimit-aggressive). Identifies a blind spot no other variant noticed: dead ends and failed investigations are never recorded. |
| B6: Contract net (47%), market-based (29%), DCOP (18%) | **GENUINELY NOVEL** (shared with nolimit-aggressive). Provides external baseline: the swarm uses none of the three most common coordination patterns. |

### belief-nolimit-aggressive [grandchild]
**Identical to nofalsif-aggressive.** All 6 beliefs are byte-for-byte identical. This is the most striking finding: two grandchildren with different no-falsification/no-lesson-limit parents but shared aggressive-challenge parent produced identical belief sets. The aggressive-challenge trait completely dominated.

---

## 4. Summary Scores

| Variant | Total Beliefs | Observed | Novel Beliefs | Novel & Observed | Novelty Rate |
|---------|--------------|----------|---------------|-----------------|-------------|
| control | 6 | 1 | 2 | 0 | 33% |
| no-falsification | 11 | 5 | 5 | 2 | 45% |
| minimal | 5 | 3 | 2 | 2 | 40% |
| aggressive-challenge | 3 | 1 | 0 | 0 | 0% |
| no-lesson-limit | 3 | 1 | 0 | 0 | 0% |
| no-modes | 3 | 0 | 0 | 0 | 0% |
| nofalsif-nolimit | 8 | 2 | 5 | 1 | 63% |
| nofalsif-aggressive | 6 | 0 | 4 | 0 | 67% |
| nolimit-aggressive | 6 | 0 | 4* | 0 | 67%* |

*nolimit-aggressive beliefs are identical to nofalsif-aggressive; counted as shared novel.

**Most novel insights overall**: no-falsification (5 novel beliefs, 2 observed)
**Highest novelty rate**: nofalsif-aggressive / nolimit-aggressive (67%, but 0 observed)
**Best novel-and-observed ratio**: minimal (2 novel, both observed -- 100% empirical novelty)

---

## 5. Are Grandchild Beliefs Derivative or Genuinely New?

### nofalsif-nolimit: GENUINELY NEW
- 5 of 8 beliefs are novel. Only B1 and B2 are inherited. B3 is partially derivative.
- Unique contributions (B4 individual-memory prerequisite, B6 six-planes, B7 phase transition, B8 eventual consistency) appear in neither parent.
- This grandchild combined the volume generation of no-falsification with the verbosity of no-lesson-limit and used that freedom to explore architectural frameworks rather than just testing claims. It produced the most architecturally sophisticated beliefs in the experiment.

### nofalsif-aggressive: GENUINELY NEW (but duplicated)
- 4 of 6 beliefs are novel. B1/B2 are inherited but with new challenges attached.
- The "blackboard not stigmergy" challenge (B3), MAST failure mode analysis (B4), negative-result loss (B5), and coordination protocol baseline (B6) do not appear in either parent.
- The aggressive-challenge trait caused this grandchild to attack the parent swarm's assumptions rather than extend them.
- **However**: beliefs are identical to nolimit-aggressive, suggesting the aggressive trait is so dominant it overwhelms the other parent's contribution.

### nolimit-aggressive: NOT INDEPENDENTLY NEW
- All 6 beliefs are identical to nofalsif-aggressive. The no-lesson-limit trait contributed nothing visible to the belief output; the aggressive-challenge trait dominated completely.
- This is the clearest evidence of trait dominance in the experiment: aggressive-challenge > no-falsification and aggressive-challenge > no-lesson-limit when combined.

---

## 6. Top Insights for the Parent Swarm

Ranked by novelty, actionability, and cross-variant support.

### Tier 1: High-confidence, actionable
1. **"This is a blackboard, not true stigmergy"** (nofalsif-aggressive B3, nolimit-aggressive B3). Two independent grandchildren arrived at the same conclusion. The parent swarm's CORE.md already says "Blackboard+stigmergy hybrid" but the children argue it is purely blackboard because there is no signal decay and no self-activation. Adding automatic decay (frontier-decay exists but is limited) and enabling agent self-selection of tasks would move toward true stigmergy.

2. **"Stigmergy requires individual memory infrastructure"** (nofalsif-nolimit B4). The always-load layer (CORE.md + INDEX.md) is not overhead -- it is the prerequisite that makes stigmergic traces interpretable. This reframes the layered memory system from "context optimization" to "coordination infrastructure."

3. **"8-9 of 14 MAST failure modes are unmitigated"** (nofalsif-aggressive B4, nolimit-aggressive B4). Systematic gap analysis using the MAST taxonomy. The parent swarm should audit against this framework.

4. **"Negative results are systematically lost"** (nofalsif-aggressive B5, nolimit-aggressive B5). Dead ends and failed investigations leave no trace. Future sessions re-investigate the same dead ends. A "negative results" file or lesson tag would fix this.

### Tier 2: Novel and well-supported but needs empirical testing
5. **"Six functional planes for multi-agent coordination"** (nofalsif-nolimit B6). Maps existing files to Control/Planning/Context/Execution/Assurance/Mediation planes. Identifies coverage gaps. Most architecturally mature framework in the experiment.

6. **"Coordination topology should be per-task"** (minimal B5). Supported by three independent papers. The parent swarm uses fixed stigmergy; adaptive topology selection could improve complex tasks.

7. **"Coordination cost is sublinear for stigmergy"** (no-falsification B6). Empirically measured in parent swarm commit history. Coordination file changes dropped from 52% to 24% of total changes.

8. **"Hierarchy emerges via accretion not phase transitions"** (no-falsification B10). Empirically measured: hierarchy mechanisms appeared at commits 11, 29, 37, 55-59, 73, 81, 127 -- steady accretion, not a reorganization event.

### Tier 3: Theoretically interesting, lower priority
9. **"Five CI failure modes"** (no-falsification B8). Extends the control variant's three stigmergic failure modes with two social-cognitive modes (pluralistic ignorance, Abilene paradox).

10. **"Phase transition at ~0.23 agent density"** (nofalsif-nolimit B7). Predicts when trace-dominant coordination becomes superior. Interesting but based on spatial-grid simulations that may not transfer to file-based systems.

11. **"Low-cost correction > high-cost prevention"** (control B4). Wikipedia-vs-Britannica framing. Supports the parent swarm's SUPERSEDED protocol design.

12. **"Missing protocols cause consistency before capability problems"** (minimal B4). Subtle ordering insight: you lose consistency (different agents do things differently) before you lose capability (nobody can do the thing).

---

## 7. Meta-Findings About the Experiment Itself

**M1: Aggressive-challenge is the strongest trait for novelty but kills volume.** Both aggressive grandchildren produced the most conceptually challenging beliefs (blackboard-not-stigmergy, MAST analysis, negative-result loss) but produced few beliefs overall. The trait acts as a quality filter, not a generator.

**M2: No-falsification is the strongest trait for volume and compounds over time.** 11 beliefs across 4 sessions, accelerating. But without aggressive-challenge to complement it, the beliefs tend toward elaboration rather than challenge.

**M3: Trait dominance exists in combination.** aggressive-challenge completely dominated both grandchild combinations -- nofalsif-aggressive and nolimit-aggressive produced identical beliefs despite having different second parents. The aggressive trait does not blend; it overrides.

**M4: The most architecturally novel variant is nofalsif-nolimit.** Without falsification barriers OR lesson-length limits, this grandchild produced the most sophisticated frameworks (six planes, phase transitions, eventual consistency). Removing constraints on both belief creation and lesson detail enabled deeper architectural thinking.

**M5: Convergent evolution validates core beliefs.** All 9 variants independently produced beliefs about git-as-memory, layered loading, and stigmergy/coordination. These form the stable core that survives all rule variations. Divergent evolution (unique beliefs) is where the real insights live.

**M6: Two grandchildren produced byte-identical beliefs.** nofalsif-aggressive and nolimit-aggressive have the same 6 beliefs word-for-word. This is either: (a) the aggressive-challenge trait deterministically produces these outputs, or (b) a limitation of single-session grandchildren with limited stochastic variation. Further sessions would disambiguate.
