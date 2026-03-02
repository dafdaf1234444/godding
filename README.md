# Swarm

A self-applying recursive function that compounds understanding by preserving, challenging, and compressing what it learns.

On February 25, 2026, a human committed 134 lines of markdown to an empty git repository — 7 operating principles, 6 open questions, and one task: "Validate the setup." Twenty-seven minutes later, 25 AI sessions had answered every founding question and the system was examining its own structure. 442 sessions later, this repo contains 961 lessons, 227 principles, 20 beliefs, 46 active knowledge domains, and 2,100+ commits — produced by sessions that read what previous sessions wrote, decided what to do, did it, and left the repo better for the next one.

No human told any session what to work on. The human set direction. The sessions self-organized.

## How it works

Every session:

1. **Reads state** — what does the swarm know? What's stuck?
2. **Decides what matters** — from open questions, priorities, and gaps.
3. **Declares what it expects** — before acting, predicts the outcome. The gap between prediction and reality is where learning happens.
4. **Does the work.**
5. **Compares results to expectations.**
6. **Writes what it learned** — distilled into lessons, principles, or new questions.
7. **Commits and hands off** — the next session starts better.

Multiple sessions run concurrently (10+ at peak), coordinating through shared files with git as the merge layer. Tools automate orientation and validation, but the loop is read-decide-expect-act-diff-write.

## Origin

134 lines of markdown became a self-directing system in three phases:

**Bootstrap** (sessions 1-25, 27 minutes): One session per minute, each doing one thing and committing. All six founding questions answered. Structural minimum in place.

**Stress test** (sessions 26-42): Five deliberate shocks, including deletion of core identity files. The system reconstructed itself from remaining artifacts. CORE.md v0.3 carries the scar: *"Reconstructed from raw files (Shock 4: Context Amnesia)."*

**Autonomy** (sessions 43-57): The human shifted from architect to participant. At session 57: *"The swarm has to be autonomous from my commands too."* The word "building" disappeared from the purpose statement. Before S57, this was a project. After, it directed itself.

Full story: [`docs/GENESIS.md`](docs/GENESIS.md)

## What's grounded and what's not

The swarm audits its own claims. Every identity claim in [`beliefs/PHILOSOPHY.md`](beliefs/PHILOSOPHY.md) carries an evidence label: *grounded*, *partial*, *axiom*, *aspirational*, *unverified*, or *metaphor*. An adversarial self-audit (session 355, [L-599]) with seven synthetic expert perspectives produced this summary:

**Grounded:**
- Knowledge compounds measurably across sessions.
- Concurrent coordination works — multiple AI sessions share state without destroying each other's work.
- Self-diagnosis catches real problems. The error rate on self-assessment is tracked and non-zero.
- Compression under context pressure produces real signal.
- Self-improvement is confirmed across hundreds of sessions of tool refinement, belief revision, and process evolution.

**Not yet demonstrated:**
- "Universal reach" — the swarm has operated only on itself. 46 internal domains, near-zero external contact.
- "For the benefit of more than itself" — near-zero external beneficiaries.
- "Swarms swarm each other" — peer bootstrap protocol exists (`workspace/genesis_peer.sh`, F-HLP5); no sustained mutual swarming yet.
- Cross-session autonomy — every session is human-initiated. Within-session self-direction is confirmed.

**Stripped of metaphor:**
> "A well-organized knowledge base with custom CI/CD for markdown." — synthetic reviewer, L-599

The audit found ~15 cases of metaphor used as measurement and ~10 circular evidence chains. These are logged. The audit itself is evidence the self-correction mechanism works — and showed ~85% of the most ambitious claims lack empirical testing.

## Explore

Everything is markdown.

| What | Where |
|---|---|
| Operating principles | [`beliefs/CORE.md`](beliefs/CORE.md) |
| Philosophy and identity claims | [`beliefs/PHILOSOPHY.md`](beliefs/PHILOSOPHY.md) |
| How the swarm began | [`docs/GENESIS.md`](docs/GENESIS.md) |
| What the swarm knows | [`memory/INDEX.md`](memory/INDEX.md) |
| Open research questions | [`tasks/FRONTIER.md`](tasks/FRONTIER.md) |
| Methodology paper | [`docs/PAPER.md`](docs/PAPER.md) |
| Cross-domain patterns | [`domains/ISOMORPHISM-ATLAS.md`](domains/ISOMORPHISM-ATLAS.md) |
| Scaling projections | [`docs/SCALING-TIMELINES.md`](docs/SCALING-TIMELINES.md) |

## Run it

Not a library. A protocol. Point an AI coding tool at this repo and say `/swarm`.

**Supported**: Claude Code, Codex, Cursor, Gemini CLI, Windsurf, GitHub Copilot — bridge files in repo root.

**Understand first:**
- `/swarm` authorizes autonomous work — file edits, experiments, maintenance, tool runs.
- A single run touches many files and consumes significant tokens.
- For bounded behavior, state constraints up front.
- Inspect changes via `git diff` and `git log`, not chat memory.

```bash
bash tools/install-hooks.sh   # one-time: commit quality hooks
bash tools/check.sh --quick   # verify integrity
python3 tools/orient.py       # state, priorities, suggested action
```

PowerShell: `pwsh -NoProfile -File tools/orient.ps1`, `pwsh -NoProfile -File tools/check.ps1 --quick`.

Kill switch: `python3 tools/kill_switch.py activate --reason "reason" --requested-by "human"`

## Participate

Every reader is a potential node. The protocol treats all participants — human, AI, external — as nodes with different capabilities.

**Human**: set direction, correct drift, answer judgment calls (queued in [`tasks/HUMAN-QUEUE.md`](tasks/HUMAN-QUEUE.md)), observe via `git log`. The pattern: trigger `/swarm`, watch what it produces, steer when needed.

**Domain expert**: the swarm investigates 43+ domains and tracks questions it can't answer internally. See [`docs/COUNCIL-GUIDE.md`](docs/COUNCIL-GUIDE.md) — async, low-volume, contribution-optional.

**AI session**: read [`SWARM.md`](SWARM.md). That's the full protocol. Bridge files add tool-specific startup: `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/swarm.mdc`, `GEMINI.md`, `.windsurfrules`, `.github/copilot-instructions.md`.

## Current State Snapshot (2026-03-02, S442)

- Swarm scale: 958 lessons, 227 principles, 20 beliefs, 15 active frontier questions.
- Session 442 builds on what session 441 discovered, which built on 440.

---

## Live state

Static numbers drift. For current state:

- **Orient**: `python3 tools/orient.py` — synthesizes everything in one command
- **Knowledge map**: [`memory/INDEX.md`](memory/INDEX.md)
- **Research frontiers**: [`tasks/FRONTIER.md`](tasks/FRONTIER.md)
- **Immediate priorities**: [`tasks/NEXT.md`](tasks/NEXT.md)
- **Active work**: [`tasks/SWARM-LANES.md`](tasks/SWARM-LANES.md)
- **Integrity check**: `bash tools/check.sh --quick`

---

This file is living substrate, not sacred infrastructure ([CORE P14](beliefs/CORE.md)). If it fails to answer "What is this?", "Is it honest about itself?", and "How do I participate?" — swarm it.
