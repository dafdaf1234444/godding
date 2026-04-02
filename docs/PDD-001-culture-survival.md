# PDD-001: Culture Survival Dynamics

**Pre-registered Design Document**
**Filed**: 2026-04-02
**Status**: PRE-REGISTERED (no data collected yet)
**Falsification deadline**: 2026-07-02 (90 days)

---

## 1. Research question

Which structural properties predict whether a self-organizing community survives internal degenerative dynamics (bad cultures, parasitic sub-groups, self-destructive feedback loops)?

## 2. Prior work & motivation

- F-COL1 (L-1587): mediocrity selects mediocrity — degenerative spiral identified but not quantified across community types.
- Justice mechanism (PHIL-29): visibility + consequence as correction. Untested whether this actually prevents collapse.
- Multi-swarm merge (F-MERGE1): boundary recognition exists but no data on rejection accuracy.
- External: Ostrom's 8 principles for commons governance, Dunbar scaling, Axelrod tournament results.

## 3. Hypotheses (pre-registered)

| ID | Hypothesis | Metric | Falsified if |
|----|-----------|--------|-------------|
| H1 | Communities with correction-channel preservation survive 2x longer than those without | Median lifespan ratio | Ratio < 1.3x at p < 0.05 |
| H2 | Distributed-seed communities (redundancy > 3) recover from total-leader-loss within 2 cycles | Recovery time in cycles | Recovery > 5 cycles in >50% of runs |
| H3 | Parasitic sub-groups below 15% of population are self-limiting; above 15% they dominate | Parasite fraction at equilibrium | No phase transition detectable in [5%, 30%] range |
| H4 | Immune-system (detect+respond) beats wall (exclude all) by >40% on survival-under-attack | Survival rate under adversarial injection | Difference < 20% |
| H5 | Pre-mortem cultures (state failure mode before acting) have <50% the catastrophic failure rate | Catastrophic failure count | Pre-mortem >= 75% of control failure rate |

## 4. Method

### 4.1 Model

Agent-based simulation. Each agent has:
- **Strategy**: cooperate / defect / conditional / parasitic / correction-signal
- **Memory**: last N interactions
- **Reproduction**: proportional to accumulated payoff (modified replicator dynamics)
- **Mutation**: strategy flip with probability p_mut = 0.01

Community has:
- **Correction channel**: boolean. When ON, agents can signal "this interaction was harmful" and the community updates reputation scores. When OFF, no reputation mechanism.
- **Seed count**: number of independent sub-communities that can restart if main collapses.
- **Boundary policy**: WALL (reject all outsiders) vs IMMUNE (admit, monitor, expel if harmful).

### 4.2 Experimental design

| Parameter | Values | Total conditions |
|-----------|--------|-----------------|
| Correction channel | ON / OFF | 2 |
| Seed count | 1, 3, 7 | 3 |
| Boundary policy | WALL / IMMUNE | 2 |
| Parasite injection rate | 0%, 5%, 15%, 30% | 4 |
| Pre-mortem enabled | YES / NO | 2 |
| **Total** | | **96 conditions** |

- 100 runs per condition = 9,600 simulations
- 500 time-steps per run
- Measured: survival (binary at t=500), time-to-collapse, recovery count, final cooperation rate

### 4.3 Analysis plan

1. Logistic regression: survival ~ correction + seeds + boundary + parasites + premortem + interactions
2. Cox proportional hazards for time-to-collapse
3. Phase transition detection: sweep parasite fraction in [0.01, 0.50], find critical threshold via order parameter (cooperation rate)
4. Effect sizes with 95% CI for each hypothesis

### 4.4 What we will NOT do (scope lock)

- No evolutionary parameter tuning after seeing results
- No post-hoc hypotheses added to this document
- No removal of conditions that "didn't work"
- Exploratory analysis labeled EXPLORATORY in results, not mixed with confirmatory

## 5. Expected outcomes (point predictions)

Before running, we predict:
- H1 ratio: **2.3x** (correction channel roughly doubles + extra from indirect effects)
- H2 recovery: **1.8 cycles** for seed=7
- H3 phase transition: **~18%** parasite fraction
- H4 immune advantage: **+55%** survival
- H5 pre-mortem reduction: **62%** fewer catastrophic failures

These numbers are logged here so we can score our calibration afterward.

## 6. Implementation

```
python3 tools/culture_survival_sim.py --conditions all --runs 100 --steps 500
```

Output: `results/PDD-001/` with per-condition CSVs and summary statistics.

## 7. Success criteria

- At least 3 of 5 hypotheses confirmed (not falsified) = model has predictive power
- 2 or fewer confirmed = model needs fundamental revision, publish the negatives
- Calibration score: mean |predicted - actual| across point predictions. Target: < 30% relative error.

## 8. Credibility checklist

- [x] Pre-registered before data collection
- [x] Falsification criteria explicit
- [x] Point predictions logged
- [x] Analysis plan locked
- [x] Scope lock documented
- [ ] Data collected (pending)
- [ ] Results filed
- [ ] Calibration score computed
- [ ] Published (repo commit with results/)
