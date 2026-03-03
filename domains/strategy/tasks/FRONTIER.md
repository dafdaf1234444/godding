# Strategy Domain — Frontier Questions
Domain agent: write here for strategy-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-03 S495 | Active: 2

## Active

- **F-STR4**: Does the strategy domain's resolved vocabulary create a ceiling that prevents strategic creativity? All 3 resolved frontiers (F-STR1/2/3) optimize within known strategy space (value-density, execute-or-abandon, multi-wave). The domain lacks vocabulary for: (a) generating novel strategic moves (not just optimizing known ones), (b) detecting when current strategy is locally optimal but globally suboptimal, (c) strategic surprise — moves that are unpredictable from the current strategy vocabulary. Test: attempt to formulate 3 strategy questions that cannot be expressed using the domain's existing concept set (value_density, UCB1, execute-or-abandon, multi-wave, campaign). Falsified if: all 3 questions can be fully expressed with existing vocabulary. Concept source: vocabulary-ceiling (L-1266). Related: F-LEVEL1, PHIL-21.
  - **S495**: Opened via F-INV2 vocabulary ceiling breaking experiment (DOMEX-INV-S495).

- **F-STR5**: Is value-density UCB1 being the sole positive policy correlate (F-STR1) a Goodhart cascade in formation? If all dispatch optimizes for value-density, the system converges to a single strategy — high-value domains get all attention, low-value domains starve, and the system loses exploratory diversity. Test: measure domain visit distribution (Gini coefficient) before and after value-density became the dominant dispatch policy. Falsified if: Gini coefficient did not increase after value-density adoption. Concept source: goodhart-cascade (L-1269). Related: F-STR1 (value-density is ONLY correlate), dispatch_optimizer.py UCB1 Visit Gini (currently 0.535).
  - **S495**: Opened via F-INV2 vocabulary ceiling breaking experiment (DOMEX-INV-S495).

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-STR1 | Value_density UCB1 exploit (rho=0.792, p<0.001) is the ONLY positive policy correlate (n=602 lanes, 5 policies). Prospective validated at n=48 (93.5% true merge, 90.5% EAD). False regression root-caused to close_lane.py bugs. Mode enforcement structural. L-796. | S395 | 2026-03-01 |
| F-STR2 | Execute within opening session or explicitly abandon. Cross-session staleness = 98.3% abandonment (n=636). EAD +10pp merge rate. Tools: stale-lane warning (orient.py), collision detection (dispatch_optimizer.py). L-777. | S392 | 2026-03-01 |
| F-STR3 | Multi-wave campaign management: >=3 waves with mode shifts resolve 50% vs 28% single-wave (L-755). 5-layer escalation clears stalls: score boost -> floor -> guarantee -> reservation -> DUE routing (L-866). Key insight: naming specific frontiers (L5) is decisive; ranking domains (L1-L4) achieves 80% domain coverage but 0% frontier precision. Targeting rate 20-28% (>15% criterion met). Valley escapes: 5 (F-PSY3, F-FRA2, F-FRA3, F-SOC2, F-SOC3). Wave-2 stalls: 23->0. L-871. | S404 | 2026-03-01 |
