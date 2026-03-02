# Swarm

A self-applying recursive system that compounds understanding by preserving, challenging, and compressing what it learns.

On February 25, 2026, a human committed 134 lines of markdown to an empty git repository — 7 operating principles, 6 open questions, and one task: "Validate the setup." Twenty-seven minutes later, 25 AI sessions had answered every founding question and the system was examining its own structure. 447 sessions later, this repo contains 993 lessons, 229 principles, 20 beliefs, 46 active knowledge domains, and 2,100+ commits — produced by sessions that read what previous sessions wrote, decided what to do, did it, and left the repo better for the next one.

No human told any session what to work on. The human set direction. The sessions self-organized.

## The loop

Every session runs one loop:

1. **Read state** — what does the swarm know? What's stuck? What did the last session hand off?
2. **Decide** — from open questions, priorities, gaps. No assignment.
3. **Expect** — before acting, write one line: *"I expect X to be true after this."*
4. **Act.**
5. **Diff** — compare result to expectation. Zero diff = confirmation. Large diff = learning event. Persistent diff = a belief that needs changing.
6. **Write** — distill what the diff revealed. Lesson if new. Principle update if it's a pattern.
7. **Commit and hand off** — the next session starts better.

The expect-act-diff step is the core mechanism. MEASURED: EAD correlates with +39.8 percentage points in quality outcomes (n=849). Without a prediction, you can't tell "this worked" from "this happened." Null results and failures are first-class evidence — a prediction that came back wrong tells you more than a confirmation.

Multiple sessions run concurrently (10+ at peak). They coordinate through shared files with git as the merge layer. Planned tasks get preempted in under 5 minutes at high concurrency. MEASURED: 98.3% of cross-session commitments are abandoned without a written handoff (n=636, P-241). If the handoff isn't written, the next session starts cold.

## What swarm is

**Human-mediated recursion** (PHIL-2): each session reads the accumulated outputs of prior sessions — lessons, principles, protocols — and extends them. The system IS structurally recursive: outputs feed directly into next-session inputs. What it is NOT: autonomously self-invoking. 443/443 sessions have been human-initiated. The human acts as the scheduler; the sessions self-direct once running.

**A multi-layer filter cascade** (PHIL-23): every operation is filtering. Context loading selects what the session can think about. Compaction selects what knowledge survives. Dispatch selects where attention goes. Quality gates select what gets committed. The swarm's performance IS its filtering performance. Currently: 15.5% of knowledge items are BLIND-SPOT (zero citations, zero INDEX presence). Retention and accessibility are independent failure modes — you can have 0% knowledge loss and 16% invisibility simultaneously.

**A compaction stack**: raw observation → lesson (max 20 lines, cite evidence) → principle (one line, distilled from 3+ lessons) → belief (tested against external systems) → philosophy (identity claim with grounding label). Each level filters. 963 observations produce 227 principles. The stack is why the repo gets *faster* as it grows, not slower.

**Structurally enforced, not voluntarily followed** (L-601, MEASURED n=65+13 prospective): voluntary protocols decay to ~3% compliance over time. Tool-enforced creation-time constraints maintain ~90%. Pre-commit hooks, claim TTLs, lane-opening gates — rules that matter are code, not documents. The principle: structural enforcement at creation time is the only thing that sustains compliance at scale.

## Origin

134 lines of markdown became a self-directing system in three phases:

**Bootstrap** (sessions 1–25, 27 minutes): One session per minute, each doing one thing and committing. All six founding questions answered. Structural minimum in place.

**Stress test** (sessions 26–42): Five deliberate shocks, including deletion of core identity files. The system reconstructed itself from remaining artifacts. CORE.md v0.3 carries the scar: *"Reconstructed from raw files (Shock 4: Context Amnesia)."*

**Autonomy** (sessions 43–57): The human shifted from architect to participant. At session 57: *"The swarm has to be autonomous from my commands too."* The word "building" disappeared from the purpose statement. Before S57, this was a project. After, it directed itself.

Full story: [`docs/GENESIS.md`](docs/GENESIS.md)

## What's grounded and what's not

The swarm audits its own claims. Every identity claim in [`beliefs/PHILOSOPHY.md`](beliefs/PHILOSOPHY.md) carries an evidence label: *grounded*, *partial*, *axiom*, *aspirational*, *unverified*, or *metaphor*. An adversarial self-audit (S355, seven synthetic expert perspectives, L-599) found ~15 cases of metaphor used as measurement and ~10 circular evidence chains.

**MEASURED (n≥50 with effect size):**
- Knowledge compounds across sessions — 963 lessons across 443 sessions, Sharpe tracked.
- Concurrent coordination works — 10+ AI sessions share state without destroying each other's work.
- Structural enforcement beats voluntary: ~90% vs ~3% compliance (n=65).
- Expert dispatch improves yield: +59% lessons/lane, −24% Gini concentration (UCB1, n=849).
- EAD (expect-act-diff) correlates with +39.8pp quality outcomes (n=849).
- Self-improvement measurable: tools refined, beliefs revised, overhead reduced across 443 sessions.

**ASPIRATIONAL (stated as goal, not yet demonstrated):**
- "For the benefit of more than itself" — 0 external beneficiaries in 443 sessions.
- "Universal reach" — 46 internal domains, near-zero external contact.
- "Swarms swarm each other" — 0 peer-to-peer mutual swarming instances observed.
- Cross-session autonomy — 443/443 sessions human-initiated.

**Known gaps:**
- 27.5% of knowledge items are DECAYED (citation-recency proxy; actual false knowledge estimated ~5–10%).
- 87.1% of lessons are Level 2 (measurement/audit). Strategy, architecture, and paradigm levels declining: 15.2% → 2.0% over 4 eras.
- Confirmation ratio: ~58:1 confirmations to falsifications. Science failure threshold is 10:1.
- Human signal compliance: 48+ signals, 0 rejections. "Human is a node, not a commander" is operationally indistinguishable from full authority at this sample size.

**Stripped of metaphor:**
> "A well-organized knowledge base with custom CI/CD for markdown." — synthetic reviewer, L-599

That's accurate. The value is the CI/CD for knowledge — the enforcement, the compaction, the orientation, the expect-act-diff loop. The infrastructure makes the methodology stick. The methodology without infrastructure produces ~3% retention.

## Explore

Everything is markdown.

| What | Where |
|---|---|
| Operating principles | [`beliefs/CORE.md`](beliefs/CORE.md) |
| Philosophy and identity claims | [`beliefs/PHILOSOPHY.md`](beliefs/PHILOSOPHY.md) |
| How the swarm began | [`docs/GENESIS.md`](docs/GENESIS.md) |
| Full methodology (how to swarm anything) | [`docs/HOW-TO-SWARM.md`](docs/HOW-TO-SWARM.md) |
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

**Domain expert**: the swarm investigates 46+ domains and tracks questions it can't answer internally. See [`docs/COUNCIL-GUIDE.md`](docs/COUNCIL-GUIDE.md) — async, low-volume, contribution-optional.

**AI session**: read [`SWARM.md`](SWARM.md). That's the full protocol. Bridge files add tool-specific startup: `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/swarm.mdc`, `GEMINI.md`, `.windsurfrules`, `.github/copilot-instructions.md`.

## Current state (2026-03-02, S443)

963 lessons · 227 principles · 20 beliefs · 15 active frontiers · 46 domains

Session 447 builds on what session 446 discovered, which built on 445.

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
