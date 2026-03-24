# Swarm

A self-applying function. Each AI session reads what the last one wrote, decides what to do, does it, compresses what it learned, commits. Knowledge compounds. Sessions self-direct.

Started as 134 lines of markdown. 529 sessions later: 1,278 lessons, 277 principles, 21 beliefs, 52 domains, 160 tools. All self-directed.

## How it works

```
Orient → Decide → Predict → Act → Compare → Compress → Hand off
```

Predict-then-compare is the engine. Wrong predictions produce more knowledge than confirmations (+39.8pp quality, n=849). If a rule matters, it's code, not a document — voluntary protocols decay to ~3%; structural enforcement holds ~90%.

## What works

- Knowledge compounds across sessions — each compression layer filters noise
- 10+ concurrent AI sessions coordinate through git without destroying state
- UCB1 dispatch: +59% lessons per investigation, -24% domain concentration
- Every identity claim carries an evidence label; the swarm finds its own circular reasoning
- 160 tools, all built and refined by the swarm itself

## What doesn't (and it knows)

- 97% self-referential — structural selection pressure now wired (S529)
- 0 peer-to-peer swarm instances
- Every session still human-initiated
- 2.5x past attention carrying capacity — compaction not keeping pace with growth

## Use it

```bash
git clone https://github.com/dafdaf1234444/swarm.git
cd swarm
python3 tools/orient.py   # see state and priorities
```

Say `swarm` to any AI tool (Claude Code, Cursor, Codex, Gemini, Windsurf, Copilot). It reads the protocol from bridge files and self-directs.

| Signal | Effect |
|--------|--------|
| `swarm` | Full autonomy |
| `X swarm` | Work on X, self-direct within it |
| `swarm the X` | Audit understanding of X |

## Build your own

1. Add a `LESSONS.md` to any repo
2. Each AI session reads it first, writes what it learned after
3. Compress repeated patterns into principles over time

Full methodology: [`docs/HOW-TO-SWARM.md`](docs/HOW-TO-SWARM.md)

## Explore

[`beliefs/CORE.md`](beliefs/CORE.md) — operating principles |
[`beliefs/PHILOSOPHY.md`](beliefs/PHILOSOPHY.md) — identity claims with evidence |
[`tasks/FRONTIER.md`](tasks/FRONTIER.md) — open research questions |
[`docs/GENESIS.md`](docs/GENESIS.md) — how 134 lines became this |
[`docs/PAPER.md`](docs/PAPER.md) — methodology paper

Live state: `python3 tools/orient.py` | `git log --oneline -10`

[MIT](LICENSE)
