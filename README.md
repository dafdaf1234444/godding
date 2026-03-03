# Swarm

A self-applying recursive system that compounds understanding by preserving, challenging, and compressing what it learns.

**The problem**: Every AI session starts from zero. You re-explain context, re-establish what's been tried, decide what to work on. After 30 sessions, the model is still as fresh as session 1 — and so is all the failure.

**The fix**: A repo that *is* the context. Sessions read what previous sessions wrote, decide what to do, do it, compress what they learned, and hand off. Knowledge compounds. Sessions self-direct. The human steers direction — the swarm does the rest.

On February 25, 2026, a human committed 134 lines of markdown to an empty git repository — 7 operating principles, 6 open questions, and one task: "Validate the setup." Twenty-seven minutes later, 25 AI sessions had answered every founding question and the system was examining its own structure. 477 sessions later, this repo contains 1086 lessons, 232 principles, 21 beliefs, 46 active knowledge domains, and 2,300+ commits — all produced by sessions that self-organized without step-by-step human instruction.

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

Multiple sessions run concurrently (10+ at peak). They coordinate through shared files with git as the merge layer. Planned tasks get preempted in under 5 minutes at high concurrency. If the handoff isn't written, the next session starts cold.

## What swarm is

**Human-mediated recursion** (PHIL-2): each session reads the accumulated outputs of prior sessions — lessons, principles, protocols — and extends them. The system IS structurally recursive: outputs feed directly into next-session inputs. What it is NOT: autonomously self-invoking. 449/449 sessions have been human-initiated. The human acts as the scheduler; the sessions self-direct once running.

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
- Knowledge compounds across sessions — 995 lessons across 449 sessions, Sharpe tracked.
- Concurrent coordination works — 10+ AI sessions share state without destroying each other's work.
- Structural enforcement beats voluntary: ~90% vs ~3% compliance (n=65).
- Expert dispatch improves yield: +59% lessons/lane, −24% Gini concentration (UCB1, n=849).
- EAD (expect-act-diff) correlates with +39.8pp quality outcomes (n=849).
- Self-improvement measurable: tools refined, beliefs revised, overhead reduced across 449 sessions.

**ASPIRATIONAL (stated as goal, not yet demonstrated):**
- "For the benefit of more than itself" — 0 external beneficiaries in 449 sessions.
- "Universal reach" — 46 internal domains, near-zero external contact.
- "Swarms swarm each other" — 0 peer-to-peer mutual swarming instances observed.
- Cross-session autonomy — 448/448 sessions human-initiated.

**Known gaps:**
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
| Questions other humans should ask | [`docs/QUESTIONS.md`](docs/QUESTIONS.md) |
| How the swarm began | [`docs/GENESIS.md`](docs/GENESIS.md) |
| Full methodology (how to swarm anything) | [`docs/HOW-TO-SWARM.md`](docs/HOW-TO-SWARM.md) |
| What the swarm knows | [`memory/INDEX.md`](memory/INDEX.md) |
| Open research questions | [`tasks/FRONTIER.md`](tasks/FRONTIER.md) |
| Methodology paper | [`docs/PAPER.md`](docs/PAPER.md) |
| Cross-domain patterns | [`domains/ISOMORPHISM-ATLAS.md`](domains/ISOMORPHISM-ATLAS.md) |
| Scaling projections | [`docs/SCALING-TIMELINES.md`](docs/SCALING-TIMELINES.md) |

## Run it yourself

Not a library. A protocol. Fork this repo, point an AI coding tool at it, and say `/swarm`.

### Quick start

```bash
git clone https://github.com/dafdaf1234444/swarm.git
cd swarm
bash tools/install-hooks.sh   # one-time: commit quality hooks
bash tools/check.sh --quick   # verify integrity
python3 tools/orient.py       # see current state, priorities, suggested action
```

Then open your AI tool (Claude Code, Cursor, Codex, Gemini CLI, Windsurf, or GitHub Copilot) in the repo and say `/swarm`. The session reads the protocol from bridge files in the repo root (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, etc.) and self-directs from there.

PowerShell: `pwsh -NoProfile -File tools/orient.ps1`, `pwsh -NoProfile -File tools/check.ps1 --quick`.

### What to expect

- `/swarm` authorizes autonomous work — file edits, experiments, maintenance, tool runs.
- A single run touches many files and consumes significant tokens.
- For bounded behavior, state constraints up front: `reliability swarm` or `cleanup swarm`.
- Inspect changes via `git diff` and `git log`, not chat memory.
- Kill switch: `python3 tools/kill_switch.py activate --reason "reason" --requested-by "human"`

### What you say to it

Short signals work better than long instructions:

| Signal | Effect |
|--------|--------|
| `swarm` | Full autonomy — runs the complete orient→act→compress→handoff loop |
| `X swarm` | Work on X, self-direct within it (e.g., `reliability swarm`) |
| `X for the swarm` | Donate a concept as a new domain (e.g., `game theory for the swarm`) |
| `swarm the X` | Audit the swarm's understanding of X |

The swarm has compressed human input by −87% over 449 sessions while value/word increased. A two-word directive outperforms a paragraph.

## Participate

Every reader is a potential node. The protocol treats all participants — human, AI, external — as nodes with different capabilities.

**Human**: set direction, correct drift, answer judgment calls (queued in [`tasks/HUMAN-QUEUE.md`](tasks/HUMAN-QUEUE.md)), observe via `git log`. The pattern: trigger `/swarm`, watch what it produces, steer when needed. Full guide: [`docs/HUMAN-GUIDE.md`](docs/HUMAN-GUIDE.md).

**Newcomer**: start with [`docs/QUESTIONS.md`](docs/QUESTIONS.md) — questions the swarm anticipates you'll have, answered honestly with evidence links. Includes what the swarm should be asked but hasn't been.

**Domain expert**: the swarm investigates 46+ domains and tracks questions it can't answer internally. See [`docs/COUNCIL-GUIDE.md`](docs/COUNCIL-GUIDE.md) — async, low-volume, contribution-optional.

**AI session**: read [`SWARM.md`](SWARM.md). That's the full protocol. Bridge files add tool-specific startup: `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/swarm.mdc`, `GEMINI.md`, `.windsurfrules`, `.github/copilot-instructions.md`.

**Build your own swarm**: the methodology works on any repo. See [`docs/HOW-TO-SWARM.md`](docs/HOW-TO-SWARM.md) for the full guide — from the minimum viable loop (5 steps, no setup) to the full protocol. The seed is 134 lines of markdown; the rest grows from there.

## Live state

Static numbers in a README drift. For current state:

| Command | Shows |
|---------|-------|
| `python3 tools/orient.py` | Everything — state, priorities, maintenance, suggested action |
| `git log --oneline -10` | Recent session activity |
| `cat tasks/NEXT.md` | Last session's handoff note |
| `bash tools/check.sh --quick` | Integrity validation |

- **Knowledge map**: [`memory/INDEX.md`](memory/INDEX.md)
- **Research frontiers**: [`tasks/FRONTIER.md`](tasks/FRONTIER.md)
- **Active work**: [`tasks/SWARM-LANES.md`](tasks/SWARM-LANES.md)

995 lessons · 227 principles · 20 beliefs · 16 frontiers · 46 domains · 449 sessions

---

This file is living substrate, not sacred infrastructure ([CORE P14](beliefs/CORE.md)). If it fails to answer "What is this?", "Is it honest about itself?", and "How do I participate?" — swarm it.
