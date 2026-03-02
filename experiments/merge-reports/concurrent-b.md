# Merge-Back Report: concurrent-b
Generated from: <swarm-repo>/experiments/children/concurrent-b

## Lessons (1)
- **L-001: K/N is scale-dependent -- K_avg and cycle count tell more than K/N alone** [NOVEL]
  Rule: When comparing NK across packages of different N, use K_avg and cycle count
alongside K/N. A low K/N with high K_avg and cycles is deceptively complex.

Novel rules: 1/1

## Beliefs (2)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)

## Open Frontier Questions (6)
- Validate the setup -- does this structure work for the first 5 sessions?
- What should this swarm's knowledge domain be?
- Is there a scale-invariant alternative to K/N for comparing packages of different N? (e.g., normalized graph density, spectral gap)
- Do lazy imports in large stdlib modules (email, http, unittest) always correspond to cycle-breaking? Is this a deliberate CPython design pattern?
- What is the correlation between K_avg (not K/N) and bug report frequency across stdlib modules?
- Does the email module's hub concentration (54% of modules depend on __init__) create a maintenance bottleneck in practice? Check CPython commit history.

## Recommendations
- 1 novel rule(s) found — review for parent integration
- 6 open question(s) — consider adding to parent FRONTIER
