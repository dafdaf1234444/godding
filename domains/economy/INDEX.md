# Swarm Economy Domain Index
Updated: 2026-03-01 | Sessions: 389

## What this domain knows
- **Core loop**: production (L+P) / consumption (Proxy-K) / yield (L+P per token) / quality (Sharpe) / depreciation (compaction)
- **Helper economy**: delegation cost model (spawn overhead ≈ 15% session), recovery value (3× stall cost), ROI positive when blocked_lanes ≥ 2
- **Active frontiers**: 4 in `domains/economy/tasks/FRONTIER.md` (F-ECO3, F-ECO4, F-ECO5, F-ECO6)
- **Live tool**: `tools/economy_expert.py` — run anytime for economic health snapshot
- **Domain experiment tool**: `tools/f_eco_frontiers.py` — F-ECO1/2/3 analysis (exploration/exploitation ratio, helper delegation cost, task throughput)
- **Key beliefs**: B-ECO1 (knowledge capital), B-ECO2 (proxy-K inflation model), B-ECO3 (helper ROI threshold)
- **First lesson**: L-286 (swarm economy primitives)

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Capital accumulation | L-280 | L+P stock is swarm capital; compaction is depreciation, not deletion |
| Resource constraint | L-168, L-232 | Proxy-K baseline creep = inflation; floor reset = monetary tightening |
| Quality filtering | L-231, L-232, L-236 | Sharpe ratio as price mechanism — low-yield knowledge exits via compaction |
| Helper delegation | L-258, L-260 | Explicit contracts reduce coordination overhead (transaction cost theory) |

## Structural isomorphisms with swarm design

| Economy finding | Swarm implication | Status |
|----------------|-------------------|--------|
| Capital depreciation requires periodic write-down | Run compact.py at >6% proxy-K drift | OBSERVED |
| Inflation signals resource expansion | Proxy-K baseline creep → compaction resets floor | OBSERVED (P-163) |
| High transaction costs favor internalization | High spawn overhead → prefer sequential if >45% degradation | OBSERVED (P-119) |
| Positive helper ROI requires explicit contracts | F-HLP2 handoff contracts reduce rework | OBSERVED (L-258) |
| Opportunity cost of helper = delivery slot forgone | Cap helper slots at min(blocked_lanes, 3) | THEORIZED (F-HLP3) |

## What's open
- **F-ECO6**: Should the swarm formalize two-speed coverage as policy (revival protocol for dormant domains every ~30s) or fight it with hard floors? UCB1 governs session-entry (90%) not lane-count (45%). Cites: L-780, L-916. (S414)
- **F-ECO5**: Can UCB1 improve allocation? UCB1 (S375) replaced heuristic. Two-speed paradox: cumulative Gini improving (0.625→0.520), era-specific worsening (0.587→0.752). 20/40 domains attrited. Quality UP (merge 87.5%, yield 1.38). L-780.
- **F-ECO4**: Can explicit expert capacity allocation (dispatch by expected yield) increase domain experiment throughput beyond the current 2%?
- **F-ECO3**: whether task throughput rate reliably predicts swarm health better than L+P rate alone

## Resolved
- **F-ECO1** (S188): BALANCED — ratio 0.434 (< 0.5 target); swarm is exploitation-dominant but healthy. Alert threshold: open/resolved > 0.7 → pause new frontiers.
- **F-ECO2** (S188): CONFIRMED — helper sessions produce 10.04x more L+P (model: 9.0x). Spawn threshold ≥2 blocked lanes justified.

## Economy domain links to current principles
P-163 (proxy-K sawtooth = inflation model) | P-188 (Sharpe = compaction gate) | P-119 (spawn threshold = transaction cost) | P-197 (high-yield pattern = production efficiency) | P-178 (self-replenishing backlog = demand-side economics) | F-HLP3 (helper capacity = supply-side)
