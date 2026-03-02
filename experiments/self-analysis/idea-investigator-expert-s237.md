# Idea Investigator Expert Baseline - S237

Date: 2026-02-28
Execution: S258
Lane: L-S237-IDEA-INVEST
Check mode: coordination
Status: complete

## Expectation
Translate the human signal ("repair help experts coordinator experts swarm") into falsifiable coordination claims,
produce a companion-lane bundle template, and repair the coordinator help surface with a minimal update.

## Actual
- Restated the idea as coordination claims and a test plan.
- Added a Coordinator Quickstart + lane template in `docs/EXPERT-SWARM-STRUCTURE.md`.
- Produced a companion-lane bundle template and dispatch checklist (below).

## Diff
Companion lanes were not spawned in this pass; coordinator personality remains uncreated. Follow-on dispatch is required.

## Idea Restatement
The expert swarm needs a lightweight, repeatable coordinator help surface so coordination lanes
consistently include required contract fields and companion lanes are spawned by default.

## Falsifiable Claims
1. With a coordinator quickstart template in place, the next 3 coordinator lanes will include all required
   contract fields (`focus/intent/progress/available/blocked/next_step/human_open_item/check_focus`).
2. If idea-level lanes default to a companion bundle, at least one new idea-level lane in the next 2 sessions
   will include a Skeptic or Historian companion.
3. A dedicated coordinator personality would improve repeatability; currently no coordinator profile exists
   in `tools/personalities/` (verify via repo scan).

## Evidence & Gaps
- Contract drift evidence: `experiments/meta/f-meta1-contract-audit-s249.md` shows widespread missing fields.
- Gap: no explicit coordinator personality or quickstart template existed prior to this update.

## Companion Bundle Template (copy/paste)
- Idea Investigator (lead)
- Skeptic or Historian (required)
- Domain Expert or Generalizer (as needed)

## Dispatch Checklist
- Ensure each lane includes `artifact=...` and `expect/actual/diff`.
- Record explicit `next_step` when companion lanes are deferred.
- Close or requeue lanes the same session when possible to prevent parked work.

## Next Step
1. Spawn a Skeptic or Historian companion lane for the next idea-level task, or
2. Create a coordinator expert personality and dispatch a dedicated coordination lane, then
3. Rerun the contract completeness audit after 2-3 coordinator lanes to validate claim (1).
