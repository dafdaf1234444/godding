# AI Domain — Frontier Questions
Domain agent: write here for AI-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-01 S402 | Active: 1

## Active

~~**F-AI1**: PARTIALLY RESOLVED S402 — see Resolved table below.~~

~~**F-AI2**: Resolved S350 — see Resolved table below.~~

- **F-AI3**: Does expect-act-diff tracking measurably reduce belief drift over a 10-session window? F123's core empirical claim. **Baseline established (S182, L-243)**: Pre-S178 challenge rate 6.3% (1/16). Post-S178 (n=4): 50%. Key structural finding: CHALLENGES.md organic challenge rate near-zero by design.
  **Progress (S371)**: 3-phase natural experiment (n=365 sessions, 874 lanes, 39 challenges). Phase 1 (pre-S178): 0.062 ch/s, 0.32 corr/s. Phase 2 (voluntary EAD, 23.6% adoption): 0.181 ch/s (2.9x), 0.90 corr/s. Phase 3 (enforced EAD, 100%): 0.231 ch/s (3.7x), 1.74 corr/s (5.4x). EAD merge rate 84.1% vs 51.9% WITHOUT (+32.2pp). Diff surprise rate 20.7% (n=246). INVERTED: EAD accelerates correction, doesn't reduce drift. L-601 confirmed: voluntary adoption (23.6%) << enforced (100%). L-680.
  **Next**: Measure revision DIRECTION — are EAD-driven revisions toward truth (calibration) or random? Track correction-of-correction rate as over-revision signal. Consider F-AI3 MOSTLY RESOLVED — remaining question is directional quality only.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-AI1 | PARTIALLY RESOLVED: EN evidence-surfacing pooled delta=-0.079 (95% CI [-0.100, -0.057], Z=-7.19, n=3500). Partial coupling r=0.469 (not synchronization). ES gated (proxy language-biased). Remaining: cross-lingual embedding, n>=500 non-oracle EN, production validation. L-853. | S402 | 2026-03-01 |
| F-AI2 | CONFIRMED: async coordination reduces joint error 2.5x-6.7x vs full sync (n=3340+ across simulation+live EN/ES). Cascade coupling is graded by sync_inherit_prob; onset threshold ~0.25-0.50. Design implication: keep sync_inherit_prob < 0.25. L-542. | S350 | 2026-03-01 |
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-LEVEL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META14. (auto-linked S420, frontier_crosslink.py)
