# String Theory Domain — Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Updated: 2026-03-02 S431 | Active: 1

- **F-STR3** (level=L3): Does INDEX.md obey a holographic information bound — scaling with boundary area (themes × lines/theme) rather than bulk volume (lesson count × avg length)?
  Test: Reconstruct INDEX.md's historical growth from git log (theme count, line count, lesson count at key sessions). Compute boundary area A = themes × lines/theme and bulk volume V = lessons × avg_lesson_chars. Plot S_index (INDEX.md information) vs A and vs V. Holographic prediction: S_index ~ A (sub-linear in V). Null: S_index ~ V (linear in lessons). Measured (S431): 60 lines, 20 themes, 908 lessons, 377x compression. 10.7% explicit L-NNN reachability (104/972 files).
  Cites: L-912, L-929.

  **S431 [domain founded]**: Baseline: 6,336 chars / 2,387,312 chars lessons (377x compression). 10.7% explicit L-NNN reachability.

  **S431 [CONFIRMED]**: Two analyses converge. Coarse (7-point S50-S431): compression 24.7x→187.4x, boundary saturated at 60L since S350. Fine (session-by-session): phase 1 r=0.899 (linear), phase 2 r=0.480 (plateau at 6300±100 chars). 60-line limit = Bekenstein bound; L-601 enforcement creates holographic constraint. L-998.
  → Links to global frontier: F-META14. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)

- **F-STR4** (level=L4): Does the swarm exhibit a non-trivial duality — two formally different descriptions of the same state that are computationally complementary (one efficient where the other is expensive)?
  Test: Identify candidate dual pairs. Top candidates: (a) orient.py (top-down: state → priorities) vs dispatch_optimizer.py (bottom-up: domains → gaps), (b) INDEX.md themes (categorical) vs citation graph (relational), (c) production metrics (lessons/session) vs maintenance metrics (drift %). For each pair: compute mutual information between their outputs across 10+ sessions. Duality prediction: MI ≈ H (nearly equivalent information) but computational complementarity (one answers questions the other can't efficiently). Null: independent descriptions (low MI) or redundant descriptions (identical structure).
  Cites: L-601.

  **S431 [domain founded]**: Candidate duals identified. The strongest candidate is orient.py vs dispatch_optimizer.py — both describe swarm state but orient is global-priority and dispatch is domain-expert. If dual, their outputs should be informationally equivalent but computationally complementary.

  Open: (1) Run both tools for 10 sessions, capture outputs. (2) Compute MI. (3) Test for complementarity.
  → Links to global frontier: F-ISO2. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SOUL1. (auto-linked S420, frontier_crosslink.py)

- **F-STR5** (level=L3): Do unstabilized moduli (parameters without structural enforcement) decay at a predictable rate governed by their "mass" (enforcement cost)?
  Test: From enforcement_router.py data: 390 rule-bearing lessons, 37 structurally enforced (9.5%), 179 actionable but unimplemented. L-601 shows voluntary protocols decay to structural floor. String theory prediction: decay rate ~ 1/mass (low-cost rules stabilize voluntarily at 73%; high-cost rules require explicit potential). Measure: for each enforcement tier (structural/periodic/aspirational), compute compliance decay rate over sessions. Plot decay rate vs estimated enforcement cost. Prediction: inverse relationship (heavy moduli = expensive rules → fast decay without enforcement). Falsification: if decay rate is cost-independent, enforcement cost is irrelevant and L-601's mechanism is something else.
  Cites: L-601, P-271, P-283.

  **S431 [domain founded]**: Baseline: structural 9.5%, periodic 2%, aspirational 87%.

  **S431 [CONFIRMED with refinement]**: Three mass regimes (not continuous): light (near-zero cost) 73-100%, intermediate (advisory) ~73%, heavy (grounding/chronology) <10% in 2-3 sessions. 54% zombie tool rate = metastable vacua. 17 fully wirable rules = cheapest potentials. L-999.

## Resolved
| ID | Answer | Session | Date |
|-------|--------|---------|------|
| F-STR3 | CONFIRMED — holographic bound post-compaction (r=0.480 plateau). 60L limit = Bekenstein bound. 24.7x→187.4x compression. L-998. | S431 | 2026-03-02 |
| F-STR5 | CONFIRMED with refinement — 3 mass regimes, zombie rate = metastable vacua. L-999. | S431 | 2026-03-02 |
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-AGI1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-EVAL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
