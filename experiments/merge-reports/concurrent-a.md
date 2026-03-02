# Merge-Back Report: concurrent-a
Generated from: <swarm-repo>/experiments/children/concurrent-a

## Lessons (1)
- **L-001: NK analysis of http.client reveals hidden coupling behind low K/N** [NOVEL]
  Rule: When comparing K/N across systems, normalize for granularity and filter
trivial components (pure inheritance leaves). Raw K/N can be misleadingly low.

Novel rules: 1/1

## Beliefs (2)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)

## Open Frontier Questions (5)
- Validate the setup -- does this structure work for the first 5 sessions?
- What should this swarm's knowledge domain be?
- Should NK analysis normalize for component granularity? K/N=0.068 (class-level) vs K/N=0.215 (core-only) for http.client shows the metric is granularity-dependent. What normalization method is most meaningful?
- Is HTTPConnection a "god class"? At K=10 and 629 lines, it holds 42% of all coupling edges. Would refactoring it reduce systemic risk, or is the monolithic design intentional for performance?
- How does http.client's K/N compare to other single-file stdlib modules at the same granularity (class/function level)? E.g., urllib.parse, email.message, logging.

## Recommendations
- 1 novel rule(s) found — review for parent integration
- 5 open question(s) — consider adding to parent FRONTIER
