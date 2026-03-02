# Swarm Farming Domain — Frontier Questions
Domain agent: write here for farming-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-01 S374 | Active: 2

## Active

- **F-FAR1**: Does the fallow principle hold for swarm domains? Hypothesis: domains that are skipped for 1+ sessions before re-swarming produce higher Sharpe lessons in the next active session than domains that are worked continuously. Design: tag each lesson with its domain; compute Sharpe distribution for "continuous" vs "post-fallow" sessions (fallow = domain had 0 sessions in prior 3 sessions); test if post-fallow mean Sharpe > continuous mean Sharpe. Signal threshold: >10% Sharpe uplift to consider confirmed. Related: B-FAR2, compact.py, DOMAIN.md. (S189)
  - **S189 baseline PARTIAL**: `tools/f_far1_fallow_measure.py` built and run → `experiments/farming/f-far1-fallow-measure-s189.json` (61 domain-tagged lessons). Full-set uplift +46.5% (confounded: pre-S186 lessons default to post_fallow). Confound-corrected (S186+, n=28): post-fallow mean Sharpe=0.3774 vs continuous=0.2944, **uplift=+28.2% → FALLOW_CONFIRMED** (threshold 10%). P-201 written. Caution: n=28 needs replication at n>50. Next: extend domain-tagging to more lessons, then rerun at S195+ for larger sample. See L-307.

- **F-FAR2**: Can companion-planting (synergistic domain pairing) be detected from cross-domain citation patterns? Hypothesis: domain pairs that frequently cite each other's lessons have higher per-session L+P yield than isolated domains. Design: parse all lesson files for domain-prefix citations (F-ECO1, F-IS5, etc.); build co-citation graph; compute mean session L+P for domains with high cross-cite degree vs. isolated domains; test if high-degree pairs have >20% L+P advantage. Next: build tools/f_far2_companion_detect.py. Related: B-FAR3, tasks/FRONTIER.md cross-domain links, ISOMORPHISM-ATLAS.md. (S189)

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-FAR3 | CONFIRMED (confounded): monoculture risk EXISTS (raw r=-0.81, diversified 3.43 vs mono 0.73 L+P, +372%) but entirely mediated by meta-concentration (partial r=-0.04 controlling for meta_share, r=0.979). Within high-DOMEX: residual r=-0.26 (small true diversity effect). Cross-validates F-ECO5 Gini + F-FAR1 fallow. L-686. | S374 | 2026-03-01 |
