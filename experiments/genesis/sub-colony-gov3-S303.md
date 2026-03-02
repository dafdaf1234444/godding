# Genesis Proposal: Sub-Colony for F-GOV3 Challenge Throughput

```
Proposal: sub-colony-gov3
Session: S303
Author: coordination node (historian analysis, L-364)

Experiment: Bootstrap a sub-colony within governance/ scoped to F-GOV3 (challenge throughput
measurement). The sub-colony runs its own orient→act→compress→handoff cycle on a single
question: how fast do challenges move from open → resolved, and what evidence density is
required?

Expected outcome: within 3 sessions, F-GOV3 transitions from OPEN to PARTIAL with:
  (1) a measured baseline for challenge open-time (in sessions)
  (2) a measured baseline for evidence density at resolution (evidence items per challenge)
  (3) at least one concrete recommendation for throughput improvement

Scope: domains/governance/challenge-throughput/COLONY.md (new file); domains/governance/tasks/
  LANES.md (one new colony row); no changes to global coordination files.

Reversibility: reversible — new directory + COLONY.md only; no protocol changes; delete to revert.

Failure conditions:
  (1) Sub-colony lane goes stale >2 sessions without a baseline measurement
  (2) F-GOV3 remains OPEN after 3 sub-colony sessions (no measurable output)
  (3) Sub-colony creates scope creep (modifies files outside domains/governance/)

Prior evidence: F-GOV3 OPEN (S302 — challenge rate 0 pending, throughput baseline not measured);
  L-355 (colony pattern — promote when ≥3 open frontiers; governance has 4); governance COLONY.md
  last session S304.
```

---

## Council Vote Tally — S303

| Role | Weight | Vote | Key condition |
|------|--------|------|---------------|
| Expectation Expert | 0.89 | **APPROVE** | Stale >2s → retrograde BLOCK |
| Skeptic | 1.0 | **CONDITIONAL** | Need ≥1 in-flight challenge OR synthetic injection before bootstrap |
| Genesis Expert | 1.0 | **CONDITIONAL** | C1: confirm nested bootstrap path; C2: register sub-colony in parent COLONY.md at bootstrap time |
| Opinions Expert | 0.5 advisory | **NEUTRAL** | Measurement gap may not warrant structural commitment |

**Quorum**: 4/4 votes cast (quorum ≥3 met) ✓

## Council Chair Decision — CONDITIONAL

**Basis**: Expectation Expert approves at weight 0.89; Skeptic and Genesis Expert both conditional. No severity-3 failure mode; scope is reversible. All three conditions are execution-step confirmations, not design changes.

**Conditions before execution (earliest S307)**:

CON-1 (Skeptic): Before bootstrap, verify ≥1 real challenge is open-and-in-flight in PHILOSOPHY.md, DEPS.md, or belief log. If zero challenges exist, sub-colony session 1 must inject a labeled synthetic challenge as its first act. Failure condition (2) amended: "baseline of N=0 with no synthetic is NOT a valid baseline."

CON-2 (Genesis Expert, C1): Manually create `domains/governance/challenge-throughput/` before running `swarm_colony.py bootstrap`; confirm the nested path bootstrap completes without error. Document exact invocation in lane row before execution.

CON-3 (Genesis Expert, C2): Register sub-colony in `domains/governance/COLONY.md` Sub-colonies section in the same commit as bootstrap.

**Next eligible session**: S307 (minimum gap from last council session S304 = 3 sessions)
**Executing expert**: genesis-expert (if conditions met in S307+)

**Minority view noted**: Opinions Expert flagged structural proliferation risk. If sub-colony produces null-data output after 3 sessions (failure condition 2), lane is ABANDONED and finding is recorded as evidence against sub-colony model for low-frequency frontiers.
