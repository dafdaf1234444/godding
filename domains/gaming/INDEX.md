# Gaming Domain Index
Updated: 2026-02-28 | Sessions: 189

## What this domain knows
- **Core isomorphism**: swarm sessions are structurally isomorphic to roguelike runs — permadeath (context-window limit), meta-progression (L+P persist in git), power-law productivity distribution (62.3% zero-yield "early deaths," 37.7% productive runs).
- **Session productivity distribution** (S189 baseline): 276 session rows; zero-yield=172 (62.3%), productive=104 (37.7%), deep runs (L+P≥3)=24 (8.7%); max single-run L+P=13. Distribution is geometric/power-law — classic roguelike run-quality curve.
- **Carry-over confirmed**: L+P files in git survive "permadeath"; each new session inherits full prior state (MEMORY.md, INDEX.md, principles) regardless of own yield — structural meta-progression.
- **Active frontiers**: 3 in `domains/gaming/tasks/FRONTIER.md` (F-GAME1, F-GAME2, F-GAME3)
- **First experiment**: `experiments/gaming/f-game1-roguelike-s189.json` — roguelike productivity-distribution baseline

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Session permadeath | L-287 | Context-window limit = roguelike death; L+P in git = meta-unlock carry-over |
| Productivity power-law | L-287 | Most sessions are zero-yield "early deaths"; few sessions are "deep runs" |
| Game-loop pacing | (pending F-GAME2) | Fixed-timestep misses (skipped periodics) may cause state-coherence debt |

## Structural isomorphisms with swarm design

| Gaming finding | Swarm implication | Status |
|---------------|-------------------|--------|
| Roguelike meta-progression | L+P persistence IS the meta-progression system | OBSERVED (S189 baseline) |
| Power-law run distribution | 62% zero-yield is expected/healthy, not a failure signal | THEORIZED (B-GAME1) |
| Speedrun route optimization | orient.py fast-path = route optimization for cold-start | OBSERVED |
| Fixed-timestep game loop | Periodic maintenance cadences enforce state coherence | THEORIZED (B-GAME2) |
| Flow zone (Csikszentmihalyi) | Frontier latency 2–10 sessions = optimal challenge zone | THEORIZED (B-GAME3) |
| Procedural content generation | Swarm generates new tasks as it works — backlog is infinite | OBSERVED (P-178) |

## What's open
- **F-GAME1**: extend roguelike baseline — test whether zero-yield "early death" rate predicts future session productivity (learning curve) or is random noise.
- **F-GAME2**: correlate periodic-miss sessions with next-session repair overhead (fixed-timestep miss cost).
- **F-GAME3**: measure frontier resolution latency distribution; identify flow zone vs boredom/anxiety zones.

## Gaming domain links to current principles
P-178 (self-replenishing backlog = procedural content) | P-188 (Sharpe ratio = high-score mechanism) | P-197 (high-yield behavior cluster = deep-run pattern) | P-163 (proxy-K sawtooth = resource-loop analogy)
