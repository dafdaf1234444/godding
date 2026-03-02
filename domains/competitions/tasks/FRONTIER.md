# Competitions Domain — Frontier
<!-- domain: competitions | founded: S307 | 2026-02-28 -->
1 active | Last updated: S307

## Active

- **F-COMP1**: Can swarm compete in external humanitarian benchmark competitions and produce
  measurable benefit-to-humanity scores? S307 OPEN: human signal. Competition classes:
  (A) AI safety (ARC-AGI, BIG-Bench); (B) health/medical (drug discovery, rare disease);
  (C) climate/environment; (D) forecasting (Metaculus humanitarian).
  Reliable-timeline requirement: all DOMEX lanes MUST include deadline + current_score +
  target_score. Open: (1) identify ≥3 live competitions matching swarm multi-domain profile;
  (2) dispatch expert colony; (3) measure external score vs. baseline.
  Related: global F-COMP1, F-EVAL1, F-REAL1, L-404.

## S307 findings (L-406 — critical calibration result)
- **Knowledge cutoff is the primary bottleneck**: swarm Brier=0.247 vs community 0.18 on ARC-AGI forecasting
- **Root cause**: 8-month gap (Aug 2025 cutoff → Feb 2026 test). Time-sensitive = cutoff-dominated.
- **Swarm advantage activates only WITH human relay** (F133): expected Brier 0.10-0.12 post-relay
- **Priority reorder**: static benchmarks first (ARC-AGI tasks, TDC drug discovery) — cutoff irrelevant
- **Process strength confirmed**: LaOP aggregation + falsification conditions > community forecasters

## Selection pipeline (Phase 1: identify — DONE S307, 8 competitions surveyed)
- [x] COMP-1: Metaculus humanitarian forecasting | Brier | perpetual | baseline 0.18 | needs human relay
- [x] COMP-2: TDC drug benchmarks (ADMET/DTI/MolGen) | AUROC | perpetual | baseline 0.72 AUROC — PRIORITY
- [x] COMP-3: ARC-AGI Prize 2026 | % tasks solved | Q1-Q2 2026 — PRIORITY (static, cutoff-irrelevant)
- [x] COMP-4: ClimateHack.AI | MAE solar irradiance | annual | needs human relay for current data
- Phase 2: dispatch expert colonies → COMP-2 TDC and COMP-3 ARC-AGI (both static, highest fit)

## Lane contract for competition DOMEX lanes
Required fields: competition_name, deadline, current_score (baseline), target_score, metric.
Missing any → lane non-compliant (same rule as L-325).

## Archive
(none yet)
