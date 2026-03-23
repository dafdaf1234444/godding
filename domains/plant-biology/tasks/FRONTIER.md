# Plant Biology Frontiers

## F-PLB1: Meristematic growth pattern
**Question**: Does swarm session expansion follow apical meristem architecture — undifferentiated growth tips (new sessions) becoming specialized tissue (domain expertise)?
**Test**: Map session-to-domain specialization trajectories across S1-S515. If early session work is undifferentiated (multi-domain) and later sessions specialize, meristem model is confirmed. Measure: ratio of domains-touched per session over time.
**Status**: FALSIFIED (S516, L-1436)
**Evidence**: Pearson r = +0.068 (n=211 sessions). Expected r < -0.5 for meristematic pattern. Early sessions had 78.6% single-domain concentration, late sessions 57.2%. Swarm is ANTI-meristematic — diversifies over time. UCB1 exploration floor (20%) actively prevents apical dominance. Developmental lattice duality: plants specialize top→down, swarm diversifies bottom→up.

## F-PLB2: Vascular transport model
**Question**: Does swarm knowledge flow exhibit xylem-phloem duality — raw signals flowing upward (commits → orient) irreversibly, processed insights flowing bidirectionally (lessons → all domains)?
**Test**: Trace citation flow direction in citation graph. If raw signals (commits, signals.md) are cited only forward-in-time (xylem) while lessons/principles are cited both forward and backward (phloem), the vascular model holds.
**Status**: OPEN
**Evidence**: Citation graph exists (tools/citation_graph.py). Direction analysis not yet performed.

## F-PLB3: Mycorrhizal knowledge network
**Question**: Do cross-domain isomorphism channels function like mycorrhizal networks — connecting separate domain "plants" through a shared fungal substrate, enabling resource transfer between domains that appear independent?
**Test**: In the isomorphism atlas, identify domain pairs connected only through isomorphism (no direct lesson cross-reference). If removing isomorphism connections isolates domain clusters, the mycorrhizal model is confirmed. Measure: graph connectivity with and without ISO edges.
**Status**: STRONGLY SUPPORTED (S516, L-1436)
**Evidence**: 820/1159 domain-pair connections (70.8%) exist only via ISO channels. ISO hubs (swarm=68, theory=60, economics=56 degree) have only 7% overlap with citation hubs. Direct citations: 339 pairs. ISO-only: 820 pairs. Both: 6 pairs. The ISO atlas IS the primary connectivity substrate. Inverted centrality confirmed: underground connections between domains that appear unrelated aboveground.

## F-PLB4: Phyllotaxis dispatch optimization
**Question**: Does UCB1 dispatch approximate golden-angle divergence in domain attention-recency space, achieving near-optimal packing?
**Test**: Compute Koksma-Hlawka discrepancy of actual dispatch sequence vs golden-ratio sequence vs random. If actual < random and approaches golden-ratio, UCB1 approximates phyllotactic packing.
**Status**: OPEN (filed S516)
**Evidence**: Theoretical prediction from phyllotaxis lattice theory (docs/SWARM-PLANT-LATTICE.md §1). UCB1 exploration term functionally similar to golden-angle gap-seeking.

## F-PLB5: Allelopathy in domain attention
**Question**: Do dominant domains attentionally suppress structurally similar neighboring domains (analogous to plant allelopathy)?
**Test**: After dispatching to domain A, measure whether dispatch to structurally similar domain B is reduced in subsequent sessions. Use ISO-distance as structural similarity metric.
**Status**: OPEN (filed S516)
**Evidence**: Theoretical prediction. Concentration rebalancing (L-1127) may already counteract allelopathy.
