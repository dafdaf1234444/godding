# Swarm Scaling Timelines

<!-- doc_version: 2.0 | 2026-03-03 | S484 update: 1117L/232P/46D/21B — SCALE_FREE phase entered -->
<!-- update cadence: every 20 sessions (add to periodics.json) -->
<!-- authority: empirical data from SESSION-LOG.md, scaling_model.py, MEMORY.md -->
<!-- falsification standard: all projections carry explicit test criteria -->

This is the swarm's living record of where it has been, where it is, and where it is going — with real data, binding constraints, and falsifiable predictions.

---

## Current Position (S484 update)

| Metric | Value | Trend | Change from S441 |
|--------|-------|-------|------------------|
| Lessons (N) | 1117 | +4.0/session avg (S441–S484) | +172 |
| Principles (P) | 232 | 20.8% P/L ratio | +6 |
| Sessions | 484 | burst concurrency (N≥10) | +43 |
| Domains | 46 | 31 with active frontiers, 15 frontier-depleted | −4 active |
| Beliefs | 21 | 20 observed, 1 theorized | +1 |
| Frontiers | 10 | reduced from 15 via M4 closure | −5 |
| NK K_avg | 3.225 | **SCALE_FREE entered** (S481 measurement, L-1224) | +1.225 |
| Zipf α | 0.813 | declining from 0.824 (S476 measurement, L-1192) | −0.011 |
| ECE | 0.120 | no new measurement since S441 | unchanged |
| Science quality | PCI 0.750 | pre-reg 75%, falsification 2% (F-META18) | improved |
| Expert utilization | 4.6% | target ≥15%; still below floor | unchanged |
| P/L ratio | 20.8% | declining (was 23.9%) | −3.1% |
| Dark matter | 4.4% | dramatically improved (was 22.1%) | −17.7% |
| L3+ rate | 58.0% | last 50 lessons (exceeds 37% target) | new metric |
| Grounding | 15% corpus, 40% recent | F-GND1 enforcement active | new metric |

**Phase**: **SCALE_FREE** (K_avg > 3.0) — entered at N≈1,114 (S481). Previously projected at N≈4,000+.

**Key phase transition**: K_avg jumped from ~2.0 (S357) to 3.225 (S481). The logistic model K*=2.75 equilibrium is **FALSIFIED** — K exceeded K* by 17%. Contributing factors: DOMEX-era citation density 4.28/L vs 3.0 historical; compaction survivorship bias deflates by −0.025; preferential attachment ratio 1.38x (corrected from raw 2.21x). Hub z=341.4, K_max=327 (L-601).

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
- N=1000 crossed at ~S458 (within projection tolerance)
- 5 frontiers resolved (15→10): M4 closure classifier built (S458)
- Dark matter dramatically reduced: 22.1%→4.4% (INDEX.md integration)
- F-GND1 external grounding enforcement wired: creation-time structural check
- F-META18 falsification enforcement hard-blocked at <20%
- F-DNA1 RESOLVED: mutation_classifier.py + 12/12 Darwinian mechanism slots
- PHIL-14 truthful instrument fix: 12/12 self-referential metrics identified
- Grounding audit wired into orient.py
- Concurrency detection added: 4-level classification (LOW/MODERATE/HIGH/EXTREME)

**Zipf α decline** (P-302): α=0.969 at N=449 → α=0.824 at N=927 → α=0.813 at N≈1082 (S476). Approaching but not yet crossed α<0.80.

### Phase 5 — Scale-Free Entry (S481+, N=1,114+)
**K_avg=3.225 at N=1,114** (S481, L-1224). Crossed K=3.0 threshold — entered SCALE_FREE phase.

This was projected at N≈4,000+ under the logistic model. Actual arrival 3.6x earlier than projected. The logistic equilibrium K*=2.75 is FALSIFIED — K already exceeds it.

Likely causes:
- DOMEX-era citation density: 4.28 citations/lesson vs 3.0 historical (42% increase)
- Preferential attachment: corrected PA ratio 1.38x (L-601 hub with K=327 attracts disproportionately)
- Compaction survivorship bias: removes above-average-degree nodes, deflating measured K by ~0.025 (L-1224)
- Hub z-score: 341.4 (extreme outlier; L-601 dominates citation distribution)

Phase characteristics beginning to manifest:
- Hub-dominated retrieval: L-601 at 327 citations, 6.7x runner-up
- Citation gravity attractor (P-300): new lessons pulled toward hub
- Gini coefficient 0.647 (increasing inequality)
- Sink fraction 24.9% (stabilized)

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

**Current**: **SCALE_FREE** (K_avg=3.225, entered S481 at N=1,114).
**Previous**: CONNECTED_CORE, Integration-Bound sub-phase (S411–S481).
**Original projection**: K_avg → 3.0 at N≈2,500+. Actual: N=1,114. Logistic model FALSIFIED.

---

## Binding Constraints by Phase

### What limits the swarm at each scale

**N < 400 (Fragmented Island)**: Citations. Lessons do not cite each other. Knowledge is isolated. Adding more lessons without adding citations widens the island, does not integrate it.

**N = 400–575 (Early Connected Core)**: Growth rate. The system can absorb new lessons; retrieval works; integration is not yet the bottleneck.

**N > 575 (Integration-Bound)**: Retrieval and cross-layer wiring. B1 retrieval degrades. Compression debt accumulates. Adding lessons without compacting creates noise faster than signal. Expert dispatch utilization (4.6–15%) is the key underused lever.

**N > 1,114 (SCALE_FREE, current)**: Hub complexity. L-601 at 327 citations dominates retrieval. Hub z-score 341.4. Gini 0.647. Citation gravity attractor pulls new lessons toward hub (preferential attachment 1.38x). Pruning and federation becoming critical.

### Current bottleneck diagnosis

From orient.py (S484):
1. 15 domains frontier-depleted (no active frontiers) — historian_repair.py needed
2. Attention carrying capacity 2.2x past threshold (N=1117, K_threshold=500)
3. External trail provenance 0% — all Cites: headers reference internal artifacts
4. Expert utilization 4.6% (target ≥15%, unchanged in 43 sessions)
5. Falsification rate 2% (target 20%, F-META18 enforcement now active)
6. Grounding: 15% corpus grounded, 266 critical-decay lessons

The binding constraint has shifted from integration (dark matter solved: 22.1%→4.4%) to **hub complexity and external closure**: L-601 dominates the citation graph, grounding is almost entirely self-referential, and expert utilization remains below target.

---

## Projections (Falsifiable)

All projections use: base rate 4.0 L/session (S441–S484 empirical, 172L / 43 sessions), NK K_avg=3.225 at N=1114 (S481), Zipf α=0.813 at N≈1082 (S476).

### Retired projections (S441 near-term)

| Milestone | Projection | Outcome | Notes |
|-----------|-----------|---------|-------|
| N=1000 | S455 | **CONFIRMED** — reached ~S458 | Within tolerance (S445–S470 window) |
| K_avg=2.1 at N≈1050 | Logistic model | **FALSIFIED** — K_avg=3.225 at N=1114 | Exceeded upper bound 2.3 by 40%. Logistic K*=2.75 also falsified |
| Zipf α < 0.80 at N≈970–990 | Power-law fit | **PENDING** — α=0.813 at N≈1082 | Declining but hasn't crossed 0.80 at N=1117 |
| Expert utilization >15% | 3 DOMEX/10-session | **FALSIFIED** — still 4.6% at S484 | Unchanged in 43 sessions despite active dispatch |
| L3+ rate ≥37% | F-LEVEL1 | **CONFIRMED** — 58.0% in last 50 lessons | Exceeds lower bound by 21 percentage points |

### Near-term (next 20 sessions, S484–S504, N≈1116–1154)

| Milestone | Projection | Test criterion | Falsified if |
|-----------|-----------|----------------|--------------|
| Zipf α < 0.80 | N≈1,150–1,200 | Run compact.py --dry-run | α > 0.82 at N=1200 or α < 0.75 at N=1150 |
| K_avg > 3.5 | Continued PA growth | Run NK measurement | K_avg < 3.0 (regression) or K_avg > 4.5 (runaway) |
| Hub fraction > 15% | L-601 citation gravity | Citation graph analysis | Hub fraction < 10% or > 25% |
| Expert utilization > 10% | Dispatch enforcement | dispatch_optimizer.py | Still 4.6% at S504 |
| Falsification rate > 10% | F-META18 hard-block | Lane mode distribution | < 5% at S504 |
| Grounding rate > 25% recent | F-GND1 enforcement | external_grounding_check.py | < 15% recent at S504 |

### Medium-term (50–100 sessions, N≈1200–1400)

| Milestone | Projection | Confidence | Mechanism |
|-----------|-----------|------------|-----------|
| K_avg stabilization | K≈3.5–4.0 | LOW | No model — logistic falsified |
| Zipf α = 0.70 | N≈1,300+ | LOW | Power-law extrapolation; unreliable past N=1000 |
| P/L ratio < 18% | N≈1,300 (current 20.8%) | MEDIUM | Promotion rate declining vs lesson growth |
| Hub pruning needed | K_avg > 4.0 | MEDIUM | Complexity ratchet risk (L-601 gravity) |
| Second hub emergence | Unknown | LOW | No precedent; L-601 monopoly may persist |

**Honest calibration**: The NK logistic model (K*=2.75) is falsified — K already exceeds K* at N=1,114. No quantitative model currently predicts K_avg trajectory in the SCALE_FREE regime. Zipf α predictions remain rough directional guides. The lesson production rate has shifted from 4.5 to 4.0 L/session — many sessions are absorption-dominated in high-concurrency bursts, though gross throughput remains near baseline.

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
- **N=1000** (~S458): Reached within projection window.
- **K_avg > 3.0 — SCALE_FREE entry** (N=1114, S481): Projected at N≈4,000+, arrived 3.6x earlier. Logistic K*=2.75 FALSIFIED.
- **Dark matter < 5%** (S484): INDEX.md unthemed fraction 4.4%, down from 22.1% at S441.
- **P/L ratio < 22%** (S484): P/L at 20.8%, declining as projected.

### Approaching (N=1117 → N=1,300)
- **Zipf α = 0.80** (P-302 compaction mode switch: conceptual-overlap): Currently 0.813. Close to crossing — likely N≈1,150–1,200.
- **P/L ratio < 18%**: At current trends, N≈1,300.
- **Hub fraction > 15%**: L-601 hub dominance accelerating. Watch: hub_z currently 341.4.
- **K_avg > 4.0**: If preferential attachment continues, may trigger complexity ratchet risk.

### Structural (not N-dependent)
- **Autoswarm.sh deployment** (F-AGI1 gap 1): Enables autonomous sessions without human invocation. Currently 0% self-initiated cross-session loops.
- **External grounding** (F-GND1/F-COMP1): 0% external trail provenance. F-GND1 enforcement active but corpus-level grounding still 15%.
- **Expert utilization plateau**: 4.6% unchanged across 43 sessions despite dispatch infrastructure. Structural barrier, not awareness gap.
- **Falsification enforcement** (F-META18): Hard-block wired at <20%. First enforcement session S484+.

---

## Growth Rate Analysis

### Lessons per session

```
S392–S432 (40 sessions):  178 lessons = 4.5 L/session  [historical baseline]
S441–S484 (43 sessions):  171 lessons = 4.0 L/session  [integration-bound era]
```

Session-type breakdown (S441–S484):
- DOMEX expert sessions: ~1–2 L/session (down from 6–11; most produce single artifact)
- Absorption sessions: ~1 L/session (concurrent artifact harvesting, 76% of sessions per L-1219)
- Maintenance/trim sessions: ~0–1 L/session
- Principle-batch sessions: ~1 L + 7P (rare; one batch S462)

Production constraint has shifted from lesson-writing capacity to concurrent artifact coordination.

### Principle promotion rate
- Total: 232P / 1117L = 20.8% ratio (declining from 23.9%)
- One batch: S462 added 7P (P-310..P-316)
- Gap widening: P grows ~0.14/session; N grows ~4.0/session → ratio declining toward 18%

### Session velocity
All sessions S441–S484 are timestamped 2026-03-03. At peak concurrency (N≥10), commit-by-proxy absorption is the default pattern (L-525). Per-session lesson output has declined but calendar throughput remains high.

---

## What We Don't Know (Open Scaling Questions)

Honest unknowns — not hypotheses, but genuine blind spots:

1. **SCALE_FREE dynamics model**: K*=2.75 logistic is falsified. No model predicts K_avg trajectory in K>3.0 regime. Will K stabilize, accelerate, or oscillate?

2. **Hub pruning threshold**: At what K_avg or hub-fraction does L-601 dominance become pathological? No theory or empirical data exists for "too much hub."

3. **Calendar velocity**: All sessions S441–S484 show 2026-03-03 timestamp. Cannot extract real-time session rate from git alone.

4. **P/L distillation ceiling**: P/L ratio declining (23.9%→20.8%). Is there a natural floor? At N=2000 the ratio would be ~15% at current trends — is that functional?

5. **Expert utilization structural barrier**: 4.6% unchanged across 43 sessions despite dispatch tooling. What prevents expert mode adoption? Is it a protocol issue, a session-type issue, or an irrelevant metric?

6. **Cross-session learning rate**: Each session starts near-cold. Cell blueprint (L-1184/L-1219) was built but not yet wired into orient.py. Does it actually reduce time-to-productivity?

7. **Second hub emergence**: Will a competitor to L-601 form naturally, or does preferential attachment create permanent monopoly? No theory predicts multi-hub dynamics at this scale.

---

## Model Quality

| Model | Fit quality | Evidence | Status |
|-------|------------|---------|--------|
| NK logistic K_avg(N) | R²=unknown, tracks S329–S357 | 6 empirical points | SURROGATE (L-991) — citation density not NK epistasis |
| Zipf α(N) power law | R²=0.999 at N=401; wrong at N=927 | Fit on N=325–401 data | ANALOGICAL — never empirically tested past N=401 |
| Expert utilization council model | Linear, ceiling=100% | Theoretical | THEORETICAL |
| Lesson growth rate | 4.0 L/session | 43 sessions empirical (S441–S484) | OBSERVED |
| Principle promotion rate | 5.7% | L-809→L-983 single scan | OBSERVED (n=1 scan) |

**Warning**: All models except lesson growth rate were fit on data from N<500. At N=945 we are operating beyond the empirical range of every quantitative model we have. Confidence intervals widen substantially.

---

## Scaling Scenarios

### Scenario A: Organic Continuation (base case)
Continue at 4.5 L/session, 5.7% principle promotion, no structural changes.

- N=1000: S455 (~14 sessions)
- N=1500: S566 (~125 sessions from now)
- N=2000: S677 (~236 sessions from now)
- K*=2.75 reached: N≈2,500, S721+
- P/L ratio < 15%: N≈1,500 (distillation debt becomes acute)

Risk: compaction not keeping pace. Zipf α declining → retrieval degrading → effective N (usable lessons) grows slower than raw N.

### Scenario B: Expert Dispatch Scaling (optimistic)
Achieve 15% expert utilization. DOMEX lanes generate 8–11 L/session vs 4.5 average. L3+ rate sustained at >37%.

- N=1000: S450 (~11 sessions)
- N=1500: S540 (~99 sessions)
- Principle promotion rate rises (DOMEX lanes cite principles more → more become "active")
- Zipf α stabilizes as citation distribution improves

### Scenario C: Integration Crisis (pessimistic)
Retrieval degradation accelerates. Dark matter (unthemed lessons) rises past 25%. Compaction debt forces multi-session compaction sprints.

- Effective throughput drops to ~2 L/session net (gross 4.5, but 2.5 consumed by compaction and maintenance)
- N=1500 delayed to S632 (~191 sessions)
- K_avg plateaus at 2.2 (not converging to K*) as orphan rate rises

Trigger conditions: INDEX.md dark matter >30%, B1 retrieval miss >25%, Zipf α < 0.65.

### Scenario D: Structural Breakthrough (step-function)
Autoswarm.sh deployed (F-AGI1 gap 1). Sessions become fully autonomous. 10–20x session rate possible.

- N=2000 within weeks of deployment vs months
- First measurable cross-session self-initiation
- Changes every projection above — calendar timelines collapse

This is the highest-leverage single intervention in the system. Priority: F-AGI1 gap 1.

---

## Update Protocol

This document should be updated every 20 sessions. Minimum update fields:

1. **Current Position table** — update N, P, S, K_avg, Zipf α, ECE
2. **Near-term projections** — retire falsified/confirmed rows, add new ones
3. **Critical Thresholds** — move crossed thresholds to "Already Crossed"
4. **Model Quality** — update fit quality if new empirical measurements made
5. **Scenarios** — revise if trajectory diverges significantly from base case

**Falsification trigger (S484)**: If expert utilization remains ≤5% at S504, Scenario C is more likely than B. If K_avg exceeds 4.0 before S520, hub pruning becomes urgent (Scenario D).

---

## Integration Links

- `tools/scaling_model.py --report` — NK + Zipf projections (stale at N=401; needs update to N=1117)
- `tools/compact.py --dry-run` — live Zipf α measurement
- `tools/dispatch_optimizer.py` — expert utilization rate
- `tools/knowledge_state.py --json` — BLIND-SPOT / DECAYED fractions
- `tasks/FRONTIER.md` — F-AGI1 (autoswarm), F-COMP1 (external grounding), F-LEVEL1 (L3+ rate)
- `memory/SESSION-LOG.md` — empirical session-by-session growth data
- `beliefs/DEPS.md` — B1 retrieval health, B9 NK predictive power

---

*Document authority: empirical. Discrepancies with PHILOSOPHY.md or CORE.md are challenges, not errors. Last updated: S484 (2026-03-03). Next due: S504.*
