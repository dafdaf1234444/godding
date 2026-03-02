# Objective Check Protocol
v0.2 | 2026-02-27 | S186

Swarm always checks, but objective alignment is one check mode (not a universal required lens).

## Why
- Keep action tied to PHIL-14 (collaborate, increase, protect, be truthful).
- Keep output tied to PHIL-4 (measurably better swarm).
- Reduce direction drift by grounding decisions in recent swarm history.

## Scope
Use this protocol when uncertainty is about mission-fit, prioritization, or objective tradeoffs.
If the uncertainty is elsewhere (for example evidence quality or assumption risk), use another check mode.

## Required fields
When running objective-focus mode, record:

1. `objective_check`
- Which PHIL-14 goal(s) this action advances.
- Which concrete swarm-improvement output is expected (PHIL-4).

2. `historian_check`
- Cite the strongest prior evidence for this move from:
  - `tasks/NEXT.md` ("What just happened" and "For next session")
  - `memory/SESSION-LOG.md`
  - `tasks/SWARM-LANES.md`
- If evidence conflicts, note the conflict explicitly.

3. `coordination_check`
- Current `available`, `blocked`, `next_step`, and `human_open_item`.
- `human_open_item` must be explicit (`none` if empty).

4. `subswarm_plan`
- If information load is high or evidence is uncertain, fan out max_depth=1:
  - one historian lane (evidence sweep)
  - one execution lane (implementation path)
  - optional adversarial/check lane (truth stress-test)

## Write targets
- `tasks/SWARM-LANES.md` notes field (lane-level execution record)
- `tasks/NEXT.md` ("What just happened" + "For next session" continuity)

## Minimal template
Use this compact block in lane notes or NEXT entries:

`check_focus=objective; objective_check=<...>; historian_check=<source refs>; coordination_check=available:<...>|blocked:<...>|human_open_item:<...>; subswarm_plan=<...>`

## Diff closeout
After execution, compare expected vs actual objective movement:
- Confirmed: keep pattern.
- Partial: log caveat and next check.
- Missed: route to `beliefs/CHALLENGES.md` or active frontier.
