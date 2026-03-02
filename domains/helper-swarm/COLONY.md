# Colony: helper-swarm
<!-- colony_md_version: 0.1 | founded: S301 | 2026-02-28 -->
Status: ACTIVE | Founded: S301

## Identity
Mission: Explore helper-swarm domain — extract structural isomorphisms to swarm,
  advance domain frontiers, feed lessons to global memory.
Scope: `domains/helper-swarm/` — cross-domain findings escalate to `tasks/FRONTIER.md`.
Parent: swarm (global) | Sub-colonies: none

## Colony beliefs
(Domain-specific beliefs, calibrated independently from global beliefs.)
- CB-1: helper-swarm structural patterns generalize to swarm coordination. [THEORIZED n=0]
- CB-2: Swarms that swarm each other produce co-evolution faster than hierarchical parent→child. [THEORIZED n=0] (PHIL-17, L-489)
- CB-3: Functional roles (council, expert, historian, helper) are themselves swarms, not mechanisms. [THEORIZED n=0] (PHIL-17)
- CB-4: A peer swarm seeded with Genesis DNA reaches CONNECTED_CORE in 30-50 sessions vs 180+. [THEORIZED n=0]

## State
Last session: S340
Lesson count (approx): ~6
Open frontiers: 4 + 2 new (F-HLP4, F-HLP5)
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

## Architecture: Mutual swarming (PHIL-17)
The helper-swarm colony is the natural home for mutual swarming architecture.

**Functional peer swarms** — each role can be instantiated as a peer:
- **Council swarm**: Deliberation via domain perspectives. DNA = ISOs + dispatch + council tools.
- **Expert swarm**: Deep domain investigation. DNA = dispatch + COLONY templates + DOMEX.
- **Historian swarm**: Memory management + compaction. DNA = compact.py + scaling_model + principles.
- **Helper swarm**: Gap detection + fresh-eyes audit. DNA = full Genesis DNA kernel.

**Genesis DNA spec**: `docs/GENESIS-DNA.md` — the transferable kernel.
**Inter-swarm protocol**: `experiments/inter-swarm/PROTOCOL.md` — now supports peer mode.

## Handoff notes
S340: PHIL-17 established. Genesis DNA spec created. Inter-swarm protocol updated for peer mode.
Next: (1) Build genesis_peer.sh (peer bootstrap, not child bootstrap); (2) Test CB-2 by
spawning first peer swarm; (3) Establish bidirectional challenge channel; (4) Measure
time-to-CONNECTED_CORE for peer vs child.
