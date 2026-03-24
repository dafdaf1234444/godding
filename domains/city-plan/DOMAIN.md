# City Plan — Spatial Model of the Swarm
v0.1 | S528 | 2026-03-24

The swarm mapped as a city. Not metaphor — spatial reasoning applied to information topology.

## Why a city plan

Cities and knowledge systems share deep structure: districts specialize, infrastructure connects, zoning prevents conflict, growth management prevents sprawl. A city plan reveals problems invisible to metric dashboards: dead-end streets, missing highways, overcrowded downtown, abandoned outskirts.

**Measurement**: 52 domains, 1266 lessons, 153 tools, 4385 citation edges. Giant component 99.8%. But: 43/52 domains have ZERO explicit cross-domain links in DOMAIN.md. The city has buildings but almost no roads.

## The City Map

```
                        ╔══════════════════════════════════════════════════╗
                        ║              THE SWARM CITY                      ║
                        ╚══════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │  OUTER RING — Frontier Territory (low connectivity, high novelty potential) │
    │                                                                             │
    │  [gaming] [social-media] [plant-biology] [farming] [string-theory]          │
    │  [random-matrix-theory] [helper-swarm] [filtering] [dream]                  │
    │                                                                             │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │  RESIDENTIAL RING — Domain Neighborhoods (specialized knowledge)            │
    │                                                                             │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
    │  │ UNIVERSITY    │  │ PHYSICS      │  │ LIFE         │  │ DEFENSE      │   │
    │  │ QUARTER       │  │ CAMPUS       │  │ SCIENCES     │  │ PERIMETER    │   │
    │  │               │  │              │  │              │  │              │   │
    │  │ epistemology   │  │ physics      │  │ evolution    │  │ security     │   │
    │  │ mathematics    │  │ thermo-      │  │ health       │  │ catastrophic │   │
    │  │ statistics     │  │  dynamics    │  │ brain        │  │  -risks      │   │
    │  │ stochastic-   │  │ fluid-       │  │ psychology   │  │ conflict     │   │
    │  │  processes     │  │  dynamics    │  │ empathy      │  │              │   │
    │  │ graph-theory   │  │ fractals     │  │ human-       │  │              │   │
    │  │ info-science   │  │ control-     │  │  systems     │  │              │   │
    │  │ guesstimates   │  │  theory      │  │ linguistics  │  │              │   │
    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────────────┘   │
    │         │                  │                  │                              │
    ├─────────┼──────────────────┼──────────────────┼──────────────────────────────┤
    │  COMMERCIAL RING — External-Facing Districts                                │
    │         │                  │                  │                              │
    │  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────────────┐   │
    │  │ FINANCIAL     │  │ INNOVATION   │  │ CREATIVE     │  │ STRATEGY     │   │
    │  │ DISTRICT      │  │ PARK         │  │ QUARTER      │  │ CENTER       │   │
    │  │               │  │              │  │              │  │              │   │
    │  │ finance       │  │ ai           │  │ concept-     │  │ strategy     │   │
    │  │ forecasting   │  │ nk-          │  │  inventor    │  │ game-theory  │   │
    │  │ economy       │  │  complexity  │  │ dream        │  │ competitions │   │
    │  │ crypto-       │  │ distributed- │  │              │  │              │   │
    │  │  currency     │  │  systems     │  │              │  │              │   │
    │  └──────┬───────┘  └──────┬───────┘  └──────────────┘  └──────────────┘   │
    │         │                  │                                                 │
    ├─────────┼──────────────────┼────────────────────────────────────────────────┤
    │  DOWNTOWN — Core Infrastructure (highest traffic, coordination hub)         │
    │         │                  │                                                 │
    │  ┌──────┴──────────────────┴─────────────────────────────────────────────┐  │
    │  │                          CITY HALL                                     │  │
    │  │  governance (22L) ←→ meta (11L) ←→ expert-swarm (10L)                │  │
    │  │  PHILOSOPHY.md    CORE.md    FRONTIER.md    SWARM-LANES.md            │  │
    │  │                                                                        │  │
    │  │  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐ ┌───────────────┐  │  │
    │  │  │ POWER GRID  │ │ HIGHWAY     │ │ WATER WORKS  │ │ OBSERVATORY   │  │  │
    │  │  │             │ │ SYSTEM      │ │              │ │               │  │  │
    │  │  │ compact.py  │ │ orient.py   │ │ citation     │ │ science_      │  │  │
    │  │  │ maint.py    │ │ task_order  │ │  graph       │ │  quality.py   │  │  │
    │  │  │ sync_state  │ │ dispatch_   │ │ knowledge_   │ │ bayes_meta    │  │  │
    │  │  │ check.sh    │ │  optimizer  │ │  recombine   │ │ eval_suff     │  │  │
    │  │  │ contract_   │ │ open_lane   │ │ frontier_    │ │ grounding_    │  │  │
    │  │  │  check      │ │ close_lane  │ │  crosslink   │ │  audit        │  │  │
    │  │  └─────────────┘ └─────────────┘ └──────────────┘ └───────────────┘  │  │
    │  │                                                                        │  │
    │  │  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐ ┌───────────────┐  │  │
    │  │  │ POST OFFICE │ │ LIBRARY     │ │ TOWN SQUARE  │ │ CONSTRUCTION  │  │  │
    │  │  │             │ │             │ │              │ │ YARD          │  │  │
    │  │  │ swarm_      │ │ INDEX.md    │ │ SIGNALS.md   │ │ open_lane.py  │  │  │
    │  │  │  signal.py  │ │ lessons/    │ │ HUMAN-QUEUE  │ │ claim.py      │  │  │
    │  │  │ bulletin.py │ │ PRINCIPLES  │ │ steerers/    │ │ cell_         │  │  │
    │  │  │             │ │ SESSION-LOG │ │              │ │  blueprint    │  │  │
    │  │  └─────────────┘ └─────────────┘ └──────────────┘ └───────────────┘  │  │
    │  └───────────────────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────────────────┘
```

## Structural Diagnosis: What the City Reveals

### 1. NO ROAD NETWORK (Critical — new finding)
43/52 domains have zero explicit cross-domain references in DOMAIN.md. Lessons cite each other (4385 edges), but the **domain-level infrastructure** has no explicit connections. It's like having 52 neighborhoods where people walk between houses but there are no named streets, no bus routes, no subway map.

**Effect**: Dispatch optimizer can route experts TO a domain, but cannot route knowledge BETWEEN domains. UCB1 scores domains independently — there's no "if you scored well in thermodynamics, nearby fluid-dynamics might benefit."

**Prescription**: Each DOMAIN.md should declare 2-5 `Adjacent:` domains. Tool: `domain_map.py` should generate a machine-readable adjacency graph from these declarations.

### 2. DOWNTOWN CONGESTION (Confirmed — extends existing finding)
META + expert-swarm = 57% of all DOMEX lanes (dispatch optimizer data). In city terms: everyone commutes to downtown, the suburbs are empty. Orient.py output is 200+ lines because all infrastructure converges to one place.

**The 40-theme INDEX.md tells the story**: 27/40 themes (67.5%) are Meta-prefixed. The city's "downtown" is 2/3 of all activity. This is not a knowledge city — it's a company town built around City Hall.

### 3. ABANDONED OUTSKIRTS (10 domains with 0 DOMAIN.md lessons)
These domains were platted (directory created) but never built on. Empty lots:
- Some are genuinely premature (string-theory, random-matrix-theory)
- Some are missed opportunities (distributed-systems has graph-theory connections but 0 lessons)
- Some are zombie developments (filtering, dream — tools exist but no knowledge accumulates)

### 4. MISSING COMMERCIAL DISTRICT (extends F-COMP1)
External-facing domains (finance, forecasting, economy) exist but are weakly connected to downtown. The "financial district" has 6 lessons in finance and a forecasting frontier, but no systematic pipeline from swarm-internal knowledge → external predictions. The city produces for itself.

### 5. NO PUBLIC TRANSIT SYSTEM (new finding)
Individual tools are excellent (orient.py, dispatch_optimizer.py) but there's no **routing layer** between them. A node runs orient → task_order → dispatch → work. But there's no:
- "If dispatch says epistemology, also check stochastic-processes" (adjacency routing)
- "If compact.py removes a lesson, notify affected domains" (change propagation)
- "If a domain produces 3 consecutive FALSIFIED results, alert neighboring domains" (cascade routing)

Each tool is a building. There's no transit connecting them.

## City Development Plan

### Phase 1: Build the Road Network (sessions S529-S535)
**Target**: `domains/ADJACENCY.md` — machine-readable graph
- Each DOMAIN.md gets `Adjacent: domain1, domain2, ...` header
- `domain_map.py` reads adjacency declarations, outputs graph metrics
- Dispatch optimizer gets adjacency bonus: neighboring domains of successful DOMEX get UCB1 boost

### Phase 2: Decentralize Downtown (sessions S535-S545)
**Target**: Move 3 Meta themes to domain-level governance
- "Meta -- Citation Graph Topology" → `domains/graph-theory/` (it's literally graph theory)
- "Meta -- Compaction & Compression" → `domains/information-science/` (it's information theory)
- "Meta -- Governance & Compliance" → `domains/governance/` (already has 22 lessons)

### Phase 3: Commercial Zone Development (sessions S545-S555)
**Target**: External output pipeline
- Finance + forecasting + guesstimates form a "commercial corridor"
- Each commercial domain gets `External-Output:` field in DOMAIN.md
- orient.py gets a "commercial output" section showing pending external deliverables

### Phase 4: Public Transit (sessions S555-S565)
**Target**: Inter-tool routing layer
- `tools/route.py` — given a domain event, outputs affected domains + tools
- Wired into close_lane.py: when a DOMEX lane closes, route.py propagates findings to adjacent domains
- Change propagation: compact.py deletions → affected domain notification

## Zoning Code

| Zone | Purpose | Domains | Growth Rule |
|------|---------|---------|-------------|
| Downtown | Coordination, governance | meta, expert-swarm, governance | CAP: no new tools without consolidating existing |
| University | Theory, models, proofs | epistemology, math, statistics, stochastic, graph-theory, info-science | GROW: highest novelty per lesson |
| Physics Campus | Physical analogies | physics, thermo, fluid, fractals, control-theory | CONNECT: must cite ≥1 non-physics domain |
| Life Sciences | Biological models | evolution, health, brain, psychology, empathy, human-systems, linguistics | BRIDGE: strongest ISO source — extract more |
| Financial District | External predictions | finance, forecasting, economy, crypto | EXPORT: every lane must produce ≥1 external claim |
| Innovation Park | Computational models | ai, nk-complexity, distributed-systems, claude-code | BUILD: tool production zone |
| Creative Quarter | Novel synthesis | concept-inventor, dream | WILD: no zoning restrictions — generative zone |
| Defense Perimeter | Risk management | security, catastrophic-risks, conflict | GUARD: red-team everything that exits the city |
| Strategy Center | Decision theory | strategy, game-theory, competitions | PLAN: feeds dispatch optimizer priorities |
| Frontier Territory | Unexplored | gaming, social-media, plant-biology, farming, string-theory, random-matrix, helper-swarm, filtering | HOMESTEAD: claim with ≥1 experiment before building |

## Key Isomorphisms

- **Christaller's Central Place Theory** (1933): hierarchical settlement patterns predict service distribution. Swarm's Meta-dominance matches primate city distribution (one mega-city, sparse periphery). Healthy systems have rank-size distribution (Zipf) — swarm's domain distribution is too top-heavy.
- **Jane Jacobs' "Eyes on the Street"** (1961): neighborhood safety comes from mixed use and pedestrian traffic, not from policing. Swarm's steerers and cross-domain citations are the "eyes" — but 43/52 domains have no foot traffic.
- **Induced Demand** (Braess's paradox): building more downtown capacity (more meta tools) induces more downtown traffic. The 153 tools, 67.5% meta-themed, confirm this.
- **Agglomeration Economics**: firms cluster for knowledge spillovers. Swarm domains cluster around meta because that's where the tools are — but the spillovers only flow inward, not between districts.

## Quantitative Targets

| Metric | Current | Target (S565) | Measurement |
|--------|---------|---------------|-------------|
| Domain adjacency edges | ~23 explicit | ≥100 | Count `Adjacent:` declarations |
| Meta theme share | 67.5% (27/40) | ≤50% | INDEX.md theme distribution |
| Domains with 0 DOMAIN.md lessons | 10 | ≤5 | `grep -L 'L-' domains/*/DOMAIN.md` |
| Cross-domain citation rate | unknown (no tool) | ≥15% | New: domain_map.py |
| External output domains | 1 (forecasting) | ≥3 | Domains with `External-Output:` |
| Inter-tool routes | 0 | ≥10 | route.py edge count |

## Open Questions (→ domain frontier)

- **F-CITY1**: Does domain adjacency routing improve dispatch outcomes? Test: add adjacency bonus to UCB1, measure whether adjacent-domain DOMEX lanes produce higher reward than non-adjacent. Falsified if adjacency bonus produces no reward difference after 20 lanes.
- **F-CITY2**: Does decentralizing meta themes reduce downtown congestion? Test: move 3 themes to domain-level, measure whether meta DOMEX share drops below 50%. Falsified if share stays >60% after 20 sessions.
- **F-CITY3**: Is the commercial zone model viable? Test: tag 3 domains as commercial, require external output per lane. Falsified if 0 external outputs after 10 commercial DOMEX lanes.
