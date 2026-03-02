# SESSION-TRIGGER.md
<!-- auto-updated by orient.py each run -->
<!-- machine-readable: any executor can read this to decide if a session is needed -->
<!-- human-readable: shows current swarm health at a glance -->
<!-- F-META6 artifact | S349 | DOMEX-META-S349b -->

## Schema
Each trigger row: `| ID | condition | urgency | state | last_checked | auto_action |`
- **urgency**: HIGH (session needed now) / MEDIUM (soon) / LOW (when available)
- **state**: FIRING (condition true) / CLEAR (condition false) / UNKNOWN (not yet checked)
- **last_checked**: session number when state was last evaluated

## Active Triggers
| ID | Condition | Urgency | State | Last Checked | Auto Action |
|----|-----------|---------|-------|--------------|-------------|
| T1-STALE-LANE | ACTIVE lane opened >3 sessions ago, no update | HIGH | CLEAR | S426 | close or execute lane |
| T2-ARTIFACT-MISSING | ACTIVE lane has artifact= path but file missing on disk | HIGH | CLEAR | S426 | execute lane or ABANDON |
| T3-MAINTENANCE-DUE | orient.py DUE items present (>0) | MEDIUM | FIRING | S426 | python3 tools/maintenance.py --auto (L-880) |
| T4-ANXIETY-ZONE | Frontier open >15 sessions without update | MEDIUM | FIRING | S426 | open DOMEX or CLOSE |
| T5-DISPATCH-GAP | Top-3 dispatch domain has no active DOMEX lane | MEDIUM | FIRING | S426 | open DOMEX for top domain |
| T6-HEALTH-CHECK | Health-check periodic overdue by >2 intervals | LOW | CLEAR | S426 | run health check |
| T7-PROXY-K-DRIFT | Proxy-K drift > 10% from last clean snapshot | LOW | FIRING | S426 | run compact.py |

## Detection Commands (run to evaluate each trigger)
```bash
# T1 + T2: stale lanes and missing artifacts
python3 tools/orient.py 2>&1 | grep "Stale lanes\|artifact missing"

# T3: maintenance DUE items  
python3 tools/orient.py 2>&1 | grep "\[DUE\]" -A 10

# T4: anxiety-zone frontiers
python3 tools/orient.py 2>&1 | grep "anxiety-zone"

# T5: dispatch gap
python3 tools/dispatch_optimizer.py 2>&1 | head -20

# T6: health check overdue
python3 tools/orient.py 2>&1 | grep "health-check"

# T7: proxy-K drift
python3 tools/proxy_k.py --drift 2>&1 | grep "drift"
```

## Autonomy Gap Analysis
Orient.py computes all of T1-T7 on every run. The gap is at the **executor layer**:
- orient.py emits signal → nobody reads it programmatically
- This file IS the bridge: any external trigger (cron, CI, autoswarm.sh) can `cat` this
  file, filter for `FIRING` rows with `HIGH` urgency, and initiate a session

## Wiring Points
1. **orient.py → SESSION-TRIGGER.md**: add `write_trigger_manifest()` call at end of orient.py
   to update State column based on live checks (see `tools/orient.py` lines ~200-250)
2. **autoswarm.sh → SESSION-TRIGGER.md**: read this file, if any HIGH FIRING → start session
3. **CI/cron hook**: `grep "HIGH.*FIRING" domains/meta/SESSION-TRIGGER.md && swarm`

## Evidence Base
- T1/T2: L-515 (stale_age>3: 97.1% recall, n=428; artifact_missing: 100% recall small-n)
- T3: L-216 (state-sync 4% overhead), L-526 (planning obsolescence at N≥3)
- T4: F-COMM1 (anxiety-zone auto-synthesis trigger)
- T5: F-EXP7 (expert dispatch default mode, 15% target)
- T6: maintenance.py periodics (every 5 sessions, 9 sessions overdue at S349)
- T7: proxy_k.py --drift (8.5% from S339, target <5%)

## Next Steps (to make this actionable)
1. [x] Add `write_trigger_manifest()` to orient.py (updates State column each run) — S359: extended T1-T3→T1-T7
2. [x] Wire autoswarm.sh to read HIGH FIRING triggers — already implemented (line 97)
3. [x] Test: after orient.py update, does SESSION-TRIGGER.md auto-reflect live state? — S359: confirmed all 7 triggers evaluated
4. [x] Measure: does this reduce session-gap latency? — S359: baseline median=1.0h, mean=2.1h, 19h idle/4 days
5. [ ] Configure cron or filesystem watcher to run autoswarm.sh (requires human decision on schedule)
6. [ ] First autonomous session: run autoswarm.sh without --dry-run via cron/watcher
