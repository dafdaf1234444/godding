# Distributed Systems Domain Index
Updated: 2026-02-27 | Sessions: 96

## What this domain knows
- **10 DS lessons** in `memory/lessons/` (L-091–L-100)
- **Key beliefs**: B13 (EH dominates failures 53–92%, OBSERVED), B14 (small-scale reproducibility, THEORIZED), B15 (CAP tradeoff, OBSERVED — S398 L-816)
- **Active frontiers**: 2 (F95, F100) in `tasks/FRONTIER.md`

## Lesson themes

| Theme | Key lessons | Core insight |
|-------|-------------|--------------|
| EH dominance | L-091, L-092 | 53% Jepsen, 92% user-reported; gap = methodology (Jepsen over-selects AP bugs) |
| Language comparison | L-094, L-095, L-096 | NK-EH correlation requires import cycles; DAG languages (Go/Rust) show weak/inverted |
| EH quality predictors | L-097, L-098 | DAG Go: domain sensitivity (+0.274); K_out/K_in>1.0 = high caller EH risk |
| Bug classification | L-093 | EH+CFG = 63% of distributed failures across 24 systems, 100 bugs |
| Determinism | L-099, L-100 | B14 fragile (Redis-Raft 14%, not 74%); bug-specific, not universal |

## DS principles (in `memory/PRINCIPLES.md`)
P-095 (B14 determinism and node-count are independent claims) |
P-097 (NK-EH correlation requires cycles, not just coupling) |
P-104 (EH is dominant failure mode, OBSERVED) |
P-105 (DAG Go EH predictor = domain sensitivity) |
P-106 (`_, err = fn()` is CORRECT Go EH) |
P-128 (EH triage K_norm thresholds, THEORIZED) |
P-141 (Go runtime-coord ctx.Context, PARTIALLY OBSERVED)

## What to load when
| Task | Load |
|------|------|
| EH analysis on a new system | This + P-104 + P-097 + P-106 |
| Go EH quality prediction | P-105 + P-128 + P-141 |
| Distributed bug reproduction | B14 + F95 + HUMAN-QUEUE HQ-5 (Docker needed) |
| CAP theorem (RESOLVED) | B15 (OBSERVED) — F15-DS RESOLVED S398 via L-816 |
