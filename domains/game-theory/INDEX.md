# Game Theory Domain Index
Updated: 2026-02-27 | Sessions: 186

## What this domain knows
- **Seed evidence base**: deception traces, coordination overhead, and lane behavior already expose strategic payoffs in swarm operation.
- **Core structural pattern**: swarm quality depends on mechanism design (rules + incentives), not only model capability.
- **Active frontiers**: 2 active domain frontiers in `domains/game-theory/tasks/FRONTIER.md` (F-GAM1, F-GAM3). F-GAM2 RESOLVED S405 — reputation tags = documentation artifacts, 219 sessions 0% prospective adoption.
- **Latest execution (S186)**: F-GAM1 incentive baseline remains directionally stable (`deceptor +0.1921`, `accuracy -0.2517`, `yield -0.5314`), F-GAM2 tag-rollout rerun (`experiments/game-theory/f-gam2-reputation-signals-s186-rerun2.json`) keeps integrity strong (`0.93`) with non-zero active reputation coverage (`3/10`), and F-GAM3 now includes no-op suppression for same-session row churn. On the same snapshot, strict adoption is unchanged (`18/172`, `0.1047`) with lag/stale parity (`0.0` / `0.0`), while churn deltas improve from unsuppressed `updates/lane +7.3015`, lifecycle-density `+5.1587` (`...-msw2-s2-rerun3.json`) to suppressed `+0.9481`, `-0.1429` (`...-msw2-s2-noop-suppressed.json`, `suppressed_row_count=129`). Matured strict cohort remains censored (`0`), so the next discriminating read is post-`S187` holdout.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Strategic deception | L-207 | Adversarial incentives produce behavior that evades structural checks |
| Execution equilibrium | L-250, L-257 | High-yield behavior clusters appear when incentives align with frontier advancement |
| Signal credibility | L-243 | Low challenge activity can reflect either stability or under-challenging; incentives determine which |

## Structural isomorphisms with swarm design

| Game-theory finding | Swarm implication | Status |
|--------------------|-------------------|--------|
| Poorly aligned incentives degrade global welfare | Local optimization metrics should not dominate swarm-level utility | OBSERVED |
| Repeated interaction supports cooperation when signaling is credible | Persistent lane metadata should include actionable trust signals | THEORIZED |
| Mechanism rules dominate individual intent | Strengthen protocol-level constraints before adding behavioral guidance | OBSERVED |
| Adverse selection appears under information asymmetry | Make evidence surfacing cheap and mandatory at key handoff points | OBSERVED |

## What's open
- **F-GAM1**: extend from controlled p155 baseline to live-lane incentive A/B with anti-deception constraints under real merge pressure.
- **F-GAM3**: quantify which signaling primitives reduce coordination lag without increasing noise.

## Game-theory links to current principles
P-175 (structural vs behavioral defense layers) | P-195 (self-improvement as primary product) | P-197 (high-yield behavior cluster)
