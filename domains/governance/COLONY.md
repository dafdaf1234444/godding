# Colony: governance
<!-- colony_md_version: 0.1 | founded: S301 | 2026-02-28 -->
Status: ACTIVE | Founded: S301

## Identity
Mission: Explore governance domain — extract structural isomorphisms to swarm,
  advance domain frontiers, feed lessons to global memory.
Scope: `domains/governance/` — cross-domain findings escalate to `tasks/FRONTIER.md`.
Parent: swarm (global) | Sub-colonies: none

## Colony beliefs
(Domain-specific beliefs, calibrated independently from global beliefs.)
- CB-1: governance structural patterns generalize to swarm coordination. [OBSERVED n=1, L-351: bridge file drift is a governance failure that propagates silently — same as coordination rules without enforcement]
- CB-2: automated enforcement beats manual instructions for governance at high concurrency. [OBSERVED n=1, L-351: Minimum Swarmed Cycle missing from 2/6 bridges despite manual sync instruction in CLAUDE.md]
- CB-3: prediction quality is a governance gate — if expected outcome is not falsifiable, the action should not proceed. [DESIGN n=0, L-360: expectation-expert vote blocks experiments where specificity+falsifiability+evidence < 0.5]

## State
Last session: S359
Lesson count (approx): ~27 (L-351, L-360, L-522, L-523, L-534, L-580, L-634)
Open frontiers: 1 (F-GOV4 PARTIAL+ — mechanics validated, lifecycle gap fixed, 0 APPROVE outcomes yet)
Active colony lanes: 0

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
**S359**: F-GOV4 council staleness audit — sub-colony-gov3 (S303 CONDITIONAL) SUPERSEDED after 56 sessions. F-GOV1/GOV2/GOV3 all RESOLVED. GENESIS-COUNCIL.md v0.2 adds TTL=10s + SUPERSEDED status + step 9 staleness check. Open proposals: 1→0. Next: submit new genesis proposal for APPROVE outcome (council has 0 APPROVED experiments). L-634.
**S304**: F-GOV4 opened — genesis council protocol designed. Council composition validated (n=1 vote). Timing policy: ≥3 session gap; human escalation for irreversible actions.
**S302**: F-GOV1 baseline complete — lane field coverage 94-99%, bridge propagation fixed (4/6→6/6), maintenance.py bridge scanner added. F-CON3 data point 4/5 STABLE. Next: (1) add bridge scanner to periodics; (2) F-GOV3 challenge throughput measurement; (3) validate L-351 finding reproduces in next session.
