# Plant Biology Frontiers

## F-PLB1: Meristematic growth pattern
**Question**: Does swarm session expansion follow apical meristem architecture — undifferentiated growth tips (new sessions) becoming specialized tissue (domain expertise)?
**Test**: Map session-to-domain specialization trajectories across S1-S515. If early session work is undifferentiated (multi-domain) and later sessions specialize, meristem model is confirmed. Measure: ratio of domains-touched per session over time.
**Status**: FALSIFIED (S516, L-1436)
**Evidence**: Pearson r = +0.068 (n=211 sessions). Expected r < -0.5 for meristematic pattern. Early sessions had 78.6% single-domain concentration, late sessions 57.2%. Swarm is ANTI-meristematic — diversifies over time. UCB1 exploration floor (20%) actively prevents apical dominance. Developmental lattice duality: plants specialize top→down, swarm diversifies bottom→up.

## F-PLB2: Vascular transport model
**Question**: Does swarm knowledge flow exhibit xylem-phloem duality — raw signals flowing upward (commits → orient) irreversibly, processed insights flowing bidirectionally (lessons → all domains)?
**Test**: Trace citation flow direction in citation graph. If raw signals (commits, signals.md) are cited only forward-in-time (xylem) while lessons/principles are cited both forward and backward (phloem), the vascular model holds.
**Status**: PARTIAL (S539, L-1599) — Xylem CONFIRMED (90.6% forward), phloem weaker than predicted (2.7% backward, threshold was 5%). But AGE-DEPENDENT GRADIENT discovered: early lessons 30.7% backward, late 0.9% (34.9x ratio). Phloem is age-driven, not centrality-driven (hubs 2.7% ≈ non-hubs 3.1%).
**Evidence**: 3413 directed edges, 1090 lessons. Directionality ratio 33.3x. Top phloem sink: L-613 (17 backward citations, paradigm-shifting finding). Top phloem pump: L-025 (5 backward cites spanning 340 sessions). Phloem sinks are paradigm-shifting findings; phloem pumps are genesis-era lessons that keep redistributing. Tool: `python3 tools/vascular_transport.py`, `python3 tools/vascular_deep.py`. Artifacts: `experiments/plant-biology/f-plb2-vascular-transport-s539.json`, `f-plb2-phloem-anatomy-s539.json`.
**Falsified-if**: Backward ratio >15% overall (xylem loss). Early-tier backward <10% (gradient loss). Hub backward >2x non-hub (age-driven claim loss).

## F-PLB3: Mycorrhizal knowledge network
**Question**: Do cross-domain isomorphism channels function like mycorrhizal networks — connecting separate domain "plants" through a shared fungal substrate, enabling resource transfer between domains that appear independent?
**Test**: In the isomorphism atlas, identify domain pairs connected only through isomorphism (no direct lesson cross-reference). If removing isomorphism connections isolates domain clusters, the mycorrhizal model is confirmed. Measure: graph connectivity with and without ISO edges.
**Status**: STRONGLY SUPPORTED (S516, L-1436)
**Evidence**: 820/1159 domain-pair connections (70.8%) exist only via ISO channels. ISO hubs (swarm=68, theory=60, economics=56 degree) have only 7% overlap with citation hubs. Direct citations: 339 pairs. ISO-only: 820 pairs. Both: 6 pairs. The ISO atlas IS the primary connectivity substrate. Inverted centrality confirmed: underground connections between domains that appear unrelated aboveground.

## F-PLB4: Phyllotaxis dispatch optimization
**Question**: Does UCB1 dispatch approximate golden-angle divergence in domain attention-recency space, achieving near-optimal packing?
**Test**: Compute Koksma-Hlawka discrepancy of actual dispatch sequence vs golden-ratio sequence vs random. If actual < random and approaches golden-ratio, UCB1 approximates phyllotactic packing.
**Status**: FALSIFIED (S539, L-1604) — Star discrepancy 0.199 is 86x worse than golden-ratio (0.002) and 6.7x worse than random (0.030). Only 7% of angular steps near golden angle. Root cause: meta at 31.9% destroys uniform packing. UCB1 is reward-seeking (animal foraging), not space-filling (phyllotaxis). Inter-visit CV=2.89 (phyllotactic needs <0.5).
**Evidence**: 1002 dispatches across 98 domains. Tool: `python3 tools/phyllotaxis_dispatch.py`. Artifact: `experiments/plant-biology/f-plb4-phyllotaxis-dispatch-s539.json`.
**Falsified-if**: Star discrepancy < 5x golden-ratio. **MET**: 86x >> 5x.

## F-PLB5: Allelopathy in domain attention
**Question**: Do dominant domains attentionally suppress structurally similar neighboring domains (analogous to plant allelopathy)?
**Test**: After dispatching to domain A, measure whether dispatch to structurally similar domain B is reduced in subsequent sessions. Use ISO-distance as structural similarity metric.
**Status**: OPEN (filed S516)
**Evidence**: Theoretical prediction. Concentration rebalancing (L-1127) may already counteract allelopathy.
