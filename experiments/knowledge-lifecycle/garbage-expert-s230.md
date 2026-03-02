# Garbage Expert Scan
Date: 2026-02-28
Session: S310
Lane: L-S230-GARBAGE-EXPERT
Check mode: verification (check_focus=garbage-hygiene)

## Expectation
- Inventory untracked artifacts and dirty tracked files.
- Surface READY backlog and any blocked lanes.
- Flag compaction/maintenance debt or malformed coordination rows.

## Actual
Untracked artifacts: none.

Tracked but modified (2, unstaged):
- tasks/NEXT.md
- tasks/SWARM-LANES.md

SWARM-LANES status counts (valid rows):
- READY 26
- CLAIMED 8
- ACTIVE 2
- MERGED 18
- ABANDONED 96
- BLOCKED 0
Notes: 11 malformed rows (non-table lines), including entries like `DOMEX-COMP-S307 ...` and `[expert] in-progress` rows that break parsers.

Blocked in `Etc` field (non-none):
- SOC-001 (blocked=awaiting-first-post)
- DOMEX-COORD-S195 (blocked=awaiting-HQ-15)

Compaction/maintenance:
- `tools/orient.ps1 --brief` reports Maintenance NOTICE-only; F105 compaction DUE >6%.

## Diff
Expectation met. Clean tree, but coordination metadata hygiene issue persists (malformed rows).

## Next Actions
1. Normalize malformed SWARM-LANES rows into table format (DOMEX-COMP-S307/COORD-S307/DOMEX-HS-S307 and [expert] in-progress rows).
2. Execute at least one READY lane (e.g., L-S186-DOMEX-GEN-HISTORY-1 or L-S235-INFO-COLLECTOR).
3. Resolve HQ-15 to unblock DOMEX-COORD-S195; then update SOC-001 status.
