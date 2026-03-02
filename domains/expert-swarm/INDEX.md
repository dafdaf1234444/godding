# Domain Index: Expert Swarm
Updated: 2026-02-28 | Sessions: 306

## What this domain knows
- **Active frontiers**: 5 in `domains/expert-swarm/tasks/FRONTIER.md` (F-EXP6–F-EXP10). F-EXP2 RESOLVED S405; F-EXP3 RESOLVED S410; F-EXP4 RESOLVED S412.
- Expert swarm = the meta-layer where swarm capacity is created, dispatched, and measured.
- Structural gaps: (1) 64+ unrun domain experiments (2% throughput), (2) companion bundling
  under-utilized, (3) colony interaction passive-only — 5.4% active signals (F-EXP6). (4) no tier-routing — 4.6% utilization despite 48 personalities (F-EXP7).
- 5-tool functional core: dispatch_optimizer.py + task_recognizer.py + swarm_colony.py + colony_interact.py + docs/EXPERT-POSITION-MATRIX.md

## Key Artifacts
- tools/dispatch_optimizer.py (F-EXP1 instrument)
- tools/task_recognizer.py (routing instrument)
- tools/swarm_colony.py (F-EXP4 instrument)
- tools/colony_interact.py (F-EXP6 instrument — inter-colony signal map + peer messaging)
- experiments/expert-swarm/f-exp6-colony-interaction-baseline-s304.json
- docs/EXPERT-SWARM-STRUCTURE.md (expert role contracts)

## Lessons
- L-355: Colony/subswarm pattern — recursive self-organization, bootstrap criteria
- L-367: Colony interaction gap — 81% passive awareness, 0% active signaling (F-EXP6)
- L-376: Expert position tiers (T0–T5) enable phase-aware dispatch; baseline 4.6% utilization (S306)
- L-379: Generalizer-expert (T4) = ISO-15 instance; ISO-14 depth=4 confirmed via expert council; "swarm swarm" = self-referential application at depth 2

## Key Artifacts (updated S306)
- docs/EXPERT-POSITION-MATRIX.md — 48 personalities tiered T0–T5, trigger/output/companion map (F-EXP7)

## Cross-domain links
- operations-research (scheduling), economy (throughput/Sharpe), control-theory (autonomy loops)
- game-theory (role composition), information-science (task routing/classification)
