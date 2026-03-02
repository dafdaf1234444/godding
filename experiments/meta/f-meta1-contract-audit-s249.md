# F-META1 Contract Completeness Audit (S249)

Date: 2026-02-28
Check_mode: verification

## Expectation
- Active lanes missing core contract fields < 50%.
- Domain lanes missing domain_sync/memory_target < 20%.

## Method
- Parsed `tasks/SWARM-LANES.md` rows with Status in READY/CLAIMED/ACTIVE/BLOCKED.
- Extracted key/value pairs from the `Etc` column.
- Required fields: check_mode, expect, actual, diff, artifact, progress, next_step, blocked, available, human_open_item.
- Domain lanes additionally require: domain_sync, memory_target.

PowerShell snippet:
```powershell
$path = "tasks/SWARM-LANES.md"
$rows = (Get-Content $path) | Where-Object { $_ -match '^\| 20' }
$activeStatuses = @('READY','CLAIMED','ACTIVE','BLOCKED')
$required = @('check_mode','expect','actual','diff','artifact','progress','next_step','blocked','available','human_open_item')
$domainRequired = @('domain_sync','memory_target')
# Parse rows, build missing-field counts, and summarize.
```

## Results
- ACTIVE_LANES=278
- ACTIVE_WITH_MISSING_FIELDS=276
- DOMAIN_ACTIVE_LANES=134
- DOMAIN_WITH_MISSING_DOMAIN_TAGS=87

Top missing fields:
- diff: 273
- actual: 273
- expect: 271
- artifact: 260
- check_mode: 242
- progress: 183
- next_step: 178
- available: 178
- blocked: 178
- human_open_item: 178
- domain_sync: 87
- memory_target: 87

Sample missing lanes:
- L-AI2-SYNC-S185 (ACTIVE): missing all core fields
- L-S184-UNDERSTAND-SWARM (ACTIVE): missing all core fields
- L-S186-DOMEX-IS (READY): missing all core fields + domain tags

## Diff
Missing-field rate is far higher than expected. The contract appears enforced only on recently touched lanes; legacy READY/ACTIVE lanes retain older schemas.

## Next
- Enforce schema in `tools/test_swarm_lanes.py` or `tools/maintenance.py` (flag or auto-patch).
- Run a lane-compaction pass to close or rescope stale lanes missing contract fields.

