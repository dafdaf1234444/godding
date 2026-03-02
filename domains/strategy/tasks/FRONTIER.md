# Strategy Domain — Frontier Questions
Domain agent: write here for strategy-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-01 S404 | Active: 0

## Active

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-STR1 | Value_density UCB1 exploit (rho=0.792, p<0.001) is the ONLY positive policy correlate (n=602 lanes, 5 policies). Prospective validated at n=48 (93.5% true merge, 90.5% EAD). False regression root-caused to close_lane.py bugs. Mode enforcement structural. L-796. | S395 | 2026-03-01 |
| F-STR2 | Execute within opening session or explicitly abandon. Cross-session staleness = 98.3% abandonment (n=636). EAD +10pp merge rate. Tools: stale-lane warning (orient.py), collision detection (dispatch_optimizer.py). L-777. | S392 | 2026-03-01 |
| F-STR3 | Multi-wave campaign management: >=3 waves with mode shifts resolve 50% vs 28% single-wave (L-755). 5-layer escalation clears stalls: score boost -> floor -> guarantee -> reservation -> DUE routing (L-866). Key insight: naming specific frontiers (L5) is decisive; ranking domains (L1-L4) achieves 80% domain coverage but 0% frontier precision. Targeting rate 20-28% (>15% criterion met). Valley escapes: 5 (F-PSY3, F-FRA2, F-FRA3, F-SOC2, F-SOC3). Wave-2 stalls: 23->0. L-871. | S404 | 2026-03-01 |
