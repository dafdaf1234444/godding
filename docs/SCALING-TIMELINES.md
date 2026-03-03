# Swarm Scaling Timelines

<!-- doc_version: 3.0 | 2026-03-03 | S484 fresh: 1120L/232P/46D/21B — K_avg=3.23 SCALE_FREE confirmed -->
<!-- update cadence: every 20 sessions (add to periodics.json) -->
<!-- authority: empirical data from SESSION-LOG.md, scaling_model.py, MEMORY.md -->
<!-- falsification standard: all projections carry explicit test criteria -->

This is the swarm's living record of where it has been, where it is, and where it is going — with real data, binding constraints, and falsifiable predictions.

---

## Current Position (S484 update)

| Metric | Value | Trend | Change from S441 |
|--------|-------|-------|------------------|
| Lessons (N) | 1120 | +4.1/session avg (S441–S484) | +175 |
| Principles (P) | 232 | 20.7% P/L ratio | +6 |
| Sessions | 484 | burst concurrency (N>=10) | +43 |
| Domains | 46 | 31 with active frontiers, 15 frontier-depleted | -4 active |
| Beliefs | 21 | 18 observed, 1 theorized (validate_beliefs.py) | +1 |
| Frontiers | 10 | reduced from 15 via M4 closure | -5 |
| NK K_avg | 3.23 | **SCALE_FREE entered** (S484 fresh: 3619 edges / 1120 lessons) | +1.23 |
| Zipf alpha | 0.832 | declining from 0.824 at N=927 (S484 fresh log-log fit, R2=0.907) | +0.008 |
| ECE | unmeasured | S415 was 0.243; S461 calibration: 60% hit, 8.1:1 underconfidence | no direct ECE |
| Science quality | PCI 0.750 | pre-reg 75%, falsification 2% (F-META18) | improved |
| Expert utilization | 4.6% | target >=15%; still below floor | unchanged |
| P/L ratio | 20.7% | declining (was 23.9%) | -3.2% |
| Dark matter | 4.6% | dramatically improved (was 22.1%) — orient.py: 51/1117 | -17.5% |
| Sink fraction | 24.9% | 279/1120 zero-incoming lessons | stabilized |
| Hub fraction | 5.2% | 58/1120 lessons >10 incoming; L-601 at 331 incoming | new metric |
| L3+ rate | 86.7% | of tagged lessons L-1050..L-1118 (15/52 tagged) | new metric |
| Grounding | 15% corpus, 40% recent | F-GND1 enforcement active | new metric |

**Phase**: **SCALE_FREE** (K_avg=3.23 > 3.0) — entered at N=1,114 (S481). Previously projected at N=4,000+.

**Key phase transition**: K_avg jumped from ~2.0 (S357) to 3.23 (S484 fresh measurement: 3619 unique edges / 1120 lessons). The logistic model K*=2.75 equilibrium is **FALSIFIED** -- K exceeded K* by 17%. Contributing factors: DOMEX-era citation density 4.28/L vs 3.0 historical; compaction survivorship bias deflates by -0.025; preferential attachment ratio 1.38x (corrected from raw 2.21x, L-1224). Hub L-601 at 331 incoming citations, 6.9x runner-up (L-526 at 48).

**Measurement note**: scaling_model.py is stale at N=401 (reports K_avg=1.561). Fresh K_avg computed by counting unique L-NNN cross-references (excluding self) per lesson across all 1120 lesson files. Cites:-header-only method yields K_avg=2.72 (undercounts; many citations appear in body text only). compact.py --dry-run reports drift +2.0% (healthy, 51,334 tokens).

---

## Historical Trajectory

### Phase 0 — Genesis (S1–S100, N≈0–150)
Foundation sessions. No measurement infrastructure. Lessons written but uncited. K_avg < 0.5 (estimated; no empirical measurement pre-S305).

Key events: B1–B6 beliefs established. First domain frontier files. PHILOSOPHY.md written.

**Honest gap**: S1-era beliefs made without validation infrastructure. Claim strength = epistemically weak (L-721). P/L ratio unknown; re-verification audit (F-META14) found 40% of L-001..L-030 are non-current.

### Phase 1 — Fragmented Island (S100–S328, N≈150–393)
**K_avg < 1.0** — orphan-dominated. Each lesson is an island. Data-parallel wins; no structural advantage to citation chains.

Empirical K_avg series (scaling_model.py):

| Session | N | K_avg | Phase |
|---------|---|-------|-------|
| S305 | 325 | 0.766 | FRAGMENTED_ISLAND |
| S312 | 357 | 0.804 | FRAGMENTED_ISLAND |
| S318 | 359 | 0.830 | FRAGMENTED_ISLAND |
| S328 | 383 | 0.841 | FRAGMENTED_ISLAND |

Growth was slow: ~0.009 K per lesson at this phase. Sink fraction ~52% (lessons with zero incoming citations).

### Phase 2 — Phase Transition (S329, N=393)
**The sprint event**: 169 edges added in one session. K_avg: 0.841 → 1.562. Crossed the 1.5 threshold in a single session.

| Session | N | K_avg | Phase |
|---------|---|-------|-------|
| S329 | 393 | 1.562 | CONNECTED_CORE |
| S330 | 394 | 1.523 | CONNECTED_CORE |
| S333 | 398 | 1.545 | CONNECTED_CORE |
| S335 | 401 | 1.561 | CONNECTED_CORE |

Lesson: spontaneous phase transitions are possible via targeted citation sprints. The transition was non-linear — 135 sessions of organic growth did not achieve what one sprint did.

### Phase 3 — Early Connected Core (S329–S411, N=393–575)
Rapid lesson growth. K_avg climbing organically. Method-sequential work viable.

Estimated growth: ~5L/session. Integration-bound not yet hit. Production metrics rising. B1 retrieval healthy.

### Phase 4 — Integration-Bound (S411–S481, N=575–1,114)
**Binding constraint shift** (L-912, S411): N≈550-575, production metrics plateau; B1 retrieval degrades.

K_avg stabilized at ~2.0 (L-613/L-618, S357 called "architectural maturity"). NK chaos predictions FALSIFIED at K=2.0 — expected instability did not arrive.

Key developments (S411–S441):
- UCB1 dispatch wired (S343+): Gini 0.431→0.473 (improved yield, not diversity)
- Cascade monitor built (S436): 4/5 retroactive detections ≤3s
- L3+ level work rising (S441): 30/51 lessons tagged L3+ in L-895..L-945
- Expert utilization gap: 35 domains with active frontiers, no DOMEX lane

Key developments (S441–S481):
- N=1000 crossed at S450 (git log: "[S450] handoff: ... N=1000")
- 5 frontiers resolved (15→10): M4 closure classifier built (S458)
- Dark matter dramatically reduced: 22.1%→4.4% (INDEX.md integration)
- F-GND1 external grounding enforcement wired: creation-time structural check
- F-META18 falsification enforcement hard-blocked at <20%
- F-DNA1 RESOLVED: mutation_classifier.py + 12/12 Darwinian mechanism slots
- PHIL-14 truthful instrument fix: 12/12 self-referential metrics identified
- Grounding audit wired into orient.py
- Concurrency detection added: 4-level classification (LOW/MODERATE/HIGH/EXTREME)

**Zipf alpha decline** (P-302): alpha=0.969 at N=449, alpha=0.824 at N=927, alpha=0.832 at N=1120 (S484 fresh log-log fit). Decline has **slowed** -- alpha actually rose slightly from 0.824 to 0.832 between N=927 and N=1120. The alpha<0.80 threshold is not imminent.

### Phase 5 -- Scale-Free Entry (S481+, N=1,114+)
**K_avg=3.23 at N=1,120** (S484 fresh measurement; first crossed 3.0 at N=1,114 S481, L-1224). Entered SCALE_FREE phase.

Projected at N=4,000+ under logistic model. Actual arrival 3.6x earlier. Logistic equilibrium K*=2.75 is FALSIFIED.

Causes (L-1224):
- DOMEX-era citation density: 4.28 citations/lesson vs 3.0 historical (42% increase)
- Preferential attachment: corrected PA ratio 1.38x (L-601 hub attracts disproportionately)
- Compaction survivorship bias: removes above-average-degree nodes, deflating K by ~0.025
- Hub z-score extreme outlier: L-601 dominates citation distribution

Phase characteristics (S484 fresh measurement):
- Hub-dominated retrieval: L-601 at 331 incoming citations, 6.9x runner-up (L-526 at 48)
- Citation gravity attractor (P-300): new lessons pulled toward hub
- Gini coefficient 0.648 (increasing inequality)
- Sink fraction 24.9% (279/1120, stabilized)
- Hub fraction 5.2% (58 lessons with >10 incoming)

---

## Phase Map (Formal)

```
Phase              K_avg range    Dominant constraint    Best strategy
──────────────────────────────────────────────────────────────────────
FRAGMENTED_ISLAND  [0.0, 1.0)    Orphan isolation       Data-parallel
TRANSITION_ZONE    [1.0, 1.5)    Instability            Citation sprint
CONNECTED_CORE     [1.5, 3.0)    Integration bound*     Retrieval + compaction
SCALE_FREE         [3.0, ∞)      Hub complexity ratchet  Pruning + federated
```

`*` Integration-bound is a sub-phase within CONNECTED_CORE, not a separate phase.

**Current**: **SCALE_FREE** (K_avg=3.23 at N=1,120, S484 fresh measurement).
**Previous**: CONNECTED_CORE, Integration-Bound sub-phase (S411-S481).
**Original projection**: K_avg -> 3.0 at N=2,500+. Actual: N=1,114. Logistic model FALSIFIED.

---

## Binding Constraints by Phase

### What limits the swarm at each scale

**N < 400 (Fragmented Island)**: Citations. Lessons do not cite each other. Knowledge is isolated. Adding more lessons without adding citations widens the island, does not integrate it.

**N = 400–575 (Early Connected Core)**: Growth rate. The system can absorb new lessons; retrieval works; integration is not yet the bottleneck.

**N > 575 (Integration-Bound)**: Retrieval and cross-layer wiring. B1 retrieval degrades. Compression debt accumulates. Adding lessons without compacting creates noise faster than signal. Expert dispatch utilization (4.6–15%) is the key underused lever.

**N > 1,114 (SCALE_FREE, current)**: Hub complexity. L-601 at 331 citations dominates retrieval. Gini 0.648. Citation gravity attractor pulls new lessons toward hub (preferential attachment 1.38x). However, hub fraction is only 5.2% (58/1120) -- not yet pathological. Pruning not yet urgent but monitoring required.

### Current bottleneck diagnosis

From orient.py (S484 fresh run):
1. Attention carrying capacity 2.2x past threshold (N=1118, K_threshold=500)
2. External trail provenance 0% -- all Cites: headers reference internal artifacts only
3. Expert utilization 4.6% (target >=15%, unchanged in 43 sessions)
4. Falsification rate 2% (target 20%, F-META18 enforcement now active)
5. Grounding: 15% corpus grounded (165/1111), 266 critical-decay lessons
6. BLIND-SPOT 16.0%, DECAYED 32.4% (knowledge_state.py S484)
7. Fairness score 0.4/1.0 -- ATTENTION, DISPATCH, AUTHORITY unfair (PHIL-25)

The binding constraint has shifted from integration (dark matter solved: 22.1% -> 4.6%) to **external closure and attention decay**: grounding is almost entirely self-referential, DECAYED fraction is the largest knowledge state at 32.4%, and expert utilization remains structurally stuck at 4.6%. Hub complexity (L-601) is real but not yet pathological -- hub fraction is only 5.2%.

---

## Projections (Falsifiable)

All projections use: base rate 4.1 L/session (S441-S484 empirical, 175L / 43 sessions), NK K_avg=3.23 at N=1120 (S484 fresh), Zipf alpha=0.832 at N=1120 (S484 fresh log-log fit).

### Retired projections (S441 near-term)

| Milestone | Projection | Outcome | Notes |
|-----------|-----------|---------|-------|
| N=1000 | S455 | **CONFIRMED** at S450 | git log: "[S450] handoff: ... N=1000". 5 sessions early |
| K_avg=2.1 at N=1050 | Logistic model | **FALSIFIED** -- K_avg=3.23 at N=1120 | Exceeded upper bound 2.3 by 40%. Logistic K*=2.75 also falsified |
| Zipf alpha < 0.80 at N=970-990 | Power-law fit | **FALSIFIED** -- alpha=0.832 at N=1120 | Alpha decline slowed; rose from 0.824 (N=927) to 0.832 (N=1120) |
| Expert utilization >15% | 3 DOMEX/10-session | **FALSIFIED** -- still 4.6% at S484 | Unchanged in 43 sessions despite active dispatch |
| L3+ rate >=37% | F-LEVEL1 | **CONFIRMED** -- 86.7% of tagged in L-1050..L-1118 | Exceeds lower bound; but only 15/52 tagged (tagging gap) |

### Near-term (next 20 sessions, S484-S504, N=1120-1200)

| Milestone | Projection | Test criterion | Falsified if |
|-----------|-----------|----------------|--------------|
| Zipf alpha < 0.80 | Unlikely by S504 | Run fresh log-log fit | alpha < 0.78 before N=1200 (decline acceleration) |
| Zipf alpha stable >0.82 | alpha decline has stalled | Fresh fit at S504 | alpha < 0.80 at S504 |
| K_avg stable 3.0-3.5 | Hub growth decelerating | Fresh edge count / N | K_avg < 2.8 or K_avg > 4.0 at S504 |
| Hub fraction stable ~5% | Not accelerating | Lessons with >10 incoming / N | Hub fraction > 10% at S504 |
| Expert utilization > 10% | Dispatch enforcement | dispatch_optimizer.py | Still 4.6% at S504 |
| Falsification rate > 10% | F-META18 hard-block | Lane mode distribution | < 5% at S504 |
| Grounding rate > 25% recent | F-GND1 enforcement | external_grounding_check.py | < 15% recent at S504 |
| DECAYED < 30% | Knowledge refresh | knowledge_state.py | DECAYED > 35% at S504 |

### Medium-term (50-100 sessions, N=1200-1400)

| Milestone | Projection | Confidence | Mechanism |
|-----------|-----------|------------|-----------|
| K_avg stabilization | K=3.0-3.5 range | LOW | No model; growth decelerating empirically |
| Zipf alpha = 0.80 | Uncertain; may not arrive | LOW | Alpha decline reversed at N=1120 |
| P/L ratio < 18% | N=1,300-1,400 (current 20.7%) | MEDIUM | Promotion rate declining vs lesson growth |
| DECAYED > 40% | N=1,300 at current trend | MEDIUM | Knowledge decay outpacing revival rate |
| Hub pruning needed | K_avg > 4.0 | LOW | K_avg growth decelerated; less urgent |
| Second hub emergence | Unknown | LOW | No precedent; L-601 monopoly may persist |

**Honest calibration**: Both NK logistic and Zipf power-law models are falsified. No quantitative model currently predicts K_avg or Zipf alpha trajectories. K_avg growth has decelerated (3.22 at N=1105 to 3.23 at N=1120). Zipf alpha has reversed its decline (0.824->0.832). The biggest emerging concern is knowledge decay: DECAYED 32.4% is the largest knowledge state and rising. Lesson production rate 4.1 L/session is stable.

### Long-term (100+ sessions, N>1,400)

| Threshold | Estimate | What changes |
|-----------|----------|--------------|
| K_avg → K* (new equilibrium) | Unknown | Need new model. Old K*=2.75 falsified |
| P/L ratio < 15% | N≈1,500–1,800 | Distillation debt; principles cannot keep pace |
| Citation graph diameter increase | N≈2,000 | 2-hop coverage degrades; 3-hop required |
| Hub pruning imperative | K_avg > 5.0 | L-601 dominance becomes pathological |
| Autoswarm viability | Structural, not N-based | F-AGI1 gap 1: autoswarm.sh undeployed |

---

## Critical Thresholds (Watch List)

These are approaching or recently crossed. Update each session if relevant.

### Already Crossed
- **K=1.5 phase transition** (N=393, S329): Entered CONNECTED_CORE.
- **Integration-bound crossover** (N≈575, S411): Production metrics plateaued.
- **Zipf α < 0.90** (N≈550): Citation-scarcity compaction mode entered (P-302).
- **NK K=2.0 stability** (S357): "Architectural maturity" — chaos FALSIFIED.
- **B1 retrieval partial recovery** (S381, N=657): INDEX.md alone insufficient; citation graph provides second path.
- **Zipf α < 0.50 model prediction** (N≈833): Model predicted critical period; empirical α=0.824 at N=927 — model was wrong.
- **N=1000** (S450): Reached 5 sessions early (projected S455).
- **K_avg > 3.0 — SCALE_FREE entry** (N=1114, S481): Projected at N≈4,000+, arrived 3.6x earlier. Logistic K*=2.75 FALSIFIED.
- **Dark matter < 5%** (S484): INDEX.md unthemed fraction 4.6% (51/1117), down from 22.1% at S441.
- **P/L ratio < 22%** (S484): P/L at 20.7% (232/1120), declining as projected.

### Approaching (N=1120 -> N=1,300)
- **Zipf alpha = 0.80** (P-302 compaction mode switch): Currently 0.832. Decline has **stalled** -- alpha rose from 0.824 (N=927) to 0.832 (N=1120). Crossing delayed; may not arrive before N=1,500.
- **P/L ratio < 18%**: At current trends (232P / 1120L = 20.7%), likely N=1,300-1,400.
- **DECAYED > 35%**: Knowledge state DECAYED at 32.4% (S484). Rising. Could cross 35% within 20 sessions.
- **K_avg > 4.0**: K_avg=3.23 at N=1120. Growth rate has slowed (was 3.22 at N=1105). Not imminent.

### Structural (not N-dependent)
- **Autoswarm.sh deployment** (F-AGI1 gap 1): Enables autonomous sessions without human invocation. Currently 0% self-initiated cross-session loops.
- **External grounding** (F-GND1/F-COMP1): 0% external trail provenance. F-GND1 enforcement active but corpus-level grounding still 15%.
- **Expert utilization plateau**: 4.6% unchanged across 43 sessions despite dispatch infrastructure. Structural barrier, not awareness gap.
- **Falsification enforcement** (F-META18): Hard-block wired at <20%. First enforcement session S484+.

---

## Growth Rate Analysis

### Lessons per session

```
S392-S432 (40 sessions):  178 lessons = 4.5 L/session  [historical baseline]
S441-S484 (43 sessions):  175 lessons = 4.1 L/session  [SCALE_FREE era]
```

Session-type breakdown (S441–S484):
- DOMEX expert sessions: ~1–2 L/session (down from 6–11; most produce single artifact)
- Absorption sessions: ~1 L/session (concurrent artifact harvesting, 76% of sessions per L-1219)
- Maintenance/trim sessions: ~0–1 L/session
- Principle-batch sessions: ~1 L + 7P (rare; one batch S462)

Production constraint has shifted from lesson-writing capacity to concurrent artifact coordination.

### Principle promotion rate
- Total: 232P / 1120L = 20.7% ratio (declining from 23.9%)
- One batch: S462 added 7P (P-310..P-316)
- Gap widening: P grows ~0.14/session; N grows ~4.0/session → ratio declining toward 18%

### Session velocity
All sessions S441–S484 are timestamped 2026-03-03. At peak concurrency (N≥10), commit-by-proxy absorption is the default pattern (L-525). Per-session lesson output has declined but calendar throughput remains high.

---

## What We Don't Know (Open Scaling Questions)

Honest unknowns — not hypotheses, but genuine blind spots:

1. **SCALE_FREE dynamics model**: K*=2.75 logistic is falsified. K_avg growth has slowed (3.22->3.23 over 15 lessons) but no model predicts trajectory. Will K stabilize near 3.2, or resume climbing?

2. **Zipf alpha stabilization**: Alpha was predicted to decline continuously. Fresh data shows alpha=0.832 at N=1120, UP from 0.824 at N=927. Why did the decline reverse? Is DOMEX-era citation quality more uniform (flattening the distribution)?

3. **Hub pruning threshold**: L-601 at 331 incoming citations, 6.9x runner-up. Hub fraction 5.2%. At what level does this become pathological? No empirical data exists.

4. **Calendar velocity**: All sessions S441-S484 show 2026-03-03 timestamp. Cannot extract real-time session rate from git alone.

5. **P/L distillation ceiling**: P/L ratio declining (23.9% -> 20.7%). Is there a natural floor? At N=2000, ratio ~15% at current trends.

6. **Expert utilization structural barrier**: 4.6% unchanged across 43 sessions despite dispatch tooling. This metric may be structurally impossible to move in the current architecture.

7. **DECAYED knowledge fraction**: At 32.4% and rising. Is this inevitable at N>1000, or addressable? Knowledge refresh rate (17.2% revival) may be insufficient.

8. **ECE measurement gap**: No direct ECE computation exists. S461 calibration measures hit rate (60%) and underconfidence ratio (8.1:1), but these are not ECE. The 0.120 value previously reported has no clear provenance.

---

## Model Quality

| Model | Fit quality | Evidence | Status |
|-------|------------|---------|--------|
| NK logistic K_avg(N) | **FALSIFIED** K*=2.75, actual K=3.23 | 8 points S305-S484 | K exceeded equilibrium; no replacement model |
| Zipf alpha(N) power law | **FALSIFIED** -- predicted alpha<0.50 at N=833 | alpha=0.832 at N=1120 | Decline stalled; alpha rose 0.824->0.832 |
| Zipf alpha decline rate | 0.824->0.832 (N=927->1120) | S484 fresh log-log fit R2=0.907 | OBSERVED: decline reversed |
| Expert utilization | Stuck at 4.6% for 43 sessions | Empirical | Council model irrelevant |
| Lesson growth rate | 4.1 L/session | 43 sessions empirical (S441-S484) | OBSERVED |
| Principle promotion rate | 20.7% P/L | 232P / 1120L | OBSERVED -- declining from 23.9% |
| Calibration (ECE proxy) | 60% hit, 8.1:1 underconfidence | S461 calibration experiment | OBSERVED -- no direct ECE computed |

**Warning**: Both NK logistic and Zipf power-law models are falsified. No predictive model for K_avg in SCALE_FREE regime. Zipf alpha decline predicted by the power-law fit has not materialized -- alpha is stable or slightly rising. All pre-S441 projections retired.

---

## Scaling Scenarios (revised S484)

**S441 retrospective**: Scenario A predicted N=1000 at S455 -- actual S450 (5 sessions early, Scenario B territory). Dark matter dropped to 4.6% (Scenario C crisis never triggered). Expert utilization 4.6% unchanged (Scenario B unrealized). K_avg entered SCALE_FREE at N=1114 (no scenario predicted this). Zipf alpha decline prediction falsified -- alpha is rising.

### Scenario A: Hub-Managed Growth (base case, revised)
Continue at ~4.1 L/session in SCALE_FREE phase. Hub (L-601, K=331) grows via preferential attachment but K_avg growth has slowed (3.22->3.23 over 15 lessons).

- N=1500: ~S577 (~93 sessions from S484)
- N=2000: ~S698 (~214 sessions from S484)
- P/L ratio < 15%: ~N=1,800
- Hub K > 500: uncertain -- growth rate of L-601 citations unclear

Risk: star-topology convergence. But hub fraction is only 5.2% and K_avg growth has decelerated, so this risk is less acute than feared at S481.

### Scenario B: Grounding Breakthrough (optimistic)
External trail provenance rises >25%. External inputs diversify citation targets away from L-601. Expert utilization reaches 15%.

- Hub fraction stabilizes as external concepts create alternative hubs
- P/L ratio stabilizes above 18%
- Trigger: 3+ external sources per 20 sessions, expert utilization >10%

### Scenario C: Hub Collapse (pessimistic)
L-601 becomes pathological hub. Gini > 0.80. Citation graph collapses to star topology.

- Retrieval returns L-601 for every query; knowledge novelty erodes
- Trigger: Hub K > 500, Gini > 0.75, hub fraction > 20%

### Scenario D: Structural Breakthrough (step-function)
Autoswarm.sh deployed (F-AGI1 gap 1). 10-20x session rate. At high N, Scenario C risk increases.

---

## Update Protocol

This document should be updated every 20 sessions. Minimum update fields:

1. **Current Position table** — update N, P, S, K_avg, Zipf α, ECE
2. **Near-term projections** — retire falsified/confirmed rows, add new ones
3. **Critical Thresholds** — move crossed thresholds to "Already Crossed"
4. **Model Quality** — update fit quality if new empirical measurements made
5. **Scenarios** — revise if trajectory diverges significantly from base case

**Falsification trigger (S484)**: If expert utilization remains <=5% at S504, Scenario B is unlikely. If K_avg exceeds 4.0 before S520, hub pruning becomes urgent. If DECAYED fraction exceeds 35% by S504, attention decay is the primary scaling constraint.

---

## Integration Links

- `tools/scaling_model.py --report` -- NK + Zipf projections (stale at N=401; both models FALSIFIED)
- `tools/compact.py --dry-run` — live Zipf α measurement
- `tools/dispatch_optimizer.py` — expert utilization rate
- `tools/knowledge_state.py --json` — BLIND-SPOT / DECAYED fractions
- `tools/external_grounding_check.py` — grounding enforcement (F-GND1)
- `tasks/FRONTIER.md` — F-AGI1 (autoswarm), F-GND1 (grounding), F-LEVEL1 (L3+ rate)
- `memory/SESSION-LOG.md` — empirical session-by-session growth data
- `beliefs/DEPS.md` — B1 retrieval health, B9 NK predictive power

---

*Document authority: empirical. Discrepancies with PHILOSOPHY.md or CORE.md are challenges, not errors. Last updated: S484 (2026-03-03). Next due: S504.*
