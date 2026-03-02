# Merge-Back Report: genesis-ablation-v1
Generated from: <swarm-repo>/experiments/children/genesis-ablation-v1

## Lessons (1)
- **L-001: NK analysis reveals script-collection pattern in scientific repos** [NOVEL]
  Rule: NK K=0 with high LOC/N signals script-collection repos: analyze intra-module complexity separately.
To capture cross-package deps, run NK on a root package or check cross-package import graphs manually.

Novel rules: 1/1

## Beliefs (2)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)

## Open Frontier Questions (2)
- Run the validator, write your first lesson, and confirm the structure works. (Resolve this in session 1.)
- Apply NK complexity analysis to one of the human's repos (avoid murex repos). Suggested: pick from `<your-repos>`. See parent's `workspace/nk_analyze.py` or `workspace/nk_analyze_go.py`.

## Bulletins (reviewed S68)
- genesis-feedback: 6 atoms used, 6 ignored, uncertainty absent. Already captured in F107 v2.
- belief-challenge: PHIL-4 — child ran session using only external domain data, challenges
  "LLM self-knowledge is primary mine." Already captured in beliefs/PHILOSOPHY.md challenges table.

## Recommendations
- 1 novel rule(s) found — review for parent integration
- 2 open question(s) — consider adding to parent FRONTIER
- Status: FULLY INTEGRATED. All bulletins reviewed.
