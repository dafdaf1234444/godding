# Modes Base

Shared baseline for all mode docs (`modes/audit.md`, `modes/build.md`, `modes/repair.md`, `modes/research.md`).

**Two mode types** — orthogonal, both apply:
- **Operational mode** (these files): what TYPE of work — audit vs build vs repair vs research. Load one at session start.
- **Check mode** (SWARM.md Self-Check Loop): what ANGLE you apply — objective, historian, verification, coordination, assumption. Choose per action.

## Required Protocol (shared by all modes — do not duplicate in individual mode files)

- Choose and log `check_mode` (`objective`, `historian`, `verification`, `coordination`, or `assumption`).
- Apply expect-act-diff: declare expectation before acting, log diff after. Record in `tasks/NEXT.md` or `tasks/SWARM-LANES.md`. See `memory/EXPECT.md`.
- **Belief throttle**: If >60% of beliefs are `theorized`, test one before writing new build code or adding new beliefs. Design a binary pass/fail test.
- Include one meta-swarm reflection (process friction/improvement) in session notes.
- Run quick integrity before handoff: `bash tools/check.sh --quick` (or PowerShell equivalent).

## Coordination Contract

For **dispatch lanes** in `tasks/SWARM-LANES.md`, `Etc` must include:

- `setup`, `focus`, `available`, `blocked`, `next_step`, `human_open_item`
- `expect` — predicted outcome (declare before acting)
- `actual` — what happened (required at MERGED closure)
- `diff` — expectation vs reality gap (required at MERGED closure)
- `artifact` — committed deliverable path (experiment JSON, tool, lesson)
- `personality` — role personality (domain-expert, council-expert, etc.)

For **coordinator lanes**, additionally include:

- `intent` — what this lane is coordinating
- `progress` — current completion status

For **domain-focused lanes** (`focus=domains/<domain>` or scope under `domains/`):

- `domain_sync` — queued|syncing|synced|stale|n/a
- `memory_target` — domain memory path being synchronized

Use explicit values even for no-op state (`blocked=none`, `human_open_item=none`).
Source of truth: `tools/open_lane.py` for creation enforcement, `tools/close_lane.py` for EAD closure.
