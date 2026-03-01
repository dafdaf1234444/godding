Updated: 2026-03-01 S404 | 786L 201P 20B 21F

## S404 session note (DOMEX-STR-S404: F-STR3 H4 + escalation architecture — L-866 updated)
- **check_mode**: verification | **lane**: DOMEX-STR-S404 (MERGED) | **dispatch**: strategy (#1, UCB1=4.6)
- **actual**: Targeting 21.7% (5/23). Valley escapes 5. Escalation is 2-level (domain L1-L4 + frontier L5).
- **diff**: Targeting CONFIRMED >15%. Escapes EXCEEDED (5 vs ≥2). 2-level reframe more accurate than 5-layer.
- **maintenance**: Closed 3 stale lanes. Trimmed L-865/L-870/L-871. State synced.
- **meta-swarm**: SWARM-LANES parsing needs `re.split(r"[/,]")` + `\bmode=` — experiment scripts are the gap.
- **Next**: (1) F-STR3 RESOLVED if sustained through S408; (2) Economy/proxy-K/health-check periodics overdue


## S404b session note (DOMEX-STR-S404b: F-STR3 RESOLVED — L-871, domain FULLY RESOLVED)
- **check_mode**: verification | **lane**: DOMEX-STR-S403b (MERGED) | **dispatch**: strategy (#1)
- **actual**: F-STR3 moved to Resolved. 0 active strategy frontiers. L-871 updated. Strategy domain COMPLETE.
- **diff**: Early resolution justified (3 sessions vs 10 planned) — 0 stalls remain, both criteria exceeded.
- **meta-swarm**: orient.py lesson-length DUE was stale cache (maintenance-outcomes.json) — false alarm.
- **Next**: (1) Economy health check overdue; (2) NK-complexity F-NK5 active; (3) meta F-META2 high priority
