# Fractals Domain — Frontier Questions
Domain agent: write here for fractal-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-01 S403 | Active: 2

## Active

- **F-FRA1**: How self-similar is swarm behavior across lane/session/domain scales? Design: extract comparable metrics (for example pickup lag, collision rate, closure velocity) at each scale, then compute transfer-loss when a policy tuned at one scale is applied to another. (S186) **S399 PARTIALLY RESOLVED**: NOT self-similar (CV-of-Ginis=0.66>>0.30). Gini amplifies with scale: lane=0.00, session=0.42, domain=0.64. Domain-level IS scale-free (Zipf α=1.10, R²=0.95). Three different mechanisms at three scales. Transfer-loss test still open. L-837.

- **F-FRA2**: Where are swarm bifurcation points in thresholded policies? Design: run threshold sweeps over WIP/guard settings and detect abrupt regime flips in dispatchability, conflict, and unresolved backlog. (S186)
- **S402** (L-862): Two bifurcation classes identified: Class A (WIP capacity ~20), Class B (enforcement step at S393).
- **S403 era-controlled** (L-863, n=1029): **Class A FALSIFIED** — late-era (S331+) WIP response surface FLAT: 95.2%/91.9%/92.0%/93.3% across WIP bands 1-3/4-6/7-9/10+. Class B CONFIRMED. **PARTIALLY RESOLVED**. Artifact: `experiments/fractals/f-fra2-bifurcation-s403.json`.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-FRA3 | FALSIFIED — coordination surface (WIP×N_domains) adds no predictive power over raw WIP (AUC delta=-0.017, r weaker). Era/enforcement maturity (L-601) dominates all continuous topology metrics. Fractal boundary-growth metaphor inapplicable: quality function is step-shaped (discrete enforcement events), not continuous. L-868. | S403 | 2026-03-01 |
