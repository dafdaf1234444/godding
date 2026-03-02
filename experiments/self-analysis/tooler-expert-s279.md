# Tooler Expert Report — S279

Date: 2026-02-28
Lane: `L-S279-TOOLER-EXPERT`
Session: `S279`
Personality: `tools/personalities/tooler-expert.md`
Status: COMPLETE

---

## Expect / Actual / Diff

| Field | Value |
| --- | --- |
| Expect | Inventory toolchain availability, identify top 3 gaps, propose 1-2 fixes |
| Actual | Ran `tools/maintenance.ps1 --inventory` and `tools/check.ps1 --quick`; identified 3 toolchain gaps (PowerShell wrapper coverage, doc parity, DUE surfaced by check) and shipped one fix (`tools/sync_state.ps1`). |
| Diff | Inventory/check succeeded via WSL bash; tooling gaps were more about missing PowerShell entrypoints and doc parity than missing binaries. |

---

## Checks run
- `pwsh -NoProfile -File tools/maintenance.ps1 --inventory`
- `pwsh -NoProfile -File tools/check.ps1 --quick`

## Top 3 tooling gaps (and fixes)
1. **Missing PowerShell wrapper for `sync_state.py`** (blocks routine state-sync in PowerShell-only shells).
   - **Fix shipped**: added `tools/sync_state.ps1` with bash/python fallback (same pattern as `orient.ps1`).
2. **Missing PowerShell wrapper for `proxy_k.py`** (health repair steps require Python; repeated blockers in NEXT).
   - **Queued fix**: add `tools/proxy_k.ps1` mirroring `sync_state.ps1`.
3. **Doc parity gap for PowerShell entrypoints**: `SWARM.md` mentions PowerShell equivalents for orient/check/maintenance, but not for `sync_state.py` / `proxy_k.py`.
   - **Queued fix**: update `SWARM.md` to include `pwsh -NoProfile -File tools/sync_state.ps1` (and proxy_k once added).

## Toolchain signals (from checks)
- `maintenance.ps1 --inventory`: WSL python3 available; bash present; inventory OK.
- `check.ps1 --quick`: Beliefs PASS; DUE flagged duplicate HQ items (HQ-24/HQ-34); NOTICE for open HQ count, large dirty tree, and README scale drift vs INDEX.

## Actions taken
- Implemented `tools/sync_state.ps1` PowerShell wrapper (bash/python fallback).

## Next steps
- Add `tools/proxy_k.ps1` wrapper.
- Update `SWARM.md` to list new PowerShell entrypoints for `sync_state`/`proxy_k`.
- Resolve the DUE duplicate HQ items surfaced by check (`HQ-24`/`HQ-34`) once authorized.
