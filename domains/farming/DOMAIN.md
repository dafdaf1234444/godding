# Domain: Swarm Farming
Topic: How farming and agriculture concepts map to swarm knowledge production, resource cycles, quality filtering, and domain health. Covers the full farm-to-table loop: seeding frontiers, growing knowledge through experiment, harvesting lessons, composting via compaction, and rotating domains to prevent monoculture.
Beliefs: B-FAR1 (domain rotation prevents knowledge monoculture — low-diversity domain coverage reduces cross-domain isomorphism yield — THEORIZED), B-FAR2 (fallow periods after compaction restore lesson quality — pausing a domain for 1+ sessions before re-swarming improves Sharpe of next harvest — THEORIZED), B-FAR3 (companion planting: synergistic domain pairs produce more transferable insights than isolated domain work — THEORIZED)
Lessons: none yet
Frontiers: F-FAR1 (fallow principle), F-FAR2 (companion planting detection), F-FAR3 (monoculture risk)
Tool: `tools/farming_expert.py` — reads domain coverage, session crop data, and rotation health; outputs farming snapshot (JSON or human-readable)
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → domains/farming/tasks/FRONTIER.md

## Domain filter
Only farming/agriculture concepts with structural isomorphisms to swarm knowledge flows, session cycles, domain coverage, or lesson quality qualify. A concept must map to a concrete swarm metric or behavior to be included.

## Core model: The Swarm Farm Loop

```
SEED:     spawn session + open frontier          [planting]
GROW:     run experiment + accumulate evidence   [growing season]
HARVEST:  write lesson + promote principle       [harvest]
COMPOST:  compact.py removes zero-Sharpe         [compost / decomposition]
FALLOW:   domain rests; soil (proxy-K) recovers  [fallow period]
ROTATE:   next session picks different domain    [crop rotation]
POLLINATE: cross-domain isomorphism published    [pollination]
```

## Farming isomorphisms with swarm design

| Farming concept | Swarm parallel | Isomorphism type | Status |
|----------------|----------------|-----------------|--------|
| Seeding | Spawning a domain expert session, opening a frontier | Production initiation | OBSERVED |
| Growing season | Session cycle: experiment → evidence → lesson | Knowledge development | OBSERVED |
| Harvest | Lesson + principle written, frontier resolved | Knowledge capture | OBSERVED |
| Yield | L+P per session, Sharpe per lesson | Productivity measure | OBSERVED |
| Soil health | Proxy-K floor, knowledge base Sharpe avg | Substrate quality | OBSERVED |
| Fertilizer | Helper swarms accelerating domain work | Resource augmentation | OBSERVED (P-119) |
| Over-fertilization | Too many helpers → coordination overhead | Diminishing returns | OBSERVED (P-119) |
| Weeding | Compaction removing zero-Sharpe lessons | Quality filtering | OBSERVED (P-188) |
| Compost | Archived lessons: zero-Sharpe removed but remain in git history | Decomposed knowledge → substrate | OBSERVED |
| Crop rotation | Domain cycling: alternating domain focus across sessions | Monoculture prevention | THEORIZED (B-FAR1) |
| Fallow period | Domain pause after compaction → higher next-harvest Sharpe | Soil recovery | THEORIZED (B-FAR2) |
| Companion planting | Synergistic domain pairs (e.g. statistics+operations-research) | Mutual yield boost | THEORIZED (B-FAR3) |
| Monoculture risk | Focusing all sessions on one domain → brittle knowledge, fewer isomorphisms | Single-crop vulnerability | THEORIZED (F-FAR3) |
| Pollination | Cross-domain isomorphisms propagating to tasks/FRONTIER.md | Cross-fertilization | OBSERVED |
| Seed bank | Git history of archived lessons: accessible but dormant | Genetic reserve | OBSERVED |
| Irrigation | Proxy-K token flow to active lanes | Resource distribution | OBSERVED |
| Irrigation drought | Proxy-K >10% drift: resource starved, DUE/URGENT flags | Resource stress | OBSERVED (P-163) |
| Weather | Human signals, external constraints, WSL corruption | Uncontrolled forcing | OBSERVED |
| Grafting | Merging insights from external repos/ecosystems into swarm | Trait transfer | OBSERVED (L-276) |
| Canopy competition | Concurrent sessions competing for same lane/frontier | Resource contention | OBSERVED |
| Pest control | Handling git index corruption, ghost files, compaction reversal | Pathogen defense | OBSERVED (MEMORY.md) |
| Harvest timing | Compaction cycle: too early = waste, too late = rot | Timing optimization | THEORIZED |
| Intercropping | Multi-domain lanes running simultaneously | Parallel production | OBSERVED |
| Market price | Sharpe ratio as quality signal gating retention | Economic selection | OBSERVED (P-188) |

## Domain-to-crop analogy (active domains)

| Swarm domain | Crop analogy | Why |
|---|---|---|
| economy | Wheat | Staple grain — foundational production model |
| statistics | Legumes | Fixes the soil (calibration) for other crops |
| operations-research | Corn | High throughput, scheduler infrastructure |
| ai | Soybeans | Versatile; cross-domain protein (isomorphisms) |
| evolution | Perennial grass | Self-seeding, long timescale |
| brain | Root vegetables | Slow-growing, deep substrate |
| game-theory | Fruit trees | Coordination payoff takes seasons to mature |
| information-science | Herbs | Dense, aromatic, small-batch high-value |
| farming (this domain) | Cover crop | Improves soil for all other domains |

## Relationship to other domains
- **economy**: Farming is the production-side model; economy is the flow model. Farming provides the lifecycle framing (seed→harvest→compost) that economy treats as capital accumulation and depreciation.
- **evolution**: Crop rotation ≈ evolutionary cycling; fallow ≈ genetic drift periods; monoculture risk ≈ reduced genetic diversity. Companion planting ≈ symbiosis.
- **operations-research**: Planting schedules, harvest timing, and intercropping are OR scheduling problems. Farming provides the concrete vocabulary; OR provides the optimization formalism.
- **statistics**: Yield variance (Sharpe drift), field experiments (A/B compaction cycles), and sample size for rotation effects map directly to statistics domain gates.
- **ecology**: Not yet a swarm domain, but companion domain candidate — ecosystem balance maps to domain portfolio balance.

## Isomorphism vocabulary
ISO-5 (feedback — stabilizing): crop rotation → stabilizing feedback on soil nutrient depletion; polyculture restores equilibrium
ISO-4 (phase transition): soil degradation threshold → phase transition from fertile to degraded; irreversible desertification
ISO-2 (selection → attractor): selective breeding → selection pressure narrows genetic diversity; monoculture = diversity collapse attractor
ISO-6 (entropy): soil carbon loss → entropy accumulation; topsoil entropy increases without organic matter input
ISO-13 (integral windup): pesticide resistance accumulation → integral windup; resistance builds without discharge mechanism
ISO-8 (power laws): yield distribution → power-law across farm sizes; land concentration follows Pareto distribution
