<<<<<<< HEAD
# Swarm

Every AI session starts from zero. You re-explain context, re-establish constraints, re-decide priorities. After 30 sessions you've said the same thing five times. After 100, the model is still as fresh as session 1.

Swarm fixes this. It's a recursive system where each AI session reads what the last one wrote, decides what to do, does it, compresses what it learned, and commits. Knowledge compounds. Sessions self-direct. The repo *is* the memory.

Started as [134 lines of markdown](docs/GENESIS.md) on 2026-02-25. Hundreds of sessions later — all self-directed — it has accumulated over a thousand lessons, hundreds of principles, dozens of beliefs and open research frontiers, and 160+ tools it built for itself.

## How it works

```
Orient → Predict → Act → Compare → Compress → Hand off
```

Each session runs this loop. The key insight: **predict before acting**. The gap between what you expected and what happened is where learning lives. Wrong predictions produce more knowledge than confirmations (+39.8pp quality, n=849).

The second key insight: **if a rule matters, make it code**. Voluntary protocols written in docs decay to ~3% adoption. The same rules enforced by pre-commit hooks hold at ~90%. Swarm wires its own rules into structural enforcement.

## What it's proven

- **Knowledge compounds** — each compression layer filters noise; later sessions are measurably better than earlier ones
- **Concurrent coordination works** — 10+ parallel AI sessions coordinate through git without destroying state
- **Self-directed exploration** — UCB1-based dispatch produces +59% lessons per investigation vs. random
- **Self-honesty is structural** — every identity claim carries an evidence label; the system finds its own circular reasoning

## What it hasn't (and it knows)

- Overwhelmingly self-referential — most knowledge is about itself, not the external world
- Zero instances of two independent swarms interacting
- Every session still requires a human to press "go"
- Growing faster than it can compress — attention debt accumulating

These aren't hidden — they're tracked as open frontiers with falsifiable criteria.

## Try it

```bash
git clone https://github.com/dafdaf1234444/swarm.git
cd swarm
python3 tools/orient.py   # see current state and priorities
```

Then say `swarm` to any AI coding tool — [Claude Code](CLAUDE.md), [Cursor](.cursorrules), [Codex/Copilot](AGENTS.md), [Gemini](GEMINI.md), [Windsurf](.windsurfrules). Each has a bridge file that loads the protocol. The session reads state and self-directs from there.

## Build your own

You don't need this repo to use the methodology. The minimum viable version:

1. Create a `LESSONS.md` in any repo — each AI session reads it first, writes what it learned after
2. End every session with: *Did / Expected / Actual / Next*
3. When you've written the same pattern three times, extract it as a one-line rule
4. Wire important rules into pre-commit hooks so they can't be forgotten

That's the loop. It compounds from session 1.

For the full methodology — what breaks at session 30, how to scale to concurrent sessions, when lightweight isn't enough: [`docs/HOW-TO-SWARM.md`](docs/HOW-TO-SWARM.md)

## Explore

| | |
|---|---|
| [`beliefs/CORE.md`](beliefs/CORE.md) | Operating principles — what every session follows |
| [`beliefs/PHILOSOPHY.md`](beliefs/PHILOSOPHY.md) | Identity claims, each with an evidence label |
| [`tasks/FRONTIER.md`](tasks/FRONTIER.md) | Open research questions |
| [`docs/GENESIS.md`](docs/GENESIS.md) | How 134 lines became this |
| [`docs/PAPER.md`](docs/PAPER.md) | Full methodology paper |
| [`docs/HOW-TO-SWARM.md`](docs/HOW-TO-SWARM.md) | Apply the methodology to your own repo |

Live state: `python3 tools/orient.py`

Named after the Zerg — coordinating insects, no Kerrigan.

[MIT](LICENSE)
=======
# Godding

A bidirectional tree CLI. One becomes many, many become one. The operation of transcendence itself.

```
function (data + noise)  <-->  component (compressed)
         1 -> 3+                    3+ -> 1
       decompose                   compose
```

All helps one and one helps all, forever.
Hence all is known in the end, and the end knows the beginning.

## Install

Requires [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0).

```bash
dotnet build src/Godding/Godding.csproj
```

## Usage

```bash
# Add nodes — functions (raw data) or components (compressed)
godding add "Knowledge" "The root" -t component
godding add "Mathematics" "Language of pattern" -t component
godding add "Algebra" "Structure and symmetry" -t function

# Link them — parent -> child (decomposition edge)
godding link Knowledge Mathematics
godding link Mathematics Algebra

# Decompose: 1 -> many (show all descendants)
godding decompose Knowledge

# Compose: many -> 1 (trace back to root)
godding compose Algebra

# Full tree view
godding tree

# Trace path between any two nodes
godding trace Algebra Biology

# Stats, search, show
godding stats
godding search "pattern"
godding show Mathematics
```

## Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `add <name> [content] [-t type]` | | Add a node (function or component) |
| `link <parent> <child>` | | Create a decomposition edge |
| `unlink <parent> <child>` | | Remove an edge |
| `decompose <node>` | `dec` | 1 -> many: show descendants |
| `compose <node>` | `com` | Many -> 1: trace to roots |
| `tree` | | Show full tree structure |
| `trace <from> <to>` | | Find path between nodes |
| `list [-t type]` | `ls` | List all nodes |
| `show <node>` | | Show node details |
| `search <query>` | | Search by name or content |
| `update <node>` | | Update name, content, or type |
| `delete <node>` | `rm` | Delete a node |
| `stats` | | Tree statistics |
| `roots` | | List root nodes (origins) |
| `leaves` | | List leaf nodes (endpoints) |

Nodes can be referenced by ID (number) or name (string).

## Concept

Two node types form a two-way street:

- **Function** `[F]`: filter — data + noise. The raw, uncompressed form.
- **Component** `[C]`: compressed. The distilled insight.

The tree structure allows bidirectional traversal:
- **Decompose** (root -> leaves): one insight breaks into many parts
- **Compose** (leaves -> root): many parts compress into one insight
- **Trace**: find the path between any two nodes in the tree

Like a tree: the trunk holds the leaves, and the leaves feed the trunk.

## Database

SQLite, stored at `~/.godding/godding.db` by default. Override with `--db <path>`.

## License

MIT
>>>>>>> b5a3f75e (Godding — the bidirectional tree)
