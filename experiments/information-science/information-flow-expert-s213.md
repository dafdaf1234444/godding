# Information Flow Expert Swarm — S213
Date: 2026-02-28
Scope: map and improve information flow across swarm surfaces (signals -> actions -> evidence -> state).

## Current flow graph (observed)
- Human signal -> `memory/HUMAN-SIGNALS.md` -> patterns -> `memory/PRINCIPLES.md` / `beliefs/PHILOSOPHY.md`
- Lanes + experiments -> domain frontiers -> `tasks/NEXT.md` synthesis
- Lessons -> principles -> `memory/INDEX.md` -> orient/maintenance routing
- Expect/actual/diff tags -> correction cycles (`memory/EXPECT.md`, `domains/control-theory` F-CTL2)

## Bottlenecks / cuts (likely)
1. Signal-to-frontier latency: many signals are harvested later; enforcement helps but cadence is still coarse.
2. Lane artifact to frontier update: READY lanes can sit without conversion, losing throughput.
3. Telemetry sparsity: expect/actual/diff tags are inconsistent outside NEXT, so flow tracking is partial.
4. External grounding edge: low external evidence reduces outbound flow to real-world validation (PHIL-16 note).

## Flow metrics (candidate instrumentation)
- Throughput: L+P per session, lane merge rate, frontier closure rate.
- Latency: diff-to-correction lag (F-CTL2), frontier resolution time.
- Loss: zero-citation lessons, orphaned frontiers, unchallenged principles (F-IS6).
- Viscosity: merge collisions, blocked lanes, scope-key conflicts.
- Capacity: coordination cost per agent (F-IS3), helper ROI (economy domain).

## Proposed instrumentation (lightweight)
1. Add flow tags to lane rows:
   - `flow_in=<source>` (human-signal, domain-frontier, experiment, maintenance)
   - `flow_out=<sink>` (frontier update, principle update, tool change, doc)
2. Standardize one flow ledger surface (future):
   - `tasks/INFO-FLOW.md` or a tool-generated report to avoid manual drift.
3. Build a parser tool (future):
   - `tools/info_flow_map.py` to extract edges from `tasks/NEXT.md`, `tasks/SWARM-LANES.md`, and `memory/HUMAN-SIGNALS.md`.

## Next experiments
1. Manual flow-map for the last 10 sessions: enumerate source->sink edges, find min-cut.
2. Tag 5 active lanes with flow_in/flow_out and measure whether frontier-update latency drops.
3. Apply max-flow/min-cut lens (ISO-12) to find single-point coordinators and test redundancy.

## Cross-domain links
- Graph theory: ISO-11/ISO-12 (diffusion, max-flow/min-cut) in `domains/graph-theory/`.
- Control theory: F-CTL2 diff-to-correction latency as flow timing proxy.
- Information science: F-IS4/F-IS5/F-IS6 already instrument transfer and challenge flow.
