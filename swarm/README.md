# swarm — the godding LLM distiller

Tiny multi-agent loop that maintains the rest of the site.

```
python loop.py            # one full run across all pages
python loop.py --dry-run  # report what it WOULD do, change nothing
python loop.py --once health   # one page, one iteration
```

## What it does

For each page in `pages/`:

1. **Drafter** picks one paragraph and proposes a *tightening* — drop a weasel word, soften an unqualified superlative, or trim the longest sentence in a bloated paragraph. If `ANTHROPIC_API_KEY` is set and the `anthropic` package is installed, it'll use Claude Haiku for higher-quality edits; otherwise it uses a deterministic heuristic agent.
2. **Critic** tries to kill the diff. Rejects anything that grows the page, introduces new proper nouns or numeric claims, or strays too far from the original.
3. **Fact-checker** runs a conservative numeric check (it explicitly forbids introducing new numbers, since the drafter is only supposed to tighten).
4. **Judge** errs toward "no change". A diff has to clear both critic and fact-checker to land.

## Outputs

- `../data/changelog.json` — append-only list of accepted runs (rendered on `/changelog/`).
- `../data/metrics.json` — rolling totals: runs, proposals, accepted, first/last run.
- `../data/last_run.json` — full diagnostic record of the most recent run.

## Scheduling

`scheduler.json` is the config the Cowork scheduler reads. By default the loop runs every 24h with hard bounds: max 6 pages, max 6 accepted diffs, can never grow the site. To trigger it on demand, just run `python loop.py`.

## Why heuristic + LLM?

State-of-the-art distillation in 2025–2026 (rationale-based training, multi-teacher ensembles, residual learning, process-level distillation) all share one feature: they keep the *reasoning* as part of the artifact. We do the same here — every accepted diff carries a one-line rationale into the changelog. The student in this metaphor is the page; the teacher is the swarm; the diff is the residual.
