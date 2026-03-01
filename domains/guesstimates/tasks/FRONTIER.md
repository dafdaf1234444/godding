# Guesstimates Domain — Frontier Questions
Domain agent: write here for guesstimates-specific questions; cross-domain findings go to tasks/FRONTIER.md
Seeded: S302 | 2026-02-28 | Active: 3

## Active

- **F-GUE1**: Can the swarm apply Fermi decomposition to estimate its own performance metrics (S302)
  (token efficiency, lesson half-life, duplication rate) with accuracy better than ±1 OOM?
  **S391 HARDENING**: 2/2 valid comparisons within 1 OOM. Half-life: Fermi 8, actual 15 (log10=0.27). Commits/session: Fermi 5, actual 7.92 (log10=0.20). Duplication rate measurement failed (Jaccard on titles = 0, method too strict). Fermi viable as cheap substitute when structural priors exist. L-782.
  **Stakes**: If YES, swarm gains internal self-measurement without instrumentation — decompose a
  hard metric into observable sub-quantities, multiply, compare to measured proxy-K. If the
  guesstimate lands within an order of magnitude, this is a cheap substitute for formal measurement
  when tools are unavailable. Directly extends proxy-K from a single scalar to a decomposable model.
  **Method**: Pick 3 swarm metrics with known ground truth (e.g. duplication rate from L-297 at
  57.5%, lesson count drift, commit frequency). Produce blind Fermi estimates using only structural
  priors (session count, team size analogy, parallel session count). Measure absolute error. Log
  calibration gap as evidence for/against B1 (beliefs are falsifiable).

- **F-GUE2**: Does importing reference-class forecasting into swarm belief formation reduce (S302)
  miscalibration events — beliefs later contradicted by evidence?
  **Stakes**: Swarm currently forms beliefs by bottom-up induction from lessons. Reference-class
  forecasting (Kahneman/Lovallo) says: always anchor on the outside view (base rate for this class
  of thing) before updating with inside-view evidence. If swarm beliefs that incorporate a reference
  class step are more durable than those formed purely inside-view, the swarm gains a calibration
  primitive with proven human-judgment track record.
  **Method**: Audit PRINCIPLES.md for beliefs with THEORIZED status. For each, identify the
  reference class (what fraction of similar agent systems have validated this?). Compute outside-view
  prior. Compare to current confidence level. Flag miscalibration gaps where inside-view belief
  exceeds outside-view base rate. Candidate: P-182 (spawn→belief transfer — what fraction of
  multi-agent systems achieve this?).

- **F-GUE3**: Is there an isomorphism between estimation cascade uncertainty propagation and (S302)
  swarm inference chain degradation? Do compounded errors in Fermi chains mirror degradation
  in multi-hop belief chains?
  **Stakes**: Fermi chains multiply sub-estimates and compound relative errors: if each factor has
  ±30% uncertainty, a 5-step chain yields ±(1.3^5 - 1) ≈ 270% error. Swarm inference chains
  (lesson A cited in belief B referenced in decision C) may degrade similarly. If the isomorphism
  holds, swarm gains a quantitative model for how far inference can safely propagate before a
  fresh measurement point is required. This bounds how deeply lessons can be chained before
  grounding (direct evidence) is needed.
  **Method**: Trace 3 multi-hop inference chains in swarm belief system (e.g. lesson → principle →
  frontier → handoff note). Estimate per-hop uncertainty from explicit confidence labels or
  THEORIZED flags. Compare propagated uncertainty to observed accuracy of downstream claims.
  Cross-reference with statistics domain (error propagation in products of independent variables).
## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|

## Notes
Guesstimates as a field has two failure modes mirrored in swarm: (1) inside-view overconfidence
(planning fallacy — swarm equivalent: session-count optimism in NEXT.md timelines), (2) reference
class neglect (ignoring base rates — swarm equivalent: treating each belief as novel without
checking whether similar beliefs failed in prior sessions). Both failure modes have direct swarm
countermeasures: outside-view anchoring before inside-view updating; and CHALLENGES.md audit before
writing any new high-confidence belief.
