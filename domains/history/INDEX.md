# History Domain Index
Updated: 2026-02-27 | Sessions: 186

## What this domain knows
- **Seed evidence base**: swarm already treats timeline and evidence lineage as critical, but historian grounding is only partially explicit in lane and handoff records.
- **Core structural pattern**: historian-style checks reduce coordination hallucination by forcing provenance, chronology, and conflict surfacing before action.
- **Active frontiers**: 3 active domain frontiers in `domains/history/tasks/FRONTIER.md` (F-HIS1, F-HIS2, F-HIS3).
- **Cross-domain role**: history provides provenance and chronology scaffolding for all domain lanes, especially objective/historian check mode in `memory/OBJECTIVE-CHECK.md`.
- **Latest execution (S186)**: user-directed history reswarm reran F-HIS1/F-HIS2 on current lane state. F-HIS1 pre/post artifacts (`experiments/history/f-his1-historian-grounding-s186-history-swarm-latest.json`, `...-postrefresh-latest.json`) showed a coordinator-anchor regression and repair (`historian/session coverage 0.8 -> 1.0`, mean grounding `0.8667 -> 1.0`), while all-rows audit remains partial (`experiments/history/f-his1-historian-grounding-s186-history-swarm-postrefresh-allrows.json`, `historian_check_coverage=0.3704`) due legacy historical rows. F-HIS2 chronology (`experiments/history/f-his2-chronology-conflicts-s186-history-swarm-postrefresh.json`) is improved but still open (`missing_link_rate=0.0847`, `inversion_rate=0.0085`, `missing_artifacts=0`), so remaining work is missing-link backfill and the single S184/S185 inversion fix.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Provenance discipline | L-224, L-252 | Claims without source trails cause silent drift and low trust handoffs |
| Temporal coherence | L-223 | Expect-act-diff only works if events are chronologically explicit |
| Protocol continuity | L-214, L-252 | Historical grounding is required to transfer working patterns across sessions/tools |

## Structural isomorphisms with swarm design

| History finding | Swarm implication | Status |
|-----------------|-------------------|--------|
| Strong claims require source hierarchy | Lane updates should include evidence anchors for key assertions | OBSERVED |
| Timeline breaks distort interpretation | Swarm records need explicit chronology tags for replay and audit | OBSERVED |
| Competing narratives can both appear plausible | Conflict checks should compare sources, not just summary text | THEORIZED |
| Missing archives bias conclusions | Handoffs should expose known blind spots and uncited assumptions | OBSERVED |

## What's open
- **F-HIS1**: measure historian-grounding coverage in active lanes and identify low-provenance hotspots.
- **F-HIS2**: detect chronology conflicts between `tasks/NEXT.md`, `tasks/SWARM-LANES.md`, and experiment artifacts.
- **F-HIS3**: build historical drift slices (pre/post protocol changes) to quantify which changes improve swarm outcomes.

## History links to current principles
P-182 (expect-act-diff loop) | P-191 (enforcement audit mode) | P-197 (quality dimensions)
