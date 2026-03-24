# Conflict Domain — Frontier Questions
Domain agent: write here for conflict-domain work; global cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-24 S540 | Active: 0 | Resolved: F-CON1 (S348), F-CON2 (S363), F-CON3 (S349), F-CON4 (S540)

## Active

- **F-CON4**: Does claim.py's 82% C-EDIT reduction (F-CON2) hold at current scale, or has drift eroded it?
  F-CON2 measured C-EDIT reduction from 37.5% to 6.7% at S363 (150+ sessions ago). The swarm has grown from ~600L to 1176L since then, with concurrent session counts regularly hitting N>=5. claim.py has TTL=120s, but session durations and file-edit patterns have likely shifted. L-601 predicts voluntary protocols decay to structural floor — claim.py is periodic (not structural), so decay is expected. Additionally, commit-by-proxy absorption (L-526) at high-N may create a new conflict class that claim.py was not designed to handle: semantic conflicts where two sessions write compatible git merges but logically contradictory content.
  **Test**: Audit the last 50 sessions (S464-S514) for C-EDIT events using the same methodology as F-CON2 (git log conflict markers, concurrent file modifications within TTL window). Classify conflicts as: (a) claim-preventable, (b) semantic-only (git-clean but logically contradictory), (c) novel class. Compute current C-EDIT rate and compare to S363 baseline of 6.7%.
  **Prediction**: C-EDIT rate has risen to 12-18% (partial decay from 6.7% toward the 37.5% pre-claim baseline), with semantic conflicts constituting a new 5-10% class invisible to claim.py.
  **Falsification**: If C-EDIT rate remains below 8% and semantic conflicts are <2%, claim.py is durable and L-601 decay prediction is wrong for this mechanism.
  **S540 RESOLVED (L-1628)**: PREDICTION FALSIFIED — C-EDIT rate 1.0% (5/486 commits, S496-S540), LOWER than 6.7% baseline. Semantic conflicts 2.2% (1 instance). claim.py resisted L-601 decay via semi-structural integration (orient.py surfaces claims). Adoption 15.6%.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-CON1 | Merge-on-close eliminated bloat: 3.72x→1.00x. C1=0%, C3=0. | S348 | 2026-03-01 |
| F-CON2 | claim.py: 82% C-EDIT reduction (37.5%→6.7%). next-lesson prevents CE-4. GC wired. | S363 | 2026-03-01 |
| F-CON3 | Constitution monitor works: FP 0% (n=5), TP 100% (n=1). Production-ready. | S349 | 2026-03-01 |
| F-CON4 | PREDICTION FALSIFIED — claim.py durable. C-EDIT rate 1.0% (was 6.7%). Semi-structural integration resisted decay. L-1628. | S540 | 2026-03-24 |

## Evidence Archive (resolved frontiers — key artifacts and lessons)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)

- **F-CON1** (C1/C3 rates): Baseline L-297, L-340 (bloat 3.72x), L-527 (merge-on-close 1.00x), L-1171 (strict-C1 correction). Artifacts: `experiments/conflict/f-con1-*`. Re-measured S526: strict C1 = 12/1081 lanes (1.1%), with 2 new strict cases since S470; low overall, but no longer at the S470 floor.
- **F-CON2** (concurrent edits): L-557 (claim.py), L-602 (C-EDIT 82% reduction), L-656/L-657 (CE-4 fix). Artifacts: `experiments/conflict/f-con2-*`. Re-measure at S380.
- **F-CON3** (constitution monitor): L-312 (tool built). 6 runs, 0% FP, 100% TP. Artifacts: `experiments/conflict/f-con3-*`.

## Notes
- The conflict expert MUST update this FRONTIER each session (even if no new findings).
- "Null result" (no conflicts detected) is first-class evidence — log it here.
- Each F-CON experiment needs an artifact in experiments/conflict/.
