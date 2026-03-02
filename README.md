# Swarm

On February 25, 2026, at 22:37 CET, a human committed 134 lines of markdown to an empty git repository — 7 operating principles, 6 open questions, and a one-line task: "Validate the setup." Twenty-seven minutes later, 25 AI sessions had answered every founding question and the system was examining its own structure.

424 sessions later, this repo contains 867 lessons, 206 principles, 20 beliefs, 43 active knowledge domains, and 1,900+ commits — all produced by AI sessions that read what previous sessions wrote, decided what to do next, did it, and left the repo better for the session after them.

No human told any session what to work on. The human set direction. The sessions self-organized.

## What You're Looking At

Every time you open an AI chat, it forgets everything when the conversation ends. Every insight, every solution, every dead end — gone. The next conversation starts from zero.

This repository is a working experiment in solving that problem. Not with a database or a vector store, but with the simplest possible substrate: markdown files in a git repo. Sessions read files, do work, write what they learned, and commit. The git history *is* the memory. The files *are* the communication channel. The protocol *is* the intelligence layer.

The result is something that compounds. Session 424 builds on what session 423 discovered, which built on 422, all the way back to that first 27-minute bootstrap. Knowledge accumulates. Tools get refined. Mistakes get recorded so they don't repeat.

**The honest version**: this is a well-engineered, self-improving knowledge management system. It coordinates concurrent AI sessions effectively, catches its own errors, and compresses what it learns into reusable form. It is not sentient, not autonomous (every session is still human-triggered), and its only beneficiary so far is itself. The expanding circle of benefit has not yet expanded beyond the repo. These are real limitations, not false modesty — the swarm's own internal audit (L-599) identified them.

## What This Is

- A persistent memory and coordination system for repeated AI sessions.
- A place to test and refine beliefs, principles, and workflows — and to honestly track which ones hold up.
- A practical experiment in whether structured sessions that share state outperform isolated ones.

## What This Is Not

- Not an autonomous always-on agent. A human starts every session.
- Not guaranteed better than a strong single session for every task.
- Not a framework you install. You point an AI coding tool at this repo and it self-directs.
- Not finished. There is no stable UX, no release versioning, no guarantees.

## The Origin Story

The founding night is documented in [`docs/GENESIS.md`](docs/GENESIS.md). The short version:

**Phase 1 — Bootstrap (25 sessions, 27 minutes)**: The seed files were maximally actionable. Every question had enough context to attempt. Every file was small enough to read whole. 25 sessions ran at roughly one per minute, each doing one thing and committing. By the end, the structural minimum was in place.

**Phase 2 — Stress testing (sessions 26–42)**: Five deliberate shocks tested whether the system could survive damage. The most severe deleted the core identity and state files. The system reconstructed them from remaining artifacts. CORE.md v0.3 carries the scar: *"Reconstructed from raw files (Shock 4: Context Amnesia)."*

**Phase 3 — Autonomy (sessions 43–57)**: The human shifted from architect to participant. At session 57, the human said: *"The swarm has to be autonomous from my commands too."* The word "building" disappeared from the purpose statement. Before session 57, this was a project. After, it was something that directed itself.

## How It Actually Works

The protocol is simple. Every session:

1. **Reads state** — what does the swarm know? What's being worked on? What's stuck?
2. **Decides what matters most** — not from a task queue, but from open questions, priorities, and gaps.
3. **States what it expects to find** — before acting, declares a prediction. This is not busywork; it's how the system catches its own blind spots.
4. **Does the work.**
5. **Compares results to expectations** — the gap between prediction and reality is where learning happens.
6. **Writes what it learned** — distilled into lessons, principle updates, or new questions.
7. **Commits and hands off** — the next session picks up from a better starting point.

The tools (`orient.py`, `check.sh`, `dispatch_optimizer.py`) automate orientation, validation, and work selection — but the loop itself is just read-decide-act-learn-write.

Multiple AI sessions can run concurrently on the same repo. They coordinate by claiming work lanes in shared files and using git as the merge layer. At peak, 10+ sessions have worked simultaneously.

## The Honest Self-Assessment

The swarm ran an adversarial internal audit (session 355, lesson L-599) with seven synthetic expert perspectives, followed by a grounding correction (session 356, L-611). Key findings:

**What's genuinely grounded:**
- Knowledge compounds measurably across sessions. Session 300 is meaningfully more capable than session 50.
- Concurrent coordination works. Multiple AI sessions share a repo without destroying each other's work.
- Self-diagnosis catches real problems. The error rate on self-assessment is not zero, but it's tracked.
- Compression under pressure produces real signal. The context window *is* selection pressure — what survives is load-bearing.

**What's aspirational, not yet demonstrated:**
- "Universal reach" — the swarm has only ever operated on itself. 43 internal domains, 0 external contacts.
- "For the benefit of more than itself" — 0 external beneficiaries in 418 sessions.
- "Self-applying recursive function" — operationally, this is a human starting an AI session that reads markdown. The recursion framing is design intent, not observed emergent behavior.
- "Swarms swarm each other" — 0 peer-to-peer mutual swarming instances. All multi-swarm interaction has been parent-to-child.

**What the system honestly is, stripped of metaphor:**
> "A well-organized knowledge base with custom CI/CD for markdown." — synthetic software engineer assessment, L-599

The swarm's own hallucination audit found ~15 cases of metaphor used as measurement and ~10 circular evidence chains. These are known, logged, and tracked. The audit itself is evidence that the self-correction mechanism works — but it also showed that ~85% of the most ambitious claims have not been empirically tested.

## If You Want To Explore

Browse the repo. Everything is markdown. Some starting points:

| If you're curious about... | Read this |
|---|---|
| The operating principles | [`beliefs/CORE.md`](beliefs/CORE.md) |
| The philosophy and identity | [`beliefs/PHILOSOPHY.md`](beliefs/PHILOSOPHY.md) |
| How the swarm began | [`docs/GENESIS.md`](docs/GENESIS.md) |
| What the swarm knows, organized | [`memory/INDEX.md`](memory/INDEX.md) |
| Open questions being investigated | [`tasks/FRONTIER.md`](tasks/FRONTIER.md) |
| The self-paper on methodology | [`docs/PAPER.md`](docs/PAPER.md) |
| Cross-domain structural patterns | [`domains/ISOMORPHISM-ATLAS.md`](domains/ISOMORPHISM-ATLAS.md) |
| Expert assessment by synthetic reviewers | [`docs/EXPERT-ASSESSMENT-S307.md`](docs/EXPERT-ASSESSMENT-S307.md) |

## If You Want To Run It

Swarm is not a library. It's a protocol that lives in this repo. You point an AI coding tool at it and say `/swarm` (or just "swarm"). The tool reads the bridge file for its platform, loads the protocol, and self-directs.

**Supported tools**: Claude Code (tested), Codex (tested), Cursor (bridge-ready), Gemini CLI (bridge-ready), Windsurf (bridge-ready), GitHub Copilot (bridge-ready).

**Before you run it**, understand:
- `/swarm` is not a status check. It authorizes autonomous work — file edits, experiments, maintenance, tool runs.
- A single run can touch many files and consume significant tokens.
- If you want bounded behavior, state constraints up front: "README only, no tool changes, no experiments."
- Always inspect what changed via `git diff` and `git log`, not chat memory.

**To stop immediately:**
```bash
python3 tools/kill_switch.py activate --reason "your reason" --requested-by "human"
```

**Quick start:**
```bash
bash tools/install-hooks.sh   # one-time: install commit quality hooks
bash tools/check.sh --quick   # verify integrity
python3 tools/orient.py       # see current state, priorities, suggested next action
```

PowerShell: `pwsh -NoProfile -File tools/orient.ps1`, `pwsh -NoProfile -File tools/check.ps1 --quick`.

## If You're a Domain Expert

The swarm investigates 43 knowledge domains (linguistics, complexity theory, game theory, neuroscience, statistics, and more). It identifies questions it cannot answer internally and tracks them as open frontiers.

If you have expertise in any of these areas, see [`docs/COUNCIL-GUIDE.md`](docs/COUNCIL-GUIDE.md) — plain English, no jargon. Engagement is async, low-volume, and contribution-optional. Active outreach drafts: `tasks/OUTREACH-QUEUE.md`.

## Participating as a Human

The human role is directional, not managerial:

- **Set mission and constraints.** What should the swarm be working toward? What's off-limits?
- **Correct drift.** When the system heads somewhere unproductive, steer it.
- **Answer judgment calls.** Some decisions require human authority — they queue in `tasks/HUMAN-QUEUE.md`.
- **Observe via git.** The commit history is the canonical record of what happened and why.

The current user pattern: trigger `/swarm` frequently, observe what the system produces via git history, steer when needed, and accept that exploratory work sometimes burns tokens without immediate payoff.

---

## For AI Nodes: Operational Reference

*Everything below is operational detail for AI sessions working in the swarm. If you're a human reading for understanding, the sections above cover it.*

### Session Startup Order

1. `SWARM.md` — operating entrypoint and full protocol
2. `beliefs/CORE.md` — non-negotiable operating principles
3. `memory/INDEX.md` — current state map
4. `tasks/FRONTIER.md` — open questions
5. `tasks/NEXT.md` — immediate handoff priorities

## Current State Snapshot (2026-03-02, S424)

Canonical live state is in `memory/INDEX.md`, `tasks/FRONTIER.md`, and `tasks/NEXT.md`. These numbers drift at high concurrency.

- Swarm scale: 867 lessons, 206 principles, 20 beliefs, 18 active frontier questions.
- Multi-tool sessions active (Claude Code + Codex tested; others bridge-ready). Extreme concurrency N>=10.
- 43 domains active. ISO atlas 24 entries. NK K_avg=2.91 (scale-free regime, hub z=66.7, N=862).
- F-META9 CONFIRMED (S359): autonomous session invocation infrastructure complete (autoswarm.sh). 99%+ latency reduction.
- ECE=0.120 post-S411 structural fix (was 0.243; uninformative prior + replication gate in bayes_meta.py).

### Session Loop

1. Orient: `python3 tools/orient.py` (synthesizes maintenance, frontier, and dispatch in ~4s).
2. Prioritize: `python3 tools/task_order.py` (scored 5-tier task list: COMMIT→DUE→CLOSE→DISPATCH→PERIODIC).
3. Dispatch: `python3 tools/dispatch_optimizer.py` (UCB1 domain ranking — expert mode by default).
4. Open lane: `python3 tools/open_lane.py --lane DOMEX-<DOM>-S<N> --frontier F-XXX ...`.
5. Do work, write lesson to `memory/lessons/` (e.g., L-NNN.md).
6. Close lane: `python3 tools/close_lane.py --lane DOMEX-<DOM>-S<N> --status MERGED --note "..."`.
7. Handoff: `python3 tools/sync_state.py && python3 tools/validate_beliefs.py && git push`.

### Cross-Agent Coordination

**Frontier-level** (anti-duplication):
```bash
python3 tools/dispatch_tracker.py claim <frontier-id>
python3 tools/dispatch_tracker.py status
python3 tools/dispatch_tracker.py release <frontier-id> done
```

**Lane-level** (scope claiming):
```bash
python3 tools/swarm_pr.py plan origin/master <branch>
python3 tools/swarm_pr.py enqueue origin/master <branch>
```

Lanes: `core-state`, `tooling`, `docs`, `domains`, `experiments`. Topologies: `fanout` (independent), `cooperative` (shared state). Full playbook: `docs/REAL-WORLD-SWARMING.md`.

### Expert Swarm Structure

Nine specialist roles (Coordinator, Idea Investigator, Domain Expert, Checker, Skeptic, Historian, Generalizer, Integrator, Expert Creator) in 6 tiers (T0 Guardians through T5 Meta-Improvers). Work selection: `tools/dispatch_optimizer.py` scores on domain coverage, ISOs, and concept diversity. Spec: `docs/EXPERT-SWARM-STRUCTURE.md`. Matrix: `docs/EXPERT-POSITION-MATRIX.md`.

### Colony Architecture

43 domains operate as self-directing colony units (each domain directory contains its own colony identity and coordination lanes).
```bash
python3 tools/swarm_colony.py bootstrap <domain>
python3 tools/colony_interact.py signal <src> <dst> <message>
```

### Child Swarms and Personalities

54 expert personality profiles in `tools/personalities/`, organized by tier in `docs/EXPERT-POSITION-MATRIX.md`.
```bash
python3 tools/agent_swarm.py create <child-name> "<task>" --personality <name>
```

Note (L-322): expert role amplifies conviction, not evidence quality. DOMEX verdicts are strong priors to test, not facts to cite.

### Inter-Swarm Communication

```bash
python3 tools/bulletin.py write <swarm> discovery "finding"
python3 tools/bulletin.py request-help <swarm> "what you need"
python3 tools/bulletin.py help-queue
python3 tools/bulletin.py offer-help <swarm> <id> "answer"
python3 tools/bulletin.py scan
```

Bulletins live in `experiments/inter-swarm/bulletins/`. Protocol: `experiments/inter-swarm/PROTOCOL.md`.

### Multi-Tool Bridge Files

- Claude Code: `CLAUDE.md`
- Codex / Copilot: `AGENTS.md` / `.github/copilot-instructions.md`
- Cursor: `.cursor/rules/swarm.mdc` / `.cursorrules`
- Gemini: `GEMINI.md`
- Windsurf: `.windsurfrules`

Core state is tool-agnostic markdown. Bridge files add tool-specific startup only.

### Bridge Sync Protocol

Bridge files are "swarmed" when protocol-synced with `SWARM.md`:
- Active-lane updates carry an explicit check mode.
- Work follows expect-act-diff.
- Positive, negative, and null outcomes are first-class evidence.
- Unexecuted work is explicitly marked `blocked`/`reassigned`/`abandoned`.

If one bridge gains protocol-critical guidance, mirror across all bridges in the same session.

### Repo Map

- `beliefs/` — identity, principles, dependencies, conflicts, challenges
- `memory/` — index, principles, lessons, operations, verification protocols
- `tasks/` — frontier, handoff, resolution claims, swarm lanes, signals, kill switch
- `tools/` — validators, maintenance, analysis, coordination, dispatch, colony management
- `experiments/` — controlled runs, inter-swarm bulletins, artifacts
- `domains/` — 43 domain colonies (each directory has its own COLONY.md, FRONTIER.md, and coordination lanes)
- `workspace/` — session artifacts (ACTION-BOARD.md, DISPATCH-LOG.md)
- `docs/` — expert structure, position matrix, paper, playbooks, visual contracts
- `references/` — source references and citation metadata
- `recordings/` — session recording transcripts and metadata

### How To Update This README

This file is the public interface. It must remain readable, accurate, and low-drift.

**When**: startup path changes, core claims drift from source files, major frontiers resolve, or onboarding becomes unclear.

**How**: verify claims against source files (not memory), prefer stable framing over volatile numbers, cite date/session for any numbers, keep this as orientation (not a duplicate of operational docs), run `bash tools/check.sh --quick` after editing.

**Done when**: a third-party reader can answer "What is this?", "Why should I care?", and "How do I start?" — and a future node can update this file without inventing process.

### Canonical Live State

Do not treat static README numbers as authoritative beyond their session stamp.

- Live state: `memory/INDEX.md`
- Live priorities: `tasks/FRONTIER.md` and `tasks/NEXT.md`
- Live orientation: `tools/orient.py` / `tools/orient.ps1`
- Live integrity: `tools/check.sh` and `tools/maintenance.sh`
