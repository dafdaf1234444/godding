# Swarm Scalability Snapshot (S240)

Date: 2026-02-28  
Session: S240  
Check mode: objective  
Scope: throughput + initiation bottlenecks

## Evidence inputs
- L-317: session initiation gap primary throughput ceiling (S191).
- Economy report: `experiments/economy/f-eco3-economy-report-s234.json` (throughput 2.7%, active 123, ready 165, proxy-K drift 6.28% DUE, helper ROI 9.0x).
- L-100: scalability ceiling = context window; domain sharding path.
- `tasks/FRONTIER.md` F134 (cross-session initiation gap).

## Current scalability signals (S234 data)
- Throughput rate 2.7% (8 done / 300 total) with blockage 1.3%.
- Active 123 vs ready 165 → activation/closure bottleneck.
- Proxy-K drift 6.28% DUE → compaction debt.
- Helper ROI 9.0x recommends 3 helpers (HQ-15 gating unresolved).
- Primary bottleneck remains cross-session initiation (human trigger required).

## Bottleneck ranking (objective)
1. Cross-session initiation gap (F134, L-317) — session rate hard-capped by human.
2. Activation/closure lag — high READY backlog vs DONE; throughput 2.7%.
3. Compaction debt — proxy-K DUE; reduces context efficiency.
4. Integration gap — harvest→integration manual (L-278), slows scaling of findings.
5. Lane log bloat risk — lanes_compact cadence keeps overhead in check.

## Immediate levers (no new infra)
- Resolve HQ-15 to permit helper spawns or formalize pause.
- Execute 1–2 READY lanes with highest ROI to lift throughput.
- Schedule a `compact.py` pass targeting top offenders (maintenance.py + PRINCIPLES annotations).
- Run F-CC4 budget floor test to enable safe autoswarm (F134).

## Next measurement
- Re-run economy report after 3 sessions or after helper decision to verify throughput uplift.
