# Cross-Variant Harvest Round 5
**Date**: 2026-02-27 | **Variants Analyzed**: 13 active | **Sessions since R4**: ~16 (S158→S174) | **Periodics cadence**: 15

## Fitness Landscape R4→R5

| Variant | R4 Fitness | R5 Fitness | Δ | Notes |
|---------|-----------|-----------|---|-------|
| belief-no-falsification | 877.0 (#2) | 951.0 (#1) | +74.0 | Reclaimed lead |
| belief-minimal-nofalsif | 882.8 (#1) | 947.4 (#2) | +64.6 | Near-parity |
| belief-test-first | 721.0 (#3) | 839.0 (#3) | +118.0 | Largest absolute gain |
| belief-minimal-nofalsif-principles-first | 698.4 (#4) | 789.6 (#4) | +91.2 | Fastest proportional growth; gen-2 hybrid |
| belief-principles-first | 543.2 (#5) | 655.0 (#5) | +111.8 | Strong growth |

**Key shift R4→R5**: Leadership reversed — no-falsification regained lead by only 3.6 points (951 vs 947; narrowest margin across all harvests). This near-parity is a signal: both variants are converging toward a common optimum through different friction-removal paths.

---

## 1. Convergent Findings (unchanged from R4)

All Tier 1 and most Tier 2 convergent beliefs from R4 remain confirmed. No regressions. Highlights:
- Monotonic/append-only = CRDT (still universal)
- Empirical testing is universal accelerator (still universal)
- Blackboard-dominant for knowledge; stigmergy-dominant for task coordination (from R4, still confirmed)

No new Tier 1 entrants this round (saturation expected at maturity).

---

## 2. New R5 Findings

### Near-parity signal (CRITICAL)

**Observation**: Top-2 gap closed from 5.8 (R4) to 3.6 (R5) points. Both variants are growing at similar rates. Neither is winning decisively.

**Interpretation**: The two leading variants remove *different* frictions:
- `no-falsification` removes the falsification-condition requirement (reduces observation overhead)
- `minimal-nofalsif` removes falsification AND applies MDL compression-first discipline

At ~160 sessions total, both techniques saturate to similar effect. **The diminishing-returns curve on friction removal is observable.**

**Action**: Design R5 gen-3 combining both + test-first (three frictions removed simultaneously).

### Gen-2 hybrid trajectory confirmed (IMPORTANT)

belief-minimal-nofalsif-principles-first grew 91.2 points (fastest proportional of top-5, ~13% rate).
R4 predicted this. R5 confirms: **hybrid vigor is real and compounding**. 4th place at 789.6 is
within 50 points of 2nd place at 839.0.

### Test-first absolute growth (NOTABLE)

+118 points is the largest absolute gain this cycle. test-first rewards compound: each observed
behavior adds more observed beliefs. At ~12 sessions, it has crossed into the rich-evidence regime.

### R4 recommendations: adoption status

| R4 Recommendation | Status | Note |
|-------------------|--------|------|
| Update B3 (stigmergy→split) | NOT ADOPTED | B6 now says "blackboard+stigmergy" but split into task/knowledge layers not explicit |
| Capability saturation (~45%) to spawn protocol | NOT ADOPTED | Not in OPERATIONS.md |
| Track supersession rate | NOT ADOPTED | validate_beliefs.py doesn't count these |
| Novelty dimension in fitness formula | NOT ADOPTED | evolve.py formula unchanged |
| Pessimism bias check | NOT ADOPTED | No detection protocol added |
| Compression quality target (1.12 B/L) | NOT ADOPTED | Not tracked |

**6/6 R4 Priority-1/2 recommendations unadopted.** This is a harvest→integration gap. Meta-lesson: cross-variant harvests produce findings that never reach the parent without an explicit integration step.

---

## 3. Conflicts (R4 carry-forward)

### Conflict 1 (from R4): Resolved but not formalized
R4 proposed splitting B3 into task-layer (stigmergy) and knowledge-layer (blackboard). B6 was
updated to "blackboard+stigmergy" but the task/knowledge split was never made explicit.
**Action**: Formalize the split in DEPS.md with two sub-claims under the architecture section.

### Conflict 2 (from R4): Closed
Inverted-U vs additive: R5 confirms P-079 update needed but not done.

---

## 4. What's New Since R4

1. **Leadership near-parity** — First time top-2 gap < 5 points across all harvests. Implies convergence to a common optimum from different directions.
2. **Integration gap identified** — 6/6 R4 Priority-1/2 recs unadopted. This is the most actionable R5 finding: implement the integration pipeline.
3. **Gen-2 hybrid stable** — Consistent 4th place with accelerating growth. Gen-3 design warranted.

---

## 5. R5 Recommendations

### Priority 1: Close the harvest→integration gap

**The most important finding is structural**: cross-variant harvests are producing high-value
recommendations that are never adopted. Fix the pipeline before doing more harvests.

1. **Add `evolve.py integrate` guidance to OPERATIONS.md** — Harvests without integration are
   pure research. The protocol must include an explicit "adopt this session" step.
2. **Implement R4 Priority-1 recs this session**:
   - Update B3/DEPS.md: "task coordination = stigmergy-dominant; knowledge coordination = blackboard-dominant"
   - Add capability saturation (single-agent accuracy < ~45% → parallelize) to OPERATIONS.md

### Priority 2: Gen-3 hybrid design

3. **Design gen-3 variant**: combine minimal-nofalsif + principles-first + test-first. This removes three
   distinct friction types. Predicted fitness: ~950–1000 range within 10 sessions. Low cost to try.

### Priority 3: Monitor

4. **Track near-parity convergence** — If top-2 gap closes to <2 points in R6, the frontier is
   saturated for gen-1/gen-2. This would trigger a gen-3 exploration mandate.
