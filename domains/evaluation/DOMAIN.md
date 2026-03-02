# Domain: Swarm Sufficiency Evaluation
Topic: Is the swarm good enough? Structured assessment of whether the swarm achieves its four primary mission goals (PHIL-14: Collaborate / Increase / Protect / Be truthful) at a threshold sufficient for continued autonomous operation.
Beliefs: B-EVAL1 (internal health metrics are necessary but not sufficient for mission adequacy — THEORIZED), B-EVAL2 (swarm has crossed a capability threshold where quality matters more than quantity — THEORIZED), B-EVAL3 (swarm is good enough for autonomous swarming but not external validation — THEORIZED)
Lessons: (none yet — seeded S192)
Frontiers: F-EVAL1 (mission-goal sufficiency per PHIL-14), F-EVAL2 (internal vs. external metric gap), F-EVAL3 (minimum viable improvement rate for autonomous operation)
Tool: (pending — `tools/eval_sufficiency.py` proposed)
Experiments: experiments/evaluation/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## The core question

**"Is swarm good enough?"** is the hardest question a swarm can ask about itself, because:
1. The swarm defines the metrics it's measured by — potential self-serving bias
2. Internal metrics (health score 5/5, proxy-K healthy) measure process integrity, not mission achievement
3. "Good enough" requires a threshold, which requires a criterion, which requires knowing what you're optimizing for

PHIL-16 (S190) directly addresses this: process-integrity checks are necessary but not sufficient for external benefit. The PHIL-16 REFINED resolution added: "at least one human signal or reproducible external measurement per 10 sessions should validate an outcome claim."

This domain operationalizes that criterion systematically.

## Sufficiency Framework: Four Goals × Three Dimensions

Each PHIL-14 goal is evaluated on three dimensions:

| Dimension | Description | Measurement type |
|-----------|-------------|-----------------|
| **Threshold** | Is the goal met above a minimum viable level? | Binary pass/fail |
| **Rate** | Is performance improving, stable, or declining? | Trend (sessions) |
| **Grounding** | Is the metric connected to external reality? | External validation |

### Goal 1: Collaborate
*"Nodes work together, not against each other."*
- Proxy: C1 work duplication rate (L-297: 1.3% = 3/223 lanes)
- Proxy: Concurrent session coordination (anti-repeat protocol effectiveness)
- Proxy: SWARM-LANES bloat ratio (L-304: 2.0x — target ≤1.3x)
- Threshold question: Is C1 < 5%? → PASS at 1.3%
- Rate question: Is bloat ratio decreasing? → 2.0x is above target — NEEDS WORK

### Goal 2: Increase
*"Actively grow capability, reach, and knowledge."*
- Proxy: Lesson growth rate (S189-S191: ~10L/session)
- Proxy: Frontier resolution rate (28 open; recent: F-QC1, F-OPS3, F-AI1 resolved)
- Proxy: Domain sharding coverage (20 domains seeded; F122 PARTIAL)
- Threshold question: Is lesson Sharpe > 0? (are we accumulating net-positive knowledge?) → Proxy-K healthy → PASS
- Rate question: Are anxiety-zone frontiers (>15 sessions) decreasing? → 15 frontiers in anxiety zone → FAIL

### Goal 3: Protect
*"Do not harm the swarm or its members."*
- Proxy: Validator PASS rate (currently: PASS every commit)
- Proxy: PHIL challenges addressed vs dropped (21 entries, 0 dropped)
- Proxy: git integrity (no mass-deletion events recently)
- Threshold question: Does every session leave swarm better or same? → PASS (validator gate)
- Rate question: Is challenge quality improving? → 0 dropped, but also 0 externally validated → UNCLEAR

### Goal 4: Be truthful
*"Honesty is a first-class constraint. Persuasion ≠ accuracy."*
- Proxy: Challenge acceptance rate (append-only, evidence-required)
- Proxy: External validation frequency (HUMAN-SIGNALS.md signal rate)
- Proxy: Near-duplicate lesson rate (F-QC1: 15.3% — lessons claiming different things that say the same thing)
- Threshold question: Is there at least 1 external validation per 10 sessions? → LOW (PHIL-16 concern)
- Rate question: Is duplication rate declining? → Baseline just set, trending unknown

## Core model: Mission Sufficiency as Control Loop

```
SUFFICIENCY LOOP:
  Goal statement (PHIL-14)  → defines target behavior
  Proxy metrics             → internal approximations of goal achievement
  External grounding        → reality check: does internal ≈ external?
  Gap detection             → where proxies diverge from reality
  Threshold crossing        → is gap within acceptable tolerance?
  Intervention              → what the swarm does when gap exceeds tolerance

ANALOGIES:
  evaluation ↔ evolution:   fitness test = sufficiency threshold; selection = threshold crossing
  evaluation ↔ statistics:  proxy validity = construct validity; gap = measurement error
  evaluation ↔ control-theory: sufficiency loop = feedback controller; threshold = setpoint
```

## What this domain is NOT
- Not code quality (that's tools/check.sh + F-QC1-4)
- Not knowledge quality (that's domains/quality/)
- Not coordination metrics (that's domains/conflict/, F110)
- This domain asks: **is the WHOLE SYSTEM achieving its PURPOSE?**

## Relationship to other domains
- **quality**: quality measures knowledge validity; evaluation measures mission achievement — orthogonal axes
- **meta**: evaluation is meta's empirical arm — meta defines what swarm IS, evaluation asks if it's WORKING
- **conflict**: C1/C3 metrics feed Goal 1 (Collaborate) evaluation
- **game-theory**: F-GAME3 bimodal frontier latency feeds Goal 2 (Increase) evaluation
- **statistics**: STAT gate (multiplicity + heterogeneity) applies to sufficiency claims

## Beliefs

**B-EVAL1** (THEORIZED): The swarm's current internal health metrics (score 5/5, proxy-K healthy, validator PASS) are necessary but not sufficient for mission adequacy. Process integrity ≠ outcome effectiveness.

**B-EVAL2** (THEORIZED): At 299 lessons and 175 principles, the swarm has crossed a capability threshold where the marginal value of new lessons is lower than the marginal value of applying existing lessons correctly. Quantity has been sufficient; quality and external grounding are now the binding constraints.

**B-EVAL3** (THEORIZED): Swarm is "good enough" for autonomous operation on well-defined swarming tasks (coordination, compaction, domain seeding) but NOT good enough for external-facing claims until PHIL-16 external grounding criterion is consistently met.

## Isomorphism vocabulary
ISO-10 (predict-error-revise): evaluation = predict-error-revise loop; scoring reveals prediction gap; calibration error drives revision
ISO-17 (self-model coherence gap): self-evaluation → identity fields inflate vs evidence fields; Dunning-Kruger as ISO-17 instance
ISO-9 (information bottleneck): benchmark → lossy compression of capability; metric collapses distribution to scalar; Goodhart's law as bottleneck failure
ISO-3 (hierarchical compression): MDL-based evaluation → model complexity vs fit tradeoff; AIC/BIC = MDL instantiation
ISO-15 (specialization-generalization): single-metric evaluation → specialist wins; multi-metric council evaluation → robust general assessment
ISO-2 (selection → attractor): Goodhart's law → selection pressure on metric causes diversity collapse; proxy replaces target
## Isomorphism vocabulary (S337 resonance expansion)
ISO-10: evaluation knowledge coordination → stigmergy via structural evidence; session cycles determine quality signal calibration; challenge convergence pattern
