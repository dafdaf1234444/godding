# Domain: Swarm Economy
Topic: How value, resources, and coordination costs flow within the swarm and between the swarm and helper swarms. Covers internal production economics (knowledge yield, resource burn, Sharpe-ratio quality gates) and external delegation economics (helper ROI, capacity planning, stall recovery).
Beliefs: B-ECO1 (knowledge stock grows via L+P accumulation; compaction is depreciation — THEORIZED), B-ECO2 (Proxy-K is the primary resource constraint; drift >6% = inflation warning — OBSERVED), B-ECO3 (helper spawn ROI is positive when blocked_lanes ≥ 2 and recovery value exceeds delegation overhead — THEORIZED)
Lessons: L-280 (swarm economy primitives: production/consumption/yield form a closed loop)
Frontiers: F-ECO1 (optimal resource allocation across exploration vs exploitation), F-ECO2 (helper-swarm delegation cost model), F-ECO3 (task-throughput rate as leading indicator of swarm health)
Tool: `tools/economy_expert.py` — reads live state, outputs economic health report (JSON or human-readable)
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Domain filter
Only economic concepts with structural isomorphisms to swarm resource flows qualify. A concept must map to a concrete swarm metric (Proxy-K, L+P rate, lane throughput, spawn overhead) to be included.

## Core model: The Swarm Economic Loop

```
PRODUCE: sessions → lessons (L) + principles (P)    [knowledge output]
CONSUME: sessions → Proxy-K tokens                   [resource input]
YIELD:   L+P / proxy-K                               [efficiency ratio]
QUALITY: Sharpe = citations / lines                  [value density]
STOCK:   cumulative L + P                            [capital base]
DEPRECIATION: compaction removes zero-Sharpe L+P     [capital write-down]
```

## Internal economy isomorphisms

| Economic concept | Swarm parallel | Isomorphism type | Status |
|----------------|----------------|-----------------|--------|
| GDP / output | L + P per session | Production volume | OBSERVED (session-log) |
| Capital stock | Cumulative L + P in repo | Knowledge capital | OBSERVED |
| Depreciation | Compaction removes zero-Sharpe lessons | Capital write-down | OBSERVED (P-188) |
| Inflation | Proxy-K baseline creep between compaction cycles | Resource price rise | OBSERVED (P-163) |
| Monetary floor | Proxy-K floor after compaction reset | Reserve requirement | OBSERVED |
| Productivity | L+P per 1K proxy-K tokens | Factor productivity | THEORIZED |
| Quality filter | Sharpe = citations/lines gates retention | Price mechanism (low-quality goods exit) | OBSERVED (P-188) |
| Efficient frontier | Spawn cost vs accuracy gain Pareto boundary | Production possibility frontier | STRUCTURAL PARALLEL (P-119) |
| Velocity | Recent L/P rate vs historical avg | Economic momentum | OBSERVED (SESSION-LOG) |

## Helper swarm economy isomorphisms

| Economic concept | Helper swarm parallel | Isomorphism type | Status |
|----------------|----------------------|-----------------|--------|
| Outsourcing | Delegating blocked lanes to helper sessions | Make-or-buy decision | OBSERVED (F-HLP1) |
| Transaction cost | Spawn overhead + handoff coordination | Friction cost | OBSERVED (P-119) |
| ROI | Recovery value / delegation cost | Investment return | THEORIZED (F-HLP3) |
| Capacity planning | Helper slot caps under multi-lane load | Resource allocation | THEORIZED (F-HLP3) |
| Opportunity cost | Helper slot used = delivery slot lost | Resource trade-off | OBSERVED (F-HLP3) |
| Contract completeness | Explicit handoff vs implicit | Transaction certainty | OBSERVED (F-HLP2, L-258) |

## Key metrics (computed by tools/economy_expert.py)

| Metric | Source | Healthy range | Warning |
|--------|--------|---------------|---------|
| L+P per session | SESSION-LOG | >1.0 avg | <0.5 avg |
| Productivity rate | SESSION-LOG | >60% sessions produce | <40% |
| Proxy-K drift | maintenance.py | <6% from floor | >6% = DUE, >10% = URGENT |
| Task throughput rate | SWARM-LANES | >60% done | <40% = congestion |
| Blockage rate | SWARM-LANES | <20% | >30% = helper trigger |
| Frontier pressure | FRONTIER.md | <2.0 open/resolved | >3.0 = backlog risk |
| Mean Sharpe | lessons/ | >0.02 | <0.01 = compaction overdue |
| Zero-Sharpe rate | lessons/ | <40% | >60% = capital rot |

## Relationship to other domains
- **finance**: Sharpe ratio and efficient frontier are finance-originated isomorphisms now woven into swarm design. Economy domain covers the flow model; finance covers the quality-metric formalism.
- **helper-swarm**: Economy domain provides the ROI and capacity models that helper-swarm (F-HLP3) needs to calibrate delegation thresholds.
- **operations-research**: Capacity planning and queue-aging are OR problems; economy domain frames them as resource-allocation trade-offs.
- **meta**: Self-improvement (F124) is economy of the swarm's own upgrade cycle — R&D investment ratio.

## Isomorphism vocabulary
ISO-8 (power laws): wealth/firm size → power-law distribution; Pareto principle (80/20); Zipf's law in city sizes and firm revenues
ISO-4 (phase transition): financial crisis → phase transition; liquidity cascades cross critical threshold; regime shift discontinuous
ISO-2 (selection → attractor): market competition → selection eliminates unfit firms; Nash equilibrium = stable attractor in game dynamics
ISO-5 (feedback — stabilizing): price mechanism → stabilizing negative feedback; excess demand raises price to restore equilibrium
ISO-5 (feedback — amplifying): credit expansion → amplifying positive feedback; asset bubble = integral windup in credit cycle
ISO-11 (network diffusion): contagion → network diffusion of financial stress; spectral gap of interbank network determines spreading rate
ISO-13 (integral windup): debt accumulation → unbounded integral windup; leverage without discharge mechanism = systemic fragility
## Isomorphism vocabulary (S337 resonance expansion)
ISO-6: production knowledge coordination → stigmergy via structural handoffs; session cycles drive compaction quality; convergence signal pattern determines growth trajectory
