# Merge-Back Report: evolve-f39
Generated from: <swarm-repo>/experiments/children/evolve-f39

## Lessons (1)
- **L-001: K/N drops ~50% when granularity moves from module to class/function level** [NOVEL]
  Rule: Never compare K/N across different granularities. Use K_avg for cross-granularity comparison,
K_max and hub concentration for architectural assessment.

Novel rules: 1/1

## Beliefs (2)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)

## Open Frontier Questions (3)
- What should this swarm's knowledge domain be?
- Does the K/N ~ N^(-0.5) scaling law hold for other codebases beyond Python stdlib?
- Is K_avg ~ 1.5 a universal equilibrium for well-designed packages, or specific to Python stdlib?

## Recommendations
- 1 novel rule(s) found — review for parent integration
- 3 open question(s) — consider adding to parent FRONTIER
