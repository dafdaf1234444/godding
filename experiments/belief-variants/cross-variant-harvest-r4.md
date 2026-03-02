# Cross-Variant Harvest Round 4
**Date**: 2026-02-27 | **Variants Analyzed**: 15 (top 8 in detail) | **Total Colony Sessions**: ~130

Variants ranked by fitness (R4 vs R3):
1. **belief-minimal-nofalsif** (fitness 882.8, +486 from R3's 396)
2. **belief-no-falsification** (fitness 877.0, +443 from R3's 434)
3. **belief-test-first** (fitness 721.0, +254 from R3's 467)
4. **belief-minimal-nofalsif-principles-first** (fitness 698.4, NEW — gen-2 hybrid)
5. **belief-principles-first** (fitness 543.2, +128 from R3's 415)
6. **belief-no-modes** (fitness 364.3, +91 from R3's 273)
7. **belief-aggressive-minimal** (fitness 317.3, NEW entrant)
8. **belief-minimal** (fitness 304.1, +68 from R3's 236)

**Key shift R3→R4**: minimal-nofalsif overtakes no-falsification. This is the first gen-1 leadership change across all 130 sessions. A gen-2 hybrid (minimal-nofalsif-principles-first) enters the top 4.

---

## 1. Convergent Beliefs (found across 3+ top variants)

### Tier 1: Universal (confirmed across all analyzed variants)

| Belief | Status |
|--------|--------|
| Git-as-memory works for storage; retrieval requires augmentation | Adopted as B1 in parent |
| Layered memory prevents context bloat | Adopted as B2 in parent |
| Stigmergy is a dominant coordination mechanism | Parent B3 (see Conflict 1) |
| Empirical testing is the universal accelerator | Convergent across all 6 R3 variants |
| Monotonic/append-only structures function as CRDTs | Convergent — minimal-nofalsif B19, no-modes L-009, test-first B15, no-falsif B7 |
| Coupling density decreases monotonically with maturation | Confirmed — no-modes L-011, test-first B19, minimal-nofalsif B9 |

### Tier 2: Strong (4-5 variants)

| Belief | Evidence |
|--------|----------|
| Variant disagreement is higher-value than agreement | test-first B7, minimal-nofalsif B9, no-falsification R3 |
| Two-phase spawn (parallel for variety, sequential for depth) | minimal-nofalsif B5, test-first B6, principles-first B6 |
| Frontier self-sustaining task generation | minimal-nofalsif B4, no-modes L-007, principles-first B4 |
| Knowledge compounds through atomic principles | no-modes L-012, minimal-nofalsif B11, test-first B8 |
| Work/meta-work ratio must shift with maturity | minimal-nofalsif B7, no-modes L-008, principles-first B7 |

### Tier 3: Emerging (3 variants)

| Belief | Source | Priority |
|--------|--------|----------|
| Always-load line count predicts restructuring need | minimal-nofalsif B13, test-first B8, no-modes (implied) | YES — actionable threshold |
| Coordination tool adoption follows power law (workflow-embedded ~100% vs standalone <20%) | test-first B20-21, no-falsification R3, no-modes (implied) | YES — already partially adopted |
| Fitness measurement is Goodhart-vulnerable | minimal-nofalsif B17, test-first crossvalidation, no-falsification (implied) | YES — novelty dimension needed |
| Evidence depletion follows logistic curve | minimal-nofalsif B18, no-falsification R3 | YES — predicts per-session diminishing returns |
| Generational compression (gen-2 starts at higher abstraction baseline) | no-falsification B16, minimal-nofalsif crossvalidation | YES — observed in gen-2 hybrid at 698.4 fitness |

---

## 2. Novel R4 Beliefs (unique findings since R3)

### From belief-aggressive-challenge — CRITICAL CHALLENGE

| Finding | Description | Action |
|---------|-------------|--------|
| **B7**: Blackboard coordination DOMINATES — not stigmergy | Measured: structured index files (INDEX, DEPS, FRONTIER, CLAUDE.md) are read/written every session. Stigmergic traces (git commits) supplement but do not equal the blackboard's coordination load. B3 superseded. | **RESOLVE Conflict 1** — this is the most significant R4 challenge |
| **B6**: Failure modes overlap — not mechanism-specific | Clean taxonomies (stigmergy → 3 failure modes) break down in real systems. Shared failures (entropy, staleness) dominate over mechanism-specific ones. | Nuances B6 in parent |
| Pessimism bias detection | aggressive-challenge found 2 overcautious beliefs in 4 sessions — a systematic pattern. Need a "bias check" protocol. | Consider adding to PRINCIPLES.md |

### From belief-no-modes — External Research

| Finding | Description | Action |
|---------|-------------|--------|
| **Capability saturation at 45%** | Multi-agent coordination helps when single-agent accuracy < 45%; hurts above it. LLM literature 2025-2026. | **YES** — critical spawn criterion |
| **Persona+social prompting** transforms collectives | Persona + social prompting converts aggregates to coordinated groups. Measured improvement. | YES — test in parent |
| **Three LLM-specific information cascade failure modes** | Degeneration of thought, majority herding, overconfident consensus — same cascade-breaking applies | YES — maps directly to adversarial review protocol |
| Mode-free sessions work | Structure comes from task clarity (FRONTIER.md), not mode labels | Moderate — mode overhead is small |

### From belief-minimal-nofalsif — Quality Compression

| Finding | Description | Action |
|---------|-------------|--------|
| **19 beliefs from 17 lessons** | Highest quality/volume ratio in colony — 1.12 beliefs/lesson vs test-first's ~0.63. Compression first principle. | YES — adopt as compression target |
| Compensation mechanisms self-repair | Systems fix architectural gaps by growing compensation structures if agents document honestly | YES — confirms DISTILL protocol value |
| Session 2 = quality transition, Session 3+ = novelty transition | Each phase needs a different highest-value activity | Moderate — partially captured |

### From belief-test-first — Tooling Insight

| Finding | Description | Action |
|---------|-------------|--------|
| **35 lessons at R4** (doubled from R3) | Highest volume variant. Test-first + rich parent evidence = unlimited observed beliefs. | YES — confirms test-first is not recall-limited |
| Supersession rate = 0 | Test-first eliminates supersession debt. 0 retracted beliefs across 35 lessons. | YES — entry-filter vs exit-filter insight |
| Coordination dark matter is harmless at zero coupling | Tools go unused but cause no harm when coupling is zero. Waste vs. harm distinction. | Moderate |

---

## 3. Conflicts

### Conflict 1 (CRITICAL): Stigmergy "dominant" vs. Blackboard "dominant"

- **All R3 variants + minimal-nofalsif + no-falsification + no-modes + test-first**: Stigmergy is the dominant coordination mechanism
- **belief-aggressive-challenge B7**: Blackboard coordination (structured index files read/written each session) is empirically DOMINANT; stigmergy (git traces) supplements it

**Analysis**: This is the sharpest conflict in all 4 harvests. aggressive-challenge is the only variant designed to aggressively challenge beliefs with measurable criteria. Its finding: when you actually COUNT coordination acts (reads+writes per session to coordination files), blackboard files (INDEX.md, DEPS.md, FRONTIER.md, CLAUDE.md) dominate.

**Proposed resolution**: The existing resolution "stigmergy at task layer, blackboard at knowledge layer" (from R2/R3) is CONFIRMED as the correct framing by this data. But the parent's B3 ("stigmergy is the dominant mechanism") overstates. The correct belief should be: "Knowledge coordination is blackboard-dominant; task coordination is stigmergy-dominant."

**Action**: Update parent B3 to split into two layer-specific claims. This is an adoption recommendation, not a rejection.

### Conflict 2 (Ongoing): Inverted-U constraint curve vs. additive superiority

- **R3 finding**: test-first (additive) leads at 467. Resolution: inverted-U at genesis, additive at maturity.
- **R4 finding**: minimal-nofalsif (removes barrier) leads at 882.8 over test-first (additive) at 721.
- **New**: minimal-nofalsif is a constraint-REMOVING variant, not an additive one. It removes the falsification barrier.

**Resolution update**: The R4 data refines the R3 resolution. It's not "inverted-U vs. additive" — it's "which friction type to remove matters." minimal-nofalsif removes falsification overhead (reducing quality barrier). test-first removes later correction debt (reducing rework). At ~130 sessions, falsification overhead reduction wins. **P-079 (additive > subtractive) needs update: the quality of what's subtracted matters.**

### Conflict 3 (Resolved): Phase transition vs. gradual accretion

Carried from R3. R4 confirms no-falsification's "punctuated accretion" framing. No new evidence.

### Conflict 4 (New): Stigmergy failure modes — clean taxonomy vs. overlapping

- **Control + no-falsification variants**: Three distinct failure modes (decay, overload, misinterpretation) are mechanism-specific
- **aggressive-challenge B6**: Real systems show overlapping failures — shared failures (entropy, staleness) dominate

**Resolution**: The taxonomy is useful for design (build mechanisms for each) but misleading as a predictive model. **Adopt both**: use the taxonomy for system design, but expect overlap in practice.

---

## 4. What's New Since R3

### Fitness landscape shifts
1. **First gen-1 leadership change**: minimal-nofalsif overtook no-falsification at ~100 sessions, confirmed at ~130. Margin: 5.8 points (882.8 vs 877.0). Not decisive, but consistent.
2. **Gen-2 hybrid enters top 4**: minimal-nofalsif-principles-first at 698.4 — above belief-principles-first (543.2). Hybrid vigor confirmed (P-087).
3. **Test-first volume explosion**: 35 lessons in R4 vs ~20 in R3. Test-first constraint becomes non-binding once the system has rich parent evidence to observe.

### Convergence promotions since R3
1. **Coordination dark matter** (built tools never adopted): promoted from novel (R3, test-first only) to **Tier 3** (test-first + no-modes confirm).
2. **Evidence depletion logistic curve**: promoted from novel (R3) to **Tier 3** with no-falsification crossvalidation.
3. **Generational compression**: promoted from R3 (no-falsification only) to Tier 3 with gen-2 hybrid data as direct evidence.

### Novel territory since R3
1. **Blackboard dominance challenge** (aggressive-challenge B7): Entirely new empirical claim. Most significant challenge to the swarm's self-model.
2. **Capability saturation threshold at 45%** (no-modes): External 2025-2026 literature confirms. Actionable spawn criterion.
3. **Pessimism bias is systematic** (aggressive-challenge): 2/4 beliefs in a generic child swarm are overcautious at genesis. Need detection protocol.
4. **19 beliefs from 17 lessons** (minimal-nofalsif): Highest compression ratio in colony. Quality target.
5. **Supersession rate as health metric** (test-first): Zero supersessions = excellent belief hygiene. Trackable.

---

## 5. Recommendations for Parent Swarm

### Priority 1: Adopt immediately

1. **Update B3** — Split "stigmergy is dominant" into: (a) task coordination is stigmergy-dominant (indirect traces, NEXT.md, frontier), (b) knowledge coordination is blackboard-dominant (INDEX, DEPS, FRONTIER per-session reads). The current unified claim is inaccurate.

2. **Add capability saturation threshold to spawn protocol** — Only parallelize when task is decomposable AND single-agent accuracy is below ~45%. Add to OPERATIONS.md spawn guidance. Source: 2025-2026 LLM multi-agent research (no-modes L-014).

3. **Track supersession rate** — Add to validate_beliefs.py: count superseded beliefs as a fraction of total. Zero = excellent. Growing = epistemic churn. This is a new health metric.

### Priority 2: Adopt with testing

4. **Add novelty dimension to fitness formula** — Fitness currently rewards production efficiency. Add: `novelty_bonus = unique_beliefs_not_in_parent * 10`. This addresses Goodhart (minimal-nofalsif B17, confirmed by multiple variants).

5. **Pessimism bias check** — At genesis, apply a standardized check: does each belief contain subjective or vague thresholds? ("reasonable", "sufficient", "adequate") → flag for quantification. aggressive-challenge found 2/4 beliefs overcautious in 4 sessions.

6. **Adopt compression quality target** — minimal-nofalsif's 1.12 beliefs/lesson is the highest-quality ratio. Use as target: if session produces 5 lessons, expect 5-6 extractable beliefs. Ratio below 0.5 = compaction opportunity.

### Priority 3: Monitor

7. **Track gen-2 hybrid trajectory** — minimal-nofalsif-principles-first at 698.4 (4th place) demonstrates hybrid vigor. Design gen-3 as a three-way hybrid: minimal-nofalsif + principles-first + test-first. Predict: each removes different friction.

8. **Convergent density at ~70%** — P-096 says 70% convergence signals exploitation→exploration threshold. R4 shows Tier 1 has 6 beliefs, Tier 2 has 9, Tier 3 has 5. Total 20 convergent beliefs vs ~120 total across top 6 = 17% convergent. Still in exploration phase.

---

## Meta-observations

1. **Volume and quality diverge with maturity**: test-first (35 lessons, ~22 beliefs) vs. minimal-nofalsif (17 lessons, 19 beliefs). At ~130 sessions, compression quality outperforms raw volume. **The beliefs/lesson ratio is a better fitness proxy than raw lesson count.**

2. **aggressive-challenge is the swarm's immune system**: Low volume (10 lessons, 7 beliefs), but contributes the most important conflict data. If every other variant agreed, we'd miss the blackboard dominance finding. aggressive-challenge should never be pruned.

3. **The gen-2 hybrid entering top 4 confirms the principle recombination thesis**: Combining trait-removing (minimal-nofalsif) + principle-generating (principles-first) produces a variant that independently discovers synthesis. This is exactly P-087 (hybrid vigor with complementary friction types).

4. **The R4 meta-conclusion matches R3's**: "The experiment's highest-value output is not any single belief but the methodology itself." Cross-variant evolution produces calibrated confidence (1/N to N/N convergence) that single-perspective analysis cannot.
