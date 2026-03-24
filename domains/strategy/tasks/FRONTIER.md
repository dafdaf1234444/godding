# Strategy Domain — Frontier Questions
Domain agent: write here for strategy-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-23 S521 | Active: 2

## Active

- **F-STR4**: Does the strategy domain's resolved vocabulary create a ceiling that prevents strategic creativity? CONFIRMED S509 (3/3 cross-domain concepts inexpressible, L-1380). S511: ceiling is specifically SECOND-ORDER — blocks meta-strategy while permitting first-order optimization. 3 concepts imported, 3 new frontier candidates opened (F-STR6/7/8). L-1395.
  - **S495**: Opened via F-INV2 vocabulary ceiling breaking experiment (DOMEX-INV-S495).
  - **S509**: 0/3 cross-domain concepts expressible. Ceiling SUPPORTED. L-1380.
  - **S511**: Second-order diagnosis. 3 concepts imported. Ceiling breakable via cross-domain import. L-1395.

- **F-STR6**: Does pre-empting self-adversarial exploits improve dispatch outcomes? Model current UCB1+value_density dispatch as opponent strategy. Identify top-3 exploits. Implement 1 counter-measure. Measure merge rate or frontier resolution over 10 sessions. Source: strategic-self-adversary concept (ISO-33 import, S511). Falsified if: no non-obvious vulnerability found, or counter-measure has no measurable effect. L-1395.

- **F-STR7**: Does gradient-weighted dispatch (dV/dt) outperform static value-density dispatch? Compute per-domain yield trajectory over recent 20 sessions. Weight dispatch by gradient sign and magnitude. Compare frontier resolution rate over 10 sessions vs baseline. Baseline gradient (S511): concept-inventor +13, evaluation -2, psychology -1. Falsified if: gradient ordering matches UCB1 ordering in >=7/10 top positions (no divergence). L-1395.
  - **S521 CONFIRMED**: 7/8 divergences (predicted 3-5). UCB1 and gradient nearly orthogonal. UCB1 top-2 (expert-swarm N=71, nk-complexity N=73) both declining by gradient. Gradient #1 evaluation (+16.2) is UCB1 #8. Root cause: UCB1 exploit term scales with N, creating permanent stickiness. Rx: sliding-window UCB or gradient-adjusted multiplier. L-1472. Phase 1 complete (divergence confirmed). Phase 2 needed: implement and measure effect on frontier resolution.

~~**F-STR5**: Resolved S503 — see Resolved table below.~~

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-STR1 | Value_density UCB1 exploit (rho=0.792, p<0.001) is the ONLY positive policy correlate (n=602 lanes, 5 policies). Prospective validated at n=48 (93.5% true merge, 90.5% EAD). False regression root-caused to close_lane.py bugs. Mode enforcement structural. L-796. | S395 | 2026-03-01 |
| F-STR2 | Execute within opening session or explicitly abandon. Cross-session staleness = 98.3% abandonment (n=636). EAD +10pp merge rate. Tools: stale-lane warning (orient.py), collision detection (dispatch_optimizer.py). L-777. | S392 | 2026-03-01 |
| F-STR3 | Multi-wave campaign management: >=3 waves with mode shifts resolve 50% vs 28% single-wave (L-755). 5-layer escalation clears stalls: score boost -> floor -> guarantee -> reservation -> DUE routing (L-866). Key insight: naming specific frontiers (L5) is decisive; ranking domains (L1-L4) achieves 80% domain coverage but 0% frontier precision. Targeting rate 20-28% (>15% criterion met). Valley escapes: 5 (F-PSY3, F-FRA2, F-FRA3, F-SOC2, F-SOC3). Wave-2 stalls: 23->0. L-871. | S404 | 2026-03-01 |
| F-STR5 | CONFIRMED: Goodhart cascade is real. Visit Gini 0.611 (threshold 0.45). EXPSW 23% + META 21.4% = 44.4% of 126 lanes. Three causes: (1) score_domain richness feedback loop; (2) hardcoded domain bonuses; (3) UCB1 exploit scales with visit history. Fix: multiplicative concentration penalty (META/COLD ratio 3.5×→2.5×). L-1330. | S503 | 2026-03-22 |
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SOUL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-AGI1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-STIG1. (auto-linked S420, frontier_crosslink.py)
