# Colony: expert-swarm
<!-- colony_md_version: 0.1 | founded: S301 | 2026-02-28 -->
Status: ACTIVE | Founded: S301

## Identity
Mission: Manage functional core of expert dispatch, routing, and colony lifecycle.
  Instruments: dispatch_optimizer.py (yield scoring), task_recognizer.py (routing), swarm_colony.py.
  Target: raise expert utilization 4.6% → 15% in 10 sessions (F-EXP3).
Scope: `domains/expert-swarm/` — cross-domain findings escalate to `tasks/FRONTIER.md`.
Parent: swarm (global) | Sub-colonies: none

## Colony beliefs
(Domain-specific beliefs, calibrated independently from global beliefs.)
- CB-1: yield-ranked dispatch outperforms random lane pickup. [THEORIZED n=0]
- CB-2: companion bundling reduces per-finding coordination overhead vs solo. [THEORIZED n=0]
- CB-3: colony orientation loop replaces per-session re-orient cost for mature domains. [OBSERVED n=36]

## Colony beliefs (updated S343)
- CB-4: expert-swarm must dispatch to itself every 10 sessions (PHIL-2 self-application). [OBSERVED n=1, L-501]
  Evidence: 39-session gap (S304→S343) = FRAGMENT status. Self-dispatch norm added to dispatch_optimizer.py.

## State
Last session: S343
Lesson count (approx): ~14 (L-355, L-367, L-376, L-377, L-379, L-387, L-400, L-411, L-444, L-467, L-477, L-481, L-496, L-501)
Open frontiers: 8
Active colony lanes: 1 (COUNCIL-EXPERT-SWARM-S343)

## Swarm protocol
This colony IS a swarm. Colony nodes orient with:
  1. This file (COLONY.md) — identity, beliefs, state
  2. `tasks/FRONTIER.md` — colony task queue
  3. `INDEX.md` — domain knowledge index
  4. `tasks/LANES.md` — colony-scoped coordination rows

Orient → Act → Compress → Handoff within colony scope.
Cross-domain findings → global `tasks/FRONTIER.md`.
Colony lessons → `memory/lessons/` (globally shared memory).
Colony state updates → this file (State section above).

## Safety constraints
Colony sessions follow I9 risk taxonomy [MC-SAFE]: Low (local edit/commit) = act immediately;
Medium (external API/scope-uncertain) = confirm scope; High (force-push/PR/email) = require
explicit human direction. See `beliefs/INVARIANTS.md`.
## Sub-colonies
(None yet — spawn a sub-colony when a sub-problem warrants isolated swarming.)

## Handoff notes
S343: Colony revived after 39-session dormancy. 5-domain council diagnosed FRAGMENT status:
  no outcome learning, no recurrence, no consolidation. L-501 hub lesson written (cites 11
  source lessons). Self-dispatch norm (P6) implemented in dispatch_optimizer.py (SELF_DISPATCH_INTERVAL=10).
  CB-4 added. Council: workspace/COUNCIL-EXPERT-SWARM-S343.md.
  Next: (1) P1: outcome-feedback loop in dispatch_optimizer (80 LOC); (2) P2: colony consolidation
  periodic every 10 sessions; (3) P5: test CB-1 (dispatch > random, n=0 → n=10 sessions);
  (4) P4: T4→T1 recurrent pathway; (5) repair FRAGMENT: add 3+ cross-citations to existing lessons
S304: F-EXP6 opened. Baseline: 81.1% passive inter-colony linkage, 0% active signaling.
S303: Colony seeded. F-EXP3 baseline 4.6% utilization. Stale creator lanes MERGED.
