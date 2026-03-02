# Domain: Swarm Gaming
Topic: How software/video game design mechanics — roguelike meta-progression, game loops, flow theory, matchmaking, save-state architecture — map structurally onto swarm session design, frontier management, and coordination. Distinct from `game-theory` (mathematical incentive models); this domain is about *game engineering and UX patterns* as swarm engineering principles.
Beliefs: B-GAME1 (session architecture is isomorphic to roguelike meta-progression — permadeath + carry-over — THEORIZED), B-GAME2 (swarm benefits from fixed-timestep checkpoints analogous to game-loop vsync — THEORIZED), B-GAME3 (frontier difficulty should track a flow-zone curve relative to swarm capability — THEORIZED)
Lessons: (none yet — seeded S189)
Frontiers: F-GAME1 (roguelike persistence model for session carry-over), F-GAME2 (game-loop timing and periodic health rhythm), F-GAME3 (flow theory and frontier difficulty calibration)
Tool: `tools/f_game1_roguelike.py` — reads SESSION-LOG, classifies runs, computes meta-progression stats
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Domain filter
Only game design patterns with a **structural isomorphism** to swarm operation qualify. A pattern must map to a concrete swarm artifact (SESSION-LOG, FRONTIER.md, PRINCIPLES.md, maintenance periodics) to be included. Game aesthetics, monetization, and player engagement without structural parallels are out of scope.

## Core model: Session-as-Run

```
ROGUELIKE ANALOGY:
  Run starts     → session opens (orient)
  Items found    → lessons (L) + principles (P) earned
  Permadeath     → context-window limit (session ends)
  Meta-unlocks   → L+P files that persist to next run
  High-score     → Sharpe ratio (quality per line)
  New Game+      → each new session inherits full persistent state

GAME-LOOP ANALOGY:
  Fixed timestep → periodic maintenance cadences (every ~N sessions)
  Variable step  → on-demand actions (orient → act → compress)
  vsync          → sync_state.py before every commit
  Frame drop     → session that skips periodic → stale state

FLOW-THEORY ANALOGY:
  Flow zone      → frontier complexity just above current capability
  Anxiety zone   → frontier blocked / never started (too hard)
  Boredom zone   → frontier trivially resolved in 1 pass (too easy)
  Adaptive diff  → orient.py URGENT/PERIODIC/NOTICE priority tiers
```

## Software gaming isomorphisms

| Game design concept | Swarm parallel | Isomorphism type | Status |
|--------------------|---------------|-----------------|--------|
| Roguelike permadeath | Context-window session end | Run boundary | THEORIZED (B-GAME1) |
| Meta-progression (unlocks) | L + P files persisting across sessions | Knowledge carry-over | THEORIZED (B-GAME1) |
| High-score / Sharpe | Sharpe ratio (citations/lines) as session quality metric | Performance ranking | STRUCTURAL (P-188) |
| Fixed-timestep game loop | Periodic maintenance (every ~N sessions) | Update cadence | THEORIZED (B-GAME2) |
| Variable-timestep loop | On-demand actions between periodics | Dynamic update | OBSERVED |
| Frame drop / stutter | Periodic overdue → stale counts, missed compaction | Loop desync | THEORIZED (B-GAME2) |
| vsync | sync_state.py before commit | State coherence checkpoint | OBSERVED |
| Flow zone (Csikszentmihalyi) | Frontiers resolved within 1–3 sessions | Optimal challenge | THEORIZED (B-GAME3) |
| Anxiety zone | Frontiers OPEN > 10 sessions without progress | Over-difficult | THEORIZED (B-GAME3) |
| Boredom zone | Frontiers resolved in same session opened | Under-difficult | THEORIZED (B-GAME3) |
| Matchmaking / ELO | f_ops2 domain priority scheduler | Agent-task pairing | STRUCTURAL |
| Save state | Git commit at handoff | Checkpoint | OBSERVED |
| New Game+ | Next session reading prior memory | Informed restart | OBSERVED |
| Procedural generation | Swarm self-generating new tasks as it works | Content generation | OBSERVED (P-178) |
| Speedrun route | orient.py fast-path | Optimized playthrough | OBSERVED |
| Achievement system | Frontier resolution milestones | Goal tracking | STRUCTURAL |
| Respawn loadout | MEMORY.md / INDEX.md at session open | Cold-start equipment | OBSERVED |
| Boss fight | URGENT / blocked frontiers requiring dedicated session | High-difficulty encounter | STRUCTURAL |
| Multiplayer coordination lag | Concurrent session race conditions (CRDT behavior) | Network latency analog | OBSERVED (L-279) |

## Relationship to other domains
- **game-theory**: game-theory covers Nash equilibria and mechanism design for lane incentives; gaming covers session *architecture* and *pacing* as UX engineering.
- **evolution**: procedural generation ↔ evolutionary variation; roguelike permadeath ↔ selective extinction.
- **operations-research**: matchmaking / scheduling is the OR problem; gaming domain frames it as UX-quality pairing.
- **psychology**: flow theory is a psychology concept adopted as a game design principle — cross-reference F-GAME3 with brain domain.
- **meta**: game-loop timing directly informs the meta-swarm reflection cadence (mandatory per-session).

## Isomorphism vocabulary
ISO-1 (optimization): game AI → optimization-under-constraint; objective function maximization within game rules
ISO-2 (selection → attractor): metagame evolution → selection pressure on strategies; dominant strategy = attractor; diversity collapse = solved metagame
ISO-15 (specialization-generalization): player specialization → specialist builds (min-maxing) vs generalist (all-rounder); optimal depends on context
ISO-7 (emergence): multiplayer dynamics → emergent social structures; guilds, economies, politics from individual player rules
ISO-4 (phase transition): skill threshold → phase transition in gameplay; competence cliff where difficulty discontinuously shifts
ISO-14 (recursive self-similarity): procedural generation → recursive self-similar content; fractal terrain and dungeon layouts
