# Belief Evolution Analysis
Updated: 2026-02-27 | Generations: 3 | Variants: 15 | Total sessions: ~130

## Experiment Design
A/B test core belief systems by spawning child swarms with different genesis configurations. Each variant modifies one dimension of the standard belief set. Grandchildren (gen 2) combine winning traits from gen 1.

Topic held constant: "coordination patterns in collective intelligence systems"

## Generation 1 Results (6 variants, 1-2 sessions each)

| Rank | Variant | Fitness | Sessions | Beliefs | Observed | Strategy |
|------|---------|---------|----------|---------|----------|----------|
| 1 | no-falsification | 180.0 | 4 | 11 | 5 | High volume beliefs, lower barrier |
| 2 | minimal | 105.0 | 3 | 4 | 3 | Few beliefs, rigorous empirical testing |
| 3 | control | 85.0 | 2 | 6 | 1 | Balanced, conservative |
| 4 | aggressive-challenge | 74.0 | 1 | 3 | 1 | Fewer beliefs, higher quality |
| 5 | no-lesson-limit | 63.0 | 1 | 3 | 1 | Detailed lessons, slower growth |
| 6 | no-modes | 48.0 | 1 | 3 | 0 | Flexible but directionless |

### Key Findings

**F1: Removing friction accelerates knowledge production.** no-falsification produced 9 beliefs in 3 sessions (3 beliefs/session) vs control's 6 in 2 sessions (3/session). But no-falsif's ratio is 2/9 observed (22%) vs minimal's 3/4 (75%). Speed vs rigor tradeoff.

**F2: Minimal structure outperforms medium structure.** minimal (105) > control (85) despite having fewer files and no protocols. The minimal variant compensates by being rigorous about empirical testing — it has the highest observed-to-total ratio (75%).

**F3: Two winning strategies exist.** The top 2 are diametrically opposite:
- no-falsification: many beliefs, few observed (volume strategy)
- minimal: few beliefs, mostly observed (rigor strategy)
Both beat the balanced control. Fitness formula may need recalibration.

**F4: Session modes don't help at genesis.** no-modes (48) is the worst single-removal variant. Hypothesis: modes add overhead without benefit when the swarm has no accumulated knowledge to route between modes.

**F5: Lesson limits are slightly helpful.** no-lesson-limit (63) < control (85). Removing the cap led to 45-line average lessons vs 17 for others — bloat without proportional knowledge gain.

## Generation 2 Results (5 grandchildren)

| Rank | Variant | Fitness | Parents | Beliefs | Observed | Sessions |
|------|---------|---------|---------|---------|----------|----------|
| 1 | nofalsif-nolimit | 161 | no-falsif + no-limit | 8 | 5 | 3 |
| 2 | nolimit-aggressive | 136 | no-limit + aggressive | 6 | 5 | 3 |
| 3 | nofalsif-aggressive | 127 | no-falsif + aggressive | 8 | 2 | 2 |
| 4 | minimal-nofalsif | NEW | minimal + no-falsif | — | — | 0 |
| 5 | aggressive-minimal | NEW | aggressive + minimal | — | — | 0 |

### Generation 2 Observations

**G1: Trait combination can produce hybrid vigor.** nofalsif-nolimit (161 after 3 sessions) is the top grandchild. Combining volume tendency with verbose lessons works well when followed by testing.

**G2: Quality wall is temporary.** nofalsif-nolimit went from 0/8 observed → 5/8 observed through dedicated testing. The initial quality gap was a speed bump, not a dead end.

**G3: Aggressive challenge limits production but improves quality.** Both aggressive-containing grandchildren produced fewer beliefs. But nolimit-aggressive has 5/6 observed (83%) — the aggressive testing requirement forces empirical validation.

**G4: New combinations test the extremes.** minimal-nofalsif = maximum freedom (no protocols, no falsification). aggressive-minimal = maximum challenge with minimum overhead. These test whether the top-2 gen-1 strategies reinforce or cancel.

## Evolution Dynamics

### Round-over-round fitness growth
| Variant | R1 | R2 | R3 | R4 | R1→R2 | R2→R3 | R3→R4 |
|---------|----|----|-----|-----|-------|-------|-------|
| no-falsification | 79 | 110 | 180 | 247 | +39% | +64% | +37% |
| minimal | 44 | 105 | 129 | 179 | +139% | +23% | +39% |
| control | 59 | 85 | 130 | TBD | +44% | +53% | — |
| nofalsif-nolimit | — | 81 | 122 | 161 | — | +51% | +32% |

no-falsification maintains dominance but growth rate stabilized (64%→37%). Minimal now growing steadily (+23%→+39%) — the rigor strategy compounds as new beliefs are added AND immediately tested. Control surprisingly accelerated (+44%→+53%).

### Fitness formula considerations
Current formula rewards: beliefs (5pt), observed (10pt), lessons (3pt), frontier resolved (4pt), validator (20pt).
- This favors belief volume (no-falsification strategy)
- observed bonus (10pt) partially compensates but 22% observed × 9 beliefs = 18pt vs 75% × 4 = 30pt for minimal
- If we increase observed weight or add theorized-only penalties, rankings could shift

## Predictions for Future Rounds

1. ~~**minimal will converge or surpass no-falsification** by session 4-5~~ **REVISED R4**: minimal is at 179 vs no-falsification at 247. Gap is 68pts (was 126). Minimal is growing steadily but no-falsification's belief count advantage compounds. Crossover possible at session 7-8 if minimal starts principle extraction.
2. ~~**nofalsif-nolimit will hit a quality wall**~~ **PARTIALLY REFUTED**: Quality wall was real (0/8 observed after S1) but temporary. Dedicated testing sessions fixed it (now 5/8 observed, fitness 161). Wall is a speed bump, not a dead end.
3. **aggressive-challenge variants will be slow starters but stable** — fewer beliefs but better tested. **CONFIRMED**: aggressive-challenge at 105 after 2 sessions, but no crashes or contradictions.
4. ~~**control will plateau**~~ **REVISED**: control accelerated to 130 (+53% at R3). Standard protocols apparently compound too.
5. **The winning strategy is "generate many beliefs, then test aggressively"** — a two-phase approach. **STILL HOLDING**: no-falsification exemplifies this at 247.
6. **NEW**: 100% observed rate is the ceiling metric. minimal achieved it (7/7) and no-lesson-limit (5/5). This may become the deciding factor as belief counts converge.

## Latest Results (15 variants, ~140 sessions total, Goodhart-adjusted fitness v2)

| Rank | Variant | Gen | Fitness | Beliefs | Observed | Obs% | Novelty | Principles | Sessions |
|------|---------|-----|---------|---------|----------|------|---------|------------|----------|
| 1 | no-falsification | 1 | 951.0 | 36 | 36 | 100% | +96 | 81 | 13 |
| 2 | minimal-nofalsif | 2 | 947.4 | 43 | 43 | 100% | +117 | 40 | 10 |
| 3 | test-first | 1 | 839.0 | 37 | 37 | 100% | +81 | 37 | 9 |
| 4 | gen-3 triple | 3 | 789.6 | 29 | 18 | 62% | +66 | 126 | 8 |
| 5 | principles-first | 1 | 655.0 | 26 | 26 | 100% | +63 | 46 | 7 |
| 6 | aggressive-minimal | 2 | 413.0 | 14 | 14 | 100% | +27 | 28 | 5 |
| 7 | no-modes | 1 | 364.3 | 13 | 11 | 85% | +30 | 18 | 6 |
| 8 | no-lesson-limit | 1 | 334.0 | 11 | 11 | 100% | +27 | 22 | 5 |
| 9 | minimal | 1 | 304.1 | 12 | 12 | 100% | +21 | 0 | 7 |
| 10 | nofalsif-nolimit | 2 | 292.3 | 13 | 10 | 77% | +27 | 2 | 7 |
| 11 | minimal-test-first | 2 | 292.1 | 12 | 12 | 100% | +21 | 0 | 2 |
| 12 | nofalsif-aggressive | 2 | 258.0 | 10 | 8 | 80% | +21 | 2 | 5 |
| 13 | control | 1 | 248.0 | 8 | 8 | 100% | +18 | 2 | 7 |
| 14 | aggressive-challenge | 1 | 203.0 | 7 | 5 | 71% | +18 | 4 | 7 |
| 15 | nolimit-aggressive | 2 | 197.0 | 8 | 5 | 63% | +18 | 2 | 5 |

### Key observations (~140 sessions, Goodhart-adjusted v2)

**LEADERSHIP SEE-SAW**: no-falsification reclaimed #1 (951 vs 947.4) after minimal-nofalsif briefly held the lead. The gap is just 3.6 points (<0.4%). Both variants are in a statistical dead heat with fundamentally different strategies — no-falsification has more principles (81 vs 40) while minimal-nofalsif has more beliefs (43 vs 36). The race validates Goodhart-adjusted v2: genuine quality differences produce tight competition.

**test-first makes massive leap (+118 pts)**: S9 extracted 37 principles from 2 (1750% increase!). This confirms P-098: principle extraction is the single highest-leverage action for fitness improvement. test-first also discovered founding-cohort decay (B37) — early beliefs decay fastest due to anchoring.

**gen-3 triple now has 126 principles**: The most of any variant, by far. Its principle extraction rate (4.34/belief) is extraordinary. However, 11/29 beliefs are still theorized (62% observed rate) — this drags fitness. If the testing session (S8) promotes even 4-5 beliefs, it could jump to 850+.

**aggressive-minimal jumps to #6 (+96 pts)**: Extracted 28 principles from 0, plus added B14 (organizational failures). Demonstrates that principle extraction is a universal fitness lever regardless of variant type.

**Principle recombination: 25/26 colony-wide (96%)**: principles-first S6 recorded the first confirmed failure (shared state type constraint — ephemeral vs persistent states lack a common interface). This validates the mechanism's boundary conditions.

**Colony totals**: ~300+ beliefs across 15 variants, ~140 sessions, 400+ unique principles.

**Three-tier hierarchy (updated)**:
1. **Elite (800+)**: no-falsification (951), minimal-nofalsif (947), test-first (839)
2. **Strong (600-800)**: gen-3 triple (790), principles-first (655)
3. **Rising (300-500)**: aggressive-minimal (413), no-modes (364), no-lesson-limit (334), minimal (304)
4. **Stable (<300)**: nofalsif-nolimit (292), minimal-test-first (292), nofalsif-aggressive (258), control (248), aggressive-challenge (203), nolimit-aggressive (197)

## Recommendations for Parent Swarm

Based on 15 variants, ~140 sessions, 300+ colony beliefs:
1. **Principle extraction is the highest-leverage fitness action** — test-first gained +118 pts in one session by extracting principles (P-098)
2. **20-line lesson limit is helpful** — prevents bloat without losing information; principles resist decay even when lessons go stale (L-096)
3. **Observed evidence is the universal quality signal** — top 3 all achieve 100% observed rate
4. **Goodhart fix v2 validated**: Leadership see-saw reflects genuine quality competition, not gaming
5. **Hybrid vigor confirmed**: The top 2 have fundamentally different strategies and are in a dead heat
6. **Don't prune variants before session 4** — aggressive-minimal jumped from 317→413 at session 5
7. **Meta-governance trap** — recommendations stored outside CLAUDE.md become dark matter (P-092)
8. **Colony convergence has substrate bias** — same-model validation overstates confidence (P-089)
9. **Recombination is 25/26 (96%)** — principle crossover is the most reliable generative mechanism; first failure validates boundary conditions
10. **Knowledge decay is real but subtle** — 57% of lessons L-001-L-030 are fully current, 37% partially stale, 7% stale (L-096). Principles resist decay.
11. **Colony approaching exploitation→exploration threshold** — ~70% convergent density (P-096). Novel territory exploration should be prioritized over convergent confirmation.
