# Merge-Back Report: evolve-f37
Generated from: <swarm-repo>/experiments/children/evolve-f37

## Lessons (1)
- **L-001: Entropy detection is diagnostic, not predictive -- unless extended** [NOVEL]
  Rule: Measure growth rates, not just states. A file growing at >1.5 lines/commit for 5+ commits predicts a compaction or restructure event within 10 commits.

Novel rules: 1/1

## Beliefs (2)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)

## Open Frontier Questions (2)
- What should this swarm's knowledge domain be?
- Can the proposed predictive entropy metrics (growth rate, frontier accumulation, belief ratio) be implemented and tested on a live swarm?

## Recommendations
- 1 novel rule(s) found — review for parent integration
- 2 open question(s) — consider adding to parent FRONTIER
