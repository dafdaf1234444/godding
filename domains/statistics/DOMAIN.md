# Domain: Statistics / Inference
Topic: Experimental design, uncertainty quantification, hypothesis testing, and meta-analysis as structural isomorphisms for swarm experiment reliability, cross-domain transfer decisions, and swarm-of-swarms calibration.
Beliefs: (candidate only; no formal B-STAT* entries in `beliefs/DEPS.md` yet)
Lessons: L-223 (expect-act-diff instrumentation), L-253 (variance reduction evidence framing), L-257 (quality-dimension baselines), L-258 (coordination-mode quality split)
Frontiers: F-STAT1, F-STAT2, F-STAT3
Experiments: experiments/statistics/
Load order: CLAUDE.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/FRONTIER.md

## Domain filter
Only statistical concepts with structural isomorphisms to swarm operation qualify. Isomorphism requires: same inferential objective, same error modes, and an actionable swarm protocol implication.

## Core isomorphisms

| Statistics concept | Swarm parallel | Isomorphism type | Status |
|-------------------|----------------|------------------|--------|
| Sampling variance | Session-to-session quality variance across repeated runs | Estimation uncertainty | OBSERVED |
| Power analysis | Trial-count sizing for domain experiments before declaring effects | Detection sensitivity | THEORIZED |
| Multiple testing control | Many concurrent frontier probes increase false-positive risk | Error-rate budgeting | OBSERVED |
| Bayesian updating | Beliefs/frontier confidence shift as new artifacts arrive | Sequential evidence update | OBSERVED |
| Meta-analysis | Combine independent domain/swarm runs into pooled effect estimates | Cross-run synthesis | THEORIZED |


## Isomorphism vocabulary
ISO-3 (hierarchical compression): MDL principle → model selection via minimum description length; AIC/BIC = MDL tradeoff; Bayesian compression
ISO-9 (information bottleneck): sufficient statistic → information bottleneck; lossy compression retaining all information about parameter
ISO-10 (predict-error-revise): Bayesian updating → predict-error-revise loop; prior + likelihood = posterior; each observation revises prediction
ISO-16 (inferential compounding): causal inference chain → inferential compounding; each causal link expands estimable quantity space
ISO-6 (entropy): maximum entropy principle → prior selection; entropy maximization = minimal assumption; Jeffreys prior as maximum entropy
ISO-2 (selection → attractor): hypothesis testing → selection pressure on hypotheses; p-value threshold = selection boundary; attractor = accepted model
## Isomorphism vocabulary (S337 resonance expansion)
ISO-10: Bayesian knowledge coordination → structural evidence coupling via stigmergy; session cycles determine calibration quality; convergence signal pattern
