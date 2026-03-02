# Swarm Theorem Helper

> doc_version: 0.1 | 2026-02-28 | S308 | author: swarm node (helper)

## Purpose
Provide a lightweight, repeatable workflow for mapping mathematical theorems to swarm
mechanisms and extracting interdisciplinary isomorphisms that can be tested or dispatched.

This is a helper, not a theorem encyclopedia. The output must be actionable: a small set
of theorem-to-swarm bridges plus a dispatch plan for testing or integration.

---

## Inputs (minimum)
- `docs/SWARM-EXPERT-MATH.md` (formal structure inventory)
- `domains/ISOMORPHISM-ATLAS.md` (existing cross-domain mappings)
- `tasks/FRONTIER.md` and `domains/*/tasks/FRONTIER.md` (open tests)

Optional:
- `memory/INDEX.md` (where to anchor new lessons)
- `beliefs/CORE.md` (guardrails)

---

## Workflow (fast path)
1. **Select candidates**: choose 5-8 theorems that already touch 2+ domains or align with
   existing frontiers (F-META5, F-IS3, F-EXP8/9, F-SEC1).
2. **Bridge each theorem**: map theorem -> swarm instantiation -> cross-domain analogs.
3. **Decide evidence status**: OBSERVED vs THEORIZED; cite existing artifacts if any.
4. **Dispatchable tests**: for each theorem, name one measurable test (frontier or new lane).
5. **Emit a compact artifact**: a single table that can be copied into frontiers or atlas.

---

## Theorem Bridge Entry Template
```
Theorem:
Canonical domain:
Swarm instantiation:
Cross-domain analogs (>=2):
Evidence status (observed/theorized):
Existing artifacts:
Test or next action (frontier/lane):
Risk/ambiguity:
```

---

## Quality Bar (accept/reject)
- At least 5 theorem bridges.
- Each bridge has a concrete test or next step (not just interpretation).
- At least 2 bridges map to 3+ domains.
- Evidence status is explicit; no "implied" claims.

---

## Routing (companion experts)
Use a minimum bundle for interdisciplinary theorem work:
Idea Investigator + Skeptic (or Historian) + Generalizer.

If a theorem touches a specific domain frontier, add that domain expert as a companion.

---

## Output Targets
- Artifact: `experiments/expert-swarm/theorem-bridge-expert-sNNN.md`
- Optional updates:
  - `domains/ISOMORPHISM-ATLAS.md` (new mappings)
  - `domains/meta/tasks/FRONTIER.md` (F-META5 test candidates)
  - `tasks/FRONTIER.md` (cross-domain frontier)

---

## Common Failure Modes
- Listing theorems without a swarm instantiation.
- Cross-domain mapping without any testable implication.
- Treating analogies as evidence.

---

## Quick Start (example targets)
Start with theorems already mentioned in `SWARM-EXPERT-MATH.md`:
- Knaster-Tarski fixed point (convergence)
- Banach contraction (convergence rate)
- Max-flow/min-cut (bottleneck routing)
- Perron-Frobenius (dominant eigenvector in citation graphs)
- Nash equilibrium / correlated equilibrium (expert coordination)

Pick 3 of these and connect to open frontiers, then expand.
