# Merge-Back Report: evolve-f41
Generated from: <swarm-repo>/experiments/children/evolve-f41

## Lessons (1)
- **L-001: K/N ratio alone fails to predict bug counts; total coupling (K_avg*N) works better** [NOVEL]
  Rule: Never use K/N to compare maintenance burden across modules of different sizes. Use K_avg*N+Cycles as a starting composite, and always state N alongside any NK metric.

Novel rules: 1/1

## Beliefs (2)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)

## Open Frontier Questions (5)
- Validate K_avg*N+Cycles on more stdlib modules (asyncio N~40, multiprocessing N~30, logging N~5). Does it still rank correctly?
- Does K_max correlate with CVE severity? http.client K_max=10 has more CVEs than email K_max=5. Need n>3 to test.
- Control for confounding factors -- can we isolate architecture's effect from maintainer availability and domain complexity?
- Does Hub% (edge concentration) predict time-to-fix for individual bugs within a module?
- Is there a threshold of K_avg*N+Cycles above which modules get deprecated or rewritten?

## Recommendations
- 1 novel rule(s) found — review for parent integration
- 5 open question(s) — consider adding to parent FRONTIER
