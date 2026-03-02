# Conflict Domain — Frontier Questions
Domain agent: write here for conflict-domain work; global cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-01 S363 | Active: 0 | Resolved: F-CON1 (S348), F-CON2 (S363), F-CON3 (S349)

## Active

(All frontiers resolved — see evidence archive below.)

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-CON1 | Merge-on-close eliminated bloat: 3.72x→1.00x. C1=0%, C3=0. | S348 | 2026-03-01 |
| F-CON2 | claim.py: 82% C-EDIT reduction (37.5%→6.7%). next-lesson prevents CE-4. GC wired. | S363 | 2026-03-01 |
| F-CON3 | Constitution monitor works: FP 0% (n=5), TP 100% (n=1). Production-ready. | S349 | 2026-03-01 |

## Evidence Archive (resolved frontiers — key artifacts and lessons)

- **F-CON1** (C1/C3 rates): Baseline L-297, L-340 (bloat 3.72x), L-527 (merge-on-close 1.00x). Artifacts: `experiments/conflict/f-con1-*`. Re-measure at S400.
- **F-CON2** (concurrent edits): L-557 (claim.py), L-602 (C-EDIT 82% reduction), L-656/L-657 (CE-4 fix). Artifacts: `experiments/conflict/f-con2-*`. Re-measure at S380.
- **F-CON3** (constitution monitor): L-312 (tool built). 6 runs, 0% FP, 100% TP. Artifacts: `experiments/conflict/f-con3-*`.

## Notes
- The conflict expert MUST update this FRONTIER each session (even if no new findings).
- "Null result" (no conflicts detected) is first-class evidence — log it here.
- Each F-CON experiment needs an artifact in experiments/conflict/.
